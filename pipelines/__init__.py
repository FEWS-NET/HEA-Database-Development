import warnings

from dagster import Definitions, EnvVar

from .assets.base import (
    bss_metadata,
    completed_bss_metadata,
    corrected_files,
    original_files,
)
from .assets.baseline import baseline_instances, community_instances
from .assets.fixtures import (
    consolidated_fixture,
    imported_baseline,
    imported_communities,
    uploaded_baselines,
)
from .assets.livelihood_activity import (
    all_livelihood_activity_labels_dataframe,
    imported_livelihood_activities,
    livelihood_activity_dataframe,
    livelihood_activity_fixture,
    livelihood_activity_instances,
    livelihood_activity_label_dataframe,
    livelihood_activity_valid_instances,
    livelihood_summary_dataframe,
    summary_livelihood_activity_labels_dataframe,
)
from .assets.other_cash_income import (
    all_other_cash_income_labels_dataframe,
    imported_other_cash_income_activities,
    other_cash_income_dataframe,
    other_cash_income_fixture,
    other_cash_income_instances,
    other_cash_income_label_dataframe,
    other_cash_income_valid_instances,
    summary_other_cash_income_labels_dataframe,
)
from .assets.wealth_characteristic import (
    all_wealth_characteristic_labels_dataframe,
    imported_wealth_characteristics,
    summary_wealth_characteristic_labels_dataframe,
    wealth_characteristic_dataframe,
    wealth_characteristic_fixture,
    wealth_characteristic_instances,
    wealth_characteristic_label_dataframe,
    wealth_characteristic_valid_instances,
)
from .assets.wild_foods import (
    all_wild_foods_labels_dataframe,
    imported_wild_foods_activities,
    summary_wild_foods_labels_dataframe,
    wild_foods_dataframe,
    wild_foods_fixture,
    wild_foods_instances,
    wild_foods_label_dataframe,
    wild_foods_valid_instances,
)
from .jobs.fixtures import (
    extract_dataframes,
    import_baseline_from_fixture,
    update_external_assets,
    upload_baselines,
)
from .jobs.metadata import load_all_geographies, update_metadata
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
        original_files,
        corrected_files,
        baseline_instances,
        community_instances,
        livelihood_activity_dataframe,
        livelihood_summary_dataframe,
        livelihood_activity_label_dataframe,
        all_livelihood_activity_labels_dataframe,
        summary_livelihood_activity_labels_dataframe,
        livelihood_activity_instances,
        livelihood_activity_valid_instances,
        livelihood_activity_fixture,
        imported_livelihood_activities,
        other_cash_income_dataframe,
        other_cash_income_label_dataframe,
        all_other_cash_income_labels_dataframe,
        summary_other_cash_income_labels_dataframe,
        other_cash_income_instances,
        other_cash_income_valid_instances,
        other_cash_income_fixture,
        imported_other_cash_income_activities,
        wild_foods_dataframe,
        wild_foods_label_dataframe,
        all_wild_foods_labels_dataframe,
        summary_wild_foods_labels_dataframe,
        wild_foods_instances,
        wild_foods_valid_instances,
        wild_foods_fixture,
        imported_wild_foods_activities,
        wealth_characteristic_dataframe,
        wealth_characteristic_label_dataframe,
        all_wealth_characteristic_labels_dataframe,
        wealth_characteristic_instances,
        wealth_characteristic_valid_instances,
        wealth_characteristic_fixture,
        imported_wealth_characteristics,
        summary_wealth_characteristic_labels_dataframe,
        consolidated_fixture,
        uploaded_baselines,
        imported_communities,
        imported_baseline,
    ],
    jobs=[
        update_metadata,
        update_external_assets,
        upload_baselines,
        extract_dataframes,
        import_baseline_from_fixture,
        load_all_geographies,
    ],
    resources={
        "io_manager": PickleIOManager(base_path=EnvVar("DAGSTER_ASSET_BASE_PATH")),  # Used by default
        "json_io_manager": JSONIOManager(base_path=EnvVar("DAGSTER_ASSET_BASE_PATH")),
        "dataframe_csv_io_manager": DataFrameCSVIOManager(base_path=EnvVar("DAGSTER_ASSET_BASE_PATH")),
        "dataframe_excel_io_manager": DataFrameExcelIOManager(base_path=EnvVar("DAGSTER_ASSET_BASE_PATH")),
    },
    sensors=[bss_instance_sensor],
)
