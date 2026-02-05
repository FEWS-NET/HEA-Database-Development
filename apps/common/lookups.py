"""
Lookup classes that support data ingestion by matching data in a Pandas DataFrame against
reference data in Django Models.
"""

import functools
import re
from abc import ABC

import pandas as pd
from django.contrib.auth.models import User
from django.db.models import Model

from .fields import translation_fields
from .models import (
    ClassifiedProduct,
    Country,
    CountryClassifiedProductAliases,
    Currency,
    UnitOfMeasure,
)
from .utils import normalize


class Lookup(ABC):
    """
    Abstract base class for lookups.
    """

    # The Django model that contains the reference data
    model = None

    # The primary key fields for the model being retrieved, typically
    # a single auto-incremented surrogate key named `id`
    id_fields = []

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

    # Ignore accents
    ignore_accents: bool = True

    # Replace any number of non-standard space characters (anything that matches r"\s+") with a single, normal space
    sanitize_spaces: bool = True

    # Ignore leading or trailing spaces in lookups
    strip: bool = True

    # Match the primary key directly
    # Normally this is a good thing, but it might be dangerous for date fields,
    # where an Excel date or other epoch-based date format might accidentally match a primary key
    match_pk: bool = True

    # Queryset Filters and Excludes
    filters: dict
    excludes: dict

    # Related models to also instantiate
    related_models = []

    def __init__(self, filters: dict = None, excludes: dict = None, require_match=None):
        # Make sure we don't have any fields in multiple categories
        assert len(set((*self.id_fields, *self.parent_fields, *self.lookup_fields))) == len(self.id_fields) + len(
            self.parent_fields
        ) + len(self.lookup_fields), "id_fields, parent_fields and lookup_fields must not contain duplicate entries"

        self.composite_key = len(self.id_fields) > 1

        self.filters = filters or dict()
        self.excludes = excludes or dict()

        # Override the require_match if necessary
        if require_match is not None:
            self.require_match = require_match

        # Create instance level caches for key methods
        self.get_lookup_df = functools.cache(self.get_lookup_df)
        self.get = functools.cache(self.get)
        self.get_instance = functools.cache(self.get_instance)

    def get_queryset_columns(self):
        return [*self.lookup_fields, *self.parent_fields, *self.id_fields]

    def get_queryset(self):
        """
        Return a queryset containing just the required fields.

        Typically this returns the various lookup fields (name, aliases, etc.) together with any
        parent fields and the primary key.

        It uses values_list to avoid hydrating a Django model, given that the result will be used
        to instantiate a DataFrame.
        """
        queryset = (
            self.model.objects.filter(**self.filters)
            .exclude(**self.excludes)
            .values_list(*self.get_queryset_columns())
        )
        return queryset

    def get_lookup_df(self):
        """
        Build a dataframe for a model that can be used to lookup the primary key.

        Create a dataframe that contains the primary key, and all the columns that
        can be used to lookup the primary key, e.g. the name, description, aliases, etc.

        Use the queryset.iterator() to prevent Django from caching the queryset, because functools.cache is used to
        cache the dataframe returned from this function.
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

    def prepare_lookup_df(self) -> pd.DataFrame:
        """
        Use DataFrame.melt to create a m:1 lookup table that can be used to lookup
        the search value and retrieve the primary key.

        Returns a DataFrame with the columns:
            - lookup_key: the column that the lookup_column from the source DataFrame will be matched against
            - lookup_value: the value that will be returned if a match is found, typically the primary key
            - any parent columns required to filter the rows from the source DataFrame when matching
        """
        df = self.get_lookup_df()

        # Melt the non-id columns
        df = df.melt(id_vars=[*self.id_fields, *self.parent_fields], value_name="lookup_key").drop(
            ["variable"], axis="columns"
        )

        # Remove rows with an empty lookup value
        # We need to fillna(False) because pd.NA can't be converted to a boolean.
        df["lookup_key"] = df["lookup_key"].where(df["lookup_key"].fillna(False).astype(bool))
        df = df[~df["lookup_key"].isnull()]

        df["lookup_key"] = self.prepare_column_for_lookup(df["lookup_key"])

        df = df.drop_duplicates()

        df = df.sort_values(by=[*self.id_fields, *self.parent_fields])

        if not self.composite_key:
            df = df.rename(columns={self.id_fields[0]: "lookup_value"})
        return df

    def prepare_column_for_lookup(self, column):
        # Always use a string lookup, because the lookup may be against columns of mixed data types
        column = column.astype(str)

        if self.sanitize_spaces:
            column = column.apply(lambda s: re.sub(r"\s+", " ", s))

        if self.case_insensitive:
            column = column.str.lower()

        if self.strip:
            column = column.str.strip()

        if self.ignore_accents:
            column = column.str.translate(normalize)

        return column

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

        if not match_column:
            if self.id_fields in df.columns:
                # Assume an existing column with the same name that we should replace
                match_column = self.id_fields
            else:
                raise ValueError(f"{self.__class__.__qualname__}.do_lookup() requires a match_column")

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
            df["lookup_candidate"] = df[lookup_column]
            df["lookup_candidate"] = self.prepare_column_for_lookup(df["lookup_candidate"])

            left_fields.append("lookup_candidate")
            right_fields.append("lookup_key")

        # Set up the fields we need in the lookup dataframe
        lookup_fields = ["lookup_value", *right_fields]

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
            errors.append("Source" if len(df) <= 10 else "Source (first 10 rows only)")
            errors.append(df[left_fields].iloc[:10].to_string(index=False))
            errors.append(
                "Expected Lookup Values" if len(lookup_df) <= 10 else "Expected Lookup Values (first 10 rows only)"
            )
            # Filter the lookup_df to only include the rows that match the parent fields
            for field in right_fields[:-1]:
                lookup_df = lookup_df[lookup_df[field].isin(df[field].unique())]
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

        # Preserve the original index
        return merge_df.set_index(df.index)

    def get_instances(self, df, column, related_models=None):
        """
        Replace the primary key value in a DataFrame column with a model instance
        """
        related_models = related_models or self.related_models
        queryset = self.model.objects.filter(pk__in=df[column].dropna().unique())
        if related_models:
            queryset = queryset.select_related(*related_models)
        model_map = {instance.pk: instance for instance in queryset.iterator()}
        df[column] = df[column].map(model_map)
        return df

    def get(self, value: str, **parent_values) -> str | None:
        """
        Return the lookup value for a single string, or None if there is no match.

        Used to do a lookup for a single value instead of a dataframe.

        Unlike `do_lookup()` this is a cached method to avoid repeated database queries.
        Note that this cache is per-instance of the Lookup class, so the class should be instantiated outside a loop
        performing repeated lookups:

            lookup = MyLookup()
            for dict_item in very_long_list:
                item["id"] = lookup.get(item["other_name"])
        """
        df = pd.DataFrame({"value": [value]})
        for parent_field in self.parent_fields:
            df[parent_field] = [parent_values[parent_field]]
        try:
            df = self.do_lookup(df, "value", "result")
            result = df.iloc[0, -1]
            return result if pd.notna(result) else None
        except ValueError:
            return None

    def get_instance(self, value: str, **parent_values) -> Model | None:
        """
        Return the Django model instance for a single string, or None if there is no match.

        Used to do a lookup for a single value instead of a dataframe.

        Unlike `do_lookup()` this is a cached method to avoid repeated database queries.
        Note that this cache is per-instance of the Lookup class, so the class should be instantiated outside a loop
        performing repeated lookups:

            lookup = MyLookup()
            for dict_item in very_long_list:
                instance = lookup.get_instance(item["other_name"])
        """
        df = pd.DataFrame({"value": [value]})
        for parent_field in self.parent_fields:
            df[parent_field] = [parent_values[parent_field]]
        try:
            df = self.do_lookup(df, "value", "result")
            df = self.get_instances(df, "result")
            result = df.iloc[0, -1]
            return result if isinstance(result, self.model) else None
        except ValueError:
            return None


class CountryClassifiedProductAliasesLookup(Lookup):
    model = CountryClassifiedProductAliases
    id_fields = ["product__cpc"]
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
    id_fields = ["cpc"]
    lookup_fields = (
        *translation_fields("common_name"),
        *translation_fields("description"),
        "aliases",
        "hs2012",
    )

    def get_queryset(self):
        """
        Exclude specific products that are unwanted duplicates.
        """
        # P23162 is Husked Rice, but we use "rice" as an alias for it. This
        # conflicts with R0113: Rice, which we never use, so ignore it.
        return super().get_queryset().exclude(cpc="R0113")

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

    def prepare_lookup_df(self):
        """
        Remove parent nodes with a single child to avoid spurious multiple match errors.

        Some Classified Product parent nodes have a single child that is the identical to the parent. For example:
            - R015	Edible roots and tubers with high starch or inulin content
              - R0151	Potatoes
                - R01510	Potatoes

        In this case, a search for "potatoes" should return the leaf node, R01510, and ignore the parent R0151.

        Some other Classified Product reuse the Description of the parent node as the Common Name of a child node.
        This allows to ensure that a search for the common name returns the preferred leaf node. For example:
            - R0141     Soya beans
                - R01411    Soya beans, seed for planting
                - R01412    Soya beans, other	            Soya beans

        In this case, a search for "soya beans" should return the leaf node, R01412, and ignore the parent R0141.

        To achieve this we need to remove the parent rows from the lookup_df, otherwise the search raises:
            ValueError: ClassifiedProductLookup found multiple ClassifiedProduct matches for some rows
        """
        df = super().prepare_lookup_df()

        # Create a DataFrame that just contains the single digits 0 through 9.
        df_digit = pd.DataFrame(range(10), columns=["digit"])

        # Create a Cartesian product of df and df_digit
        df_all = pd.merge(df.assign(key=1), df_digit.assign(key=1), on="key").drop("key", axis=1)

        # Create the "child_candidate" column that adds the 0-9 to the end of the lookup_value
        df_all["child_candidate"] = df_all["lookup_value"] + df_all["digit"].astype(str)

        # Merge with the original DataFrame on the child_candidate column and lookup_key to find only the rows
        # that contain valid child codes where the lookup_key in the child is the same as the lookup_key in the parent.
        unwanted_parents = df_all.merge(
            df,
            left_on=["child_candidate", "lookup_key"],
            right_on=["lookup_value", "lookup_key"],
            suffixes=[None, "_child"],
        )

        # Drop the extra columns so the shape matches the original dataframe.
        unwanted_parents = unwanted_parents[["lookup_value", "lookup_key"]]

        # Drop the unwanted parents from the original DataFrame
        df = pd.concat([df, unwanted_parents]).drop_duplicates(keep=False)
        return df


class UnitOfMeasureLookup(Lookup):
    model = UnitOfMeasure
    id_fields = ["abbreviation"]
    lookup_fields = (
        *translation_fields("description"),
        "aliases",
    )


class UserLookup(Lookup):
    model = User
    id_fields = ("id",)
    lookup_fields = [
        "username",
        "email",
        "first_name",
        "last_name",
    ]

    def get_lookup_df(self):
        """
        Build a dataframe for a model that can be used to lookup the primary key.

        Create a dataframe that contains the primary key, and all the columns that
        can be used to lookup the primary key, e.g. the name, description, aliases, etc.

        Use the queryset.iterator() to prevent Django from caching the queryset.
        """
        df = super().get_lookup_df()

        # Also include the full name in the fields to lookup
        df["full_name"] = df.apply(
            lambda row: " ".join([x for x in [row["first_name"].strip(), row["last_name"].strip()] if x]),
            axis="columns",
        )

        return df
