"""
Load fixtures from corrected files
"""

from dagster import define_asset_job

from ..assets.fixtures import (
    consolidated_fixture,
    consolidated_instances,
    imported_baseline,
    validated_instances,
)
from ..assets.livelihood_activity import livelihood_activity_instances
from ..assets.other_cash_income import other_cash_income_instances
from ..assets.seasonal_production_performance import (
    hazard_instances,
    seasonal_production_performance_instances,
)
from ..assets.wealth_characteristic import wealth_characteristic_instances
from ..assets.wild_foods import wild_foods_instances
from ..partitions import bss_instances_partitions_def

import_baseline_from_fixture = define_asset_job(
    name="import_baseline_from_fixture",
    selection=(
        wealth_characteristic_instances,
        livelihood_activity_instances,
        other_cash_income_instances,
        wild_foods_instances,
        consolidated_instances,
        validated_instances,
        consolidated_fixture,
        imported_baseline,
        seasonal_production_performance_instances,
        hazard_instances,
    ),
    partitions_def=bss_instances_partitions_def,
)
