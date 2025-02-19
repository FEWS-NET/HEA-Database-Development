"""
Load fixtures from corrected files
"""

from dagster import define_asset_job

from ..assets.base import bss_metadata, completed_bss_metadata
from ..assets.baseline import baseline_instances
from ..assets.fixtures import (
    consolidated_fixture,
    imported_baseline,
    uploaded_baselines,
)
from ..assets.livelihood_activity import (
    all_livelihood_activity_labels_dataframe,
    livelihood_activity_dataframe,
    livelihood_activity_instances,
    livelihood_activity_label_dataframe,
    livelihood_activity_valid_instances,
    summary_livelihood_activity_labels_dataframe,
)
from ..assets.other_cash_income import (
    all_other_cash_income_labels_dataframe,
    other_cash_income_dataframe,
    other_cash_income_instances,
    other_cash_income_label_dataframe,
    other_cash_income_valid_instances,
    summary_other_cash_income_labels_dataframe,
)
from ..assets.wealth_characteristic import (
    all_wealth_characteristic_labels_dataframe,
    summary_wealth_characteristic_labels_dataframe,
    wealth_characteristic_dataframe,
    wealth_characteristic_instances,
    wealth_characteristic_label_dataframe,
    wealth_characteristic_valid_instances,
)
from ..assets.wild_foods import (
    all_wild_foods_labels_dataframe,
    summary_wild_foods_labels_dataframe,
    wild_foods_dataframe,
    wild_foods_instances,
    wild_foods_label_dataframe,
    wild_foods_valid_instances,
)
from ..partitions import bss_files_partitions_def, bss_instances_partitions_def

import_baseline_from_fixture = define_asset_job(
    name="import_baseline_from_fixture",
    selection=(
        wealth_characteristic_instances,
        livelihood_activity_instances,
        other_cash_income_instances,
        wild_foods_instances,
        wealth_characteristic_valid_instances,
        livelihood_activity_valid_instances,
        other_cash_income_valid_instances,
        wild_foods_valid_instances,
        consolidated_fixture,
        imported_baseline,
    ),
    partitions_def=bss_instances_partitions_def,
)


update_external_assets = define_asset_job(
    name="update_external_assets",
    selection=(
        bss_metadata,
        completed_bss_metadata,
    ),
    partitions_def=bss_files_partitions_def,
)

upload_baselines = define_asset_job(
    name="upload_baselines",
    selection=(
        baseline_instances,
        uploaded_baselines,
    ),
    partitions_def=bss_files_partitions_def,
)

extract_dataframes = define_asset_job(
    name="extract_dataframes",
    selection=(
        wealth_characteristic_dataframe,
        livelihood_activity_dataframe,
        other_cash_income_dataframe,
        wild_foods_dataframe,
        wealth_characteristic_label_dataframe,
        livelihood_activity_label_dataframe,
        other_cash_income_label_dataframe,
        wild_foods_label_dataframe,
        all_wealth_characteristic_labels_dataframe,
        all_livelihood_activity_labels_dataframe,
        all_other_cash_income_labels_dataframe,
        all_wild_foods_labels_dataframe,
        summary_wealth_characteristic_labels_dataframe,
        summary_livelihood_activity_labels_dataframe,
        summary_other_cash_income_labels_dataframe,
        summary_wild_foods_labels_dataframe,
    ),
    partitions_def=bss_instances_partitions_def,
)
