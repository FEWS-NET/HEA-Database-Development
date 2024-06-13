import json

from dagster import Config, EnvVar
from pydantic import Field


class BSSMetadataConfig(Config):
    # The fspec path of the spreadsheet containing the BSS Metadata and Corrections
    bss_metadata_workbook: str = EnvVar("BSS_METADATA_WORKBOOK")
    # The fsspec storage options for the BSS metadata spreadsheet
    bss_metadata_storage_options: dict = json.loads(EnvVar("BSS_METADATA_STORAGE_OPTIONS").get_value("{}"))
    # The fspec path of the root folder containing the BSSs
    # For example:
    # "/home/user/Temp/Baseline Storage Sheets (BSS)"
    # or "gdrive://Discovery Folder/Baseline Storage Sheets (BSS)"
    bss_files_folder: str = EnvVar("BSS_FILES_FOLDER")
    # The fsspec storage options for the BSS root folder
    bss_files_storage_options: dict = json.loads(EnvVar("BSS_FILES_STORAGE_OPTIONS").get_value("{}"))
    preview_rows: int = Field(default=10, description="The number of rows to show in DataFrame previews")
    strict: bool = Field(
        default=False, description="Whether to raise an error if a worksheet is only partially recognized"
    )


class ReferenceDataConfig(Config):
    # The list of worksheet names to load from the reference data workbook.
    # If empty, all worksheets that match a Django model will be loaded.
    sheet_names: list[str] = []
