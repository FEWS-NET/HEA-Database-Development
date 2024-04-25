import json
import os

import django
import pandas as pd
from dagster import AssetExecutionContext, MetadataValue, Output, asset

from baseline.models import Hazard  # NOQA: E402
from metadata.lookups import HazardCategoryLookup, SeasonNameLookup  # NOQA: E402

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

# Indexes of header rows in the Timeline dataframe (year, community)
HEADER_ROWS = [
    4,
]
YEAR_COLUMNS = ["Year of harvest", "year", "Year", "Année", "Production year", "Production Year"]

HAZARD_TYPE_COLUMNS = {
    Hazard.ChronicOrPeriodic.CHRONIC: [
        "Chronic hazards:",
        "Chronic hazards (every year):",
        "Alás croniques",
        "Alás chroniques",
        "Aléas croniques",
        "Aléas/ risques - ranking 1 à 8",
        "Aleás croniques",
        "Aléas chroniques",
    ],
    Hazard.ChronicOrPeriodic.PERIODIC: ["Periodic hazards (not every year):"],
}


@asset(partitions_def=bss_files_partitions_def)
def seasonal_production_performance_dataframe(config: BSSMetadataConfig, corrected_files) -> Output[pd.DataFrame]:
    """
    DataFrame asset for seasonal production performance from a BSS in 'Timeline' sheet
    """
    return get_bss_dataframe(
        config,
        corrected_files,
        "Timeline",
        start_strings=YEAR_COLUMNS,
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
    baseline_instances,
    seasonal_production_performance_dataframe,
) -> Output[dict]:
    """
    Seasonal Production Performance instances extracted from the Timeline sheet of the BSS.
    """
    partition_key = context.asset_partition_key_for_output()
    result = {
        "SeasonalProductionPerformance": seasonal_production_performance_dataframe.to_dict(orient="records"),
    }
    metadata = {
        "num_seasonal_production_performances": 0,
    }
    if seasonal_production_performance_dataframe.empty:
        # We don't have a Timeline sheet with seasonal production performance for this BSS
        # so prepare an empty dataframe with 0 counts
        metadata["message"] = (
            f"Empty seasonal production encountered for partition {partition_key}, due to missing timeline sheet"
        )
        return Output(
            result,
            metadata=metadata,
        )
    df = seasonal_production_performance_dataframe
    baseline_df = baseline_instances
    reference_year_end_date = baseline_df["LivelihoodZoneBaseline"][0]["reference_year_end_date"]
    reference_year_start_date = baseline_df["LivelihoodZoneBaseline"][0]["reference_year_start_date"]

    df = df.reset_index(drop=True)
    # The last column is the average, let us drop it
    df = df.drop(df.columns[-1], axis=1)
    # Make the column names the first row
    df.columns = df.iloc[0]
    df = df.drop([0, 1])
    df = df.reset_index(drop=True)

    def get_year_column_name(df):
        for column_name in YEAR_COLUMNS:
            if column_name in df.columns:
                return column_name
        raise ValueError(
            "No candidate columns found for the year from %s, current columns %s" % (YEAR_COLUMNS, df.columns)
        )

    # Get the name of the first matching year column
    year_column_name = get_year_column_name(df)
    df = df.rename(columns={year_column_name: "year"})
    df["year"] = df["year"].astype(str)

    df = df.melt(id_vars="year", var_name="community", value_name="seasonal_performance")

    columns = ["year", "community", "seasonal_performance"]
    df = df.dropna(subset=columns)
    # Some BSSs may contain the Timeline sheet but the entries for seasonal performance could just be empty
    if df.empty:
        metadata["message"] = f"Empty seasonal production encountered for partition {partition_key}"
        return Output(
            result,
            metadata=metadata,
        )
    df = df[df[columns].apply(lambda x: x.str.strip()).all(axis=1)]

    # Function to extract start and end dates
    def extract_dates(year):
        if pd.notna(year):
            if len(year) == 4:  # Check if it's a single year value
                start_date = f"{year}-{reference_year_start_date.split('-')[1]}-01"
                end_date = f"{int(year) + 1}-{reference_year_end_date.split('-')[1]}-01"
            else:
                if "/" in year:
                    start_year, end_year = map(str, year.split("/"))
                elif "-" in year:
                    start_year, end_year = map(str, year.split("-"))
                elif ":" in year:
                    start_year, end_year = map(str, year.split(":"))
                elif " " in year:
                    start_year, end_year = map(str, year.split())
                else:
                    raise ValueError(f"Invalid year format {str(year)}")
                # check if the year format provided is with 2 or 4 digits
                if end_year and len(end_year) == 2:
                    end_year = start_year[:2] + end_year

                start_date = f"({int(start_year)}-{int(reference_year_start_date.split(' - ')[1])}-01)"
                end_date = f"({int(end_year)}-{int(reference_year_start_date.split(' - ')[1])}-01)"
        else:
            raise ValueError("Year is not recognized")
        return start_date, end_date

    # Apply the function to create new 'Start Date' and 'End Date' columns
    df[["performance_year_start_date", "performance_year_end_date"]] = df["year"].apply(
        lambda x: pd.Series(extract_dates(x))
    )
    # Add season for a season Lookup, a default season is Harvest
    # We may need to update this for some BSS that my have season
    seasonnamelookup = SeasonNameLookup()

    def get_season():
        return [seasonnamelookup.get("Harvest", country_id=baseline_df["LivelihoodZone"][0]["country_id"])]

    df["season"] = "Harvest"
    df["season"] = df["season"].apply(lambda c: get_season())

    # Create function for looking for the community
    def get_community(community):
        for community_dict in baseline_df["Community"]:
            if community_dict["name"] == community:
                return [
                    community_dict["livelihood_zone_baseline"][0],
                    baseline_df["LivelihoodZoneBaseline"][0]["reference_year_end_date"],
                    community_dict["full_name"],
                ]
        return None
        # raise ValueError(
        #     "Unable to get community %s, perhaps that is wrongly spelled:" % (community)
        # )

    df["community"] = df["community"].apply(lambda c: get_community(c))
    df = df.dropna(subset="community")
    seasonal_performances = df.to_dict(orient="records")
    result = {
        "SeasonalProductionPerformance": seasonal_performances,
    }
    metadata = {
        "num_seasonal_production_performances": len(seasonal_performances),
        "preview": MetadataValue.md(f"```json\n{json.dumps(result, indent=4)}\n```"),
    }

    return Output(
        result,
        metadata=metadata,
    )


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


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def hazard_instances(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    baseline_instances,
    hazards_dataframe,
) -> Output[dict]:
    """
    Hazard instances extracted from the Timeline sheet of the BSS.
    """
    partition_key = context.asset_partition_key_for_output()
    result = {
        "Hazard": hazards_dataframe.to_dict(orient="records"),
    }
    metadata = {
        "hazards": 0,
    }
    if hazards_dataframe.empty:
        # We don't have a Timeline sheet with Hazard for this BSS so prepare an empty dataframe with 0 counts
        metadata["message"] = f"Empty Hazard encountered for partition {partition_key}, due to missing timeline sheet"
        return Output(
            result,
            metadata=metadata,
        )
    df = hazards_dataframe
    baseline_df = baseline_instances
    df = df.reset_index(drop=True)
    # The last column is the average, let us drop it
    df = df.drop(df.columns[-1], axis=1)
    # Make the column names the first row
    df.columns = df.iloc[0]
    df = df.drop(0)

    def get_year_column_name(df):
        for column_name in YEAR_COLUMNS:
            if column_name in df.columns:
                return column_name
        raise ValueError(
            "No candidate columns found for the year from %s, current columns %s" % (YEAR_COLUMNS, df.columns)
        )

    # Get the name of the first matching year column
    year_column_name = get_year_column_name(df)
    df = df.rename(columns={year_column_name: "ranking"})

    # Determine is chronic vs periodic
    df = df.melt(id_vars="ranking", var_name="community", value_name="hazard_category")

    df["chronic_or_periodic"] = Hazard.ChronicOrPeriodic.CHRONIC
    periodic_encountered = False
    for index, row in df.iterrows():
        if row["ranking"] in HAZARD_TYPE_COLUMNS[Hazard.ChronicOrPeriodic.PERIODIC]:
            periodic_encountered = True
        if row["ranking"] in HAZARD_TYPE_COLUMNS[Hazard.ChronicOrPeriodic.CHRONIC]:
            periodic_encountered = False
        if periodic_encountered:
            df.loc[index, "chronic_or_periodic"] = Hazard.ChronicOrPeriodic.PERIODIC

    # Drop empty or invalid ranking and hazard values
    df = df[df["ranking"].apply(lambda x: isinstance(x, int) and x != "")]
    df = df[
        df["hazard_category"].apply(
            lambda x: isinstance(x, str) and x.strip() != "" and not pd.isna(x) and not pd.isnull(x)
        )
    ]
    # Some BSSs may contain the Timeline sheet but the entries for Hazards could just be empty
    if df.empty:
        metadata["message"] = f"Empty Hazards encountered for partition {partition_key}"
        return Output(
            result,
            metadata=metadata,
        )
    df["hazard_category"] = df["hazard_category"].str.lower()
    df = HazardCategoryLookup().do_lookup(df, "hazard_category", "hazard_category")

    def get_community(community):
        for community_dict in baseline_df["Community"]:
            if community_dict["name"] == community:
                return [
                    community_dict["livelihood_zone_baseline"][0],
                    baseline_df["LivelihoodZoneBaseline"][0]["reference_year_end_date"],
                    community_dict["full_name"],
                ]
        return None
        # raise ValueError(
        #     "Unable to get community %s, perhaps that is wrongly spelled:" % (community)
        # )

    df["community"] = df["community"].apply(lambda c: get_community(c))
    df = df.dropna(subset="community")
    hazards = df.to_dict(orient="records")
    result = {
        "Hazard": hazards,
    }
    metadata = {
        "num_hazards": len(hazards),
        "preview": MetadataValue.md(f"```json\n{json.dumps(result, indent=4)}\n```"),
    }

    return Output(
        result,
        metadata=metadata,
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
    config: BSSMetadataConfig, hazard_labels_dataframe: dict[str, pd.DataFrame]
) -> Output[pd.DataFrame]:
    """
    Combined dataframe of the Hazards labels in use across all BSSs.
    """
    return get_all_bss_labels_dataframe(config, hazard_labels_dataframe)


@asset(io_manager_key="dataframe_csv_io_manager")
def summary_hazard_labels_dataframe(
    config: BSSMetadataConfig, all_hazard_labels_dataframe: pd.DataFrame
) -> Output[pd.DataFrame]:
    """
    Summary of the Hazards labels in use across all BSSs.
    """
    return get_summary_bss_label_dataframe(config, all_hazard_labels_dataframe)


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
