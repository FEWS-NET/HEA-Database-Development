"""
Lookup classes that support data ingestion by matching data in a Pandas DataFrame against
reference data in Django Models.
"""
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
    lookup_fields = [
        "name_en",
        "name_fr",
        "name_es",
        "name_ar",
        "name_pt",
        "description_en",
        "description_fr",
        "description_es",
        "description_ar",
        "description_pt",
        "aliases",
    ]


class LivelihoodCategoryLookup(ReferenceDataLookup):
    model = LivelihoodCategory


class WealthCharacteristicLookup(ReferenceDataLookup):
    model = WealthCharacteristic


class WealthGroupCategoryLookup(ReferenceDataLookup):
    model = WealthGroupCategory
