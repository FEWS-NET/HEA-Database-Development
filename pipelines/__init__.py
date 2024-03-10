import warnings

from dagster import Definitions, EnvVar

from .assets.base import (
    bss_corrections,
    bss_metadata,
    completed_bss_metadata,
    corrected_files,
    original_files,
)
from .assets.baseline import baseline_instances
from .assets.fixtures import (
    consolidated_fixture,
    consolidated_instances,
    imported_baseline,
    uploaded_baseline,
    validated_instances,
)
from .assets.livelihood_activity import (
    all_livelihood_activity_labels_dataframe,
    livelihood_activity_dataframe,
    livelihood_activity_instances,
    livelihood_activity_label_dataframe,
    summary_livelihood_activity_labels_dataframe,
)
from .assets.other_cash_income import (
    all_other_cash_income_labels_dataframe,
    other_cash_income_dataframe,
    other_cash_income_instances,
    other_cash_income_label_dataframe,
    summary_other_cash_income_labels_dataframe,
)
from .assets.wealth_characteristic import (
    all_wealth_characteristic_labels_dataframe,
    summary_wealth_characteristic_labels_dataframe,
    wealth_characteristic_dataframe,
    wealth_characteristic_instances,
    wealth_characteristic_label_dataframe,
)
from .assets.wild_foods import (
    all_wild_foods_labels_dataframe,
    summary_wild_foods_labels_dataframe,
    wild_foods_dataframe,
    wild_foods_instances,
    wild_foods_label_dataframe,
)
from .jobs.metadata import update_metadata
from .resources import (
    DataFrameCSVIOManager,
    DataFrameExcelIOManager,
    JSONIOManager,
    PickleIOManager,
)
from .sensors import bss_instance_sensor

# Ignore ExperimentalWarning: Function `DagsterInstance.report_runless_asset_event`
warnings.filterwarnings("ignore", r"Function `DagsterInstance.report_runless_asset_event` is experimental")

defs = Definitions(
    assets=[
        bss_metadata,
        completed_bss_metadata,
        bss_corrections,
        original_files,
        corrected_files,
        baseline_instances,
        livelihood_activity_dataframe,
        livelihood_activity_label_dataframe,
        all_livelihood_activity_labels_dataframe,
        summary_livelihood_activity_labels_dataframe,
        livelihood_activity_instances,
        other_cash_income_dataframe,
        other_cash_income_label_dataframe,
        all_other_cash_income_labels_dataframe,
        summary_other_cash_income_labels_dataframe,
        other_cash_income_instances,
        wild_foods_dataframe,
        wild_foods_label_dataframe,
        all_wild_foods_labels_dataframe,
        summary_wild_foods_labels_dataframe,
        wild_foods_instances,
        wealth_characteristic_dataframe,
        wealth_characteristic_label_dataframe,
        all_wealth_characteristic_labels_dataframe,
        wealth_characteristic_instances,
        summary_wealth_characteristic_labels_dataframe,
        consolidated_instances,
        validated_instances,
        consolidated_fixture,
        uploaded_baseline,
        imported_baseline,
    ],
    jobs=[update_metadata],
    resources={
        "io_manager": PickleIOManager(base_path=EnvVar("DAGSTER_ASSET_BASE_PATH")),  # Used by default
        "json_io_manager": JSONIOManager(base_path=EnvVar("DAGSTER_ASSET_BASE_PATH")),
        "dataframe_csv_io_manager": DataFrameCSVIOManager(base_path=EnvVar("DAGSTER_ASSET_BASE_PATH")),
        "dataframe_excel_io_manager": DataFrameExcelIOManager(base_path=EnvVar("DAGSTER_ASSET_BASE_PATH")),
    },
    sensors=[bss_instance_sensor],
)
