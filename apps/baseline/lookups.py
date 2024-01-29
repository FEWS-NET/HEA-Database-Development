"""
Baseline Lookup classes that support data ingestion by matching data in a Pandas DataFrame against
reference data in Django Models.
"""
from common.lookups import Lookup

from .models import SeasonalActivity


class SeasonalActivityLookup(Lookup):
    id_fields = ["id"]
    model = SeasonalActivity
    lookup_fields = ["additional_identifier", "seasonal_activity_type"]
