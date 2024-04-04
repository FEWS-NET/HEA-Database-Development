import os

import django
import pandas as pd
from dagster import AssetExecutionContext, Output, asset

from ..configs import BSSMetadataConfig
from ..partitions import bss_files_partitions_def, bss_instances_partitions_def
from .base import (
    get_all_bss_labels_dataframe,
    get_bss_dataframe,
    get_bss_label_dataframe,
    get_summary_bss_label_dataframe,
)

# set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hea.settings.production")

# Configure Django with our custom settings before importing any Django classes
django.setup()

# Indexes of header rows in the Data3 dataframe (wealth_group_category, district, village)
HEADER_ROWS = [
    4,
]


@asset(partitions_def=bss_files_partitions_def)
def seasonal_production_performance_dataframe(config: BSSMetadataConfig, corrected_files) -> Output[pd.DataFrame]:
    """
    DataFrame asset for seasonal production performance from a BSS in 'Timeline' sheet
    """
    return get_bss_dataframe(
        config,
        corrected_files,
        "Timeline",
        start_strings=["Year of harvest", "year", "Année", "Production year"],
        end_strings=[
            "Chronic hazards:",
            "Chronic hazards (every year):",
            "Alás croniques",
            "Alás chroniques",
            "Aléas croniques",
            "Aléas/ risques - ranking 1 à 8",
            "Aleás croniques",
            "Aléas chroniques",
        ],
        header_rows=HEADER_ROWS,
        num_summary_cols=1,
    )


@asset(partitions_def=bss_files_partitions_def)
def seasonal_production_performance_label_dataframe(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    seasonal_production_performance_dataframe: pd.DataFrame,
) -> Output[pd.DataFrame]:
    """
    Dataframe of Seasonal Production Perf (Timeline) Label References
    """
    return get_bss_label_dataframe(
        context,
        config,
        seasonal_production_performance_dataframe,
        "seasonal_production_performance_dataframe",
        len(HEADER_ROWS),
    )


@asset(io_manager_key="dataframe_csv_io_manager")
def all_seasonal_production_performance_labels_dataframe(
    config: BSSMetadataConfig, seasonal_production_performance_label_dataframe: dict[str, pd.DataFrame]
) -> Output[pd.DataFrame]:
    """
    Combined dataframe of the seasonal production performance labels in use across all BSSs.
    """
    return get_all_bss_labels_dataframe(config, seasonal_production_performance_label_dataframe)


@asset(io_manager_key="dataframe_csv_io_manager")
def summary_seasonal_production_performance_labels_dataframe(
    config: BSSMetadataConfig, all_seasonal_production_performance_labels_dataframe: pd.DataFrame
) -> Output[pd.DataFrame]:
    """
    Summary of the seasonal production performance labels in use across all BSSs.
    """
    return get_summary_bss_label_dataframe(config, all_seasonal_production_performance_labels_dataframe)


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def seasonal_production_performance_instances(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    completed_bss_metadata,
    seasonal_production_performance_dataframe,
) -> Output[dict]:
    """
    Seasonal Production Performance instances extracted from the Timeline sheet of the BSS.
    """
    df = seasonal_production_performance_dataframe
    # The last column is the average, let us drop it
    df = df.drop(df.columns[-1], axis=1)
    df = df.melt(id_vars="Year of harvest", var_name="community", value_name="seasonal_performance")
    df["Year"] = pd.to_datetime(df["Year"], errors="coerce")

    # Function to extract start and end dates
    def extract_dates(year):
        if pd.notna(year):
            if isinstance(year, int):
                start_date = pd.Timestamp(year, 1, 1)
                end_date = pd.Timestamp(year, 12, 31)
            elif isinstance(year, pd.Timestamp):
                start_date = year
                end_date = year + pd.offsets.DateOffset(years=1) - pd.offsets.Day(1)
            else:  # Assume it's a string with a range
                start_year, end_year = map(int, year.split(" - "))
                start_date = pd.Timestamp(start_year, 1, 1)
                end_date = pd.Timestamp(end_year, 12, 31)
            return start_date, end_date
        else:
            return None, None

    # Apply the function to create new 'Start Date' and 'End Date' columns
    df[["performance_year_start_date", "performance_year_end_date"]] = df["Year"].apply(
        lambda x: pd.Series(extract_dates(x))
    )
    # TODO: agree on season default value, cover other cases for the year and return the expected dict


@asset(partitions_def=bss_files_partitions_def)
def hazards_dataframe(config: BSSMetadataConfig, corrected_files) -> Output[pd.DataFrame]:
    """
    DataFrame asset for Hazards from a BSS in 'Timeline' sheet
    """
    return get_bss_dataframe(
        config,
        corrected_files,
        "Timeline",
        start_strings=[
            "Chronic hazards:",
            "Chronic hazards (every year):",
            "Alás croniques",
            "Alás chroniques",
            "Aléas croniques",
            "Aléas/ risques - ranking 1 à 8",
            "Aleás croniques",
            "Aléas chroniques",
        ],
        header_rows=HEADER_ROWS,
        num_summary_cols=1,
    )


@asset(partitions_def=bss_files_partitions_def)
def hazard_labels_dataframe(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    hazards_dataframe: pd.DataFrame,
) -> Output[pd.DataFrame]:
    """
    Dataframe of Hazards (Timeline) Label References
    """
    return get_bss_label_dataframe(context, config, hazards_dataframe, "hazards_dataframe", len(HEADER_ROWS))


@asset(io_manager_key="dataframe_csv_io_manager")
def all_hazard_labels_dataframe(
    config: BSSMetadataConfig, hazards_dataframe_label_dataframe: dict[str, pd.DataFrame]
) -> Output[pd.DataFrame]:
    """
    Combined dataframe of the Hazards labels in use across all BSSs.
    """
    return get_all_bss_labels_dataframe(config, hazards_dataframe_label_dataframe)


@asset(io_manager_key="dataframe_csv_io_manager")
def summary_hazard_labels_dataframe(
    config: BSSMetadataConfig, all_hazards_labels_dataframe: pd.DataFrame
) -> Output[pd.DataFrame]:
    """
    Summary of the Hazards labels in use across all BSSs.
    """
    return get_summary_bss_label_dataframe(config, all_hazards_labels_dataframe)


@asset(partitions_def=bss_files_partitions_def)
def events_dataframe(config: BSSMetadataConfig, corrected_files) -> Output[pd.DataFrame]:
    """
    DataFrame asset for events from a BSS in 'Timeline' sheet
    """
    return get_bss_dataframe(
        config,
        corrected_files,
        "Timeline",
        start_strings=["Periodic hazards (not every year):", "Aléas periodiques"],
        header_rows=HEADER_ROWS,
    )
