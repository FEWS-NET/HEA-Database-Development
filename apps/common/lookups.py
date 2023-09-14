"""
Lookup classes that support data ingestion by matching data in a Pandas DataFrame against
reference data in Django Models.
"""
from abc import ABC

import pandas as pd

from .models import (
    ClassifiedProduct,
    Country,
    CountryClassifiedProductAliases,
    Currency,
    UnitOfMeasure,
)


class Lookup(ABC):
    """
    Abstract base class for lookups.
    """

    # The Django model that contains the reference data
    model = None

    # The primary key fields for the model being retrieved, typically
    # a single auto-incremented surrogate key named `id`
    id_fields = None

    # The fields passed from the dataframe that are used to constrain the lookup,
    # typically the fields that are foreign keys from the model being looked up to
    # other metadata also present in the source file. The source dataframe should
    # contain the primary key of the parent object in the parent field - not the
    # parent object itself. The parent fields can be specified using Django's
    # double-underscore notation to specify fields from related models. In this case,
    # the source dataframe should contain a column with the name of the actual field,
    # not the full path that includes the related model.
    parent_fields = []

    # If the parent_fields are required, then this class raises an error if they
    # are not present in the source dataframe. This can be set to False in subclasses
    # to allow partial matches using whatever parent fields are available.
    require_parent_fields = True

    # If a match is required, then this class raises an error if the lookup fails
    # to match any rows in the source dataframe. This can be set to False in subclasses
    # where matches are not expected, such as CountryClassifiedProductAliasesLookup.
    require_match = True

    # The fields in the lookup model that are used to lookup the value provided by the dataframe,
    # such as the name, description, aliases, etc.
    lookup_fields = None

    # Use case-insensitive lookups
    case_insensitive: bool = True

    # Ignore leading or trailing spaces in lookups
    strip: bool = True

    # Match the primary key directly
    # Normally this is a good thing, but it might be dangerous for date fields,
    # where an Excel date or other epoch-based date format might accidentally match a primary key
    match_pk: bool = True

    # Queryset Filters
    filters: dict

    # Related models to also instantiate
    related_models = []

    def __init__(self, filters: dict = {}):
        # Make sure we don't have any fields in multiple categories
        assert len(set(self.id_fields + self.parent_fields + self.lookup_fields)) == len(self.id_fields) + len(
            self.parent_fields
        ) + len(self.lookup_fields), "id_fields, parent_fields and lookup_fields must not contain duplicate entries"

        self.composite_key = len(self.id_fields) > 1

        self.filters = filters

    def get_queryset_columns(self):
        return self.lookup_fields + self.parent_fields + self.id_fields

    def get_queryset(self):
        """
        Return a queryset containing just the required fields.

        Typically this returns the various lookup fields (name, aliases, etc.) together with any
        parent fields and the primary key.

        It uses values_list to avoid hydrating a Django model, given that the result will be used
        to instantiate a DataFrame.
        """
        queryset = self.model.objects.filter(**self.filters).values_list(*self.get_queryset_columns())
        return queryset

    def get_lookup_df(self):
        """
        Build a dataframe for a model that can be used to lookup the primary key.

        Create a dataframe that contains the primary key, and all the columns that
        can be used to lookup the primary key, e.g. the name, description, aliases, etc.

        Use the queryset.iterator() to prevent Django from caching the queryset.
        """
        df = pd.DataFrame(list(self.get_queryset().iterator()), columns=self.get_queryset_columns())

        # The primary key should match itself (for most models)!
        if self.match_pk and not self.composite_key:
            df["pk"] = df[self.id_fields[0]]

        # If aliases is in the list of lookup fields then separate it into columns
        if "aliases" in df.columns:
            # Start by replacing None/null alias values with an empty list
            df["aliases"] = df["aliases"].apply(lambda x: x if x else [])
            # Append the aliases as separate columns
            df = pd.concat([df.drop("aliases", axis="columns"), pd.DataFrame(df["aliases"].tolist())], axis="columns")

        return df

    def prepare_lookup_df(self):
        """
        Use DataFrame.melt to create a m:1 lookup table that can be used to lookup
        the search value and retrieve the primary key.
        """
        df = self.get_lookup_df()

        # Melt the non-id columns
        df = df.melt(id_vars=self.id_fields + self.parent_fields, value_name="lookup_key").drop(
            ["variable"], axis="columns"
        )

        # Remove rows with an empty lookup value
        # We need to fillna(False) because pd.NA can't be converted to a boolean.
        df["lookup_key"] = df["lookup_key"].where(df["lookup_key"].fillna(False).astype(bool))
        df = df[~df["lookup_key"].isnull()]

        # Always use a string lookup, because the lookup may be against columns of mixed data types
        df["lookup_key"] = df["lookup_key"].astype(str)

        if self.case_insensitive:
            df["lookup_key"] = df["lookup_key"].str.lower()

        if self.strip:
            df["lookup_key"] = df["lookup_key"].str.strip()

        df = df.drop_duplicates()

        df = df.sort_values(by=self.id_fields + self.parent_fields)

        if not self.composite_key:
            df = df.rename(columns={self.id_fields[0]: "lookup_value"})
        return df

    def do_lookup(
        self,
        df: pd.DataFrame,
        lookup_column: str = None,
        match_column: str = None,
        exact_match: bool = True,
        update: bool = False,
    ):
        """
        Perform the lookup using an existing dataframe.

        Use the columns from an existing dataframe against the lookup dataframe
        to find the matching id field, and add that as a column to the original
        dataframe and return it.

        df: the Pandas DataFrame containing the data we are going to lookup from
        lookup_column: the column in the dataframe that will be compared to the lookup columns to find a match
        match_column: the column in the dataframe that will contain the id of the matched object
        exact_match: the lookup value must match a single instance of the lookup model
        update: update the match column in the dataframe from the lookup matches, but leave existing rows unchanged
            if there isn't a match
        """
        # If the dataframe to match against is empty, then there is no point doing the lookup
        if df.empty:
            raise ValueError(f"{self.__class__.__qualname__} received empty source dataframe")

        if not match_column and self.id_fields in df.columns:
            # Assume an existing column with the same name that we should replace
            match_column = self.id_fields

        # The source dataframe should contain the field name, but the parent field may include a
        # path through related models.
        target_fields = [field.split("__")[-1] for field in self.parent_fields]

        # If we need parent fields to do the lookup, then they must be in the existing DataFrame already.
        if self.require_parent_fields:
            if not set(target_fields).issubset(df.columns):
                raise ValueError(
                    f"{self.__class__.__qualname__} is missing parent column(s): {set(target_fields) - set(df.columns)}"  # NOQA: E501
                )

        # If we are updating, then we also need the match column to already exist
        if update and match_column not in df.columns:
            raise ValueError(f"{self.__class__.__qualname__} is missing match column {match_column}")

        # Set up the fields to match on
        left_fields = [field for field in target_fields if field in df.columns]
        right_fields = [field for field in self.parent_fields if field.split("__")[-1] in df.columns]

        if lookup_column:
            # Always use a string lookup, because the lookup may be against columns of mixed data types
            df["lookup_candidate"] = df[lookup_column].astype(str)

            if self.case_insensitive:
                df["lookup_candidate"] = df["lookup_candidate"].str.lower()

            if self.strip:
                df["lookup_candidate"] = df["lookup_candidate"].str.strip()

            left_fields.append("lookup_candidate")
            right_fields.append("lookup_key")

        # Set up the fields we need in the lookup dataframe
        lookup_fields = ["lookup_value"] + right_fields

        # Get the lookup dataframe, dropping duplicates to eliminate duplicates caused by
        # lookup key and primary key when there isn't actually a lookup_column to need them
        lookup_df = self.prepare_lookup_df()[lookup_fields].drop_duplicates()

        try:
            merge_df = df.merge(lookup_df, how="left", left_on=left_fields, right_on=right_fields)
        except ValueError as e:
            # Mismatched column types
            errors = [f"{self.__class__.__qualname__} has mismatched column dtypes:"]
            for left, right in zip(left_fields, right_fields):
                if df[left].dtype != lookup_df[right].dtype:
                    errors.append(
                        f"Source column {left} with dtype {df[left].dtype} doesn't match lookup column {right} with dtype {lookup_df[right].dtype}"  # NOQA: E501
                    )
            raise ValueError("\n".join(errors)) from e

        # If we didn't match anything, then the set up is probably wrong
        if self.require_match and merge_df["lookup_value"].isnull().values.all():
            errors = []
            errors.append(f"{self.__class__.__qualname__} didn't find any matches:")
            errors.append("Source")
            errors.append(df[left_fields].iloc[:10].to_string(index=False))
            errors.append("Lookup Reference")
            errors.append(lookup_df[right_fields].iloc[:10].to_string(index=False))
            raise ValueError("\n".join(errors))

        # Make sure we didn't add any rows!
        if exact_match and len(merge_df) != len(df):
            columns = [lookup_column if column == "lookup_candidate" else column for column in left_fields]
            duplicates = merge_df[columns + ["lookup_value"]].drop_duplicates()
            duplicates = duplicates.loc[
                ~duplicates["lookup_value"].isnull() & duplicates.duplicated(columns, keep=False)
            ]
            duplicates = duplicates.rename(columns={"lookup_value": match_column})
            raise ValueError(
                f"{self.__class__.__qualname__} found multiple {self.model.__name__} matches for some rows:\n{duplicates.to_string(index=False)}"  # NOQA: E501
            )

        # Keep values from the existing dataframe where we don't have a match
        if update and not merge_df["lookup_value"].empty:
            merge_df["lookup_value"] = merge_df["lookup_value"].mask(
                merge_df["lookup_value"].isnull(), merge_df[match_column]
            )

        if match_column in merge_df.columns:
            merge_df = merge_df.rename(columns={match_column: f"{match_column}_original"})

        merge_df = merge_df.rename(columns={"lookup_value": match_column})

        # Drop redundant columns
        if lookup_column:
            merge_df = merge_df.drop(["lookup_candidate", "lookup_key"], axis="columns")

        return merge_df

    def get_instances(self, df, column, related_models=None):
        """
        Replace the primary key value in a DataFrame column with a model instance
        """
        related_models = related_models or self.related_models
        queryset = self.model.objects.filter(pk__in=df[column].unique())
        if related_models:
            queryset = queryset.select_related(*related_models)
        model_map = {instance.pk: instance for instance in queryset.iterator()}
        df[column] = df[column].map(model_map)
        return df


class CountryClassifiedProductAliasesLookup(Lookup):
    model = CountryClassifiedProductAliases
    id_fields = ["product__cpcv2"]
    parent_fields = ["country"]
    lookup_fields = ["aliases"]
    require_match = False

    def get_queryset(self):
        """
        Data Series must be for leaf Products, so filter out Products with children
        """
        queryset = super().get_queryset()
        queryset = queryset.filter(product__numchild=0)
        return queryset


class CountryLookup(Lookup):
    model = Country
    id_fields = ["iso3166a2"]
    lookup_fields = [
        "iso_en_ro_name",
        "iso_en_ro_proper",
        "iso_en_name",
        "iso_fr_name",
        "bgn_name",
        "bgn_proper",
        "bgn_longname",
        "pcgn_name",
        "pcgn_proper",
        "iso3166a3",
        "iso3166n3",
        "aliases",
    ]

    def get_lookup_df(self):
        """
        Build a dataframe for a model that can be used to lookup the primary key.
        """
        df = super().get_lookup_df()

        # Make sure iso3166n3 is represented as an int (e.g. 804) rather than a float (e.g. 804.0).
        # The column is forced to float because Kosovo doesn't have an ISO 3166 N3 code and so is np.nan,
        # which is a float, so the whole column adopts a float dtype.
        df["iso3166n3"] = df["iso3166n3"].astype("Int64")

        return df


class CurrencyLookup(Lookup):
    model = Currency
    id_fields = ["iso4217a3"]
    lookup_fields = [
        "iso4217n3",
        "iso_en_name",
    ]


class ClassifiedProductLookup(Lookup):
    # Note that this class differs from FDW because it doesn't force matching
    # products to be leaf nodes in the tree.  If that behavior is required in
    # HEA, then pass `filters={"numchild": 0}` when instantiating the Lookup.
    model = ClassifiedProduct
    id_fields = ["cpcv2"]
    lookup_fields = ["common_name", "description", "aliases", "hs2012"]

    def get_lookup_df(self):
        """
        Build a dataframe for a model that can be used to lookup the primary key.

        Create a dataframe that contains the primary key, and all the columns that
        can be used to lookup the primary key, e.g. the name, description, aliases, etc.

        Use the queryset.iterator() to prevent Django from caching the queryset.
        """
        df = super().get_lookup_df()

        # Split hs2012 into columns
        # Start by replacing None/null alias values with an empty list
        df["hs2012"] = df["hs2012"].apply(lambda x: x if x else [])
        # Append the hs2012 codes as separate columns
        df = pd.concat([df.drop("hs2012", axis="columns"), pd.DataFrame(df["hs2012"].tolist())], axis="columns")

        return df


class UnitOfMeasureLookup(Lookup):
    model = UnitOfMeasure
    id_fields = ["abbreviation"]
    lookup_fields = [
        "description",
        "aliases",
    ]
