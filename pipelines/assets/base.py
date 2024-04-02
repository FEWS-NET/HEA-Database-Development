"""
Base functions for performing operations on BSS spreadsheets.
"""

import numbers
import os
from io import BytesIO
from typing import Optional

import django
import msoffcrypto
import openpyxl
import pandas as pd
import xlrd
import xlwt
from dagster import (
    AssetExecutionContext,
    DagsterEventType,
    EventRecordsFilter,
    MetadataValue,
    Output,
    asset,
)
from gdrivefs.core import GoogleDriveFile
from openpyxl.comments import Comment
from openpyxl.utils import get_column_letter
from openpyxl.utils.cell import coordinate_to_tuple, rows_from_range
from upath import UPath
from xlutils.copy import copy as copy_xls

from ..configs import BSSMetadataConfig
from ..partitions import bss_files_partitions_def
from ..utils import get_index, prepare_lookup

# set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hea.settings.production")

# Configure Django with our custom settings before importing any Django classes
django.setup()

from common.lookups import CountryLookup  # NOQA: E402

# Map of values in cell A3 of the WB, Data, Data2, and Data3 worksheets to the language of the BSS
LANGS = {
    "wealth group": "en",
    "group de richesse": "fr",
    "groupe de richesse": "fr",
    "groupe socio-economique": "fr",
    "group socio-economique": "fr",
}

# List of labels that indicate the start of the summary columns from row 3 in the Data, Data, and Data3 worksheets
SUMMARY_LABELS = [
    "BASELINE",
    "BASE DE RÉFÉRENCE",
    "REFERENCE",
    "REFERENCE DE BASE",
    "BASE DE RÉFÉRENAE",
    "range",
    "interval",
]


@asset
def bss_metadata(context: AssetExecutionContext, config: BSSMetadataConfig) -> Output[pd.DataFrame]:
    """
    A DataFrame containing the BSS Metadata.
    """
    p = UPath(config.bss_metadata_workbook, **config.bss_metadata_storage_options)

    with p.fs.open(p.path, mode="rb", cache_type="bytes") as f:
        # Google Sheets have to exported rather than read directly
        if isinstance(f, GoogleDriveFile) and (f.details["mimeType"] == "application/vnd.google-apps.spreadsheet"):
            f = BytesIO(p.fs.export(p.path, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))

        df = pd.read_excel(f, sheet_name="Metadata", engine="openpyxl")

    df["reference_year_start_date"] = df["reference_year_start_date"].dt.date
    df["reference_year_end_date"] = df["reference_year_end_date"].dt.date
    df["valid_from_date"] = df["valid_from_date"].dt.date
    df["valid_to_date"] = df["valid_to_date"].dt.date
    df["data_collection_start_date"] = df["data_collection_start_date"].dt.date
    df["data_collection_end_date"] = df["data_collection_end_date"].dt.date
    df["publication_date"] = df["publication_date"].dt.date

    # Add the partition key and a flag indicating whether the BSS file exists
    partition_key_df = df[["country_id", "code", "reference_year_end_date"]]
    partition_key_df = CountryLookup().get_instances(partition_key_df, "country_id")
    df["partition_key"] = partition_key_df[["country_id", "code", "reference_year_end_date"]].apply(
        lambda x: f"{x.iloc[0].iso_en_ro_proper}~{x.iloc[1]}~{x.iloc[2]}", axis="columns"
    )

    partitions = bss_files_partitions_def.get_partition_keys(dynamic_partitions_store=context.instance)

    partitions_to_delete = [partition for partition in partitions if partition not in df["partition_key"].tolist()]
    for partition_key in partitions_to_delete:
        context.instance.delete_dynamic_partition(bss_files_partitions_def.name, partition_key)

    new_partitions = df[df["bss_exists"] & ~df["partition_key"].isin(partitions)]["partition_key"].tolist()
    context.instance.add_dynamic_partitions(bss_files_partitions_def.name, new_partitions)

    return Output(
        df,
        metadata={
            "num_baselines": len(df),
            "preview": MetadataValue.md(
                df[["partition_key", "bss_path", "status", "name_en", "main_livelihood_category_id"]]
                .head(config.preview_rows)
                .to_markdown(index=False)
                .replace("~", "\\~")  # Escape the ~ in the partition_key, otherwise it is rendered as strikethrough
            ),
        },
    )


@asset
def completed_bss_metadata(config: BSSMetadataConfig, bss_metadata) -> Output[pd.DataFrame]:
    """
    A DataFrame containing the BSS Metadata that has been completed sufficiently to allow the BSS to be loaded.
    """
    required_columns = [
        "bss_path",
        "code",
        "country_id",
        "source_organization",
        "name_en",
        "main_livelihood_category_id",
        "currency_id",
        "reference_year_start_date",
        "reference_year_end_date",
        "valid_from_date",
    ]
    bss_metadata = bss_metadata[bss_metadata["bss_exists"]].sort_values(by="bss_path")
    mask = bss_metadata[required_columns].applymap(lambda x: x == "")

    # Drop rows where any of the specified columns have empty strings
    complete_df = bss_metadata[~mask.any(axis="columns")]
    incomplete_df = bss_metadata[mask.any(axis="columns")]

    return Output(
        complete_df,
        metadata={
            "num_baselines": len(bss_metadata),
            "num_complete": len(complete_df),
            "num_incomplete": len(incomplete_df),
            "complete": MetadataValue.md(
                complete_df[["bss_path", "name_en", "main_livelihood_category_id"]].to_markdown()
            ),
            "incomplete": MetadataValue.md(
                incomplete_df[["bss_path", "status", "name_en", "main_livelihood_category_id"]].to_markdown()
            ),
            "preview": MetadataValue.md(
                complete_df[["bss_path", "status", "name_en", "main_livelihood_category_id"]]
                .head(config.preview_rows)
                .to_markdown()
            ),
        },
    )


@asset
def bss_corrections(context: AssetExecutionContext, config: BSSMetadataConfig) -> Output[pd.DataFrame]:
    """
    A DataFrame containing approved corrections to cells in BSS spreadsheets.
    """
    p = UPath(config.bss_metadata_workbook, **config.bss_metadata_storage_options)

    with p.fs.open(p.path, mode="rb", cache_type="bytes") as f:
        # Google Sheets have to exported rather than read directly
        if isinstance(f, GoogleDriveFile) and (f.details["mimeType"] == "application/vnd.google-apps.spreadsheet"):
            f = BytesIO(p.fs.export(p.path, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))

        df = pd.read_excel(f, sheet_name="Corrections", engine="openpyxl")

    return Output(
        df,
        metadata={
            "num_baselines": df["bss_path"].nunique(),
            "num_corrections": len(df),
            "preview": MetadataValue.md(df.head(config.preview_rows).to_markdown()),
        },
    )


@asset(partitions_def=bss_files_partitions_def)
def original_files(context: AssetExecutionContext, config: BSSMetadataConfig, bss_metadata) -> Output[BytesIO]:
    """
    Original BSS files as used by the HEA community.
    """
    partition_key = context.asset_partition_key_for_output()
    partition_metadata = bss_metadata[bss_metadata["partition_key"] == partition_key]
    if partition_metadata.empty:
        raise ValueError(f"No BSS metadata found for partition key `{partition_key}`")
    bss_path = partition_metadata["bss_path"].iloc[0]
    p = UPath(config.bss_files_folder, bss_path, **config.bss_files_storage_options)

    # Prepare the metadata for the output
    output_metadata = {"bss_path": p.path}

    with p.fs.open(p.path, mode="rb") as f:
        return Output(BytesIO(f.read()), metadata=output_metadata)


@asset(partitions_def=bss_files_partitions_def)
def corrected_files(
    context: AssetExecutionContext, config: BSSMetadataConfig, original_files, bss_metadata, bss_corrections
) -> Output[BytesIO]:
    """
    BSS files with any necessary corrections applied.
    """
    partition_key = context.asset_partition_key_for_output()
    bss_path = bss_metadata[bss_metadata["partition_key"] == partition_key]["bss_path"].iloc[0]

    def validate_previous_value(cell, expected_prev_value, prev_value):
        """
        Inline function to validate the existing value of a cell is the expected one, prior to correcting it.
        """
        # "#N/A" is inconsistently loaded as nan, even when copied and pasted in Excel or GSheets
        if not isinstance(prev_value, numbers.Number):
            prev_value = str(prev_value).strip()
            expected_prev_value = str(expected_prev_value).strip()
            for null_value in ["None", "nan", "#N/A", "N/A"]:  # Note that #N/A must be before N/A!
                prev_value = prev_value.replace(null_value, "")
                expected_prev_value = expected_prev_value.replace(null_value, "")
        if expected_prev_value != prev_value:
            raise ValueError(
                "Unexpected prior value in source BSS. "
                f"BSS `{partition_key}`, cell `{cell}`, "
                f"value found `{prev_value}`, expected `{expected_prev_value}`."
            )

    # Find the corrections for this BSS
    corrections_df = bss_corrections[bss_corrections["bss_path"] == bss_path]

    # Prepare the metadata for the output
    output_metadata = {"num_corrections": len(corrections_df)}

    # Excel silently encrypts .xls files if there are locked worksheets, which
    # prevents xlrd from reading them. It uses a hard-coded password to do it!
    # See https://stackoverflow.com/questions/22789951/xlrd-error-workbook-is-encrypted-python-3-2-3
    try:
        wb_msoffcrypto_file = None
        xlrd_wb = xlrd.open_workbook(file_contents=original_files.getvalue(), formatting_info=True, on_demand=True)
        # xlrd can only read XLS files, so we need to use xlutils.copy_xls to create something we can edit
        wb = copy_xls(xlrd_wb)
    except xlrd.biffh.XLRDError as e:
        if str(e) == "Workbook is encrypted":
            # Try and unencrypt workbook with magic password
            wb_msoffcrypto_file = msoffcrypto.OfficeFile(original_files)
            try:
                # Yes, this is actually a thing!
                wb_msoffcrypto_file.load_key(password="VelvetSweatshop")
            except Exception as e:
                raise RuntimeError("Cannot process encrypted workbook") from e
            # Magic Excel password worked
            buffer = BytesIO()
            wb_msoffcrypto_file.decrypt(buffer)
            xlrd_wb = xlrd.open_workbook(file_contents=buffer.getvalue(), formatting_info=True, on_demand=True)
            # xlrd can only read XLS files, so we need to use xlutils.copy_xls to create something we can edit
            wb = copy_xls(xlrd_wb)
        else:
            # We assume that the file is an xlsx file that can be read by openpyxl
            xlrd_wb = None  # Required to suppress spurious unbound variable errors from Pyright
            # Need data_only=True to get the values of cells that contain formulas
            wb = openpyxl.load_workbook(original_files, data_only=True)

    if corrections_df.empty and not wb_msoffcrypto_file:
        # No corrections and file not encrypted, so just leave the file unaltered
        return Output(original_files, metadata=output_metadata)

    # Apply the corrections
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


def get_bss_dataframe(
    config: BSSMetadataConfig,
    filepath_or_buffer,
    bss_sheet: str,
    start_strings: list[str],
    end_strings: Optional[list[str]] = None,
    header_rows: list[int] = [3, 4, 5],  # List of row indexes that contain the Wealth Group and other headers
    num_summary_cols: Optional[int] = None,
) -> pd.DataFrame:
    """
    Retrieve a worksheet from a BSS and return it as a DataFrame.

    Uses Excel row numbers, starting from 1, and column letters, starting from A.
    """
    try:
        df = pd.read_excel(filepath_or_buffer, bss_sheet, header=None)
    except ValueError:
        # The requested worksheet does not exist in the file
        return Output(
            pd.DataFrame(),
            metadata={
                "worksheet": bss_sheet,
                "row_count": "Worksheet not present in file",
            },
        )

    # Use a 1-based index to match the Excel Row Number
    df.index += 1
    # Set the column names to match Excel
    df.columns = [get_column_letter(col + 1) for col in df.columns]

    # Find the last column before the summary column, which is in row 3
    end_col = get_index(SUMMARY_LABELS, df.loc[3], offset=-1)
    if not end_col:
        raise ValueError(f'No cell containing any of the summary strings: {", ".join(SUMMARY_LABELS)}')

    if not num_summary_cols:
        # If the number of summary columns wasn't specified, then assume that
        # there is one summary column for each wealth category, from row 3.
        num_summary_cols = df.loc[3, "B":end_col].dropna().nunique()
    end_col = df.columns[df.columns.get_loc(end_col) + num_summary_cols]

    # Find the row index of the start of the Livelihood Activities or Wealth Group Characteristic Values
    start_row = get_index(start_strings, df.loc[1:, "A"])
    if not start_row:
        raise ValueError(f'No cell in Column A containing any of the start strings: {", ".join(start_strings)}')

    if end_strings:
        # Find the row before the first row that contains an end string
        end_row = get_index(
            end_strings,
            df.loc[start_row:, "A"],
            offset=-1,
        )
        if not end_row:
            # The WB worksheet typically doesn't have a totals section at the bottom, so if we didn't find
            # an end string, then use the last row rather than raising an error.
            end_row = df.index[-1]
    else:
        # Use the last row. We don't use the last row that contains a label, because the WB worksheet contains data
        # for rows that rely on copying down the label in column A from a previous row.
        end_row = df.index[-1]

    # Find the language based on the value in cell A3
    lang = LANGS[df.loc[3, "A"].strip().lower()]

    # Filter to just the Wealth Group header rows and the Livelihood Activities
    df = pd.concat([df.loc[header_rows, :end_col], df.loc[start_row:end_row, :end_col]])

    # Copy the label from the previous cell for rows that have data but have a blank label.
    # For example, sometimes the wealth characteristic label is only filled in for the first wealth category:
    #   |     | A                                              | B                   | C                  |
    #   |----:|:-----------------------------------------------|:--------------------|:-------------------|
    #   |   1 | MALAWI HEA BASELINES 2015                      | Southern Lakeshore  | Southern Lakeshore |
    #   |  18 | Land area owned (acres)                        | VP                  | 1.4                |
    #   |  19 |                                                | P                   | 1.4                |
    #   |  20 |                                                | M                   | 1.4                |
    #   |  21 |                                                | B/O                 | 1.4                |
    #   |  22 | Camels: total owned at start of year           | VP                  | 0                  |

    # We do this by setting the missing values to pd.NA and then using .ffill()
    # Note that we need to replace the None with something else before the mask() and ffill() so that only
    # the masked values are replaced.
    df["A"] = (
        df["A"]
        .replace({None: ""})
        .mask(
            df["A"].isna() & df.loc[:, "B":].notnull().any(axis="columns"),
            pd.NA,
        )
        .ffill()
    )

    # Replace NaN with "" ready for Django
    df = df.fillna("")

    # Create a sample of rows that contain data, because the first rows may not contain any values.
    # For example the Data sheet contains data for Camel's Milk first, which isn't a common Livelihood Activity.
    sample_df = df[df.loc[:, "B":].apply(lambda row: sum((row != 0) & (row != "")), axis="columns") > 0]
    sample_rows = min(len(sample_df), config.preview_rows)

    return Output(
        df,
        metadata={
            "worksheet": bss_sheet,
            "lang": lang,
            "row_count": len(df),
            "datapoint_count": int(
                df.loc[:, "B":].apply(lambda row: sum((row != 0) & (row != "")), axis="columns").sum()
            ),
            "preview": MetadataValue.md(df.head(config.preview_rows).to_markdown()),
            "sample": MetadataValue.md(sample_df.sample(sample_rows).to_markdown()),
        },
    )


def get_bss_label_dataframe(
    context: AssetExecutionContext, config: BSSMetadataConfig, df: pd.DataFrame, asset_key: str, num_header_rows: int
) -> Output[pd.DataFrame]:
    """
    Dataframe of Label References for a worksheet in a BSS.
    """
    if df.empty:
        return Output(
            pd.DataFrame(),
            metadata={
                "row_count": "Worksheet not present in file",
            },
        )

    # The summary columns won't have a community, so find the column after the last column with a community name
    last_community_col = df.loc[5][df.loc[5].replace("", pd.NA).notna()].index[-1]
    summary_start_col = df.columns[df.columns.get_loc(last_community_col) + 1]

    df = df.iloc[num_header_rows:]  # Ignore the header rows
    instance = context.instance
    dataframe_materialization = instance.get_event_records(
        event_records_filter=EventRecordsFilter(
            event_type=DagsterEventType.ASSET_MATERIALIZATION,
            asset_key=context.asset_key_for_input(asset_key),
            asset_partitions=[context.asset_partition_key_for_input(asset_key)],
        ),
        limit=1,
    )[0].asset_materialization

    label_df = pd.DataFrame()
    label_df["label"] = df["A"]
    label_df["label_lower"] = prepare_lookup(label_df["label"])
    label_df["bss"] = context.asset_partition_key_for_output()
    label_df["lang"] = dataframe_materialization.metadata["lang"].text
    label_df["worksheet"] = dataframe_materialization.metadata["worksheet"].text
    label_df["row_number"] = df.index
    label_df["datapoint_count"] = df.loc[:, "B":].apply(lambda row: sum((row != 0) & (row != "")), axis="columns")

    # Store a bool to indicate whether the row contains any summary data
    summary_cols = df.loc[:, summary_start_col:].fillna(0).map(lambda x: 0 if isinstance(x, str) else x).astype(float)
    label_df["in_summary"] = summary_cols.sum(axis="columns") > 0

    # Create a sample of rows that contain data, because the first rows may not contain any values.
    # For example the Data sheet contains data for Camel's Milk first, which isn't a common Livelihood Activity.
    sample_df = label_df[label_df["in_summary"]]
    sample_rows = min(len(sample_df), config.preview_rows)

    return Output(
        label_df,
        metadata={
            "num_labels": len(label_df),
            "num_datapoints": int(label_df["datapoint_count"].sum()),
            "num_summaries": int(label_df["in_summary"].sum()),
            # Escape the ~ in the partition_key, otherwise it is rendered as strikethrough
            "preview": MetadataValue.md(label_df.head(config.preview_rows).to_markdown().replace("~", "\\~")),
            "sample": MetadataValue.md(sample_df.sample(sample_rows).to_markdown().replace("~", "\\~")),
        },
    )


def get_all_bss_labels_dataframe(
    config: BSSMetadataConfig, label_dataframe: dict[str, pd.DataFrame]
) -> Output[pd.DataFrame]:
    """
    Combined dataframe of the activity labels in use across all BSSs.
    """
    df = pd.concat(list(label_dataframe.values()))
    return Output(
        df,
        metadata={
            "num_labels": len(df),
            "num_datapoints": int(df["datapoint_count"].sum()),
            "num_summaries": int(df["in_summary"].sum()),
            # Escape the ~ in the partition_key, otherwise it is rendered as strikethrough
            "preview": MetadataValue.md(df.sample(config.preview_rows).to_markdown().replace("~", "\\~")),
            "sample": MetadataValue.md(
                df[df["in_summary"]].sample(config.preview_rows).to_markdown().replace("~", "\\~")
            ),
        },
    )


def get_summary_bss_label_dataframe(
    config: BSSMetadataConfig, all_labels_dataframe: dict[str, pd.DataFrame]
) -> Output[pd.DataFrame]:
    df = all_labels_dataframe.sort_values(by=["label_lower", "row_number", "filename"])

    # Group by label_lower and aggregate
    df = (
        df.groupby("label_lower")
        .agg(
            langs=(
                "lang",
                lambda x: ", ".join(x.sort_values().unique()),
            ),  # Create comma-separated list of unique languages
            datapoint_count_sum=("datapoint_count", "sum"),
            in_summary_sum=("in_summary", "sum"),
            unique_filename_count=("filename", pd.Series.nunique),
            min_row_number=("row_number", "min"),
            max_row_number=("row_number", "max"),
            filename_for_min_row=("filename", "first"),  # Assuming df is sorted by row_number within each group
            filename_for_max_row=("filename", "last"),  # Assuming df is sorted by row_number within each group
        )
        .reset_index()
    )

    df = df.sort_values(by=["min_row_number", "label_lower", "filename_for_min_row", "filename_for_max_row"])
    df = df.rename(
        columns={"label_lower": "label", "datapoint_count_sum": "datapoint_count", "in_summary_sum": "summary_count"}
    )
    return Output(
        df,
        metadata={
            "num_labels": len(df),
            "num_datapoints": int(df["datapoint_count"].sum()),
            "preview": MetadataValue.md(df.sample(config.preview_rows).to_markdown()),
            "datapoint_preview": MetadataValue.md(
                df[df["datapoint_count"] > 0].sample(config.preview_rows).to_markdown()
            ),
        },
    )
