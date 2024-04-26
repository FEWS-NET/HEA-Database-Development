"""
Lookup classes that support data ingestion by matching data in a Pandas DataFrame against
reference data in Django Models.
"""

from common.fields import translation_fields
from common.lookups import Lookup

from .models import (
    HazardCategory,
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
    # Set parent field to country_id so that we can use 'Season 1' and 'Season 2' aliases in all countries.
    parent_fields = ["country_id"]
    lookup_fields = [
        *translation_fields("name"),
        *translation_fields("description"),
        "aliases",
    ]


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


class HazardCategoryLookup(ReferenceDataLookup):
    model = HazardCategory
