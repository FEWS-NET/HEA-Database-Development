"""
Dagster assets related to the Livelihood Zone and Community, read from the 'WB' worksheet in a BSS.

An example of relevant rows from the worksheet:
    | Row | A                         | B                   | C                                          | D                                          | E                                          | F                                          | G                |
    |-----|---------------------------|---------------------|--------------------------------------------|--------------------------------------------|--------------------------------------------|--------------------------------------------|------------------|
    |   0 | MALAWI HEA BASELINES 2015 | Southern Lakeshore  | Southern Lakeshore                         |                                            |                                            |                                            |                  |
    |   1 |                           |                     | Community interviews                       |                                            |                                            |                                            |                  |
    |   2 | WEALTH GROUP              |                     |                                            |                                            |                                            |                                            |                  |
    |   3 | District                  | Salima and Mangochi | Salima                                     | Salima                                     | Salima                                     | Salima                                     | Dedza            |
    |   4 | Village                   |                     | Mtika                                      | Pemba                                      | Ndembo                                     | Makanjira                                  | Kasakala         |
    |   5 | Interview number:         |                     | 1                                          | 2                                          | 3                                          | 4                                          | 5                |
    |   6 | Interviewers              |                     | Kandiwo, Ethel, Fyawupi, Daniel, Chipiliro | Kandiwo, Ethel, Fyawupi, Daniel, Chipiliro | Kandiwo, Ethel, Fyawupi, Chipiliro, Daniel | Kandiwo, Ethel, Fyawupi, Chipiliro, Daniel | Chipiliro, Imran |
"""  # NOQA: E501

import json
import os

import django
import pandas as pd
from dagster import AssetExecutionContext, MetadataValue, Output, asset

from ..configs import BSSMetadataConfig
from ..partitions import bss_files_partitions_def, bss_instances_partitions_def
from .base import SUMMARY_LABELS

# set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hea.settings.production")

# Configure Django with our custom settings before importing any Django classes
django.setup()

from baseline.lookups import CommunityLookup  # NOQA: E402
from baseline.models import Community, LivelihoodZoneBaseline  # NOQA: E402
from metadata.lookups import WealthGroupCategoryLookup  # NOQA: E402


def get_wealth_group_dataframe(
    df: pd.DataFrame, livelihood_zone_baseline: LivelihoodZoneBaseline, worksheet_name: str, partition_key: str
) -> pd.DataFrame:
    """
    Get a list of the WealthGroup natural keys for each column in the BSS WB, Data, Data2, or Data3 worksheet.

    The Wealth Group is based on the Wealth Group Category from Row 3 and the Community Full Name from Rows 4 and 5.
    In the Summary columns, typically the Wealth Group Category is in Row 4 rather than Row 3.

    For the WB sheet, the values start in Column C, because Column A contains the Wealth Group Characteristic,
    and Column B also contains a Wealth Group Category. For the Data, Data2, and Data3 sheets, the values start in
    Column B - Column A contains the Livelihood Activity label and there is no copy of the Wealth Group Category.
    """

    # Build a dataframe of the relevant columns
    try:
        start_column = "C" if worksheet_name == "WB" else "B"
        wealthgroupcategorylookup = WealthGroupCategoryLookup()
        wealth_group_df = df.loc[3:5, start_column:].transpose().reset_index()
        wealth_group_df.columns = ["bss_column", "wealth_group_category", "district", "name"]
        wealth_group_df = wealthgroupcategorylookup.do_lookup(
            wealth_group_df, "wealth_group_category", "wealth_group_category"
        )
        wealth_group_df["name"] = wealth_group_df["name"].str.strip()
        wealth_group_df["district"] = wealth_group_df["district"].str.strip()

        # Create the full name from the district and the community name, and fall back
        # to just the community name if the district is blank.
        wealth_group_df["full_name"] = wealth_group_df.fillna("").apply(
            lambda row: row["name"] + ", " + row["district"] if row["district"] else row["name"], axis="columns"
        )

        # Ignore text in the District and Community row that are in the from the summary columns.
        first_wealth_category_index = wealth_group_df["wealth_group_category"].notnull().idxmax()

        wealth_group_df["full_name"] = wealth_group_df["full_name"].mask(
            wealth_group_df["wealth_group_category"].isnull() & (wealth_group_df.index >= first_wealth_category_index),
            "",
        )

        # In the Summary columns in the Data, Data2, Data3 worksheets, the Wealth
        # Group Category is in Row 4 (District)rather than Row 3 (Wealth Group Category)
        # so do a second lookup to update the blank rows.
        # If this doesn't find any new values, then it's because in a WB worksheet
        # there are no extra Wealth Group Categories on Row 4
        try:
            wealth_group_df = wealthgroupcategorylookup.do_lookup(
                wealth_group_df, "district", "wealth_group_category", update=True
            )
            # Remove the duplicate wealth_group_category_original column created by the second do_lookup(),
            # which otherwise causes problems when trying to merge dataframes, e.g. when building the wealth_group_df.
            wealth_group_df = wealth_group_df.loc[:, ~wealth_group_df.columns.duplicated()]
        except ValueError:
            pass
        # Check if there are unrecognized wealth group categories and report
        wealth_group_missing_category_df = wealth_group_df[
            wealth_group_df["wealth_group_category"].isnull()
            & wealth_group_df["wealth_group_category_original"].notnull()
            & ~wealth_group_df["wealth_group_category_original"]
            .str.lower()
            .isin([label.lower() for label in SUMMARY_LABELS])  # Exclude rows with summary labels (case-insensitive)
            & (wealth_group_df["wealth_group_category_original"].str.strip() != "")  # Exclude rows with empty strings
        ]
        if not wealth_group_missing_category_df.empty:
            unique_values = set(wealth_group_missing_category_df["wealth_group_category_original"].unique())
            raise ValueError(
                "%s has unrecognized wealth group category in %s:\n%s"
                % (partition_key, worksheet_name, "\n".join(unique_values))
            )
        # Lookup the Community instances
        community_lookup = CommunityLookup()
        wealth_group_df["livelihood_zone_baseline"] = livelihood_zone_baseline.id  # required parent for lookup
        wealth_group_df = community_lookup.do_lookup(wealth_group_df, "full_name", "community")
        wealth_group_df = community_lookup.get_instances(wealth_group_df, "community")

        # Check that the community names are recognized
        unmatched_full_names = wealth_group_df[
            (wealth_group_df["full_name"] != "") & wealth_group_df["community"].isna()
        ][["bss_column", "full_name"]]
        if not unmatched_full_names.empty:
            raise ValueError(
                "%s contains unmatched Community full_name values in worksheet %s:\n%s\n\nExpected names are:\n  %s"
                % (
                    partition_key,
                    worksheet_name,
                    unmatched_full_names.to_markdown(index=False),
                    "\n  ".join(
                        Community.objects.filter(livelihood_zone_baseline_id=livelihood_zone_baseline.id).values_list(
                            "full_name", flat=True
                        )
                    ),
                )
            )

        # Replace the livelihood_zone_baseline and the community with their natural key, ready for creating a fixture
        wealth_group_df["livelihood_zone_baseline"] = [livelihood_zone_baseline.natural_key()] * len(wealth_group_df)
        wealth_group_df["community"] = wealth_group_df.apply(
            lambda row: (
                (
                    livelihood_zone_baseline.livelihood_zone_id,
                    livelihood_zone_baseline.reference_year_end_date.isoformat(),
                    # Note that we need to use the actual full_name from the instance, not the one calculated from
                    # the BSS, which might have been matched using an alias.
                    row["community"].full_name,
                )
                if pd.notna(row["community"])
                else None
            ),
            axis="columns",
        )
        # Add the natural key for the wealth group
        wealth_group_df["natural_key"] = wealth_group_df.fillna("").apply(
            lambda row: (
                livelihood_zone_baseline.livelihood_zone_id,
                livelihood_zone_baseline.reference_year_end_date.isoformat(),
                row["wealth_group_category"],
                # Note that we need to use the actual name from the instance, not the one calculated from
                # the BSS, which might have been matched using an alias.
                row["community"][2] if row["community"] else "",
            ),
            axis="columns",
        )
        wealth_group_df = wealth_group_df.replace(pd.NA, None)
    except Exception as e:
        raise RuntimeError(
            "Unable to identify Wealth Groups in BSS %s worksheet %s" % (partition_key, worksheet_name)
        ) from e

    return wealth_group_df


@asset(partitions_def=bss_files_partitions_def, io_manager_key="json_io_manager")
def baseline_instances(
    context: AssetExecutionContext, config: BSSMetadataConfig, completed_bss_metadata
) -> Output[dict]:
    """
    LivelihoodZone and LivelihoodZoneBaseline instances extracted from the BSS.
    """
    partition_key = context.asset_partition_key_for_output()

    # Find the metadata for this BSS
    try:
        metadata = completed_bss_metadata[completed_bss_metadata["partition_key"] == partition_key].iloc[0]
    except IndexError:
        raise ValueError("No complete entry in the BSS Metadata worksheet for %s" % partition_key)

    # Prepare the dataframe for converting to a JSON fixture
    # Convert date columns to isoformat strings
    for column in [
        "reference_year_start_date",
        "reference_year_end_date",
        "valid_from_date",
        "valid_to_date",
        "data_collection_start_date",
        "data_collection_end_date",
        "publication_date",
    ]:
        metadata[column] = metadata[column].isoformat() if pd.notna(metadata[column]) and metadata[column] else None
    # Ensure pd.NA char columns contain empty strings
    for column in [
        "alternate_code",
        "name_en",
        "name_es",
        "name_fr",
        "name_pt",
        "name_ar",
        "description_en",
        "description_es",
        "description_fr",
        "description_pt",
        "description_ar",
    ]:
        metadata[column] = metadata[column] if pd.notna(metadata[column]) else ""
    # Make sure the livelihood_category_id is lowercase
    metadata["main_livelihood_category_id"] = metadata["main_livelihood_category_id"].lower().strip()

    # Key in the result dict must match the name of the model class they will be imported to.
    # The value must be a list of instances to import into that model, where each instance
    # is a dict of field names and values.
    # If the field is a foreign key to a model that supports a natural key (i.e. the model has a `natural_key`
    # method), then the field value should be a list of components to the natural key.
    result = {
        "LivelihoodZone": [
            {
                # Get country and code from the filename
                "country_id": metadata["country_id"],
                "code": metadata["code"],
                "alternate_code": metadata["alternate_code"],
                "name_en": metadata["name_en"],
                "name_es": metadata["name_es"],
                "name_fr": metadata["name_fr"],
                "name_pt": metadata["name_pt"],
                "name_ar": metadata["name_ar"],
                "description_en": metadata["description_en"],
                "description_es": metadata["description_es"],
                "description_fr": metadata["description_fr"],
                "description_pt": metadata["description_pt"],
                "description_ar": metadata["description_ar"],
            }
        ],
        "LivelihoodZoneBaseline": [
            {
                "livelihood_zone_id": metadata["code"],
                "name_en": metadata["name_en"],
                "name_es": metadata["name_es"],
                "name_fr": metadata["name_fr"],
                "name_pt": metadata["name_pt"],
                "name_ar": metadata["name_ar"],
                "description_en": metadata["description_en"],
                "description_es": metadata["description_es"],
                "description_fr": metadata["description_fr"],
                "description_pt": metadata["description_pt"],
                "description_ar": metadata["description_ar"],
                "source_organization": [
                    metadata["source_organization"],
                ],  # natural key is always a list
                "main_livelihood_category_id": metadata["main_livelihood_category_id"],
                "reference_year_start_date": metadata["reference_year_start_date"],
                "reference_year_end_date": metadata["reference_year_end_date"],
                "valid_from_date": metadata["valid_from_date"],
                "valid_to_date": metadata["valid_to_date"],
                "data_collection_start_date": metadata["data_collection_start_date"],
                "data_collection_end_date": metadata["data_collection_end_date"],
                "publication_date": metadata["publication_date"],
                "bss": metadata["bss_path"],
                "currency_id": metadata["currency_id"],
            }
        ],
    }

    try:
        preview = json.dumps(result, indent=4)
    except TypeError as e:
        raise ValueError("Cannot serialize Community fixture to JSON. Failing dict is\n %s" % result) from e

    return Output(
        result,
        metadata={
            "preview": MetadataValue.md(f"```json\n{preview}\n```"),
        },
    )


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def community_instances(context: AssetExecutionContext, config: BSSMetadataConfig, corrected_files) -> Output[dict]:
    """
    Community instances extracted from the BSS.
    """
    partition_key = context.asset_partition_key_for_output()
    data_df = pd.read_excel(corrected_files, "WB", header=None)

    # Find the communities

    # Transpose to get data in columns
    community_df = data_df.iloc[2:7].transpose()
    # Check that the columns are what we expect
    expected_column_sets = (
        ["WEALTH GROUP", "GROUPE SOCIO-ECONOMIQUE", "GROUPE DE RICHESSE"],
        [
            "District",
            "Arrondissement",
            "Département",
            "Commune",
            "Cercle",
            "Sous-préfecture",
            "Région et cercle",  # 2023 Mali BSSs
            "LGA",  # Local Government Area, in the 2023 Nigeria BSSs
            "Province et territoire",  # 2024 DRC BSSs
        ],
        [
            "Village",
            "Village or settlement",
            "Village ou site",
            "Village ou location:",
            "Village ou localité:",
            "Village ou localité",
            "Village et commune",  # 2023 Mali BSSs
            "Commune et village",  # 2023 Mali BSSs
            "Quartier",
            "Quartier/Secteur",
        ],
        ["Interview number:", "Numéro d'entretien", "Numero d'entretien"],
        ["Interviewers", "Enquetêur(s)", "Intervieweurs"],
    )
    found_columns = community_df.iloc[0].str.strip().tolist()
    for i, column in enumerate(found_columns):
        if column not in expected_column_sets[i]:
            raise ValueError(
                "Cannot identify Communities from header %s, expected one of %s"
                % (column, ", ".join(expected_column_sets[i]))
            )
    # Normalize the column names
    community_df.columns = ["wealth_group_category", "district", "name", "interview_number", "interviewers"]
    community_df = community_df[1:]
    # Find the initial set of Communities by only finding rows that have both a `district` and a `community`,
    # and don't have a `wealth_group_category`. Also ignore the `Comments` row.
    community_df = (
        community_df[(community_df["district"] != "Comments") & (community_df["wealth_group_category"].isna())][
            ["district", "name", "interview_number", "interviewers"]
        ]
        .dropna(subset=["name"])
        .drop_duplicates()
    )
    # Create the full_name from the community and district, and fall back
    # to just the community name if the district is empty/nan.
    community_df["name"] = community_df["name"].str.strip()
    community_df["district"] = community_df["district"].str.strip()
    # Create the full name from the district and the community name, and fall back
    # to just the community name if the district is blank.
    community_df["full_name"] = community_df.fillna("").apply(
        lambda row: row["name"] + ", " + row["district"] if row["district"] else row["name"], axis="columns"
    )
    community_df = community_df.drop(columns="district")
    # Add the natural key for the livelihood zone baseline
    community_df["livelihood_zone_baseline"] = community_df["full_name"].apply(
        lambda full_name: partition_key.split("~")[1:]
    )

    # Replace NaN with "" ready for Django
    community_df = community_df.fillna("")

    result = {"Community": community_df.to_dict(orient="records")}

    try:
        preview = json.dumps(result, indent=4)
    except TypeError as e:
        raise ValueError("Cannot serialize Community fixture to JSON. Failing dict is\n %s" % result) from e

    return Output(
        result,
        metadata={
            "preview": MetadataValue.md(f"```json\n{preview}\n```"),
            "num_communities": len(community_df),
        },
    )
