import warnings

from dagster import Definitions, EnvVar

from .assets.baseline import (
    baseline_fixture,
    bss_corrections,
    bss_files_metadata,
    bss_metadata,
    completed_bss_metadata,
    corrected_files,
)
from .assets.livelihood_activity import (
    activity_label_dataframe,
    all_activity_labels_dataframe,
    livelihood_activity_dataframe,
    livelihood_activity_fixture,
)
from .assets.wealth_characteristic import (
    all_wealth_characteristic_labels_dataframe,
    wealth_characteristic_dataframe,
    wealth_characteristic_fixture,
    wealth_characteristic_label_dataframe,
)
from .jobs.metadata import update_metadata
from .resources import (
    DataFrameCSVIOManager,
    GoogleClientResource,
    JSONIOManager,
    PickleIOManager,
)
from .sensors import bss_file_sensor

# Ignore ExperimentalWarning: Function `DagsterInstance.report_runless_asset_event`
warnings.filterwarnings("ignore", r"Function `DagsterInstance.report_runless_asset_event` is experimental")

defs = Definitions(
    assets=[
        bss_metadata,
        completed_bss_metadata,
        bss_corrections,
        bss_files_metadata,
        corrected_files,
        baseline_fixture,
        livelihood_activity_dataframe,
        activity_label_dataframe,
        all_activity_labels_dataframe,
        livelihood_activity_fixture,
        wealth_characteristic_dataframe,
        wealth_characteristic_label_dataframe,
        all_wealth_characteristic_labels_dataframe,
        wealth_characteristic_fixture,
    ],
    jobs=[update_metadata],
    resources={
        "google_client": GoogleClientResource(credentials_json=EnvVar("GOOGLE_APPLICATION_CREDENTIALS")),
        "io_manager": PickleIOManager(),  # Used by default
        "json_io_manager": JSONIOManager(),
        "dataframe_csv_io_manager": DataFrameCSVIOManager(),
    },
    sensors=[bss_file_sensor],
)
