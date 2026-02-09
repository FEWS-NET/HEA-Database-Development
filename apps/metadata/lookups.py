"""
Lookup classes that support data ingestion by matching data in a Pandas DataFrame against
reference data in Django Models.
"""

import pandas as pd

from common.fields import translation_fields
from common.lookups import Lookup

from .models import (
    LivelihoodCategory,
    ReferenceData,
    Season,
    WealthCharacteristic,
    WealthGroupCategory,
)


class ReferenceDataLookup(Lookup):
    model = ReferenceData
    id_fields = ["code"]
    lookup_fields = (
        *translation_fields("name"),
        *translation_fields("description"),
        "aliases",
    )


class LivelihoodCategoryLookup(ReferenceDataLookup):
    model = LivelihoodCategory


class WealthCharacteristicLookup(ReferenceDataLookup):
    model = WealthCharacteristic


class WealthGroupCategoryLookup(ReferenceDataLookup):
    model = WealthGroupCategory


class SeasonLookup(Lookup):
    model = Season
    id_fields = ["id"]
    # Set parent field to include:
    #   - country_id so that we can use 'Season 1' and 'Season 2' aliases in all countries.
    #   - purpose so that we can use the 'Season 1' and 'Season 2' alias for different purposes within the same country.
    parent_fields = ["country_id", "purpose"]
    require_parent_fields = False
    lookup_fields = [
        *translation_fields("name"),
        *translation_fields("description"),
        "aliases",
    ]

    def prepare_lookup_df(self) -> pd.DataFrame:
        df = super().prepare_lookup_df()
        # Seasons with a null purpose can be used to match any purpose for that country that doesn't have specific seasons defined,
        # so duplicate any rows with a null purpose for all possible purposes for that country.
        all_purposes = [choice[0] for choice in self.model._meta.get_field("purpose").choices]
        all_countries = df["country_id"].unique().tolist()
        for country in all_countries:
            country_df = df[df["country_id"] == country]
            null_purpose_rows = country_df[country_df["purpose"].isnull()]
            for purpose in all_purposes:
                # Only add duplicate rows for purposes that aren't already defined for this country
                if purpose not in country_df["purpose"].unique():
                    purpose_df = null_purpose_rows.copy()
                    purpose_df["purpose"] = purpose
                    df = pd.concat([df, purpose_df], ignore_index=True)
        return df

    def do_lookup(
        self,
        df: pd.DataFrame,
        lookup_column: str = None,
        match_column: str = None,
        exact_match: bool = True,
        update: bool = False,
    ):
        # We need country_id to do the lookup.
        if "country_id" not in df.columns:
            raise ValueError(f"{self.__class__.__qualname__} is missing parent column(s): country_id")
        # We can use purpose or strategy_type as the parent field, and default it to None if not provided.
        purpose_provided = "purpose" in df.columns
        if not purpose_provided:
            # Allow strategy_type as an alias for purpose
            if "strategy_type" in df.columns:
                df["purpose"] = df["strategy_type"]
            # If purpose is not provided, we set it to None so that we can match against seasons with a null purpose.
            else:
                df["purpose"] = None

        df = super().do_lookup(
            df,
            lookup_column=lookup_column,
            match_column=match_column,
            exact_match=exact_match,
            update=update,
        )
        if not purpose_provided:
            df = df.drop(columns=["purpose"])
        return df


class SeasonNameLookup(SeasonLookup):
    """
    Season Lookup that returns the season name in English, instead of the id.

    This is useful when constructing the natural key for a Django fixture.
    """

    id_fields = ["name_en"]
    lookup_fields = [
        "id",
        "name_es",
        "name_fr",
        "name_pt",
        "name_ar",
        *translation_fields("description"),
        "aliases",
    ]
