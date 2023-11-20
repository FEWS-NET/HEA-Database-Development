"""
Lookup classes that support data ingestion by matching data in a Pandas DataFrame against
reference data in Django Models.
"""
from common.lookups import Lookup

from .models import (
    LivelihoodCategory,
    ReferenceData,
    Season,
    SeasonalActivityType,
    WealthCharacteristic,
    WealthGroupCategory,
)


class ReferenceDataLookup(Lookup):
    model = ReferenceData
    id_fields = ["code"]
    lookup_fields = [
        "name",
        "description",
        "aliases",
    ]


class LivelihoodCategoryLookup(ReferenceDataLookup):
    model = LivelihoodCategory


class WealthCharacteristicLookup(ReferenceDataLookup):
    model = WealthCharacteristic


class WealthGroupCategoryLookup(ReferenceDataLookup):
    model = WealthGroupCategory


class SeasonalActivityTypeLookup(ReferenceDataLookup):
    model = SeasonalActivityType


class SeasonLookup(Lookup):
    model = Season
    id_fields = [
        "name",
    ]

    lookup_fields = ["description", "country"]
