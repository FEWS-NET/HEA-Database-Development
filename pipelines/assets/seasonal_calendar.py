"""
Dagster assets related to Seasonal Calender, read from the 'Seas Cal' worksheet in a BSS.

An example of relevant rows from the worksheet:

        |SEASONAL CALENDAR                                                                                                   |Fill 1s in the relevant months                                                                                                                                              |
        |-----------------|--------|------|----|------|------|------|------|------|-------|-------|-------|-------|----------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|-------|
        |                 |        |      |    |      |      |      |      |      |       |       |       |       |          |       |       |       |       |       |       |       |       |       |       |       |
        |village -->      |Njobvu  |      |    |      |      |      |      |      |       |       |       |       |Kalikokha |       |       |       |       |       |       |       |       |       |       |       |
        |month -->        |4       |5     |6   |7     |8     |9     |10    |11    |12     |1      |2      |3      |4         |5      |6      |7      |8      |9      |10     |11     |12     |1      |2      |3      |
        |Seasons          |        |      |    |      |      |      |      |      |       |       |       |       |          |       |       |       |       |       |       |       |       |       |       |       |
        |rainy            |        |      |    |      |      |      |      |1     |1      |1      |1      |       |          |       |       |       |       |       |       |1      |1      |1      |1      |1      |
        |winter           |        |      |    |      |      |      |      |      |       |       |       |       |          |1      |1      |1      |       |       |       |       |       |       |       |       |
        |hot              |        |      |    |      |      |      |      |      |       |       |       |       |          |       |       |       |       |1      |1      |1      |1      |1      |       |       |
        |Maize rainfed    |        |      |    |      |      |      |      |      |       |       |       |       |          |       |       |       |       |       |       |       |       |       |       |       |
        |land preparation |        |      |    |1     |1     |1     |1     |      |       |       |       |       |          |       |       |1      |1      |1      |1      |       |       |       |       |       |
        |planting         |        |      |    |      |      |      |      |1     |1      |1      |       |       |          |       |       |       |       |       |       |1      |1      |       |       |       |
        |weeding          |        |      |    |      |      |      |      |      |       |1      |1      |1      |          |       |       |       |       |       |       |       |1      |1      |1      |       |
        |green consumption|1       |      |    |      |      |      |      |      |       |       |       |1      |          |       |       |       |       |       |       |       |       |       |1      |1      |
        |harvesting       |        |      |1   |1     |      |      |      |      |       |       |       |       |1         |1      |       |       |       |       |       |       |       |       |       |       |
        |threshing        |        |      |    |1     |1     |      |      |      |       |       |       |       |1         |1      |1      |1      |       |       |       |       |       |       |       |       |
        |Tobacco          |        |      |    |      |      |      |      |      |       |       |       |       |          |       |       |       |       |       |       |       |       |       |       |       |
        |land preparation |        |      |    |1     |1     |1     |      |      |       |       |       |       |1         |1      |1      |1      |       |       |       |       |       |       |       |       |
        |planting         |        |      |    |      |      |1     |1     |1     |       |       |       |       |          |       |       |       |1      |1      |       |       |       |       |       |       |
        |weeding          |        |      |    |      |      |      |      |      |1      |       |       |       |          |       |       |       |       |       |1      |1      |       |       |       |       |
        |green consumption|        |      |    |      |      |      |      |      |       |       |       |       |          |       |       |       |       |       |       |       |       |       |       |       |
        |harvesting       |        |      |    |      |      |      |      |      |       |1      |1      |1      |1         |       |       |       |       |       |       |       |       |       |1      |1      |
        |threshing        |        |      |    |      |      |      |      |      |       |       |       |       |          |       |       |       |       |       |       |       |       |       |       |       |

     
"""  # NOQA: E501

import functools
import json
import math
import os

import django
import numpy as np
import pandas as pd
from dagster import AssetExecutionContext, MetadataValue, Output, asset

from baseline.models import Community, LivelihoodZoneBaseline  # NOQA: E402
from metadata.models import ActivityLabel  # NOQA: E402
from metadata.models import LabelStatus  # NOQA: E402

from .. import imported_baselines
from ..configs import BSSMetadataConfig
from ..partitions import bss_instances_partitions_def
from .base import (
    get_all_bss_labels_dataframe,
    get_bss_dataframe,
    get_bss_label_dataframe,
)
from .fixtures import get_fixture_from_instances, validate_instances

# set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hea.settings.production")

# Configure Django with our custom settings before importing any Django classes
django.setup()

# Indexes of header rows in the seasonal_calendar dataframe
HEADER_ROWS = [
    3,
]
SEAS_CAL = "Seas Cal"
# Cut-off percentage to determine the threshold of occurrences
CUT_OFF = 0.5


@asset(partitions_def=bss_instances_partitions_def)
def seasonal_calendar_dataframe(config: BSSMetadataConfig, corrected_files) -> Output[pd.DataFrame]:
    """
    DataFrame of seasonal calendar from a BSS
    """
    return get_bss_dataframe(
        config,
        corrected_files,
        "Seas Cal",
        start_strings=["Village :", "village -->"],
        header_rows=HEADER_ROWS,
    )


@asset(partitions_def=bss_instances_partitions_def)
def seasonal_calendar_label_dataframe(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    seasonal_calendar_dataframe,
) -> Output[pd.DataFrame]:
    """
    Dataframe of seasonal calendar (Seas Cal) Label References
    """
    return get_bss_label_dataframe(
        context, config, seasonal_calendar_dataframe, "seasonal_calendar_dataframe", len(HEADER_ROWS)
    )


@asset(io_manager_key="dataframe_csv_io_manager")
def all_seasonal_calendar_labels_dataframe(
    config: BSSMetadataConfig, seasonal_calendar_label_dataframe: dict[str, pd.DataFrame]
) -> Output[pd.DataFrame]:
    """
    Combined dataframe of the seasonal calendar labels in use across all BSSs wherever the sheet is available.
    """
    return get_all_bss_labels_dataframe(config, seasonal_calendar_label_dataframe)


@functools.cache
def get_seas_cal_label() -> dict[str, dict]:
    """ """
    label_map = {
        instance["activity_label"].lower(): instance
        for instance in ActivityLabel.objects.filter(
            status=LabelStatus.COMPLETE, activity_type=SEAS_CAL, is_start=True
        ).values(
            "activity_label",
            "is_start",
            "product",
            "season",
            "additional_identifier",
            "notes",
        )
    }
    return label_map


def get_seas_cal_instances_from_dataframe(
    context: AssetExecutionContext,
    df: pd.DataFrame,
    livelihood_zone_baseline: LivelihoodZoneBaseline,
    partition_key: str,
) -> Output[dict]:
    # Read the df, from its first column after doing the formatting and try creating the
    # SeasonalActvity and SeasonalActivityOccurence
    # Remove the bottom part that usually contains empty or 0 entry with 'Other' or 'autre'
    last_valid_index = df[~df.iloc[:, 0].str.lower().isin(["other", "autre"])].index[-1]
    df_original = df.iloc[: last_valid_index + 1]
    df_original.reset_index(drop=True, inplace=True)
    # drop first row
    df_original = df_original.drop(0).reset_index(drop=True)
    # Rename initial values for clarity
    df_original.iloc[0, 0] = "community"
    df_original.iloc[1, 0] = "month"

    df_original.replace("", np.nan, inplace=True)
    df_original.iloc[0, 1:] = df_original.iloc[0, 1:].ffill(axis=0)

    # Drop season rows
    df_original = df_original.drop(index=range(2, 6))
    df_original.reset_index(drop=True, inplace=True)

    df = df_original

    # Get the label mapping dictionary
    label_mapping = get_seas_cal_label()

    # Extract the first two rows for community and month information
    community_row = df.iloc[0, 1:]
    month_row = df.iloc[1, 1:]

    # Initialize results and current header
    results = []
    current_header = None
    has_children = False

    # Iterate over rows, starting from row 3 (index 2)
    for index, row in df.iloc[2:].iterrows():
        label_value = row.iloc[0].lower().strip()
        # Check if the row is a header based on label_mapping
        if label_value in label_mapping:
            # Add standalone entry if previous header had no children
            if current_header and not has_children:
                mapping_data = label_mapping[current_header]
                results.append(
                    {
                        "seasonal_activity_label": current_header,
                        "product": mapping_data["product"],
                        "additional_identifier": mapping_data["additional_identifier"],
                        "seasonal_activity_type": None,
                        "community": None,
                        "month": None,
                        "occurrence": None,
                    }
                )
            # Update header and reset tracking for children
            current_header = label_value
            has_children = False
        elif current_header:
            # Process each child row for presence values
            if row.iloc[2:].notna().any():
                has_children = True
                for col_index, presence_value in row.iloc[2:].items():
                    if not pd.isnull(presence_value):
                        presence_value = int(presence_value)
                    if not pd.isnull(presence_value) and presence_value >= 1:
                        presence_value = int(presence_value)  # Convert to int if not NaN
                        mapping_data = label_mapping[current_header]

                        result_row = {
                            "seasonal_activity_label": current_header,
                            "product": mapping_data["product"],
                            "additional_identifier": mapping_data["additional_identifier"].strip(),
                            "seasonal_activity_type": label_value,
                            "community": community_row[col_index],
                            "month": month_row[col_index],
                            "occurrence": presence_value,
                        }
                        results.append(result_row)

    # Add final standalone entry if last header has no children
    if current_header and not has_children:
        mapping_data = label_mapping[current_header]
        results.append(
            {
                "seasonal_activity_label": current_header,
                "product": mapping_data["product"],
                "additional_identifier": mapping_data["additional_identifier"].strip(),
                "seasonal_activity_type": None,
                "community": None,
                "month": None,
                "occurrence": None,
            }
        )
    df_results = pd.DataFrame(results)
    # drop if community wasn't provided for some rows
    df_results.dropna(subset=["community"], inplace=True)

    df_seasonal_activity = df_results.copy()
    df_seasonal_activity.fillna("")
    df_seasonal_activity.drop_duplicates(
        subset=["product", "additional_identifier", "seasonal_activity_type"], inplace=True
    )
    # add livelihood_zone_baseline's natual key to the datafame
    df_seasonal_activity["livelihood_zone_baseline"] = [
        [livelihood_zone_baseline.livelihood_zone_id, livelihood_zone_baseline.reference_year_end_date.isoformat()]
    ] * len(df_seasonal_activity)
    # we don't have a specific season to tie to
    df_seasonal_activity["season"] = [[] for _ in range(len(df_seasonal_activity))]
    seasonal_activities = df_seasonal_activity[
        ["livelihood_zone_baseline", "seasonal_activity_type", "product", "additional_identifier", "season"]
    ].to_dict(orient="records")

    # populate the community full name from the corresponding livelihood_zone_baseline
    community_list = Community.objects.filter(livelihood_zone_baseline=livelihood_zone_baseline)
    community_dict = {
        community.name.lower(): {
            "full_name": community.full_name,
            "aliases": [alias.strip().lower() for alias in community.aliases] if community.aliases else [],
        }
        for community in community_list
    }
    df_zonal_level = df_results[df_results["community"].isin(["Synthèse", "Results"])]
    df_community_level = df_results[~df_results["community"].isin(["Synthèse", "Results"])]

    def lookup_community_full_name(name):
        name = name.strip().lower()
        if name in community_dict:
            return community_dict[name]["full_name"]
        # If not found, search through aliases
        for community_info in community_dict.values():
            if name in community_info["aliases"]:
                return community_info["full_name"]

        # If no match is found, return a default value or keep as-is
        raise ValueError(
            "%s contains unmatched Community name values in worksheet %s:\n%s\n\nExpected names are:\n  %s"
            % (
                partition_key,
                "Seas Cal",
                name,
                "\n  ".join(
                    Community.objects.filter(livelihood_zone_baseline=livelihood_zone_baseline).values_list(
                        "name", flat=True
                    )
                ),
            )
        )

    # Populate 'full_name' to the community DataFrame
    df_community_level["community"] = df_community_level["community"].apply(lookup_community_full_name)
    # For the zone level, we shall use an aggregate occurrence as cut-off, i.e. if the total reported is greater than
    # the CUT_OFF or more we shall consider its occurrence for the zone

    no_of_communities = len(df_community_level["community"].unique())
    threshold = math.ceil(CUT_OFF * no_of_communities)
    df_zonal_level = df_zonal_level[df_zonal_level["occurrence"] >= threshold]
    # we can merge the two now
    df = pd.concat([df_community_level, df_zonal_level], ignore_index=True)

    # Extract the start and end dates considering a continuous block of months if present
    # Define month boundaries in a dictionary (simplified with 365 days in a year)
    month_days = {
        1: (1, 31),
        2: (32, 59),
        3: (60, 90),
        4: (91, 120),
        5: (121, 151),
        6: (152, 181),
        7: (182, 212),
        8: (213, 243),
        9: (244, 273),
        10: (274, 304),
        11: (305, 334),
        12: (335, 365),
    }

    # Function to build start and end dates for contiguous blocks
    # Fill missing values with a placeholder
    df["product"] = df["product"].fillna("<missing>")
    df["additional_identifier"] = df["additional_identifier"].fillna("<missing>")

    def build_start_end_dates(group):
        occurrences = group["month"].sort_values().tolist()
        blocks = []
        start_month = occurrences[0]
        prev_month = start_month

        for i in range(1, len(occurrences)):
            current_month = occurrences[i]
            if current_month == prev_month + 1 or (prev_month == 12 and current_month == 1):
                prev_month = current_month
            else:
                blocks.append((start_month, prev_month))
                start_month = current_month
                prev_month = current_month

        blocks.append((start_month, prev_month))

        date_ranges = []
        for start, end in blocks:
            start_day = month_days[start][0]
            end_day = month_days[end][1]
            date_ranges.append({"start": start_day, "end": end_day})

        return pd.DataFrame(date_ranges)

    # Group by all relevant columns and apply the function
    result = (
        df.groupby(["product", "additional_identifier", "seasonal_activity_type", "community"], dropna=False)
        .apply(build_start_end_dates)
        .reset_index(level=[0, 1, 2, 3], drop=False)
    )

    # Replace the placeholder back with NaN for a clean final output
    result["product"].replace("<missing>", pd.NA, inplace=True)
    result["additional_identifier"].replace("<missing>", pd.NA, inplace=True)

    # replace the 'Results' community placeholder with NaN for the community representing zonal value
    result.loc[result["community"].isin(["Synthèse", "Results"]), "community"] = np.nan
    result = result.fillna("")

    def create_seasonal_activity_column(row):
        """
        Combine seasonal activity natural keys to create the column.
        """
        columns = ["seasonal_activity_type", "product", "additional_identifier"]
        non_null_values = [lz for lz in row["livelihood_zone_baseline"]]
        non_null_values += [str(row[col]) for col in columns if pd.notna(row[col])]
        row["seasonal_activity"] = non_null_values
        return row

    def update_community(row):
        identifers = [lz for lz in row["livelihood_zone_baseline"]]
        if not row["community"]:
            row["community"] = None
            return row
        identifers.append(row["community"])
        row["community"] = identifers
        return row

    # Assign the livelihood_zone_baseline for each row
    result["livelihood_zone_baseline"] = [
        [livelihood_zone_baseline.livelihood_zone_id, livelihood_zone_baseline.reference_year_end_date.isoformat()]
    ] * len(result)

    # Apply the function and update each row in result
    result = result.apply(create_seasonal_activity_column, axis=1)
    result = result.apply(update_community, axis=1)

    seasonal_activity_occurences = result[
        ["livelihood_zone_baseline", "seasonal_activity", "community", "start", "end"]
    ].to_dict(orient="records")
    result = {
        "SeasonalActivity": seasonal_activities,
        "SeasonalActivityOccurrence": seasonal_activity_occurences,
    }
    metadata = {
        "num_seasonal_activities": len(seasonal_activities),
        "num_seasonal_activity_occurences": len(seasonal_activity_occurences),
        "preview": MetadataValue.md(f"```json\n{json.dumps(result, indent=4)}\n```"),
    }
    return Output(
        result,
        metadata=metadata,
    )


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def seasonal_calendar_instances(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    seasonal_calendar_dataframe,
) -> Output[dict]:
    """ """
    partition_key = context.asset_partition_key_for_output()
    livelihood_zone_baseline = LivelihoodZoneBaseline.objects.get_by_natural_key(*partition_key.split("~")[1:])

    instances = get_seas_cal_instances_from_dataframe(
        context, seasonal_calendar_dataframe, livelihood_zone_baseline, partition_key
    )
    if isinstance(instances, Output):
        instances = instances.value

    metadata = {f"num_{key.lower()}": len(value) for key, value in instances.items()}
    metadata["total_instances"] = sum(len(value) for value in instances.values())
    metadata["preview"] = MetadataValue.md(f"```json\n{json.dumps(instances, indent=4)}\n```")

    return Output(
        instances,
        metadata=metadata,
    )


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def validated_seas_cal_instances(
    context: AssetExecutionContext,
    seasonal_calendar_instances,
) -> Output[dict]:
    """
    Validated seas_cal instances from a BSS, ready to be loaded via a Django fixture.
    """
    partition_key = context.asset_partition_key_for_output()
    # validate the instances using the common method
    validate_instances(seasonal_calendar_instances, partition_key)

    metadata = {f"num_{key.lower()}": len(value) for key, value in seasonal_calendar_instances.items()}
    metadata["total_instances"] = sum(len(value) for value in seasonal_calendar_instances.values())
    metadata["preview"] = MetadataValue.md(f"```json\n{json.dumps(seasonal_calendar_instances, indent=4)}\n```")
    return Output(
        seasonal_calendar_instances,
        metadata=metadata,
    )


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def consolidated_seas_cal_fixtures(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    validated_seas_cal_instances,
) -> Output[list[dict]]:
    """
    Consolidate the season calendar fixtures to make it ready for importing
    """
    metadata, fixture = get_fixture_from_instances(validated_seas_cal_instances)
    metadata["preview"] = MetadataValue.md(f"```json\n{json.dumps(fixture, indent=4)}\n```")
    return Output(
        fixture,
        metadata=metadata,
    )


@asset(partitions_def=bss_instances_partitions_def)
def imported_seas_cals(
    context: AssetExecutionContext,
    consolidated_seas_cal_fixtures,
) -> Output[None]:
    """
    Attempt to import the season calendar given the consolidated seas_cal fixtures using the
    imported_baselines common method
    """

    return imported_baselines(None, consolidated_seas_cal_fixtures)
