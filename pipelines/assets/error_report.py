"""
Dagster asset that consolidates the `errors` metadata from the latest materialization of every asset partition.

When `BSSMetadataConfig.strict` is False, assets log their errors and record them in an `errors` metadata entry
instead of failing, so that the valid data can still be loaded. This asset gathers those errors into a single
spreadsheet so that they can be reviewed and corrected together.
"""

import datetime
import re
import textwrap
from collections.abc import Iterable

import pandas as pd
from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetRecordsFilter,
    DagsterEventType,
    DagsterInstance,
    DynamicPartitionsDefinition,
    MetadataValue,
    Output,
    asset,
)
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE

# The metadata key that assets use to record errors when running in non-strict mode.
ERRORS_METADATA_KEY = "errors"

# Maximum number of materializations to fetch in a single event log query. Each one includes all of its metadata,
# which can be several MB, so keep this small to limit memory use.
FETCH_BATCH_SIZE = 20

# Values starting with these characters can be interpreted as a formula when opened in Excel.
FORMULA_PREFIXES = ("=", "+", "-", "@")

# Excel cannot store more than 32,767 characters in a single cell.
MAX_EXCEL_CELL_LENGTH = 32_767

DEFAULT_WORKSHEETS = {
    "livelihood_activity_instances": "Data",
    "other_cash_income_instances": "Data2",
    "wild_foods_instances": "Data3",
    "livelihood_product_category_instances": "Exp factors",
    "livelihood_product_category_valid_instances": "Exp factors",
    "seasonal_activity_instances": "Seas Cal",
    "seasonal_activity_valid_instances": "Seas Cal",
}


CONTINUATION_LINE_RE = re.compile(r"^(\s|[{}\[\]|])")

# Cell references, e.g. 'Summ'!A939, 'Data'!C45, 'Data'!212:212 or 'Data'!C:C
CELL_REFERENCE_RE = re.compile(
    r"'(?P<worksheet>[^']+)'!(?:(?P<row_range>\d+):\d+|(?P<column_range>[A-Z]+):[A-Z]+|(?P<column>[A-Z]+)?(?P<row>\d+))"
)

# The bss_sheet, bss_column and bss_row attributes in the JSON dump of an instance, e.g. "bss_row": 66
BSS_ATTRIBUTE_RE = re.compile(r'"bss_(?P<attribute>sheet|column|row)": "?(?P<value>[^",\n]+)"?')

# Row references in plain text, e.g. "from row 76" or "on row 12"
ROW_RE = re.compile(r"\b(?:from|on|in|for|at) row (?P<row>\d+)\b")

# Column references in plain text, e.g. "in summary column F"
COLUMN_RE = re.compile(r"\bcolumn (?P<column>[A-Z]{1,3})\b")

# A reference to a record in an error message from validate_instances(), e.g. "FoodPurchase 224"
RECORD_RE = re.compile(r"\b(?P<model>[A-Z][a-z]+(?:[A-Z][a-z]+)+) \d+\b")

# An unrecognized foreign key, e.g. "Unrecognized 'livelihood_strategy' foreign key ('BF01', ...) for"
FOREIGN_KEY_RE = re.compile(r"^Unrecognized '(?P<field>\w+)' foreign key (?:\(.*\)|\S+) for ")

# The model that each foreign key refers to, for foreign keys to records that can be validated by the same asset.
# Foreign keys are validated against the records that passed validation, so if the referenced record has an error
# too, the unrecognized foreign key is a knock-on error that goes away when that error is fixed.
KNOCK_ON_FOREIGN_KEYS = {
    "baseline_livelihood_activity": "LivelihoodActivity",
    "livelihood_strategy": "LivelihoodStrategy",
    "livelihoodactivity_ptr": "LivelihoodActivity",
    "wealth_group": "WealthGroup",
}

# Columns that identify a BSS in the summaries
BSS_COLUMNS = ["country", "livelihood_zone", "reference_year_end_date", "partition_key"]

ERROR_REPORT_COLUMNS = [
    "country",
    "livelihood_zone",
    "reference_year_end_date",
    "asset_name",
    "partition_key",
    "worksheet",
    "column",
    "row",
    "error_type",
    "is_knock_on",
    "error",
    "details",
    "run_id",
    "materialized_at",
]


def split_errors(errors_text: str) -> list[str]:
    """
    Split the text of an `errors` metadata entry into the individual error messages.
    """
    text = errors_text.strip()
    # Remove the surrounding markdown code fence, e.g. ```text ... ```
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
    if text.endswith("```"):
        text = text[:-3]

    errors = []
    for line in text.splitlines():
        if not line.strip() and not errors:
            continue
        if errors and (not line.strip() or CONTINUATION_LINE_RE.match(line)):
            errors[-1] += f"\n{line}"
        else:
            errors.append(line)
    return [error.strip() for error in errors if error.strip()]


def get_error_location(error: str, asset_name: str = "") -> dict[str, str | int | None]:
    """
    Get the worksheet, column and row that an error message refers to.
    """
    location = {"worksheet": None, "column": None, "row": None}
    if match := CELL_REFERENCE_RE.search(error):
        location["worksheet"] = match["worksheet"]
        location["column"] = match["column"] or match["column_range"]
        row = match["row"] or match["row_range"]
        location["row"] = int(row) if row else None

    if not location["row"] and not location["column"]:
        # Use the first value of each attribute, which belongs to the instance rather than any "changes"
        attributes = {}
        for match in BSS_ATTRIBUTE_RE.finditer(error):
            attributes.setdefault(match["attribute"], match["value"].strip())
        location["worksheet"] = location["worksheet"] or attributes.get("sheet")
        if attributes.get("column", "null") != "null":
            location["column"] = attributes["column"]
        if attributes.get("row", "").isdigit():
            location["row"] = int(attributes["row"])

    if not location["row"] and not location["column"]:
        # A label containing a newline can push the row reference onto the next line.
        summary = error.split("\n", 1)[0]
        for text in (summary, error):
            if match := ROW_RE.search(text):
                location["row"] = int(match["row"])
            if match := COLUMN_RE.search(text):
                location["column"] = match["column"]
            if location["row"] or location["column"]:
                break

    if not location["worksheet"] and (location["row"] or location["column"]):
        location["worksheet"] = DEFAULT_WORKSHEETS.get(asset_name)
    return location


def get_error_type(error: str) -> str:
    """
    Get the type of an error, by removing the parts of the message that are specific to one record.

    This removes the record number, cell reference, natural key, foreign key value and any other numbers, so that the
    same problem can be counted across BSSs. Quoted labels and field names are kept, because they are usually what
    needs to be fixed, e.g. an ActivityLabel for 'revenu'.
    """
    error_type = error.split(" with natural key ")[0]
    error_type = FOREIGN_KEY_RE.sub(r"Unrecognized '\g<field>' foreign key … for ", error_type)
    error_type = CELL_REFERENCE_RE.sub("…", error_type)
    error_type = RECORD_RE.sub(r"\g<model>", error_type)
    return re.sub(r"\d+(?:\.\d+)?", "<n>", error_type)


def clean_excel_value(value: str) -> str:
    """
    Make a string safe to store in an Excel cell.
    """
    value = ILLEGAL_CHARACTERS_RE.sub("", value)
    # Error messages include text from the BSS, so prevent it from being written as an active formula.
    if value.startswith(FORMULA_PREFIXES):
        value = f"'{value}"
    if len(value) > MAX_EXCEL_CELL_LENGTH:
        suffix = "\n... [truncated]"
        value = value[: MAX_EXCEL_CELL_LENGTH - len(suffix)] + suffix
    return value


def get_partition_attributes(partition_key: str | None) -> dict[str, str]:
    """
    Get the country, livelihood zone and reference year end date from a BSS partition key.
    """
    parts = (partition_key or "").split("~")
    if len(parts) != 3:
        return {"country": "", "livelihood_zone": "", "reference_year_end_date": ""}
    return dict(zip(["country", "livelihood_zone", "reference_year_end_date"], parts))


def get_error_rows(
    asset_name: str, partition_key: str | None, run_id: str, timestamp: float, errors_text: str
) -> list[dict]:
    """
    Convert the `errors` metadata from a single materialization into rows for the error report.
    """
    materialized_at = datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
    rows = []
    for error in split_errors(errors_text):
        summary, _, details = error.partition("\n")
        location = get_error_location(error, asset_name)
        if location["worksheet"]:
            location["worksheet"] = clean_excel_value(location["worksheet"])
        rows.append(
            {
                **get_partition_attributes(partition_key),
                "asset_name": asset_name,
                "partition_key": partition_key or "",
                **location,
                "error_type": clean_excel_value(get_error_type(summary)),
                "error": clean_excel_value(summary),
                # Remove the indentation added to continuation lines by `get_errors_metadata`
                "details": clean_excel_value(textwrap.dedent(details)),
                "run_id": run_id,
                # Excel doesn't support timezone-aware datetimes
                "materialized_at": materialized_at.replace(tzinfo=None),
            }
        )
    return rows


def get_knock_on_errors(df: pd.DataFrame) -> pd.Series:
    """
    Return whether each error is an unrecognized foreign key to a record that has an error in the same asset and BSS.
    """
    failed_records = set(zip(df["partition_key"], df["asset_name"], df["error"].str.extract(RECORD_RE)["model"]))
    referenced_models = df["error"].str.extract(FOREIGN_KEY_RE)["field"].map(KNOCK_ON_FOREIGN_KEYS)
    return pd.Series(
        [
            isinstance(model, str) and (partition_key, asset_name, model) in failed_records
            for partition_key, asset_name, model in zip(df["partition_key"], df["asset_name"], referenced_models)
        ],
        index=df.index,
        dtype=bool,
    )


def get_error_report(rows: list[dict]) -> dict[str, pd.DataFrame]:
    """
    Return the worksheets for the error report, from the error rows for all the assets.

    The summaries count BSS rows rather than errors, because one problem in a BSS row produces an error for each
    Wealth Group column, and for each model in a multi-table inheritance hierarchy, such as LivelihoodActivity and
    FoodPurchase. Knock-on errors aren't counted, because they go away when the error they depend on is fixed.
    """
    df = pd.DataFrame(rows, columns=ERROR_REPORT_COLUMNS).astype({"row": "Int64"})
    df = df.sort_values(
        ["country", "livelihood_zone", "reference_year_end_date", "asset_name"], kind="stable"
    ).reset_index(drop=True)
    df["is_knock_on"] = get_knock_on_errors(df)

    counted = df[~df["is_knock_on"]].copy()
    # Errors without a row are counted individually
    counted["bss_row"] = (
        counted["partition_key"] + "!" + counted["worksheet"].fillna("") + "!" + counted["row"].astype(str)
    ).where(counted["row"].notna(), counted["partition_key"] + "!" + counted["error"])

    # One row per type of error, starting with the ones that affect the most BSSs
    error_type_df = (
        counted.groupby("error_type")
        .agg(
            num_bss=("partition_key", "nunique"),
            num_countries=("country", lambda countries: countries[countries != ""].nunique()),
            num_bss_rows=("bss_row", "nunique"),
            num_errors=("error", "size"),
            assets=("asset_name", lambda asset_names: ", ".join(sorted(asset_names.unique()))),
        )
        .join(
            counted.drop_duplicates("error_type")
            .set_index("error_type")[["partition_key", "worksheet", "column", "row", "error"]]
            .add_prefix("example_")
        )
        .sort_values(["num_bss", "num_bss_rows"], ascending=False)
        .reset_index()
    )

    asset_summary_df = df.groupby("asset_name").agg(
        num_partitions=("partition_key", "nunique"),
        num_errors=("error", "size"),
        num_knock_on_errors=("is_knock_on", "sum"),
        # Errors from older materializations may already be fixed, so re-run the asset before relying on them
        oldest_materialized_at=("materialized_at", "min"),
    )
    asset_summary_df.insert(
        1,
        "num_bss_rows",
        counted.groupby("asset_name")["bss_row"].nunique().reindex(asset_summary_df.index, fill_value=0),
    )

    # One row per BSS, with the number of BSS rows with errors from each asset in a separate column
    bss_summary_df = counted.pivot_table(
        index=BSS_COLUMNS, columns="asset_name", values="bss_row", aggfunc="nunique", fill_value=0
    )
    bss_summary_df.insert(0, "num_bss_rows", counted.groupby(BSS_COLUMNS)["bss_row"].nunique())

    return {
        "Summary by Error Type": error_type_df,
        "Summary by Asset": asset_summary_df.reset_index(),
        "Summary by BSS": bss_summary_df.reset_index().rename_axis(columns=None),
        "Errors": df,
    }


def get_latest_materialization_records(
    instance: DagsterInstance, asset_key: AssetKey, partition_keys: set[str] | None
) -> Iterable:
    """
    Yield the event log record of the latest materialization for each partition of a partitioned asset.
    """
    if partition_keys is not None and not partition_keys:
        # An empty set would be treated as "no filter" by the event log storage.
        return
    latest_storage_ids = instance.get_latest_storage_id_by_partition(
        asset_key, DagsterEventType.ASSET_MATERIALIZATION, partitions=partition_keys
    )
    storage_ids = sorted(latest_storage_ids.values())
    for i in range(0, len(storage_ids), FETCH_BATCH_SIZE):
        batch = storage_ids[i : i + FETCH_BATCH_SIZE]
        result = instance.fetch_materializations(
            AssetRecordsFilter(asset_key=asset_key, storage_ids=batch), limit=len(batch)
        )
        yield from result.records


@asset(io_manager_key="dataframe_excel_io_manager")
def error_report(context: AssetExecutionContext) -> Output[dict[str, pd.DataFrame]]:
    """
    A spreadsheet of all the errors from the latest materialization of every asset partition.
    """
    instance = context.instance
    asset_graph = context.repository_def.asset_graph

    rows = []
    for asset_key in sorted(asset_graph.materializable_asset_keys, key=lambda key: key.to_user_string()):
        if asset_key == context.asset_key:
            continue
        asset_name = asset_key.to_user_string()
        partitions_def = asset_graph.get(asset_key).partitions_def

        if partitions_def is None:
            event = instance.get_latest_materialization_event(asset_key)
            records = [(None, event.run_id, event.timestamp, event.asset_materialization)] if event else []
        else:
            partition_keys = (
                set(instance.get_dynamic_partitions(partitions_def.name))
                if isinstance(partitions_def, DynamicPartitionsDefinition)
                else None
            )
            # A generator, so that only one batch of materializations is held in memory at a time
            records = (
                (record.partition_key, record.run_id, record.timestamp, record.asset_materialization)
                for record in get_latest_materialization_records(instance, asset_key, partition_keys)
            )

        for partition_key, run_id, timestamp, materialization in records:
            errors_metadata = materialization.metadata.get(ERRORS_METADATA_KEY) if materialization else None
            if errors_metadata is None:
                continue
            rows.extend(get_error_rows(asset_name, partition_key, run_id, timestamp, str(errors_metadata.value)))

    sheets = get_error_report(rows)
    df = sheets["Errors"]
    metadata = {
        "num_errors": len(df),
        "num_knock_on_errors": int(df["is_knock_on"].sum()),
        "num_bss_rows_with_errors": int(sheets["Summary by BSS"]["num_bss_rows"].sum()),
        "num_error_types": len(sheets["Summary by Error Type"]),
        "num_assets_with_errors": df["asset_name"].nunique(),
        "num_partitions_with_errors": df["partition_key"].nunique(),
        "num_countries_with_errors": df.loc[df["country"] != "", "country"].nunique(),
        "summary": MetadataValue.md(sheets["Summary by Asset"].to_markdown(index=False)),
    }
    return Output(sheets, metadata=metadata)
