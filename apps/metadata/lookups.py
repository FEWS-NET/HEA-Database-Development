"""
Lookup classes that support data ingestion by matching data in a Pandas DataFrame against
reference data in Django Models.
"""
from common.fields import translation_fields
from common.lookups import Lookup

from .models import (
    LivelihoodCategory,
    ReferenceData,
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
