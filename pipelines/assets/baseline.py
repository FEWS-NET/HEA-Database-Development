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

import pandas as pd
from dagster import AssetExecutionContext, MetadataValue, Output, asset

from ..configs import BSSMetadataConfig
from ..partitions import bss_files_partitions_def, bss_instances_partitions_def


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
    metadata["main_livelihood_category_id"] = metadata["main_livelihood_category_id"].lower()

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
    community_df["full_name"] = community_df.name.str.cat(community_df.district, sep=", ").fillna(community_df.name)
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
