import os

import django
from dagster import AssetSelection, RunRequest, SensorResult, sensor

from .assets.livelihood_activity import (
    livelihood_activity_dataframe,
    livelihood_activity_instances,
)
from .assets.other_cash_income import (
    other_cash_income_dataframe,
    other_cash_income_instances,
)
from .assets.wealth_characteristic import (
    wealth_characteristic_dataframe,
    wealth_characteristic_instances,
)
from .assets.wild_foods import wild_foods_dataframe, wild_foods_instances
from .partitions import bss_instances_partitions_def

# set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hea.settings.production")

# Configure Django with our custom settings before importing any Django classes
django.setup()

from baseline.models import LivelihoodZoneBaseline  # NOQA: E402


@sensor(
    asset_selection=AssetSelection.keys(
        livelihood_activity_dataframe.key,
        livelihood_activity_instances.key,
        other_cash_income_dataframe.key,
        other_cash_income_instances.key,
        wild_foods_dataframe.key,
        wild_foods_instances.key,
        wealth_characteristic_dataframe.key,
        wealth_characteristic_instances.key,
    ),
    minimum_interval_seconds=600,
)
def bss_instance_sensor(context):
    """
    Detects when a BSS instance has been added to the database and triggers the import pipeline.
    """
    dagster_instance = context.instance
    livelihoood_zone_baselines = [
        "~".join(livelihoood_zone_baseline[:2] + (livelihoood_zone_baseline[2].isoformat(),))
        for livelihoood_zone_baseline in LivelihoodZoneBaseline.objects.all()
        .order_by("livelihood_zone__country__iso_en_ro_name", "livelihood_zone__code", "reference_year_end_date")
        .values_list("livelihood_zone__country__iso_en_ro_proper", "livelihood_zone__code", "reference_year_end_date")
    ]

    partitions = bss_instances_partitions_def.get_partition_keys(dynamic_partitions_store=dagster_instance)

    for partition in partitions:
        if partition not in livelihoood_zone_baselines:
            dagster_instance.delete_dynamic_partition(bss_instances_partitions_def.name, partition)

    new_partitions = [
        livelihoood_zone_baseline
        for livelihoood_zone_baseline in livelihoood_zone_baselines
        if livelihoood_zone_baseline not in partitions
    ]

    return SensorResult(
        run_requests=[
            RunRequest(partition_key=livelihoood_zone_baseline) for livelihoood_zone_baseline in new_partitions
        ],
        dynamic_partitions_requests=[bss_instances_partitions_def.build_add_request(new_partitions)],
    )
