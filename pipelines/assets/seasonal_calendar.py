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
import re

import django
import numpy as np
import pandas as pd
from dagster import (
    AssetExecutionContext,
    DagsterEventType,
    EventRecordsFilter,
    MetadataValue,
    Output,
    asset,
)
from django.db.models import F
from googletrans import Translator

from ..configs import BSSMetadataConfig
from ..partitions import bss_instances_partitions_def
from ..utils import prepare_lookup
from .base import (
    get_all_bss_labels_dataframe,
    get_bss_dataframe,
)
from .fixtures import get_fixture_from_instances, import_fixture, validate_instances

# set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hea.settings.production")

# Configure Django with our custom settings before importing any Django classes
django.setup()

from baseline.models import Community, LivelihoodZoneBaseline  # NOQA: E402
from common.lookups import ClassifiedProductLookup  # NOQA: E402
from common.models import ClassifiedProduct  # NOQA: E402
from metadata.lookups import SeasonalActivityTypeLookup, SeasonNameLookup  # NOQA: E402
from metadata.models import ActivityLabel  # NOQA: E402

# Use the enum value rather than a string
SEAS_CAL_ACTIVITY_TYPE = ActivityLabel.LivelihoodActivityType.SEAS_CAL

# No extra header rows for Seas Cal: the village row IS the start row returned by get_bss_dataframe,
HEADER_ROWS = []

# The first two rows returned for Seas Cal are structural (village names, month numbers) and must be
# skipped when building the label dataframe.
NUM_STRUCTURAL_ROWS = 2

# Cut-off fraction: a zone-level occurrence is kept only when it is >= this fraction of communities.
CUT_OFF = 0.5

# Regex patterns that identify the first row of the standalone single-line section in a Seas Cal sheet.
# Once any label matches, that row and all subsequent rows with month data are self-contained seasonal
STANDALONE_SECTION_PATTERNS = [
    re.compile(r"^livestock\b", re.IGNORECASE),  # English: "Livestock migration", "Livestock disease" …
    re.compile(r"\bb[eé]tail\b", re.IGNORECASE),  # French: "Migration bétail", "Pic maladies de bétail" …
]

# Month number → (first_day_of_year, last_day_of_year) mapping, simplified to 365 days.
MONTH_DAYS = {
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
        start_col_fallbacks=["B"],
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
    return get_seas_cal_label_dataframe(context, config, seasonal_calendar_dataframe, "seasonal_calendar_dataframe")


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
    return get_summary_seas_cal_label_dataframe(config, all_seasonal_calendar_labels_dataframe)


def get_seas_cal_label_dataframe(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    df: pd.DataFrame,
    asset_key: str,
) -> Output[pd.DataFrame]:
    """
    Label dataframe for the Seas Cal worksheet.
    """
    if df.empty:
        return Output(pd.DataFrame(), metadata={"row_count": "Worksheet not present in file"})

    instance = context.instance
    dataframe_materialization = instance.get_event_records(
        event_records_filter=EventRecordsFilter(
            event_type=DagsterEventType.ASSET_MATERIALIZATION,
            asset_key=context.asset_key_for_input(asset_key),
            asset_partitions=[context.asset_partition_key_for_input(asset_key)],
        ),
        limit=1,
    )[0].asset_materialization

    # Village row (iloc 0) carries community names and the zone-level sentinel.
    village_row = df.iloc[0, 1:]  # skip col A ("village -->")
    results_col = next(
        (col for col, val in village_row.items() if str(val).strip() in {"Results", "Synthèse"}),
        None,
    )

    # Community data columns = everything between col B and Results (exclusive).
    if results_col:
        all_data_cols = list(df.loc[:, "B":results_col].columns)
        community_cols = all_data_cols[:-1]  # drop the Results column itself
    else:
        community_cols = list(df.loc[:, "B":].columns)

    # Skip structural header rows (village + month); data labels start at iloc 2.
    data_df = df.iloc[NUM_STRUCTURAL_ROWS:]

    label_df = pd.DataFrame(index=data_df.index)
    label_df["label"] = data_df["A"]
    label_df["label_lower"] = prepare_lookup(label_df["label"])
    label_df["bss"] = context.asset_partition_key_for_output()
    label_df["lang"] = dataframe_materialization.metadata["lang"].text
    label_df["worksheet"] = dataframe_materialization.metadata["worksheet"].text
    label_df["row_number"] = data_df.index

    community_data = data_df[community_cols].replace("", np.nan)
    label_df["datapoint_count"] = community_data.apply(lambda row: int(sum(row.notna() & (row != 0))), axis="columns")

    # in_summary: True when the Results column has a non-zero count for this row.
    if results_col:
        results_series = (
            data_df[results_col].replace("", np.nan).fillna(0).map(lambda x: 0.0 if isinstance(x, str) else float(x))
        )
        label_df["in_summary"] = results_series > 0
    else:
        label_df["in_summary"] = False

    # Drop blank labels, then trim trailing "other"/"autre" end-marker rows (same logic as
    # get_seas_cal_instances_from_dataframe) while preserving any mid-sheet "Other" section header.
    label_df = label_df[label_df["label"].notna() & (label_df["label"] != "")]
    last_valid = np.where(~label_df["label_lower"].isin(["other", "autre"]))[0]
    if len(last_valid) > 0:
        label_df = label_df.iloc[: last_valid[-1] + 1]

    sample_df = label_df[label_df["in_summary"]]
    sample_rows = min(len(sample_df), config.preview_rows)

    return Output(
        label_df,
        metadata={
            "num_labels": len(label_df),
            "num_datapoints": int(label_df["datapoint_count"].sum()),
            "num_summaries": int(label_df["in_summary"].sum()),
            "preview": MetadataValue.md(label_df.head(config.preview_rows).to_markdown().replace("~", "\\~")),
            "sample": MetadataValue.md(
                sample_df.sample(sample_rows).sort_index().to_markdown().replace("~", "\\~")
                if sample_rows > 0
                else "No Results data found"
            ),
        },
    )


def get_summary_seas_cal_label_dataframe(
    config: BSSMetadataConfig,
    all_labels_dataframe: pd.DataFrame,
) -> Output[pd.DataFrame]:
    """
    Deduplicated summary of Seas Cal labels across all BSSs.

    Column layout matches summary_livelihood_activity_labels_dataframe so that the same
    Google Sheet template and ActivityLabel upload process works for both activity types.
    """
    df = all_labels_dataframe.sort_values(by=["label_lower", "row_number", "bss"])

    df = (
        df.groupby("label_lower")
        .agg(
            langs=("lang", lambda x: ", ".join(x.sort_values().unique())),
            datapoint_count=("datapoint_count", "sum"),
            summary_count=("in_summary", "sum"),
            unique_bss_count=("bss", pd.Series.nunique),
            # Count BSSs where this label had no month data (datapoint_count==0).
            zero_datapoint_bss_count=("datapoint_count", lambda x: (x == 0).sum()),
            min_row_number=("row_number", "min"),
            max_row_number=("row_number", "max"),
            bss_for_min_row=("bss", "first"),
            bss_for_max_row=("bss", "last"),
        )
        .reset_index()
    )

    df = df.sort_values(by=["min_row_number", "label_lower", "bss_for_min_row", "bss_for_max_row"])

    translator = Translator()

    def translate_label(label, langs):
        non_en = [lang.strip() for lang in langs.split(",") if lang.strip() != "en"]
        if not non_en:
            return label
        try:
            return translator.translate(label, dest="en", src=non_en[0]).text
        except Exception:
            return ""

    df["translation"] = df.apply(lambda x: translate_label(x["label_lower"], x["langs"]), axis="columns")

    label_metadata_df = pd.DataFrame.from_records(
        ActivityLabel.objects.filter(activity_type=SEAS_CAL_ACTIVITY_TYPE)
        .annotate(label=F("activity_label"))
        .values(
            "label",
            "status",
            "is_start",
            "attribute",
            "product__common_name_en",
            "season",
            "additional_identifier",
            "notes",
        )
    )

    if not label_metadata_df.empty:
        label_metadata_df["label_lower"] = prepare_lookup(label_metadata_df["label"])
        label_metadata_df = label_metadata_df.drop(columns=["label"])
        df = df.merge(label_metadata_df, on="label_lower", how="left")

    # Ensure all ActivityLabel columns are present even before any records exist.
    for col in [
        "status",
        "is_start",
        "attribute",
        "product__common_name_en",
        "season",
        "additional_identifier",
        "notes",
        "strategy_type",
        "payment_product_name",
        "unit_of_measure_id",
        "currency_id",
    ]:
        if col not in df.columns:
            df[col] = pd.NA

    df = df.rename(
        columns={
            "label_lower": "activity_label",
            "product__common_name_en": "product_name",
        }
    )

    df["activity_type"] = SEAS_CAL_ACTIVITY_TYPE

    # Infer is_start for rows with no ActivityLabel record
    # Rule 1 — zero-data non-SeasonalActivityType label → product/livestock-group header (is_start=True)
    # Rule 2 — standalone-section boundary pattern → is_start=True
    #   Labels matching STANDALONE_SECTION_PATTERNS mark the start of the single-line
    #   standalone section (e.g. "Livestock migration", "Migration bétail").
    # Rule 3 — after boundary with data → standalone activity (is_start=True)
    #   (e.g. "agricultural labour peak", "chicken sales", "high staple food prices").
    # Rule 4 — before boundary with data → sub-activity (is_start=False)
    #   Labels before the boundary with month data are sub-activities under a crop or
    #   livestock-group header (e.g. "land preparation", "birth", "heat").

    missing_is_start = df["is_start"].isna()

    # Rule 1: build seasonal activity type code set and identify zero-data non-SAT labels.
    sat_lookup = SeasonalActivityTypeLookup(require_match=False)
    sat_candidates = df.loc[missing_is_start, ["activity_label"]].rename(columns={"activity_label": "label"})
    if not sat_candidates.empty:
        sat_candidates = sat_lookup.do_lookup(sat_candidates, "label", "sat_code")
        in_sat = sat_candidates["sat_code"].notna()
    else:
        in_sat = pd.Series(dtype=bool)

    rule1 = missing_is_start & (df["datapoint_count"] == 0) & ~in_sat.reindex(df.index, fill_value=False)
    df.loc[rule1, "is_start"] = True
    missing_is_start = df["is_start"].isna()

    # Rule 2: identify standalone-section boundary from STANDALONE_SECTION_PATTERNS.
    matches_standalone = df["activity_label"].apply(
        lambda lbl: any(p.search(lbl) for p in STANDALONE_SECTION_PATTERNS)
    )
    rule2 = missing_is_start & matches_standalone
    df.loc[rule2, "is_start"] = True

    standalone_rows = df.loc[matches_standalone, "min_row_number"]
    standalone_boundary = standalone_rows.min() if not standalone_rows.empty else None

    # Rules 3 & 4: use boundary row to split remaining unlabelled rows.
    missing_is_start = df["is_start"].isna()
    if standalone_boundary is not None:
        after_boundary = df["min_row_number"] >= standalone_boundary
        df.loc[missing_is_start & after_boundary & (df["datapoint_count"] > 0), "is_start"] = True
        df.loc[missing_is_start & ~after_boundary & (df["datapoint_count"] > 0), "is_start"] = False
    else:
        # No standalone boundary found: any remaining data rows are treated as sub-activities.
        df.loc[missing_is_start & (df["datapoint_count"] > 0), "is_start"] = False

    # Remaining zero-data rows that are in SAT (e.g. a sub-activity with no data in any BSS)
    # stay as is_start=False.
    df.loc[df["is_start"].isna(), "is_start"] = False

    # For inferred header rows (Rules 1 & 2), attempt to resolve product_name via
    # ClassifiedProductLookup to give users a meaningful bootstrap starting point.
    inferred_header = rule1 | rule2
    needs_product_lookup = inferred_header & df["product_name"].isna()
    if needs_product_lookup.any():
        product_candidates = df.loc[needs_product_lookup, ["activity_label"]].rename(
            columns={"activity_label": "label"}
        )
        product_candidates = ClassifiedProductLookup(require_match=False).do_lookup(
            product_candidates, "label", "product_id"
        )
        product_name_map = dict(ClassifiedProduct.objects.values_list("cpc", "common_name_en"))
        df.loc[needs_product_lookup, "product_name"] = product_candidates["product_id"].map(product_name_map)

    # Reorder columns to match summary_livelihood_activity_labels_dataframe exactly.
    col_order = [
        "activity_label",
        "langs",
        "datapoint_count",
        "summary_count",
        "unique_bss_count",
        "zero_datapoint_bss_count",
        "min_row_number",
        "max_row_number",
        "bss_for_min_row",
        "bss_for_max_row",
        "translation",
        "activity_type",
        "status",
        "is_start",
        "strategy_type",
        "attribute",
        "product_name",
        "payment_product_name",
        "unit_of_measure_id",
        "currency_id",
        "season",
        "additional_identifier",
        "notes",
    ]
    df = df[[c for c in col_order if c in df.columns]]

    preview_n = min(len(df), config.preview_rows)
    datapoint_df = df[df["datapoint_count"] > 0]
    datapoint_n = min(len(datapoint_df), config.preview_rows)

    return Output(
        df,
        metadata={
            "num_labels": len(df),
            "num_datapoints": int(df["datapoint_count"].sum()),
            "preview": MetadataValue.md(df.sample(preview_n).to_markdown().replace("~", "\\~")),
            "datapoint_preview": MetadataValue.md(
                datapoint_df.sample(datapoint_n).to_markdown().replace("~", "\\~")
                if datapoint_n > 0
                else "No labels with data found"
            ),
        },
    )


@functools.cache
def get_seas_cal_label() -> tuple[dict[str, dict], dict[str, dict]]:
    """
    Return (header_labels, subactivity_labels) for all complete Seas Cal ActivityLabel records.
    """
    base_qs = ActivityLabel.objects.filter(
        status=ActivityLabel.LabelStatus.OVERRIDE,
        activity_type=SEAS_CAL_ACTIVITY_TYPE,
    )
    header_labels = {
        inst["activity_label"].lower(): inst
        for inst in base_qs.filter(is_start=True).values(
            "activity_label",
            "attribute",
            "product_id",
            "season",
            "additional_identifier",
        )
    }
    subactivity_labels = {
        inst["activity_label"].lower(): inst
        for inst in base_qs.filter(is_start=False).values(
            "activity_label",
            "attribute",
        )
    }
    return header_labels, subactivity_labels


def _build_contiguous_blocks(months: list[int]) -> list[dict]:
    """
    Return a list of {start, end} day-of-year dicts for each contiguous run of months.
    """
    if not months:
        return []

    blocks = []
    start_month = months[0]
    prev_month = start_month

    for current_month in months[1:]:
        consecutive = current_month == prev_month + 1 or (prev_month == 12 and current_month == 1)
        if consecutive:
            prev_month = current_month
        else:
            blocks.append({"start": MONTH_DAYS[start_month][0], "end": MONTH_DAYS[prev_month][1]})
            start_month = current_month
            prev_month = current_month

    blocks.append({"start": MONTH_DAYS[start_month][0], "end": MONTH_DAYS[prev_month][1]})
    return blocks


def _resolve_season(season_str: str | None, season_name_map: dict[str, str]) -> list:
    """Return the Season M2M natural-key list [[name_en]], or [] when the season is unresolved."""
    if not season_str:
        return []
    name_en = season_name_map.get(season_str)
    return [[name_en]] if name_en else []


def get_seas_cal_instances_from_dataframe(
    context: AssetExecutionContext,
    df: pd.DataFrame,
    livelihood_zone_baseline: LivelihoodZoneBaseline,
    partition_key: str,
) -> tuple[dict, list[str]]:
    """
    Parse the Seas Cal dataframe and return SeasonalActivity and SeasonalActivityOccurrence instance dicts,
    along with a list of unrecognized labels.
    """
    lz_id = livelihood_zone_baseline.livelihood_zone_id
    ref_year = livelihood_zone_baseline.reference_year_end_date.isoformat()

    # Trim trailing "other" / "autre" filler rows that carry no real data.
    if df.empty or df.shape[1] == 0:
        return {}, []
    valid_rows = df[~df.iloc[:, 0].str.lower().isin(["other", "autre"])]
    if valid_rows.empty:
        return {}, []
    last_valid_index = valid_rows.index[-1]
    df_original = df.iloc[: last_valid_index + 1].reset_index(drop=True)

    # Row 0 is the village/community header; row 1 is the month header.
    # (No drop(0) needed here — HEADER_ROWS=[] means get_bss_dataframe does not duplicate row 3.)
    df_original.iloc[0, 0] = "community"
    df_original.iloc[1, 0] = "month"

    # get_bss_dataframe fills NaN with "", so restore NaN for the forward-fill to work correctly.
    df_original.replace("", np.nan, inplace=True)
    # Forward-fill community names across all month columns within each community block.
    df_original.iloc[0, 1:] = df_original.iloc[0, 1:].ffill()

    # After the community and month rows (indices 0 and 1), the sheet has:
    #   index 2 : "Seasons" structural header — drop this row silently.
    #   index 3+ : season-name rows (Rain, Dry season, …)
    #   first row with NO data after the season names = first crop-section header.
    seasons_header_idx = 2
    drop_until = seasons_header_idx + 1  # start scanning the row after "Seasons"
    while drop_until < len(df_original):
        if df_original.iloc[drop_until, 1:].notna().any():
            # Row has data in month columns → it is a season-name row, keep scanning.
            drop_until += 1
        else:
            break  # first row with no data = first crop/activity section header
    df_original = df_original.drop(index=range(seasons_header_idx, drop_until)).reset_index(drop=True)

    _cached_header_labels, subactivity_labels = get_seas_cal_label()

    # For header labels that have no product FK configured, fall back to ClassifiedProductLookup
    # so that livestock headers (e.g. "Camel", "Dromedary") get a product just as crop headers do.
    no_product = [lbl for lbl, data in _cached_header_labels.items() if not data["product_id"]]
    if no_product:
        _resolved_products = ClassifiedProductLookup(require_match=False).do_lookup(
            pd.DataFrame({"label": no_product}), "label", "product_cpc"
        )
        _product_map: dict[str, str] = {
            row["label"]: row["product_cpc"]
            for _, row in _resolved_products.iterrows()
            if pd.notna(row["product_cpc"])
        }
        header_labels = {
            lbl: ({**data, "product_id": _product_map.get(lbl) or data["product_id"]})
            for lbl, data in _cached_header_labels.items()
        }
    else:
        header_labels = _cached_header_labels

    # Build a one-shot SAT code cache: label text → SeasonalActivityType.code.
    _all_data_labels = df_original.iloc[2:, 0].dropna().map(lambda x: str(x).lower().strip()).unique().tolist()
    sat_code_cache: dict[str, str] = {}
    if _all_data_labels:
        _resolved = SeasonalActivityTypeLookup(require_match=False).do_lookup(
            pd.DataFrame({"label": _all_data_labels}), "label", "sat_code"
        )
        sat_code_cache = {
            row["label"]: row["sat_code"] for _, row in _resolved.iterrows() if pd.notna(row["sat_code"])
        }

    # Resolve season name strings from ActivityLabel.season to Season.name_en using country context.
    country_code = livelihood_zone_baseline.livelihood_zone.country_id
    unique_season_strs = sorted({v["season"] for v in header_labels.values() if v.get("season")})
    season_name_map: dict[str, str] = {}
    if unique_season_strs:
        season_df = pd.DataFrame({"season": unique_season_strs, "country_id": country_code})
        resolved_df = SeasonNameLookup(require_match=False).do_lookup(season_df, "season", "season")
        season_name_map = {
            row["season_original"]: row["season"] for _, row in resolved_df.iterrows() if pd.notna(row["season"])
        }

    df = df_original

    # community_row / month_row use the original column-letter index from get_bss_dataframe.
    community_row = df.iloc[0, 1:]
    month_row = df.iloc[1, 1:]

    # Some French BSSs place a structural label ("Village :", "Site :", …) in col B
    _VILLAGE_LABELS = {"village :", "site :", "site", "village"}
    community_row = community_row.where(
        ~community_row.str.lower().str.strip().isin(_VILLAGE_LABELS),
        other=np.nan,
    )

    # Pre-scan for livestock/crop product headers that lack an ActivityLabel record but
    # resolve to a ClassifiedProduct (e.g. "Camels", "Cattle").  These become inferred
    # headers: zero-data rows that name a product, followed by SAT-type sub-activities.
    _zero_data_non_header_candidates = {
        str(row.iloc[0]).lower().strip()
        for _, row in df.iloc[2:].iterrows()
        if pd.notna(row.iloc[0])
        and not row.iloc[1:].notna().any()
        and str(row.iloc[0]).lower().strip() not in header_labels
    }
    inferred_product_map: dict[str, str] = {}
    if _zero_data_non_header_candidates:
        _ip_resolved = ClassifiedProductLookup(require_match=False).do_lookup(
            pd.DataFrame({"label": list(_zero_data_non_header_candidates)}), "label", "product_cpc"
        )
        inferred_product_map = {
            r["label"]: r["product_cpc"] for _, r in _ip_resolved.iterrows() if pd.notna(r["product_cpc"])
        }

    # iterate over activity rows
    results: list[dict] = []
    unrecognized_labels: list[str] = []
    unrecognized_subactivities: set[str] = set()
    current_header: str | None = None
    has_children = False

    for index, row in df.iloc[2:].iterrows():
        raw_label = row.iloc[0]
        if pd.isna(raw_label):
            continue
        label_value = str(raw_label).lower().strip()
        data_cols = row.iloc[1:]

        # A configured header label (is_start=True, OVERRIDE) should be redirected to child
        # handling when we are under a product-bearing header and the label is a SAT type.
        # Example: "heat" (standalone in header_labels) under "Cattle" (inferred) → child.
        _treat_as_child = (
            label_value in header_labels
            and current_header is not None
            and sat_code_cache.get(label_value) is not None
            and (
                current_header in inferred_product_map
                or (current_header in header_labels and header_labels[current_header].get("product_id"))
            )
        )

        if label_value in header_labels and not _treat_as_child:
            # Configured header row
            if current_header and not has_children:
                if current_header in header_labels:
                    mapping_data = header_labels[current_header]
                    results.append(
                        {
                            "seasonal_activity_label": current_header,
                            "product_id": mapping_data["product_id"],
                            "additional_identifier": (mapping_data["additional_identifier"] or "").strip(),
                            "seasonal_activity_type": None,
                            "community": None,
                            "month": None,
                            "occurrence": None,
                        }
                    )
                # Inferred headers with no children are silently dropped.
            current_header = label_value
            has_children = False

            # Standalone activities carry their month data in the same row as their label.
            if data_cols.notna().any():
                has_children = True
                mapping_data = header_labels[current_header]
                sat_code = mapping_data.get("attribute") or sat_code_cache.get(label_value) or label_value
                if not mapping_data.get("attribute") and not sat_code_cache.get(label_value):
                    unrecognized_subactivities.add(label_value)
                for col_index, presence_value in data_cols.items():
                    occurrence = (
                        int(presence_value)
                        if isinstance(presence_value, (int, float)) and not pd.isnull(presence_value)
                        else (1 if not pd.isnull(presence_value) and str(presence_value).strip() else None)
                    )
                    if occurrence is not None and occurrence >= 1:
                        results.append(
                            {
                                "seasonal_activity_label": current_header,
                                "product_id": mapping_data["product_id"],
                                "additional_identifier": (mapping_data["additional_identifier"] or "").strip(),
                                "seasonal_activity_type": sat_code,
                                "community": community_row[col_index],
                                "month": int(month_row[col_index]),
                                "occurrence": occurrence,
                            }
                        )

        elif current_header:
            # Child row under a configured or inferred header
            if current_header in header_labels:
                _hdr = header_labels[current_header]
                _product_id = _hdr["product_id"]
                _additional_id = (_hdr["additional_identifier"] or "").strip()
            else:
                _product_id = inferred_product_map.get(current_header)
                _additional_id = ""

            if data_cols.notna().any():
                has_children = True
                sub_lookup = subactivity_labels.get(label_value, {})
                sat_code = sub_lookup.get("attribute") or sat_code_cache.get(label_value) or label_value
                if not sub_lookup.get("attribute") and not sat_code_cache.get(label_value):
                    unrecognized_subactivities.add(label_value)
                for col_index, presence_value in data_cols.items():
                    occurrence = (
                        int(presence_value)
                        if isinstance(presence_value, (int, float)) and not pd.isnull(presence_value)
                        else (1 if not pd.isnull(presence_value) and str(presence_value).strip() else None)
                    )
                    if occurrence is not None and occurrence >= 1:
                        results.append(
                            {
                                "seasonal_activity_label": current_header,
                                "product_id": _product_id,
                                "additional_identifier": _additional_id,
                                "seasonal_activity_type": sat_code,
                                "community": community_row[col_index],
                                "month": int(month_row[col_index]),
                                "occurrence": occurrence,
                            }
                        )
            else:
                # Zero-data row while a header is active.
                if current_header in inferred_product_map:
                    if label_value in inferred_product_map:
                        # Transition to the next inferred product header.
                        current_header = label_value
                        has_children = False
                    # Otherwise stay in the current inferred-header context.
                else:
                    # Under a configured header: zero-data row is a section boundary.
                    if not has_children:
                        mapping_data = header_labels[current_header]
                        results.append(
                            {
                                "seasonal_activity_label": current_header,
                                "product_id": mapping_data["product_id"],
                                "additional_identifier": (mapping_data["additional_identifier"] or "").strip(),
                                "seasonal_activity_type": None,
                                "community": None,
                                "month": None,
                                "occurrence": None,
                            }
                        )
                    if label_value in inferred_product_map:
                        # This boundary row is itself a new inferred product header.
                        current_header = label_value
                        has_children = False
                    else:
                        unrecognized_labels.append(str(raw_label))
                        current_header = None
                        has_children = False

        else:
            # no active header context
            if not data_cols.notna().any():
                if label_value in inferred_product_map:
                    # Start an inferred product-group header (e.g. "Camels", "Cattle").
                    current_header = label_value
                    has_children = False
                else:
                    unrecognized_labels.append(str(raw_label))

    if current_header and not has_children:
        if current_header in header_labels:
            mapping_data = header_labels[current_header]
            results.append(
                {
                    "seasonal_activity_label": current_header,
                    "product_id": mapping_data["product_id"],
                    "additional_identifier": (mapping_data["additional_identifier"] or "").strip(),
                    "seasonal_activity_type": None,
                    "community": None,
                    "month": None,
                    "occurrence": None,
                }
            )
        # Inferred headers with no children need no flush record.

    if unrecognized_subactivities:
        context.log.warning(
            "No ActivityLabel (is_start=False, status=Override) found for %d Seas Cal sub-activity label(s) "
            "in %s: %s. Using raw label text as SeasonalActivityType.code — this will fail FK validation "
            "unless SeasonalActivityType records with matching codes exist. "
            "Add ActivityLabel records with attribute=<SeasonalActivityType.code> to resolve.",
            len(unrecognized_subactivities),
            partition_key,
            ", ".join(sorted(unrecognized_subactivities)),
        )

    df_results = pd.DataFrame(results)

    # When no crop headers were recognised (e.g. ActivityLabel not yet configured for this
    # BSS), df_results is empty and has no columns.
    if df_results.empty or "community" not in df_results.columns:
        context.log.warning(
            "No Seas Cal activities could be extracted for partition %s. "
            "Ensure ActivityLabel records exist with status=OVERRIDE, activity_type=Seas Cal, is_start=True "
            "for all crop headers in this BSS.",
            partition_key,
        )
        return {"SeasonalActivity": [], "SeasonalActivityOccurrence": []}, unrecognized_labels

    # Drop entries that have no community (standalone header rows with no occurrence data).
    df_results = df_results.dropna(subset=["community"])

    # Build SeasonalActivity instances
    seen_activities: set[tuple] = set()
    seasonal_activities: list[dict] = []

    for _, row in df_results.iterrows():
        sat_code = row["seasonal_activity_type"]
        product_cpc = row["product_id"] or ""
        additional_id = row["additional_identifier"] or ""
        key = (sat_code, product_cpc, additional_id)
        if key in seen_activities:
            continue
        seen_activities.add(key)
        seasonal_activities.append(
            {
                "natural_key": [lz_id, ref_year, sat_code, product_cpc, additional_id],
                "livelihood_zone_baseline": [lz_id, ref_year],
                "seasonal_activity_type": sat_code,
                "product": product_cpc or None,  # None when no product
                "additional_identifier": additional_id,
                "season": _resolve_season(
                    header_labels.get(row["seasonal_activity_label"], {}).get("season"), season_name_map
                ),
            }
        )

    # Community lookup using full_name
    community_list = Community.objects.filter(livelihood_zone_baseline=livelihood_zone_baseline)
    community_dict = {
        community.name.lower(): {
            "full_name": community.full_name,
            "aliases": [alias.strip().lower() for alias in community.aliases] if community.aliases else [],
        }
        for community in community_list
    }

    def lookup_community_full_name(name: str) -> str:
        name_lower = name.strip().lower()
        if name_lower in community_dict:
            return community_dict[name_lower]["full_name"]
        for community_info in community_dict.values():
            if name_lower in community_info["aliases"]:
                return community_info["full_name"]
        raise ValueError(
            "%s contains unmatched Community name values in worksheet Seas Cal:\n%s\n\nExpected names are:\n  %s"
            % (
                partition_key,
                name,
                "\n  ".join(
                    Community.objects.filter(livelihood_zone_baseline=livelihood_zone_baseline).values_list(
                        "name", flat=True
                    )
                ),
            )
        )

    zone_labels = {"Synthèse", "Results"}
    df_zonal_level = df_results[df_results["community"].isin(zone_labels)].copy()
    df_community_level = df_results[~df_results["community"].isin(zone_labels)].copy()

    df_community_level["community"] = df_community_level["community"].apply(lookup_community_full_name)

    # Zone-level: keep occurrences reported by at least CUT_OFF fraction of communities.
    no_of_communities = len(df_community_level["community"].unique())
    threshold = math.ceil(CUT_OFF * no_of_communities)
    df_zonal_level = df_zonal_level[df_zonal_level["occurrence"] >= threshold]

    df_all = pd.concat([df_community_level, df_zonal_level], ignore_index=True)

    _MISSING = "<missing>"
    df_all["product_id"] = df_all["product_id"].fillna(_MISSING)
    df_all["additional_identifier"] = df_all["additional_identifier"].fillna(_MISSING)

    # Build start/end day-of-year pairs per contiguous month block
    seasonal_activity_occurrences: list[dict] = []

    for (sat_code, product_cpc_raw, additional_id_raw, community_name), group in df_all.groupby(
        ["seasonal_activity_type", "product_id", "additional_identifier", "community"],
        dropna=False,
    ):
        product_cpc = "" if product_cpc_raw == _MISSING else (product_cpc_raw or "")
        additional_id = "" if additional_id_raw == _MISSING else (additional_id_raw or "")

        # community_name is the full_name string for community-level rows, or a zone sentinel.
        if pd.isna(community_name) or community_name in zone_labels:
            community_full_name = ""
            community_fk = None
        else:
            community_full_name = community_name
            community_fk = [lz_id, ref_year, community_full_name]

        sa_natural_key = [lz_id, ref_year, sat_code, product_cpc, additional_id]

        months = group["month"].tolist()  # preserve BSS column order — do NOT sort
        for block in _build_contiguous_blocks(months):
            start, end = block["start"], block["end"]
            seasonal_activity_occurrences.append(
                {
                    "natural_key": sa_natural_key + [community_full_name, str(start), str(end)],
                    "seasonal_activity": sa_natural_key,
                    "livelihood_zone_baseline": [lz_id, ref_year],
                    "community": community_fk,
                    "start": start,
                    "end": end,
                }
            )

    return {
        "SeasonalActivity": seasonal_activities,
        "SeasonalActivityOccurrence": seasonal_activity_occurrences,
    }, unrecognized_labels


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def seasonal_calendar_instances(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    seasonal_calendar_dataframe,
) -> Output[dict]:
    """
    SeasonalActivity and SeasonalActivityOccurrence instance dicts extracted from a BSS Seas Cal sheet.
    """
    partition_key = context.asset_partition_key_for_output()
    livelihood_zone_baseline = LivelihoodZoneBaseline.objects.get_by_natural_key(*partition_key.split("~")[1:])

    instances, unrecognized_labels = get_seas_cal_instances_from_dataframe(
        context, seasonal_calendar_dataframe, livelihood_zone_baseline, partition_key
    )

    if unrecognized_labels:
        message = "Unrecognized Seas Cal crop header labels in %s:\n%s" % (
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
    metadata["preview"] = MetadataValue.md(f"```json\n{json.dumps(instances, indent=4)}\n```")
    return Output(instances, metadata=metadata)


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def seasonal_calendar_valid_instances(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    seasonal_calendar_instances,
) -> Output[dict]:
    """
    Validated Seas Cal instances from a BSS, ready to be loaded via a Django fixture.
    """
    partition_key = context.asset_partition_key_for_output()
    return validate_instances(context, config, seasonal_calendar_instances, partition_key)


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def seasonal_calendar_fixture(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    seasonal_calendar_valid_instances,
) -> Output[list[dict]]:
    """
    Django fixture for the seasonal calendar data, ready for import.
    """
    return get_fixture_from_instances(seasonal_calendar_valid_instances)


@asset(partitions_def=bss_instances_partitions_def)
def imported_seasonal_calendars(
    context: AssetExecutionContext,
    seasonal_calendar_fixture,
) -> Output[None]:
    """
    Seasonal calendar data imported into the Django database from the consolidated fixture.
    """
    return import_fixture(seasonal_calendar_fixture)
