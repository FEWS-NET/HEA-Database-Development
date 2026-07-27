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
from ..assets.key_parameter import (
    key_parameter_dataframe,
    key_parameter_instances,
    key_parameter_valid_instances,
    livelihood_activity_groups,
)
from ..assets.livelihood_activity import (
    all_livelihood_activity_labels_dataframe,
    livelihood_activity_dataframe,
    livelihood_activity_instances,
    livelihood_activity_label_dataframe,
    livelihood_activity_label_recognition_dataframe,
    livelihood_activity_valid_instances,
    livelihood_summary_dataframe,
    summary_livelihood_activity_labels_dataframe,
)
from ..assets.livelihood_product_category import (
    livelihood_product_category_dataframe,
    livelihood_product_category_instances,
    livelihood_product_category_valid_instances,
    other_food_purchase_summ_dataframe,
)
from ..assets.other_cash_income import (
    all_other_cash_income_labels_dataframe,
    other_cash_income_dataframe,
    other_cash_income_instances,
    other_cash_income_label_dataframe,
    other_cash_income_valid_instances,
    summary_other_cash_income_labels_dataframe,
)
from ..assets.seasonal_calendar import (
    imported_seasonal_activities,
    seasonal_activity_fixture,
    seasonal_activity_instances,
    seasonal_activity_valid_instances,
    seasonal_calendar_dataframe,
    summary_seasonal_calendar_labels_dataframe,
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

create_consolidated_fixture = define_asset_job(
    name="create_consolidated_fixture",
    selection=(
        wealth_characteristic_instances,
        livelihood_activity_instances,
        other_cash_income_instances,
        wild_foods_instances,
        livelihood_activity_groups,
        key_parameter_instances,
        livelihood_product_category_instances,
        seasonal_activity_instances,
        wealth_characteristic_valid_instances,
        livelihood_activity_valid_instances,
        other_cash_income_valid_instances,
        wild_foods_valid_instances,
        key_parameter_valid_instances,
        livelihood_product_category_valid_instances,
        seasonal_activity_valid_instances,
        consolidated_fixture,
    ),
    partitions_def=bss_instances_partitions_def,
)

# imported_baseline runs in the django_loaddata concurrency pool
# (with the limit set at /deployment/concurrency), so that we
# can avoid duplicate primary key errors. Therefore we need to
# run imported_baseline separately from other assets, otherwise
# the limit applies to them too.
import_baseline_from_fixture = define_asset_job(
    name="import_baseline_from_fixture",
    selection=(imported_baseline,),
    partitions_def=bss_instances_partitions_def,
)

import_seas_cal_from_fixture = define_asset_job(
    name="import_seas_cal_from_fixture",
    selection=(
        seasonal_activity_instances,
        seasonal_activity_valid_instances,
        seasonal_activity_fixture,
        imported_seasonal_activities,
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
        livelihood_summary_dataframe,
        key_parameter_dataframe,
        other_food_purchase_summ_dataframe,
        livelihood_product_category_dataframe,
        wealth_characteristic_label_dataframe,
        livelihood_activity_label_dataframe,
        other_cash_income_label_dataframe,
        wild_foods_label_dataframe,
        seasonal_calendar_dataframe,
    ),
    partitions_def=bss_instances_partitions_def,
)

# The summary labels dataframe assets contain a call to Google Translate, which
# is slow. We don't want to run them as part of the extract_dataframes job,
# because it causes the creation of the all labels and summary dataframes and
# the translation of each label to happen per partition, instead of only
# once - after all the partition-level dataframes have been created.
summarize_dataframes = define_asset_job(
    name="summarize_dataframes",
    selection=(
        all_wealth_characteristic_labels_dataframe,
        all_livelihood_activity_labels_dataframe,
        all_other_cash_income_labels_dataframe,
        all_wild_foods_labels_dataframe,
        summary_wealth_characteristic_labels_dataframe,
        summary_livelihood_activity_labels_dataframe,
        summary_other_cash_income_labels_dataframe,
        summary_wild_foods_labels_dataframe,
        summary_seasonal_calendar_labels_dataframe,
        livelihood_activity_label_recognition_dataframe,
    ),
    partitions_def=bss_instances_partitions_def,
)
