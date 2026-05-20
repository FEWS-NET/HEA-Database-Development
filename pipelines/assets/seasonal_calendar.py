"""
Dagster assets related to Seasonal Calendar, read from the 'Seas Cal' worksheet in a BSS.

An example of relevant rows from the worksheet:

    |    | A                 | B      |   C |   D |   E |   F |   G |   H |   I |   J |   K |   L |   M | N            |   O |   P |   Q |   R |   S |   T |
    |---:|:------------------|:-------|----:|----:|----:|----:|----:|----:|----:|----:|----:|----:|----:|:-------------|----:|----:|----:|----:|----:|----:|
    |  1 | SEASONAL CALENDAR |        |     |     |     |     |     |     |     |     |     |     |     |              |     |     |     |     |     |     |
    |  2 |                   |        |     |     |     |     |     |     |     |     |     |     |     |              |     |     |     |     |     |     |
    |  3 | village -->       | Lamisu |     |     |     |     |     |     |     |     |     |     |     | Garin Kabaru |     |     |     |     |     |     |
    |  4 | month -->         | 9      |  10 |  11 |  12 |   1 |   2 |   3 |   4 |   5 |   6 |   7 |   8 | 9            |  10 |  11 |  12 |   1 |   2 |   3 |
    |  5 | Seasons           |        |     |     |     |     |     |     |     |     |     |     |     |              |     |     |     |     |     |     |
    |  6 | Rain              | 1      |     |     |     |     |     |     |     |     |   1 |   1 |   1 | 1            |     |     |     |     |     |     |
    |  7 | Dry season        |        |   1 |   1 |   1 |   1 |   1 |   1 |   1 |   1 |     |     |     |              |   1 |   1 |   1 |   1 |   1 |   1 |
    |  8 | enter name here   |        |     |     |     |     |     |     |     |     |     |     |     |              |     |     |     |     |     |     |
    |  9 | Millet            |        |     |     |     |     |     |     |     |     |     |     |     |              |     |     |     |     |     |     |
    | 10 | land preparation  |        |     |     |     |     |     |     |     |   1 |   1 |     |     |              |     |     |     |     |     |     |
    | 11 | planting          |        |     |     |     |     |     |     |     |     |   1 |   1 |     |              |     |     |     |     |     |     |
    | 12 | weeding           |        |     |     |     |     |     |     |     |     |     |   1 |   1 |              |     |     |     |     |     |     |
    | 13 | harvesting        | 1      |   1 |   1 |     |     |     |     |     |     |     |     |     | 1            |   1 |   1 |     |     |     |     |
    | 14 | threshing         |        |     |   1 |   1 |     |     |     |     |     |     |     |     |              |     |   1 |   1 |     |     |     |
    | 15 | Sorghum           |        |     |     |     |     |     |     |     |     |     |     |     |              |     |     |     |     |     |     |
    | 16 | land preparation  |        |     |     |     |     |     |     |     |   1 |   1 |     |     |              |     |     |     |     |     |     |
    | 17 | planting          |        |     |     |     |     |     |     |     |     |   1 |   1 |     |              |     |     |     |     |     |     |
    | 18 | weeding           |        |     |     |     |     |     |     |     |     |     |   1 |   1 |              |     |     |     |     |     |     |
    | 19 | harvesting        | 1      |   1 |   1 |     |     |     |     |     |     |     |     |     | 1            |   1 |   1 |     |     |     |     |
    | 20 | threshing         |        |     |   1 |   1 |     |     |     |     |     |     |     |     |              |     |   1 |   1 |     |     |     |

Note that the product lines act as a header row and that product applies to the lines immediately below it
that contain the seasonal activity type.

Some other BSSs have the product in column A and the seasonal_activity_type in column B, e.g. NE08-GAY~2016:

    |    | A                     | B                     | C                |   D |   E |   F |   G |   H |   I |   J |   K |   L |   M |   N | O             |   P |   Q |   R |   S |   T |
    |---:|:----------------------|:----------------------|:-----------------|----:|----:|----:|----:|----:|----:|----:|----:|----:|----:|----:|:--------------|----:|----:|----:|----:|----:|
    |  1 |                       | CALENDRIER SAISONIER  |                  |     |     |     |     |     |     |     |     |     |     |     |               |     |     |     |     |     |
    |  2 |                       |                       |                  |     |     |     |     |     |     |     |     |     |     |     |               |     |     |     |     |     |
    |  3 | Activités/évenements  | Village :             | Tounga Tahirou   |     |     |     |     |     |     |     |     |     |     |     | Koira Tégui I |     |     |     |     |     |
    |  4 |                       | mois (1-12)           | 9                |  10 |  11 |  12 |   1 |   2 |   3 |   4 |   5 |   6 |   7 |   8 | 9             |  10 |  11 |  12 |   1 |   2 |
    |  5 |                       |                       |                  |     |     |     |     |     |     |     |     |     |     |     |               |     |     |     |     |     |
    |  6 | Pluie                 |                       | 1                |   1 |     |     |     |     |     |   1 |   1 |   1 |   1 |   1 | 1             |   1 |     |     |     |     |
    |  7 | Mil                   | Préparation du sol    |                  |     |     |     |     |     |   1 |   1 |     |     |     |     |               |     |     |     |     |     |
    |  8 |                       | Semis                 |                  |     |     |     |     |     |     |     |   1 |     |     |     |               |     |     |     |     |     |
    |  9 |                       | Sarclage/labour       |                  |     |     |     |     |     |     |     |     |   1 |   1 |   1 |               |     |     |     |     |     |
    | 10 |                       | Récolte               | 1                |   1 |     |     |     |     |     |     |     |     |     |     | 1             |   1 |     |     |     |     |
    | 11 | Sorgho                | Préparation du sol    |                  |     |     |     |     |     |   1 |   1 |     |     |     |     |               |     |     |     |     |     |
    | 12 |                       | Semis                 |                  |     |     |     |     |     |     |     |   1 |   1 |     |     |               |     |     |     |     |     |
    | 13 |                       | Sarclage/labour       |                  |     |     |     |     |     |     |     |     |   1 |   1 |   1 |               |     |     |     |     |     |
    | 14 |                       | Récolte               |                  |   1 |   1 |     |     |     |     |     |     |     |     |     |               |   1 |   1 |     |     |     |
    | 15 | Riz                   |                       |                  |     |     |     |     |     |     |     |     |     |     |     |               |     |     |     |     |     |
    | 16 | Maraîchage            | Préparation du sol    | 1                |   1 |     |     |     |     |     |     |     |     |     |     | 1             |   1 |     |     |     |     |
    | 17 |                       | Pépinière et répicage |                  |     |   1 |   1 |     |     |     |     |     |     |     |     |               |     |   1 |   1 |     |     |
    | 18 |                       | Récolte et vente      |                  |     |     |     |     |   1 |   1 |   1 |     |     |     |     |               |     |     |     |     |   1 |
    | 19 | Mangue                |                       |                  |     |     |     |     |     |   1 |   1 |   1 |   1 |     |     |               |     |     |     |     |     |
    | 20 | Exploitation rôneraie |                       |                  |     |   1 |   1 |     |     |     |   1 |   1 |     |     |     |               |     |   1 |   1 |     |     |


"""  # NOQA: E501

import json
import os

import django
import pandas as pd
from dagster import (
    AssetExecutionContext,
    MetadataValue,
    Output,
    asset,
)
from googletrans import Translator

from ..configs import BSSMetadataConfig
from ..partitions import bss_instances_partitions_def
from .base import (
    get_all_bss_labels_dataframe,
    get_bss_dataframe,
    get_bss_label_dataframe,
)
from .fixtures import get_fixture_from_instances, import_fixture, validate_instances

# set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hea.settings.production")

# Configure Django with our custom settings before importing any Django classes
django.setup()

from baseline.lookups import CommunityLookup  # NOQA: E402
from baseline.models import LivelihoodZoneBaseline  # NOQA: E402
from common.lookups import ClassifiedProductLookup  # NOQA: E402
from common.utils import get_start_end_day_ranges_from_months  # NOQA: E402
from metadata.lookups import SeasonalActivityTypeLookup  # NOQA: E402

# Indexes of header rows in the 'Seas Cal' dataframe (community name, month number)
HEADER_ROWS = [3, 4]

# BSSs don't contain reconciled Baseline-level Seasonal Activity Occurrences, so we create a
# Baseline Seasonal Activity Occurrence when >= this fraction of communities report occurrence
# of the Seasonal Activity in a given month.
COMMUNITY_OCCURRENCE_THRESHOLD = 0.6


@asset(partitions_def=bss_instances_partitions_def)
def seasonal_calendar_dataframe(config: BSSMetadataConfig, corrected_files) -> Output[pd.DataFrame]:
    """
    DataFrame of seasonal calendar from a BSS
    """
    return get_bss_dataframe(
        config,
        corrected_files,
        "Seas Cal",
        start_strings=["Village :", "village -->", "Site :", "Site", "site :"],
        header_rows=HEADER_ROWS,
        num_summary_cols=12,  # There is one summary column per month.
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

    # Determine whether the worksheet has products in column A and activity types in column B.
    seasonalactivitytypelookup = SeasonalActivityTypeLookup()
    try:
        seasonalactivitytypelookup.do_lookup(seasonal_calendar_dataframe, "B", "seasonal_activity_type")
        num_label_cols = 2
    except ValueError:
        num_label_cols = 1

    return get_bss_label_dataframe(
        context,
        config,
        seasonal_calendar_dataframe,
        "seasonal_calendar_dataframe",
        len(HEADER_ROWS),
        num_summary_cols=12,  # There is one summary column per month.
        num_label_cols=num_label_cols,
    )


@asset(io_manager_key="dataframe_csv_io_manager")
def all_seasonal_calendar_labels_dataframe(
    config: BSSMetadataConfig, seasonal_calendar_label_dataframe: dict[str, pd.DataFrame]
) -> Output[pd.DataFrame]:
    """
    Combined dataframe of the seasonal calendar labels in use across all BSSs wherever the sheet is available.
    """
    return get_all_bss_labels_dataframe(config, seasonal_calendar_label_dataframe)


@asset(io_manager_key="dataframe_csv_io_manager")
def summary_seasonal_calendar_labels_dataframe(
    config: BSSMetadataConfig, all_seasonal_calendar_labels_dataframe: pd.DataFrame
) -> Output[pd.DataFrame]:
    """
    Summary of the Seas Cal labels in use across all BSSs, with recognition status and translations.
    """
    df = all_seasonal_calendar_labels_dataframe.sort_values(by=["label_lower", "row_number", "bss"])

    # Group by label_lower and aggregate
    df = (
        df.groupby("label_lower")
        .agg(
            # Create comma-separated list of unique languages
            langs=("lang", lambda x: ", ".join(x.sort_values().unique())),
            datapoint_count=("datapoint_count", lambda x: x.fillna(0).sum()),
            # Force single True/False values to 1/0 and then sum.
            summary_count=("in_summary", lambda x: x.fillna(0).astype(int).sum()),
            unique_bss_count=("bss", pd.Series.nunique),
            min_row_number=("row_number", "min"),
            max_row_number=("row_number", "max"),
            bss_for_min_row=("bss", "first"),  # Assuming df is sorted by row_number within each group
            bss_for_max_row=("bss", "last"),  # Assuming df is sorted by row_number within each group
        )
        .reset_index()
        .rename(columns={"label_lower": "label"})
        .sort_values(by=["min_row_number", "label", "bss_for_min_row", "bss_for_max_row"])
    )

    # Add a translation of the label
    translator = Translator()

    def translate_label(label, langs):
        """
        Use the Google Translate API to translate the label from <lang> to English
        """
        langs = [lang.strip() for lang in langs.split(",") if lang.strip() != "en"]
        if not langs:
            return label
        try:
            translation = translator.translate(label, dest="en", src=langs[0])
            return translation.text
        except Exception:
            return ""

    df["translation"] = df.apply(lambda x: translate_label(x["label"], x["langs"]), axis="columns")

    # Prepare the lookups
    classifiedproductlookup = ClassifiedProductLookup()
    seasonalactivitytypelookup = SeasonalActivityTypeLookup()

    # Add a column for the recognized Seasonal Activity Type or Product.
    # Update the status in priority order to match the logic in seasonal_activity_instances, so that the status
    # reports a Seasonal Activity Type for labels that match both a Seasonal Activity Type and a Product.
    df["status"] = "Not recognized"
    df = classifiedproductlookup.do_lookup(df, "label", "product_id")
    df["product_name"] = df["product_id"]
    df = classifiedproductlookup.get_attribute(df, "product_name", "common_name_en")
    df.loc[df["product_id"].notna(), "status"] = "Product"
    df = seasonalactivitytypelookup.do_lookup(df, "label", "seasonal_activity_type")
    df.loc[df["seasonal_activity_type"].notna(), "status"] = "Seasonal activity type"

    return Output(
        df.replace({pd.NA: ""}),
        metadata={
            "num_labels": len(df),
            "num_datapoints": int(df["datapoint_count"].sum()),
            "num_summaries": int(df["summary_count"].sum()),
            "preview": MetadataValue.md(df.sample(config.preview_rows).to_markdown()),
            "datapoint_preview": MetadataValue.md(
                df[df["datapoint_count"] > 0].sample(config.preview_rows).to_markdown()
            ),
        },
    )


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def seasonal_activity_instances(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    seasonal_calendar_dataframe,
) -> Output[dict]:
    """
    SeasonalActivity and SeasonalActivityOccurrence instance dicts extracted from a BSS Seas Cal sheet.
    """
    if seasonal_calendar_dataframe.empty:
        return Output({}, metadata={"message": "No 'Seas Cal' worksheet found in this BSS"})

    partition_key = context.asset_partition_key_for_output()
    livelihood_zone_baseline = LivelihoodZoneBaseline.objects.get_by_natural_key(*partition_key.split("~")[1:])
    livelihood_zone_id = livelihood_zone_baseline.livelihood_zone_id
    reference_year_end_date = livelihood_zone_baseline.reference_year_end_date.isoformat()

    df = seasonal_calendar_dataframe
    num_header_rows = 2  # community, month

    # Prepare the lookups
    communitylookup = CommunityLookup()
    classifiedproductlookup = ClassifiedProductLookup()
    seasonalactivitytypelookup = SeasonalActivityTypeLookup()

    # Determine whether the worksheet has products in column A and activity types in column B.
    try:
        seasonalactivitytypelookup.do_lookup(df, "B", "seasonal_activity_type")
        first_data_column = "C"
    except ValueError:
        first_data_column = "B"

    # The last 12 columns are the summary columns.
    last_community_col = df.columns[-13]
    first_summary_column = df.columns[-12]

    # The BSS will probably have merged cells for the community names in row 3, so copy them across
    df.loc[3] = df.loc[3].replace("", pd.NA).ffill()

    # Check that we can recognize all the communities
    communities = []
    unrecognized_communities = []
    for column in df.loc[3, first_data_column:last_community_col].index:
        if ((df.loc[5:, column].isin([0, "0", "", None])) | pd.isna(df.loc[5:, column])).all():
            communities.append(None)  # This column has no data, so we can ignore it in the community lookup.
        else:
            community = communitylookup.get_instance(
                df.loc[3, column], livelihood_zone_baseline=livelihood_zone_baseline.pk
            )
            if community:
                communities.append(community)
            else:
                if df.loc[3, column] not in unrecognized_communities:  # Avoid duplicates in the error message
                    unrecognized_communities.append(df.loc[3, column])
    if unrecognized_communities:
        raise ValueError(f"Unrecognized communities in row 3: {unrecognized_communities}")
    communities = pd.Series(communities, index=df.loc[3, first_data_column:last_community_col].index)

    # Process the main part of the sheet to find the Seasonal Activities and their Occurrences.

    # Although the structure of this worksheet is not as complicated as the Data sheet, and we could build instances
    # using vector DataFrame operations, it is easier to maintain this code if it follows the same structure as the
    # `livelihood_activity_instances`. Therefore, we iterate over the rows rather than use vector operations.

    def finalize_occurences():
        """
        Finalize the SeasonalActivityOccurrences for the current community and months, and add them to the list.
        """
        nonlocal seasonal_activity_occurrence
        nonlocal months
        nonlocal seasonal_activity
        nonlocal community
        nonlocal seasonal_activity_occurrences

        ranges = get_start_end_day_ranges_from_months(months)
        for range in ranges:
            seasonal_activity_occurrence["start"] = range[0]
            seasonal_activity_occurrence["end"] = range[1]
            seasonal_activity_occurrence["natural_key"] = seasonal_activity["natural_key"] + [
                community.full_name if community else "",
                range[0],
                range[1],
            ]
            seasonal_activity_occurrences.append(seasonal_activity_occurrence.copy())

    # Iterate over the rows
    seasonal_activities = []
    seasonal_activity_occurrences = []
    unrecognized_labels = []
    errors = []
    product_id = ""
    for row in df.iloc[num_header_rows:].index:  # Ignore the header rows
        try:
            column = None
            label = df.loc[row, "A"].strip()
            if not label:
                # Ignore blank rows
                continue
            seasonal_activity_type = None
            additional_identifier = ""
            # Attempt to match the label to a Seasonal Activity Type.
            seasonal_activity_type = seasonalactivitytypelookup.get_instance(label)
            if not seasonal_activity_type:
                # We didn't match a Seasonal Activity Type for this label, so check if it's a product
                product_id = classifiedproductlookup.get(label)
                if not product_id and any(df.loc[row, first_data_column:].notna()):
                    # If we don't recognize the label as either a Seasonal Activity Type or a product,
                    # and there is data in this row, then add it to the unrecognized labels list.
                    unrecognized_labels.append(label)
                    continue
            # Some BSSs have labels in column B too
            if first_data_column == "C":
                label_b = df.loc[row, "B"].strip()
                if label_b:
                    if not seasonal_activity_type:
                        seasonal_activity_type = seasonalactivitytypelookup.get_instance(label_b)
                        if not seasonal_activity_type and any(df.loc[row, first_data_column:].notna()):
                            # If we don't recognize the label as either a Seasonal Activity Type,
                            # and there is data in this row, then add it to the unrecognized labels list.
                            unrecognized_labels.append(label_b)
                            continue
                    else:
                        additional_identifier = label

            # If we have any occurrences for this row, then build the SeasonalActivity instance
            if any(df.loc[row, first_data_column:].notna()):
                label = (label, label_b) if first_data_column == "C" else label  # composite label for trouble-shooting
                if not seasonal_activity_type:
                    errors.append(f"Couldn't identify SeasonalActivity matching label {label} from row {row}")
                    continue
                elif seasonal_activity_type.has_product and not product_id:
                    errors.append(
                        f"Couldn't identify Product for SeasonalActivity {seasonal_activity_type} matching label {label} from row {row}"
                    )
                    continue
                elif not seasonal_activity_type.has_product:
                    # This Seasonal Activity Type doesn't require a product, so clear the product_id to be prevent it
                    # from being inherited by a subsequent row.
                    product_id = ""

                seasonal_activity = {
                    "seasonal_activity_type_id": seasonal_activity_type.pk,
                    "product_id": product_id,
                    "additional_identifier": additional_identifier,
                    "is_key": seasonal_activity_type.is_key,
                    # Save the bss row and the label to aid trouble-shooting
                    "bss_row": row,
                    "label": label,
                    # Add the foreign keys and natural keys
                    "livelihood_zone_baseline": [livelihood_zone_id, reference_year_end_date],
                    "natural_key": [
                        livelihood_zone_id,
                        reference_year_end_date,
                        seasonal_activity_type.pk,
                        product_id,
                        additional_identifier,
                    ],
                }
                seasonal_activities.append(seasonal_activity)

                # Iterate over the month columns to build the SeasonalActivityOccurrences for this row
                community = None
                months = []
                for column in df.loc[row, first_data_column:last_community_col].index:
                    if df.loc[row, column] in [0, "0", "", None] or pd.isna(df.loc[row, column]):
                        # Skip columns without data
                        continue
                    if communities.get(column) != community:
                        # The community has changed, so finalize the Occurrences for the previous community.
                        if community and months:
                            finalize_occurences()
                        # Start the Occurrences for the new community
                        community = communities[column]
                        months = []
                        seasonal_activity_occurrence = {
                            "seasonal_activity": seasonal_activity["natural_key"],
                            "livelihood_zone_baseline": [livelihood_zone_id, reference_year_end_date],
                            "community": community.natural_key(),
                            # Save the bss row and column and the label to aid trouble-shooting
                            "bss_row": row,
                            "bss_column": column,
                            "label": label,
                        }
                    months.append(int(df.loc[4, column]))

                # Finalize Occurences for the last community in this row
                if community and months:
                    finalize_occurences()

                # Create the Baseline Occurrences for this Seasonal Activity by checking if they meet the occurrence threshold.
                community_count = communities.nunique()
                community = None
                months = []
                seasonal_activity_occurrence = {
                    "seasonal_activity": seasonal_activity["natural_key"],
                    "livelihood_zone_baseline": [livelihood_zone_id, reference_year_end_date],
                    "community": None,
                    # Save the bss row and column and the label to aid trouble-shooting
                    "bss_row": row,
                    "bss_column": column,
                    "label": label,
                }
                for column in df.loc[row, first_summary_column:].index:
                    try:
                        if df.loc[row, column] >= (community_count * COMMUNITY_OCCURRENCE_THRESHOLD):
                            months.append(int(df.loc[4, column]))
                    except TypeError:
                        errors.append(
                            f"Unexpected value '{df.loc[row, column]}' in summary column {column} from {label} for row {row}"
                        )
                if months:
                    finalize_occurences()
        except Exception as e:
            if column:
                raise RuntimeError(
                    "Unhandled error in BSS %s processing cell '%s'!%s%s for label '%s'"
                    % (partition_key, "Seas Cal", column, row, label)
                ) from e
            else:
                raise RuntimeError(
                    "Unhandled error in BSS %s processing row '%s'!%s with label '%s'"
                    % (partition_key, "Seas Cal", row, label)
                ) from e

    instances = {
        "SeasonalActivity": seasonal_activities,
        "SeasonalActivityOccurrence": seasonal_activity_occurrences,
    }
    if unrecognized_labels:
        # Drop duplicates in the unrecognized labels list for the error message
        unrecognized_labels = list(dict.fromkeys(unrecognized_labels))
        message = "Unrecognized Seas Cal labels in %s:\n%s" % (
            partition_key,
            "\n".join(f"  - {label}" for label in unrecognized_labels),
        )
        if config.strict:
            raise ValueError(message)
        else:
            context.log.warning(message)

    metadata = {f"num_{key.lower()}": len(value) for key, value in instances.items()}
    metadata["total_instances"] = sum(len(value) for value in instances.values())
    metadata["num_unrecognized_labels"] = len(unrecognized_labels)
    if unrecognized_labels:
        metadata["unrecognized_labels"] = MetadataValue.md("\n".join(f"- {label}" for label in unrecognized_labels))
    metadata["pct_seasonal_activities_recognized"] = (
        round(100 * (len(seasonal_activities) / (len(seasonal_activities) + len(unrecognized_labels))))
        if seasonal_activities or unrecognized_labels
        else ""
    )
    metadata["label_columns"] = "A:B" if first_data_column == "C" else "A"
    metadata["preview"] = MetadataValue.md(f"```json\n{json.dumps(instances, indent=4, ensure_ascii=False)}\n```")

    if errors:
        if config.strict:
            raise RuntimeError(
                "Missing or inconsistent metadata in BSS %s worksheet '%s':\n%s"
                % (partition_key, "Seas Cal", "\n".join(errors))
            )
        else:
            context.log.error(
                "Missing or inconsistent metadata in BSS %s worksheet '%s':\n%s"
                % (partition_key, "Seas Cal", "\n".join(errors))
            )
            metadata["errors"] = MetadataValue.md(f'```text\n{"\n".join(errors)}\n```')

    return Output(instances, metadata=metadata)


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def seasonal_activity_valid_instances(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    seasonal_activity_instances,
) -> Output[dict]:
    """
    Validated SeasonalActivity and SeasonalActivityOccurrence instances from a BSS, ready to be loaded via a Django fixture.
    """
    partition_key = context.asset_partition_key_for_output()
    return validate_instances(context, config, seasonal_activity_instances, partition_key)


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def seasonal_activity_fixture(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    seasonal_activity_valid_instances,
) -> Output[list[dict]]:
    """
    Django fixture for the SeasonalActivity and SeasonalActivityOccurrence data from a BSS.
    """
    return get_fixture_from_instances(seasonal_activity_valid_instances)


@asset(partitions_def=bss_instances_partitions_def)
def imported_seasonal_activities(
    context: AssetExecutionContext,
    seasonal_activity_fixture,
) -> Output[None]:
    """
    Imported Django fixture of SeasonalActivity and SeasonalActivityOccurrence data for a BSS, added to the Django database.
    """
    return import_fixture(seasonal_activity_fixture)
