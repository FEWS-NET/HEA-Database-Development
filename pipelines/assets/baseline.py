import json
from io import BytesIO
from pathlib import Path

import openpyxl
import pandas as pd
import xlrd
import xlwt
from dagster import (
    AssetExecutionContext,
    Config,
    DynamicPartitionsDefinition,
    MetadataValue,
    Output,
    asset,
)
from openpyxl.comments import Comment
from openpyxl.utils.cell import coordinate_to_tuple, rows_from_range
from pydantic import Field
from xlutils.copy import copy as copy_xls

bss_files_partitions_def = DynamicPartitionsDefinition(name="bss_files")


class BSSMetadataConfig(Config):
    gdrive_id: str = Field(
        default="15XVXFjbom1sScVXbsetnbgAnPpRux2AgNy8w5U8bXdI", description="The id of the BSS Metadata Google Sheet."
    )
    bss_root_folder: str = Field(
        default="/home/roger/Temp/Baseline Storage Sheets (BSS)",
        description="The path of the root folder containing the BSSs",
    )
    preview_rows: int = Field(default=10, description="The number of rows to show in DataFrame previews")


@asset(required_resource_keys={"google_client"})
def bss_metadata(context: AssetExecutionContext, config: BSSMetadataConfig) -> Output[pd.DataFrame]:
    """
    A DataFrame containing the BSS Metadata.
    """
    gc = context.resources.google_client.get_gspread_client()
    sh = gc.open_by_key(config.gdrive_id)
    worksheet = sh.worksheet("Metadata")
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    return Output(df, metadata={"num_baselines": len(df)})


@asset
def completed_bss_metadata(config: BSSMetadataConfig, bss_metadata) -> Output[pd.DataFrame]:
    """
    A DataFrame containing the BSS Metadata that has been completed sufficiently to allow the BSS to be loaded.
    """
    required_columns = [
        "bss_path",
        "code",
        "country",
        "source_organization",
        "name_en",
        "main_livelihood_category",
        "currency",
        "reference_year_start_date",
        "reference_year_end_date",
        "valid_from_date",
    ]
    mask = bss_metadata[required_columns].applymap(lambda x: x == "")

    # Drop rows where any of the specified columns have empty strings
    df = bss_metadata[~mask.any(axis="columns")]
    return Output(
        df,
        metadata={"num_baselines": len(df), "preview": MetadataValue.md(df.head(config.preview_rows).to_markdown())},
    )


@asset(required_resource_keys={"google_client"})
def bss_corrections(context: AssetExecutionContext, config: BSSMetadataConfig) -> Output[pd.DataFrame]:
    """
    A DataFrame containing approved corrections to cells in BSS spreadsheets.
    """
    gc = context.resources.google_client.get_gspread_client()
    sh = gc.open_by_key(config.gdrive_id)
    worksheet = sh.worksheet("Corrections")
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    return Output(
        df,
        metadata={
            "num_baselines": df["bss_path"].nunique(),
            "num_corrections": len(df),
            "preview": MetadataValue.md(df.head(config.preview_rows).to_markdown()),
        },
    )


@asset(partitions_def=bss_files_partitions_def)
def bss_files_metadata():
    pass


@asset(partitions_def=bss_files_partitions_def)
def corrected_files(context: AssetExecutionContext, config: BSSMetadataConfig, bss_corrections) -> Output[BytesIO]:
    """
    BSS files with any necessary corrections applied.
    """
    partition_key = context.asset_partition_key_for_output()
    file_path = Path(config.bss_root_folder, partition_key)
    for extension in [".xls", ".xlsx"]:
        if file_path.with_suffix(extension).exists():
            file_path = file_path.with_suffix(extension)

    def validate_previous_value(cell, expected_prev_value, prev_value):
        """
        Inline function to validate the existing value of a cell is the expected one, prior to correcting it.
        """
        # "#N/A" is inconsistently loaded as nan, even when copied and pasted in Excel or GSheets
        prev_value = str(prev_value).replace("None", "").replace("nan", "#N/A").strip()
        expected_prev_value = str(expected_prev_value)
        if expected_prev_value != prev_value:
            raise ValueError(
                "Unexpected prior value in source BSS. "
                f"BSS `{partition_key}`, cell `{cell}`, "
                f"value found `{prev_value}`, expected `{expected_prev_value}`."
            )

    # Find the corrections for this BSS
    corrections_df = bss_corrections[bss_corrections["bss_path"] == partition_key]

    # Prepare the metadata for the output
    output_metadata = {"bss_path": file_path, "num_corrections": len(corrections_df)}

    if corrections_df.empty:
        # No corrections, so just leave the file unaltered
        with open(file_path, "rb") as fh:
            return Output(BytesIO(fh.read()), metadata=output_metadata)
    else:
        if file_path.suffix == ".xls":
            # xlrd can only read XLS files, so we need to use xlutils.copy_xls to create something we can edit
            xlrd_wb = xlrd.open_workbook(file_path, formatting_info=True, on_demand=True)
            wb = copy_xls(xlrd_wb)
        else:
            xlrd_wb = None  # Required to suppress spurious unbound variable errors from Pyright
            wb = openpyxl.load_workbook(file_path)
        for correction in corrections_df.itertuples():
            for row in rows_from_range(correction.range):
                for cell in row:
                    if isinstance(wb, xlwt.Workbook):
                        row, col = coordinate_to_tuple(cell)
                        prev_value = xlrd_wb.sheet_by_name(correction.worksheet_name).cell_value(row - 1, col - 1)
                        if (
                            xlrd_wb.sheet_by_name(correction.worksheet_name).cell(row - 1, col - 1).ctype
                            == xlrd.XL_CELL_ERROR
                        ):
                            # xlrd.error_text_from_code returns, eg, "#N/A"
                            prev_value = xlrd.error_text_from_code[
                                xlrd_wb.sheet_by_name(correction.worksheet_name).cell_value(row - 1, col - 1)
                            ]
                        validate_previous_value(cell, correction.prev_value, prev_value)
                        # xlwt uses 0-based indexes, but coordinate_to_tuple uses 1-based, so offset the values
                        wb.get_sheet(correction.worksheet_name).write(row - 1, col - 1, correction.value)
                    else:
                        cell = wb[correction.worksheet_name][cell]
                        validate_previous_value(cell, correction.prev_value, cell.value)
                        cell.value = correction.value
                        cell.comment = Comment(
                            f"{correction.author} on {correction.correction_date}: {correction.comment}",  # NOQA: E501
                            author=correction.author,
                        )

        buffer = BytesIO()
        wb.save(buffer)
        return Output(buffer, metadata=output_metadata)


@asset(partitions_def=bss_files_partitions_def)
def baseline_fixture(
    context: AssetExecutionContext, config: BSSMetadataConfig, completed_bss_metadata, corrected_files
) -> Output[dict]:
    """
    Django fixtures for the LivelihoodZone, LivelihoodZoneBaseline and Community records in the BSSs.

    The first rows of the sheet look like:
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
    partition_key = context.asset_partition_key_for_output()

    data_df = pd.read_excel(corrected_files, "WB", header=None)

    # Find the metadata for this BSS
    try:
        metadata = completed_bss_metadata[completed_bss_metadata["bss_path"] == partition_key].iloc[0]
    except IndexError:
        raise ValueError("No complete entry in the BSS Metadata worksheet for %s" % partition_key)

    # Key in the result dict must match the name of the model class they will be imported to.
    # The value must be a list of instances to import into that model, where each instance
    # is a dict of field names and values.
    # If the field is a foreign key to a model that supports a natural key (i.e. the model has a `natural_key`
    # method), then the field value should be a list of components to the natural key.
    result = {
        "LivelihoodZone": [
            {
                # Get country and code from the filename
                "country": metadata["country"],
                "code": metadata["code"],
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
                "livelihood_zone": metadata["code"],
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
                "main_livelihood_category": str(metadata["main_livelihood_category"]).lower(),
                "reference_year_start_date": metadata["reference_year_start_date"],
                "reference_year_end_date": metadata["reference_year_end_date"],
                "valid_from_date": metadata["valid_from_date"],
                "valid_to_date": None if pd.isna(metadata["valid_to_date"]) else metadata["valid_to_date"],
                "data_collection_start_date": None
                if pd.isna(metadata["data_collection_start_date"])
                else metadata["data_collection_start_date"],
                "data_collection_end_date": None
                if pd.isna(metadata["data_collection_end_date"])
                else metadata["data_collection_end_date"],
                "publication_date": None if pd.isna(metadata["publication_date"]) else metadata["publication_date"],
            }
        ],
    }

    # Find the communities
    # Transpose to get data in columns
    community_df = data_df.iloc[2:7].transpose()
    # Check that the columns are what we expect
    expected_column_sets = (["WEALTH GROUP", "District", "Village", "Interview number:", "Interviewers"],)
    found_columns = community_df.iloc[0].str.strip().tolist()
    if not any(found_columns == expected_columns for expected_columns in expected_column_sets):
        raise ValueError("Cannot identify Communities from columns %s" % ", ".join(found_columns))
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
        lambda full_name: [metadata["code"], metadata["reference_year_end_date"]]
    )

    # Replace NaN with "" ready for Django
    community_df = community_df.fillna("")
    result["Community"] = community_df.to_dict(orient="records")

    return Output(
        result,
        metadata={"num_communities": len(community_df), "preview": json.dumps(result, indent=4)},
    )
