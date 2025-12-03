"""
Dagster assets related to the main Livelihood Activities, read from the 'Data' worksheet in a BSS.

An example of relevant rows from the worksheet:
    |     | A                                             | B                                | C                    | D             | E              | F                  | G             |
    |----:|:----------------------------------------------|:---------------------------------|:---------------------|:--------------|:---------------|:-------------------|:--------------|
    |   1 | MALAWI HEA BASELINES 2015                     | Southern Lakeshore               |                      |               |                |                    |               |
    |   2 |                                               |                                  |                      |               |                |                    |               |
    |   3 | WEALTH GROUP                                  | V.Poor                           | V.Poor               | V.Poor        | V.Poor         | V.Poor             | V.Poor        |
    |   4 | District/Ward number                          | Salima                           | Salima               | Salima        | Salima         | Dedza              | Mangochi      |
    |   5 | Village                                       | Mtika                            | Pemba                | Ndembo        | Makanjira      | Kasakala           | Kalanje       |
    |  58 | LIVESTOCK PRODUCTION:                         |                                  |                      |               |                |                    |               |
    |  86 | Cows' milk                                    |                                  |                      |               |                |                    |               |
    |  87 | no. milking animals                           | 0                                | 0                    | 0             | 0              | 0                  |               |
    |  88 | season 1: lactation period (days)             |                                  |                      |               |                |                    |               |
    |  89 | daily milk production per animal (litres)     | 0                                | 0                    | 0             | 0              |                    |               |
    |  90 | total production (litres)                     | 0                                | 0                    | 0             | 0              |                    |               |
    |  91 | sold/exchanged (litres)                       | 0                                | 0                    | 0             | 0              |                    |               |
    |  92 | price (cash)                                  |                                  |                      |               |                |                    |               |
    |  93 | income (cash)                                 | 0                                | 0                    | 0             | 0              |                    |               |
    |  94 | type of milk sold/other use (skim=0, whole=1) | 1                                | 1                    | 1             | 1              | 1                  | 1             |
    |  95 | other use (liters)                            | 0                                | 0                    | 0             | 0              |                    | 0             |
    |  96 | season 2: lactation period (days)             |                                  |                      |               |                |                    |               |
    |  97 | daily milk production per animal (litres)     | 0                                | 0                    | 0             | 0              |                    | 0             |
    |  98 | total production (litres)                     | 0                                | 0                    | 0             | 0              |                    | 0             |
    |  99 | sold/exchanged (litres)                       | 0                                | 0                    | 0             | 0              |                    | 0             |
    | 100 | price (cash)                                  |                                  |                      |               |                |                    |               |
    | 101 | income (cash)                                 | 0                                | 0                    | 0             | 0              |                    | 0             |
    | 102 | type of milk sold/other use (skim=0, whole=1) | 1                                | 1                    | 1             | 1              | 1                  | 1             |
    | 103 | other use (liters)                            | 0                                | 0                    | 0             | 0              |                    | 0             |
    | 104 | % cows' milk sold                             |                                  |                      |               |                |                    |               |
    | 105 | ghee/butter production (kg)                   |                                  |                      |               |                |                    |               |
    | 106 | ghee/butter (other use)                       |                                  |                      |               |                |                    |               |
    | 107 | ghee/butter sales: kg sold                    |                                  |                      |               |                |                    |               |
    | 108 | ghee/butter price (cash)                      |                                  |                      |               |                |                    |               |
    | 109 | ghee/butter income (cash)                     |                                  |                      |               |                |                    |               |
    | 110 | milk+ghee/butter kcals (%) - 1st season       |                                  |                      |               |                |                    |               |
    | 111 | milk+ghee/butter kcals (%) - 2nd season       |                                  |                      |               |                |                    |               |
    | 112 | % cows' ghee/butter sold: ref year            |                                  |                      |               |                |                    |               |
    | 172 | Cow meat: no. animals slaughtered             | 0                                | 0                    | 0             | 0              |                    | 0             |
    | 173 | carcass weight per animal (kg)                | 0                                | 0                    | 0             | 0              |                    | 0             |
    | 174 | kcals (%)                                     | 0                                | 0                    | 0             | 0              |                    | 0             |
    | 189 | Cattle sales - export: no. sold               | 0                                | 0                    | 0             | 0              |                    | 0             |
    | 190 | price (cash)                                  |                                  |                      |               |                |                    |               |
    | 191 | income (cash)                                 | 0                                | 0                    | 0             | 0              |                    | 0             |
    | 192 | Cattle sales - local: no. sold                | 0                                | 0                    | 0             | 0              |                    | 0             |
    | 193 | price (cash)                                  |                                  |                      |               |                |                    |               |
    | 194 | income (cash)                                 | 0                                | 0                    | 0             | 0              |                    | 0             |
    | 195 | cattle offtake (% sold/slaughtered)           |                                  |                      |               |                |                    |               |
"""  # NOQA: E501

import functools
import json
import os
import re
from pathlib import Path

import django
import pandas as pd
from dagster import AssetExecutionContext, MetadataValue, Output, asset
from django.db.models.functions import Lower
from upath import UPath

from ..configs import BSSMetadataConfig
from ..partitions import bss_instances_partitions_def
from ..utils import class_from_name, get_sample_data, prepare_lookup
from .base import (
    get_all_bss_labels_dataframe,
    get_bss_dataframe,
    get_bss_label_dataframe,
    get_summary_bss_label_dataframe,
)
from .baseline import get_wealth_group_dataframe
from .fixtures import get_fixture_from_instances, import_fixture, validate_instances

# set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hea.settings.production")

# Configure Django with our custom settings before importing any Django classes
django.setup()

from baseline.models import (  # NOQA: E402
    LivelihoodActivity,
    LivelihoodStrategy,
    LivelihoodZoneBaseline,
    MilkProduction,
)
from common.lookups import ClassifiedProductLookup, UnitOfMeasureLookup  # NOQA: E402
from metadata.lookups import SeasonNameLookup  # NOQA: E402
from metadata.models import (  # NOQA: E402
    ActivityLabel,
    LivelihoodActivityScenario,
    LivelihoodStrategyType,
)

# Indexes of header rows in the Data3 dataframe (wealth_group_category, district, village, household size)
# The household size is included in the header rows because it is used to calculate the kcals_consumed
HEADER_ROWS = [3, 4, 5, 40]

WORKSHEET_MAP = {
    ActivityLabel.LivelihoodActivityType.LIVELIHOOD_ACTIVITY: "Data",
    ActivityLabel.LivelihoodActivityType.OTHER_CASH_INCOME: "Data2",
    ActivityLabel.LivelihoodActivityType.WILD_FOODS: "Data3",
    ActivityLabel.LivelihoodActivityType.LIVELIHOOD_SUMMARY: "Data",
}


@asset(partitions_def=bss_instances_partitions_def)
def livelihood_activity_dataframe(config: BSSMetadataConfig, corrected_files) -> Output[pd.DataFrame]:
    """
    DataFrame of Livelihood Activities from a BSS
    """
    return get_bss_dataframe(
        config,
        corrected_files,
        "Data",
        start_strings=["LIVESTOCK PRODUCTION:", "production animale:"],
        end_strings=[
            "income minus expenditure",
            "Revenus moins dépenses",
            "Revenu moins dépense",
            "revenu moins dépenses",  # 2023 Mali BSSs
            "revenu mois dépenses",  # 2024 DRC BSSs
        ],
        header_rows=HEADER_ROWS,
    )


@asset(partitions_def=bss_instances_partitions_def)
def livelihood_activity_label_dataframe(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    livelihood_activity_dataframe,
) -> Output[pd.DataFrame]:
    """
    Dataframe of Livelihood Activity Label References for a single BSS.
    """
    return get_bss_label_dataframe(
        context, config, livelihood_activity_dataframe, "livelihood_activity_dataframe", len(HEADER_ROWS)
    )


@asset(io_manager_key="dataframe_csv_io_manager")
def all_livelihood_activity_labels_dataframe(
    config: BSSMetadataConfig, livelihood_activity_label_dataframe: dict[str, pd.DataFrame]
) -> Output[pd.DataFrame]:
    """
    Combined dataframe of the Livelihood Activity labels in use across all BSSs.
    """
    return get_all_bss_labels_dataframe(config, livelihood_activity_label_dataframe)


@asset(io_manager_key="dataframe_csv_io_manager")
def summary_livelihood_activity_labels_dataframe(
    config: BSSMetadataConfig, all_livelihood_activity_labels_dataframe: pd.DataFrame
) -> Output[pd.DataFrame]:
    """
    Summary of the Livelihood Activity labels in use across all BSSs.
    """
    return get_summary_bss_label_dataframe(
        config, all_livelihood_activity_labels_dataframe, ActivityLabel.LivelihoodActivityType.LIVELIHOOD_ACTIVITY
    )


@asset(partitions_def=bss_instances_partitions_def)
def livelihood_summary_dataframe(config: BSSMetadataConfig, corrected_files) -> Output[pd.DataFrame]:
    """
    DataFrame of the Livelihood Activity Summary from a BSS

    The summary is at the beginning of the Data worksheet, before the main Livelihood Activities.
    It contains the total values for income, expenditure, kcals consumed, etc. by Strategy Type for each Wealth Group.
    """
    return get_bss_dataframe(
        config,
        corrected_files,
        "Data",
        start_strings=["food summary: total (%)", "synthèse de nourriture : total (%)"],
        end_strings=["wealth characteristics", "caractéristiques socio-économiques"],
        header_rows=HEADER_ROWS,
    )


@asset(partitions_def=bss_instances_partitions_def)
def livelihood_summary_label_dataframe(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    livelihood_summary_dataframe,
) -> Output[pd.DataFrame]:
    """
    Dataframe of Livelihood Summary Label References for a single BSS
    """
    return get_bss_label_dataframe(
        context, config, livelihood_summary_dataframe, "livelihood_summary_dataframe", len(HEADER_ROWS)
    )


@asset(io_manager_key="dataframe_csv_io_manager")
def all_livelihood_summary_labels_dataframe(
    config: BSSMetadataConfig, livelihood_summary_label_dataframe: dict[str, pd.DataFrame]
) -> Output[pd.DataFrame]:
    """
    Combined dataframe of the Livelihood Summary labels in use across all BSSs.
    """
    return get_all_bss_labels_dataframe(config, livelihood_summary_label_dataframe)


@asset(io_manager_key="dataframe_csv_io_manager")
def summary_livelihood_summary_labels_dataframe(
    config: BSSMetadataConfig, all_livelihood_summary_labels_dataframe: pd.DataFrame
) -> Output[pd.DataFrame]:
    """
    Summary of the Livelihood Summary labels in use across all BSSs.
    """
    return get_summary_bss_label_dataframe(
        config, all_livelihood_summary_labels_dataframe, ActivityLabel.LivelihoodActivityType.LIVELIHOOD_ACTIVITY
    )


@functools.cache
def get_livelihood_activity_regexes() -> list:
    """
    Return a list of regex strings that the attributes associated with an activity label.

    Each entry in the list is a tuple of the compiled regex, the strategy_type, a True/False value
    that indicates whether the regex marks the start of a new Livelihood Activity, and the attribute
    that the data in the row represents.

    Some activity labels from column A in the Data, Data2, and Data3 worksheets can occur for more than
    one strategy type, for example both the PaymentInKind and OtherCashIncome. Therefore, generally rely
    on the strategy_type detected from the section header in column A, e.g. "PAYMENT IN KIND", and we
    only return the strategy_type when necessary.
    """
    # Fetch the list of regexes, strategy types and start flags
    with open(Path(__file__).parent / "livelihood_activity_regexes.json") as f:
        livelihood_activity_regexes = json.load(f)

    # Create regex patterns for metadata attributes to replace the placeholders in the regexes
    placeholder_patterns = {
        "label_pattern": r"[a-zà-ÿ][a-zà-ÿ',/ \.\>\-\(\)]+?",
        "product_pattern": r"(?P<product_id>[a-zà-ÿ][a-zà-ÿ1-9',/ \.\>\-\(\)]+?)",
        "season_pattern": r"(?P<season>season [12]|saison [12]|[12][a-z] season||[12][a-zà-ÿ] saison|r[eé]colte principale|principale r[eé]colte|gu|deyr+?)",  # NOQA: E501
        "additional_identifier_pattern": r"\(?(?P<additional_identifier>rainfed|irrigated|pluviale?|irriguée|submersion libre|submersion contrôlée|flottant)\)?",
        "unit_of_measure_pattern": r"(?P<unit_of_measure_id>[a-z]+)",
        "nbr_pattern": r"(?:n[b|o]r?)\.?",
        "vendu_pattern": r"(?:quantité )?vendu(?:e|s|ss|es|ses)?",
        "separator_pattern": r" ?[:-]?",
    }
    # Compile the regexes
    compiled_regexes = []
    for pattern, strategy_type, is_start, attribute in livelihood_activity_regexes:
        try:
            pattern = re.compile(pattern.format(**placeholder_patterns), flags=re.IGNORECASE)
            compiled_regexes.append((pattern, strategy_type, is_start, attribute))
        except Exception as e:
            raise ValueError(f"Invalid livelihood_activity_regexes entry: {pattern}") from e

    return compiled_regexes


@functools.cache
def get_livelihood_activity_regular_expression_attributes(label: str) -> dict:
    """
    Return a dict of the attributes for a well-known Livelihood Activity label using regular expression matches.
    """
    label = prepare_lookup(label)
    attributes = {
        "activity_label": None,
        "strategy_type": None,
        "is_start": None,
        "product_id": None,
        "unit_of_measure_id": None,
        "season": None,
        "additional_identifier": None,
        "attribute": None,
        "notes": None,
    }
    for pattern, strategy_type, is_start, attribute in get_livelihood_activity_regexes():
        match = pattern.fullmatch(label)
        if match:
            attributes.update(match.groupdict())
            attributes["activity_label"] = label
            attributes["strategy_type"] = strategy_type
            attributes["is_start"] = is_start
            if isinstance(attribute, dict):
                # Attribute contains a dict of attributes, e.g. notes, etc.
                attributes.update(attribute)
            else:
                # Attribute is a string containing the attribute name
                attributes["attribute"] = attribute
            # Save the matched pattern to aid trouble-shooting
            attributes["notes"] = (
                attributes["notes"] + " " + f' r"{pattern.pattern}"'
                if attributes["notes"]
                else f'r"{pattern.pattern}"'
            )
            # Return the first matching pattern
            return attributes

    # Didn't match any patterns, so return empty attributes
    return attributes


@functools.cache
def get_livelihood_activity_label_map(activity_type: str) -> dict[str, dict]:
    """
    Return a dict of the attributes for the Livelihood Activities, stored in the ActivityLabel Django model.
    """
    label_map = {
        instance["activity_label"].lower(): instance
        for instance in ActivityLabel.objects.filter(
            status=ActivityLabel.LabelStatus.OVERRIDE, activity_type=activity_type
        ).values(
            "activity_label",
            "strategy_type",
            "is_start",
            "product_id",
            "unit_of_measure_id",
            "season",
            "additional_identifier",
            "attribute",
            "notes",
        )
    }
    return label_map


@functools.cache
def get_label_attributes(label: str, activity_type: str) -> pd.Series:
    """
    Return the attributes for a LivelihoodActivity label from Column A in the Data, Data2, or Data3 worksheet.

    The most common labels are matched against the list or regular expressions returned from
    get_livelihood_activity_regexes(). This means that common patterns can be matched using
    aliases for product and unit of measure, without needing to maintain every possible label
    individually in the ActivityLabel model.

    Before looking for a regex match, if the label has a corresponding instance in the ActivityLabel
    model with status=OVERRIDE, then it returns the attributes from that instance. This allows us to
    support labels that are too complex to match with a regex. For example, the ButterProduction
    labels often contain the name of the milk that the butter is derived from, and so we need to
    return a CPC code that is different to the one matched by the product in the label. This also
    allows us to create new labels to support new BSSs without needing to update code. We use the
    ActivityLabel instances before testing the regexes, so that we can override the regexes if
    necessary, e.g. to ignore labels containing a product_id that doesn't match any of the
    ClassifiedProduct instances.

    The attributes are returned as a Pandas Series so that they are easily converted to a Dataframe.
    If the label isn't recognized at all, then it returns a Series of pd.NA.
    """
    label = prepare_lookup(label)
    try:
        return pd.Series(get_livelihood_activity_label_map(activity_type)[label])
    except KeyError:
        # No entry in the ActivityLabel model instance for this label, so attempt to match against the regexes
        attributes = get_livelihood_activity_regular_expression_attributes(label)
        return pd.Series(attributes)


def get_all_label_attributes(labels: pd.Series, activity_type: str, country_code: str | None) -> pd.DataFrame:
    """
    Return a DataFrame of the attributes for all of the labels in the supplied Series.

    The Product, Unit of Measure and Season attributes are processed using the relevant Lookup classes so that the
    resulting DataFrame contains the correct identifiers for these attributes.

    The country_code parameter is optional so that this function can be used to test individual labels,
    but it should be provided when processing a BSS because the Season lookup is country-specific.
    """
    # Clear caches for the functions, so that we use the lastest data from the database
    get_label_attributes.cache_clear()
    get_livelihood_activity_label_map.cache_clear()

    # Prepare the lookups, so they cache the individual results
    classifiedproductlookup = ClassifiedProductLookup(
        require_match=False  # It is possible that there won't be any Product matches, e.g. for LivelihoodSummary labels
    )
    unitofmeasurelookup = UnitOfMeasureLookup(
        require_match=False  # It is possible that there won't be any Unit of Measure matches, e.g. for OtherCashIncome
    )
    seasonnamelookup = SeasonNameLookup(
        require_match=False  # It is possible that there won't be any Season matches, e.g. for OtherCashIncome
    )

    # Build a dataframe of the attributes for each Label, including lookups for Product, Unit of Measure and Season
    all_label_attributes = labels.apply(lambda x: get_label_attributes(x, activity_type)).fillna("")
    all_label_attributes = classifiedproductlookup.do_lookup(all_label_attributes, "product_id", "product_id")
    all_label_attributes["product_id"] = all_label_attributes["product_id"].replace(pd.NA, None)
    all_label_attributes = unitofmeasurelookup.do_lookup(
        all_label_attributes, "unit_of_measure_id", "unit_of_measure_id"
    )
    all_label_attributes["unit_of_measure_id"] = all_label_attributes["unit_of_measure_id"].replace(pd.NA, None)
    # Add the country_id because it is required for the Season lookup
    if country_code:
        all_label_attributes["country_id"] = country_code
        all_label_attributes = seasonnamelookup.do_lookup(all_label_attributes, "season", "season")
        all_label_attributes["season"] = all_label_attributes["season"].replace(pd.NA, None)
    # Make sure we keep the same index so we can match by row number
    all_label_attributes.index = labels.index
    return all_label_attributes


@asset
def livelihood_activity_label_recognition_dataframe(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    all_livelihood_activity_labels_dataframe: pd.DataFrame,
    all_other_cash_income_labels_dataframe: pd.DataFrame,
    all_wild_foods_labels_dataframe: pd.DataFrame,
    all_livelihood_summary_labels_dataframe: pd.DataFrame,
):
    """
    A saved spreadsheet showing how each BSS label is recognized, either from the ActivityLabel model or a regex.
    """
    # Path to the output spreadsheet
    p = UPath(config.bss_label_recognition_workbook, **config.bss_label_recognition_storage_options)

    all_livelihood_activity_labels_dataframe["activity_type"] = (
        ActivityLabel.LivelihoodActivityType.LIVELIHOOD_ACTIVITY
    )
    all_other_cash_income_labels_dataframe["activity_type"] = ActivityLabel.LivelihoodActivityType.OTHER_CASH_INCOME
    all_wild_foods_labels_dataframe["activity_type"] = ActivityLabel.LivelihoodActivityType.WILD_FOODS
    all_livelihood_summary_labels_dataframe["activity_type"] = ActivityLabel.LivelihoodActivityType.LIVELIHOOD_SUMMARY

    # Build a dataframe of all the Activity Labels from all BSSs
    all_labels_df = pd.concat(
        [
            all_livelihood_activity_labels_dataframe,
            all_other_cash_income_labels_dataframe,
            all_wild_foods_labels_dataframe,
            all_livelihood_summary_labels_dataframe,
        ],
        ignore_index=True,
    )

    # Add the regular expressions
    regex_attributes_df = pd.DataFrame.from_records(
        all_labels_df["label"].astype(str).map(get_livelihood_activity_regular_expression_attributes)
    )
    all_labels_df = all_labels_df.join(
        regex_attributes_df,
        how="left",
    )

    # Add the labels from the database
    db_labels_df = pd.DataFrame.from_records(
        ActivityLabel.objects.annotate(label_lower=Lower("activity_label")).values(
            "label_lower",
            "activity_type",
            "status",
            "strategy_type",
            "is_start",
            "product_id",
            "unit_of_measure_id",
            "currency_id",
            "season",
            "additional_identifier",
            "attribute",
            "notes",
        )
    )
    all_labels_df = all_labels_df.join(
        db_labels_df.set_index(["label_lower", "activity_type"]),
        on=("label_lower", "activity_type"),
        how="left",
        rsuffix="_db",
        lsuffix="_regex",
    )

    # GDriveFS doesn't support updating existing files, it always create a new file with same name.
    # This leads to multiple files with the same name in the folder, so we delete any existing files first.
    if p.exists():
        # @TODO This doesn't work with the current version of gdrivefs, possibly because of an error
        # with accessing Shared Drives. For now, we need to manually delete the old files before running
        # the asset again.
        # We need to experiment and possibly create a custom gdrivefs that reuses code from KiLuigi's GoogleDriveTarget
        p.unlink()

    # Save the dataframe to an Excel workbook
    with p.fs.open(p.path, mode="wb") as f:
        with pd.ExcelWriter(f, engine="openpyxl") as writer:
            all_labels_df.to_excel(writer, index=False, sheet_name="All Labels")


def get_instances_from_dataframe(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    df: pd.DataFrame,
    livelihood_zone_baseline: LivelihoodZoneBaseline,
    activity_type: str,
    num_header_rows: int,
    partition_key: str,
) -> Output[dict]:
    """
    LivelhoodStrategy and LivelihoodActivity instances extracted from the BSS from the Data, Data2 or Data3 worksheets.
    """
    if df.empty:
        # There are no Livelihood Activities in the BSS for this activity type,
        # so return an empty set of instances.
        return Output(
            {
                "LivelihoodStrategy": [],
                "LivelihoodActivity": [],
            },
            metadata={
                "num_livelihood_strategies": 0,
                "num_livelihood_activities": 0,
            },
        )

    worksheet_name = WORKSHEET_MAP[activity_type]

    errors = []

    # Save the natural key to the livelihood zone baseline for later use.
    livelihood_zone_baseline_key = [
        livelihood_zone_baseline.livelihood_zone_id,
        livelihood_zone_baseline.reference_year_end_date.isoformat(),
    ]

    # Save the identifier for Season 2 because we need it when creating MilkProduction instances
    season2_name = SeasonNameLookup().get("Season 2", country_id=livelihood_zone_baseline.livelihood_zone.country_id)

    # Prepare a lookup for ClassifiedProduct, so it caches and reuses the results of .get() lookups
    classifiedproductlookup = ClassifiedProductLookup()

    # Get a dataframe of the Wealth Groups for each column
    wealth_group_df = get_wealth_group_dataframe(df, livelihood_zone_baseline, worksheet_name, partition_key)

    # Summary columns are those with a Wealth Group Category but not a Community
    summary_columns = wealth_group_df[
        (wealth_group_df["wealth_group_category"].notnull()) & (wealth_group_df["community"].isnull())
    ]["bss_column"].tolist()

    # Get a dataframe of the attributes for each label in column A
    all_label_attributes = get_all_label_attributes(
        df["A"], activity_type, livelihood_zone_baseline.livelihood_zone.country_id
    )

    # Check that we recognize all of the activity labels
    # The unrecognized labels are rows after the header rows where column A is not blank,
    # but the matching row in all_label_attributes dataframe has a blank activity_label.
    # Group the resulting dataframe so that we have a label and a list of the rows where it occurs.
    allow_unrecognized_labels = True
    # Identify rows where Column A is non-empty and the label wasn't recognized
    unrecognized_labels = df.iloc[num_header_rows:][
        (df["A"].iloc[num_header_rows:] != "") & (all_label_attributes.iloc[num_header_rows:]["activity_label"] == "")
    ]
    if unrecognized_labels.empty:
        # Keep the same shape as the non-empty case (label, rows, datapoint_count, in_summary)
        unrecognized_labels = pd.DataFrame(columns=["label", "rows", "datapoint_count", "in_summary"])
    else:
        # Boolean mask of which cells are numeric (coerce non-numeric to NaN then notna)
        numeric_mask = unrecognized_labels.loc[:, "B":].apply(lambda col: pd.to_numeric(col, errors="coerce").notna())
        # Count numeric datapoints per row
        unrecognized_labels["datapoint_count"] = numeric_mask.sum(axis=1)
        # Count numeric datapoints per row that are in the summary columns
        summary_numeric_mask = unrecognized_labels.loc[:, summary_columns].apply(
            lambda col: pd.to_numeric(col, errors="coerce").notna()
        )
        unrecognized_labels["summary_datapoint_count"] = summary_numeric_mask.sum(axis=1)
        # Aggregate datapoint count by label
        unrecognized_labels.loc[:, "label"] = prepare_lookup(unrecognized_labels["A"])
        unrecognized_labels = (
            unrecognized_labels.groupby("label")
            .agg(
                rows=("A", lambda x: ",".join(x.index.astype(str))),
                datapoints=("datapoint_count", "sum"),
                summary_datapoints=("summary_datapoint_count", "sum"),
            )
            .reset_index()
        )
        # Sort the rows by the first row number where the label occurs
        unrecognized_labels = unrecognized_labels.sort_values(
            by="rows", key=lambda x: x.str.split(",").str.get(0).astype(int)
        )
        message = "Unrecognized activity labels:\n\n" + unrecognized_labels.to_markdown(index=False)
        if allow_unrecognized_labels:
            context.log.warning(message)
        else:
            raise ValueError(message)

    # Process the main part of the sheet to find the Livelihood Activities

    # Regex matching is unreliable because of inconsistencies across BSSs from different countries. However, there are
    # a finite number of activity labels (the value in column A) in use across the global set of BSSs. Therefore,
    # we map the strings to attributes directly.

    # Some of the attributes, such as the Product apply to the following rows as well as the row that they are defined
    # on. Similarly, some values in Column A can appear in more than one LivelihoodStrategy, such as PaymentInKind and
    # OtherCashIncome - the labor description is the same but the compensation is different.
    # Therefore, we iterate over the rows rather than attempting to use vector operations.

    # Iterate over the rows
    strategy_type = None
    activity_field_names = None
    livelihood_strategy = previous_livelihood_strategy = None
    livelihood_strategies = []
    livelihood_activities = []
    livelihood_activities_for_strategy = previous_livelihood_activities_for_strategy = []
    for row in df.iloc[num_header_rows:].index:  # Ignore the Wealth Group header rows
        column = None
        try:
            label = df.loc[row, "A"]
            if not label:
                # Ignore blank rows
                continue
            # Get the attributes
            label_attributes = all_label_attributes.loc[row]
            if (
                not label_attributes[
                    [
                        "strategy_type",
                        "is_start",
                        "product_id",
                        "unit_of_measure_id",
                        "season",
                        "additional_identifier",
                        "attribute",
                    ]
                ]
                .astype(bool)
                .any()
            ):
                # Ignore rows that don't contain any relevant data (or which aren't recognized by get_label_attributes)
                continue

            # When we process the values for the LivelihoodActivity records, we need to know the actual attribute
            # that the values in this row are for
            activity_attribute = label_attributes["attribute"]

            if label_attributes["is_start"]:
                # We are starting a new livelihood activity, so append the previous livelihood strategy
                # to the list, provided that it has at least one Livelihood Activity where there is some income,
                # expediture or consumption. This excludes empty activities that only contain attributes for,
                # for example, 'type_of_milk_sold_or_other_uses'.
                # Also ignore any livelihood activities that don't have a Wealth Category component to the Wealth Group
                # natural key. These are from blank columns between Wealth Category groups in the BSS, which sometimes
                # contain data where values or formulae have been copied across all the columns in a row.
                non_empty_livelihood_activities = [
                    livelihood_activity
                    for livelihood_activity in livelihood_activities_for_strategy
                    if livelihood_activity["wealth_group"][2]  # Make sure there is a Wealth Category
                    and any(
                        (
                            field in livelihood_activity
                            and (livelihood_activity[field] or livelihood_activity[field] == 0)
                        )
                        for field in ["income", "expenditure", "kcals_consumed", "percentage_kcals"]
                    )
                ]

                # Don't save Livelihood Strategies from the Data worksheet that are captured in more detail on the
                # Data2 or Data3 worksheets. These strategies have entries in the Data sheet like
                # 'Construction cash income -- see Data2'
                if non_empty_livelihood_activities:
                    # Assertion to prevent linting from complaining about possible None values
                    assert livelihood_strategy is not None, (
                        "Found Livelihood Activities from row %s, but there is no Livelihood Strategy defined." % row
                    )
                    if re.match(
                        r"^.*(?:data ?[23]|prochaine feuille)$", livelihood_strategy["activity_label"], re.IGNORECASE
                    ):
                        non_empty_livelihood_activities = []

                if non_empty_livelihood_activities:
                    # Finalize the livelihood strategy and activities, making various adjustments for quirks in the BSS

                    # Assertion to prevent linting from complaining about possible None values
                    assert livelihood_strategy is not None, (
                        "Found Livelihood Activities from row %s, but there is no Livelihood Strategy defined." % row
                    )

                    # Copy the attribute from the previous livelihood strategy if this is a Livelihood Summary and the
                    # attribute hasn't been set by the label_attributes.
                    if (
                        activity_type == ActivityLabel.LivelihoodActivityType.LIVELIHOOD_SUMMARY
                        and not activity_attribute
                        and previous_livelihood_strategy
                        and previous_livelihood_activities_for_strategy
                    ):
                        for attribute in ["income", "expenditure", "percentage_kcals"]:
                            if attribute in previous_livelihood_activities_for_strategy[0]:
                                activity_attribute = attribute
                                break
                        if not activity_attribute:
                            raise ValueError(
                                f"Could not determine attribute for Livelihood Summary strategy from row {row}"
                            )

                    # Copy the product_id for MilkProduction and ButterProduction from the previous livelihood strategy
                    # if necessary.
                    if (
                        livelihood_strategy["strategy_type"] in ["MilkProduction", "ButterProduction"]
                        and ("product_id" not in livelihood_strategy or not livelihood_strategy["product_id"])
                        and livelihood_strategy["season"] == season2_name
                        and previous_livelihood_strategy
                        and previous_livelihood_strategy["product_id"]
                    ):
                        livelihood_strategy["attribute_rows"]["product_id"] = row
                        livelihood_strategy["product_id"] = previous_livelihood_strategy["product_id"]

                    # Copy the milking_animals for camels and cattle from the previous livelihood activities
                    # if necessary.
                    if (
                        livelihood_strategy["strategy_type"] == "MilkProduction"
                        and livelihood_strategy["season"] == season2_name
                        and previous_livelihood_activities_for_strategy
                    ):
                        # Assertion to prevent linting from complaining about possible None values
                        assert previous_livelihood_strategy is not None, (
                            "Found Previous Livelihood Activities from row %s, but there is no Previous Livelihood Strategy defined."
                            % row
                        )
                        if (
                            "milking_animals" in previous_livelihood_strategy["attribute_rows"]
                            and "milking_animals" not in livelihood_strategy["attribute_rows"]
                        ):
                            livelihood_strategy["attribute_rows"]["milking_animals"] = row
                            for i in range(len(previous_livelihood_activities_for_strategy)):
                                if "milking_animals" in previous_livelihood_activities_for_strategy[i]:
                                    livelihood_activities_for_strategy[i]["milking_animals"] = (
                                        previous_livelihood_activities_for_strategy[i]["milking_animals"]
                                    )

                    # Calculate kcals_consumed if the livelihood activity only contains the percentage_kcals.
                    # This is typical for ButterProduction and consumption of green crops.
                    # Derive it by multiplying percentage_kcals by:
                    #   2100 (kcals per person per day) * 365 (days per year) * average_household_size (from Row 40)
                    if (
                        "percentage_kcals" in livelihood_strategy["attribute_rows"]
                        and "kcals_consumed" not in livelihood_strategy["attribute_rows"]
                    ):
                        livelihood_strategy["attribute_rows"]["kcals_consumed"] = row
                        for i, livelihood_activity in enumerate(livelihood_activities_for_strategy):
                            # The household size will always be the 4th header row in the dataframe, even though the
                            # original row number (which is the index) will be different between the Data and Data3
                            # worksheets
                            column = df.columns[i + 1]
                            household_size = df.iloc[3, i + 1]
                            livelihood_activity["kcals_consumed"] = (
                                livelihood_activity["percentage_kcals"] * 2100 * 365 * household_size
                                if livelihood_activity["percentage_kcals"] and household_size
                                else None
                            )

                    # Normalize the `type_of_milk_sold_or_other_uses`, e.g. from `type of milk sold/other use (skim=0, whole=1)`  # NOQA: E501
                    if "type_of_milk_sold_or_other_uses" in livelihood_strategy["attribute_rows"]:
                        livelihood_strategy["attribute_rows"]["type_of_milk_sold_or_other_uses"] = row
                        for livelihood_activity in livelihood_activities_for_strategy:
                            livelihood_activity["type_of_milk_sold_or_other_uses"] = (
                                MilkProduction.MilkType.WHOLE
                                if livelihood_activity["type_of_milk_sold_or_other_uses"]
                                else MilkProduction.MilkType.SKIM
                            )

                    # Add the `type_of_milk_consumed`, because it is not present in any current BSS
                    if (
                        livelihood_strategy["strategy_type"] == "MilkProduction"
                        and "type_of_milk_consumed" not in livelihood_strategy["attribute_rows"]
                    ):
                        livelihood_strategy["attribute_rows"]["type_of_milk_consumed"] = row
                        for livelihood_activity in livelihood_activities_for_strategy:
                            # We assume that people drink whole milk. This is not always true, but is the assumption
                            # that is embedded in the ButterProduction calculations in current BSSs
                            livelihood_activity["type_of_milk_consumed"] = MilkProduction.MilkType.WHOLE

                    # Add the `times_per_year` to FoodPurchase, PaymentInKind and OtherCashIncome,
                    # because it is not in the current BSSs
                    if (
                        "times_per_month" in livelihood_strategy["attribute_rows"]
                        and "months_per_year" in livelihood_strategy["attribute_rows"]
                        and "times_per_year" not in livelihood_strategy["attribute_rows"]
                        and "times_per_year" in activity_field_names
                    ):
                        livelihood_strategy["attribute_rows"]["times_per_year"] = row
                        for livelihood_activity in livelihood_activities_for_strategy:
                            livelihood_activity["times_per_year"] = (
                                livelihood_activity["times_per_month"] * livelihood_activity["months_per_year"]
                                if livelihood_activity["times_per_month"] and livelihood_activity["months_per_year"]
                                else 0
                            )

                    # Calculate the times per year if the livelihood activity only contains the unit_multiple or
                    # people_per_household and the kcals_consumed. For some livelihood strategies, this is implicit in
                    # the formula used to calculate percentage_kcals in the BSS. For example:
                    # School Feeding: `=IF(B534="","",B534/B$40*5/12*5/7*0.33)`.
                    # I.e. percentage_kcals = number_of_children / average_household_size * 5/12 * 5/7 * 0.33,
                    # which implies that children receive school meals 5 days a week, 5 months a year, and those meals
                    # contain 1/3 of the required daily kcals, i.e. 2100 / 3 = 700 kcals.
                    # We can calculate the times_per_year by dividing the kcals_consumed by the kcals_per_unit and the
                    # unit_multiple (i.e. the number of children receiving school meals). This will give the correct
                    # answer even if the number of months per year or days per week is different. However, it will not
                    # return the correct answer if the formula in the BSS is using a different value for the percentage
                    # of daily calories per person provided by the school meals, typically 0.33.
                    # Similarly, for Labor Migration: `=IF(B553="","",B553/B$40*B554/12)`
                    # I.e. percentage_kcals = number_of_people / average_household_size * number_of_months / 12.
                    # which implies that household members who migrate temporarily do not consume the household's food
                    # during those months and instead obtain their full kcals (2100) from other sources.
                    if (
                        "percentage_kcals" in livelihood_strategy["attribute_rows"]
                        and (
                            "unit_multiple" in livelihood_strategy["attribute_rows"]
                            or "people_per_household" in livelihood_strategy["attribute_rows"]
                        )
                        and "product_id" in livelihood_strategy["attribute_rows"]
                        and "times_per_year" not in livelihood_strategy["attribute_rows"]
                        and "times_per_year" in activity_field_names
                    ):
                        livelihood_strategy["attribute_rows"]["times_per_year"] = row
                        for i, livelihood_activity in enumerate(livelihood_activities_for_strategy):
                            # The household size will always be the 4th header row in the dataframe, even though the
                            # original row number (which is the index) will be different between the Data and Data3
                            # worksheets
                            column = df.columns[i + 1]
                            kcals_per_unit = classifiedproductlookup.get_instance(
                                livelihood_strategy["product_id"]
                            ).kcals_per_unit
                            number_of_units = livelihood_activity.get(
                                "unit_multiple", None
                            ) or livelihood_activity.get("people_per_household", None)
                            livelihood_activity["times_per_year"] = (
                                round(livelihood_activity["kcals_consumed"] / kcals_per_unit / number_of_units)
                                if number_of_units
                                and kcals_per_unit
                                and livelihood_activity["kcals_consumed"] is not None
                                else 0
                            )

                    # Add the `payment_per_time` and `unit_of_measure` to PaymentInKind, if they are missing.
                    # For example, labor migration is recorded in the BSS as the number of household members who
                    # migrate, and the number of months that they are absent for. This is coded as a product (S9HD)
                    # with a kcals_per_unit of 2100, so the payment_per_time is 1 and the unit_of_measure is 'ea'.
                    if (
                        "payment_per_time" in activity_field_names
                        and "payment_per_time" not in livelihood_strategy["attribute_rows"]
                        and "product_id" in livelihood_strategy["attribute_rows"]
                    ):
                        kcals_per_unit = classifiedproductlookup.get_instance(
                            livelihood_strategy["product_id"]
                        ).kcals_per_unit
                        if kcals_per_unit == 2100:
                            livelihood_strategy["attribute_rows"]["payment_per_time"] = row
                            if "unit_of_measure_id" not in livelihood_strategy["attribute_rows"]:
                                livelihood_strategy["attribute_rows"]["unit_of_measure_id"] = row
                                livelihood_strategy["unit_of_measure_id"] = "ea"
                            for livelihood_activity in livelihood_activities_for_strategy:
                                livelihood_activity["payment_per_time"] = 1

                    # Add the natural keys for the livelihood strategy to the activities.
                    # This is the last step so that we are sure that the attributes in the livelihood_strategy are
                    # final. For example, the Season 1, etc. alias has been replaced with the real natural key.
                    for i, livelihood_activity in enumerate(livelihood_activities_for_strategy):
                        livelihood_activity["livelihood_strategy"] = livelihood_zone_baseline_key + [
                            livelihood_strategy["strategy_type"],
                            livelihood_strategy["season"] or "",  # Natural key components must be "" rather than None
                            livelihood_strategy["product_id"]
                            or "",  # Natural key components must be "" rather than None
                            livelihood_strategy["additional_identifier"],
                        ]

                    # Natural keys are always a list, so convert the season name if it is set
                    if livelihood_strategy["season"]:
                        livelihood_strategy["season"] = [livelihood_strategy["season"]]

                    # Some Livelihood Activities are only partially defined and have data for the Wealth Groups,
                    # but not for the Summary. In these cases, we can ignore the Wealth Group-level Livelihood Activity
                    # data. Note that if there is Summary data, then we need to include the Livelihood Strategy and
                    # Activities in the fixture, or raise an exception.
                    strategy_is_valid = True

                    # Find the non-empty summary activities, so we can use them to decide whether to raise errors.
                    # Note that we save non-empty livelihood activities that include 0 values for income, expenditure,
                    # or kcals_consumed, but we don't count summary activities that have 0 values for these fields.
                    non_empty_summary_activities = [
                        livelihood_activity
                        for livelihood_activity in livelihood_activities_for_strategy
                        if livelihood_activity["wealth_group"][3] == ""
                        and any(
                            (field in livelihood_activity and livelihood_activity[field])
                            for field in ["income", "expenditure", "kcals_consumed", "percentage_kcals"]
                        )
                    ]

                    # Check the Livelihood Strategy has a Season if one is required.
                    # (e.g. for MilkProduction and ButterProduction).
                    if (
                        livelihood_strategy["strategy_type"] in LivelihoodStrategy.REQUIRES_SEASON
                        and activity_type != ActivityLabel.LivelihoodActivityType.LIVELIHOOD_SUMMARY
                        and ("season" not in livelihood_strategy or not livelihood_strategy["season"])
                    ):
                        strategy_is_valid = False
                        # Include the header rows so that we can see which Wealth Groups are affected
                        rows = df.index[:num_header_rows].tolist() + [livelihood_strategy["row"]]
                        error_message = "Cannot determine season from '%s' for %s %s on row %s for label '%s':\n%s" % (
                            livelihood_strategy["season_original"],
                            "summary" if non_empty_summary_activities else "non-summary",
                            livelihood_strategy["strategy_type"],
                            livelihood_strategy["row"],
                            livelihood_strategy["activity_label"],
                            get_sample_data(df, rows).to_markdown(),
                        )
                        if not non_empty_summary_activities:
                            # No summary activities so we don't need to log an error, a warning is sufficient
                            context.log.warning(error_message)
                        else:
                            # Summary activities exist, so we need to raise an error
                            errors.append(error_message)

                    # Check the Livelihood Strategy has a product_id if one is required.
                    if (
                        livelihood_strategy["strategy_type"] in LivelihoodStrategy.REQUIRES_PRODUCT
                        and activity_type != ActivityLabel.LivelihoodActivityType.LIVELIHOOD_SUMMARY
                        and ("product_id" not in livelihood_strategy or not livelihood_strategy["product_id"])
                    ):
                        strategy_is_valid = False
                        # Include the header rows so that we can see which Wealth Groups are affected
                        rows = df.index[:num_header_rows].tolist() + [livelihood_strategy["row"]]
                        error_message = (
                            "Cannot determine product_id from '%s' for %s %s on row %s for label '%s':\n%s"
                            % (
                                livelihood_strategy["product_id_original"],
                                "summary" if non_empty_summary_activities else "non-summary",
                                livelihood_strategy["strategy_type"],
                                livelihood_strategy["row"],
                                livelihood_strategy["activity_label"],
                                get_sample_data(df, rows).to_markdown(),
                            )
                        )
                        if not non_empty_summary_activities:
                            # No summary activities so we don't need to log an error, a warning is sufficient
                            context.log.warning(error_message)
                        else:
                            # Summary activities exist, so we need to raise an error
                            errors.append(error_message)

                    # For invalid strategies, we have appended an error, and can raise them all at the end.
                    if strategy_is_valid:

                        # Append the stategies and activities to the lists of instances to create.
                        livelihood_strategies.append(livelihood_strategy)
                        livelihood_activities += non_empty_livelihood_activities

                # Now that we have saved the previous livelihood strategy and activities, we can start a new one.

                # There are cases where attributes get copied to the new Livelihood Strategy or Livelihood Activities,
                # notably for MilkProduction and ButterProduction for camels and cattle.
                # Therefore, take a copy of the previous livelihood_strategy in case we need it.
                previous_livelihood_strategy = livelihood_strategy.copy() if livelihood_strategy else None
                previous_livelihood_activities_for_strategy = [
                    livelihood_activity.copy() for livelihood_activity in livelihood_activities_for_strategy
                ]

                # Headings like CROP PRODUCTION: set the strategy type for subsequent rows.
                # Some other labels imply specific strategy types, such as MilkProduction, MeatProduction or LivestockSales
                if label_attributes["strategy_type"]:
                    strategy_type = label_attributes["strategy_type"]
                    # Get the valid fields names so we can determine if the attribute is stored in LivelihoodActivity.extra
                    # LivestockProduction is an artificial, composite strategy type representing the sum of
                    # MilkProduction, ButterProduction and MeatProduction. It isn't stored in the database, and it only
                    # requires income, expenditure and kcals_consumed, so we use the base LivelihoodActivity model.
                    model = (
                        LivelihoodActivity
                        if strategy_type == "LivestockProduction"
                        else class_from_name(f"baseline.models.{strategy_type}")
                    )
                    activity_field_names = [field.name for field in model._meta.concrete_fields]
                    # Also include values that point directly to the primary key of related objects
                    activity_field_names += [
                        field.get_attname()
                        for field in model._meta.concrete_fields
                        if field.get_attname() not in activity_field_names
                    ]

                # Raise an error if we find attributes without a strategy_type being set, unless we are processing
                # the Livelihood Summary section, where we set the attribute from the section heading without wanting
                # to save the actual data.
                if not strategy_type and activity_type != ActivityLabel.LivelihoodActivityType.LIVELIHOOD_SUMMARY:
                    raise ValueError(
                        "Found attributes %s from row %s without a strategy_type set" % (label_attributes, row)
                    )

                # Initialize the new livelihood strategy
                livelihood_strategy = {
                    "livelihood_zone_baseline": livelihood_zone_baseline_key,
                    "strategy_type": strategy_type,
                    "season": label_attributes.get("season", None),
                    "product_id": label_attributes.get("product_id", None),
                    "unit_of_measure_id": label_attributes.get("unit_of_measure_id", None),
                    "currency_id": livelihood_zone_baseline.currency_id,
                    "additional_identifier": label_attributes.get("additional_identifier", None),
                    # Save the row, label and attribute/row map, to aid trouble-shooting
                    "row": row,
                    "activity_label": label,
                    # Similarly, save the original values (i.e. aliases) for season, product and unit of measure.
                    "season_original": label_attributes.get("season_original", None),
                    "product_id_original": label_attributes.get("product_id_original", None),
                    "unit_of_measure_original": label_attributes.get("unit_of_measure_id_original", None),
                }
                # Keep track of which row each attribute came from, to aid trouble-shooting
                livelihood_strategy["attribute_rows"] = {
                    attribute: row
                    for attribute in [
                        "strategy_type",
                        "season",
                        "product_id",
                        "unit_of_measure_id",
                        "currency_id",
                        "additional_identifier",
                    ]
                    if livelihood_strategy[attribute]
                }

                # Initialize the list of livelihood activities for the new livelihood strategy
                livelihood_activities_for_strategy = [
                    {
                        "livelihood_zone_baseline": livelihood_zone_baseline_key,
                        "strategy_type": livelihood_strategy["strategy_type"],
                        "scenario": LivelihoodActivityScenario.BASELINE,
                        "wealth_group": wealth_group_df.iloc[i]["natural_key"],
                        # Include the column and row to aid trouble-shooting
                        "bss_sheet": worksheet_name,
                        "bss_column": df.columns[i + 1],
                        "bss_row": row,
                        "activity_label": label,
                    }
                    for i in range(len(df.loc[row, "B":]))
                ]

            else:

                # We are not starting a new Livelihood Strategy, but there may be
                # additional attributes that need to be added to the current one.

                # If we have attributes but haven't started a livelihood_strategy, then raise an error.
                if not livelihood_strategy:
                    additional_attributes = [label_attributes["attribute"]] if label_attributes["attribute"] else []
                    for attribute in [
                        "is_start",
                        "product_id",
                        "unit_of_measure_id",
                        "season",
                        "additional_identifier",
                        "notes",
                    ]:
                        if label_attributes[attribute]:
                            additional_attributes.append(attribute)
                    raise ValueError(
                        "Found attributes from label '%s' in row %s without an existing LivelihoodStrategy: %s"
                        % (label_attributes["activity_label"], row, ", ".join(additional_attributes))
                    )

                # Only update expected keys, and only if we found a value for that attribute that doesn't conflict with
                # an existing value.
                for attribute, value in label_attributes.items():
                    if attribute in livelihood_strategy and attribute not in ["activity_label", "pattern"] and value:
                        if not livelihood_strategy[attribute]:
                            # Attribute not yet set for the `livelihood_strategy`, so it is safe to set it.
                            livelihood_strategy[attribute] = value
                            livelihood_strategy["attribute_rows"][attribute] = row

                        # If this attribute is already set for the `livelihood_strategy`, then the value should be the
                        # same. For example, we may detect the unit of measure multiple times for a single
                        # `livelihood_strategy`:
                        #     Maize rainfed: kg produced
                        #     sold/exchanged (kg)
                        #     other use (kg)
                        # But if we receive different values for the same attribute, it probably indicates a metadata
                        # inconsistency for that attribute (or possibly a failure to recognize the start of the next
                        # Livelihood Strategy
                        elif (
                            attribute != "product_id"
                            and livelihood_strategy[attribute] != value
                            and not attribute.endswith("_original")
                        ) or (
                            # For the product_id we only check using startswith because sometimes the subsequent rows
                            # specify a parent of the main product for the Livelihood Strategy. For example, for a
                            # LivestockSales strategy, the first row may be Sheep - Export Quantity (L02122HB) but a
                            # subsequent row, such as percentage_sold_slaughtered, may be  for just Sheep (L02122).
                            # We also ignore Shoats (L02129AA) because the offtake for shoats (sheep and goats
                            # together) may be specified after the Livelihood Strategies for sheep and goats
                            # separately.
                            # @TODO Note that percentage_sold_slaughtered (i.e. % offtake) should really be a
                            # Wealth Group Characteristic Value rather than a Livelihood Activity attribute. In future,
                            # we could attempt to create a single Wealth Group Characteristic Value when we encounter
                            # this attribute.
                            attribute == "product_id"
                            and not livelihood_strategy["product_id"].startswith(value)
                            and not value == "L02129AA"
                        ):
                            errors.append(
                                "Found different value '%s' from row %s for existing attribute '%s' with value '%s' from row %s"
                                % (
                                    value,
                                    row,
                                    attribute,
                                    livelihood_strategy[attribute],
                                    livelihood_strategy["attribute_rows"][attribute],
                                )
                            )

            # Update the LivelihoodActivity records
            if any(value for value in df.loc[row, "B":].astype(str).str.strip()):

                # Some labels are ambiguous and map to different attributes depending on the strategy_type.
                if activity_attribute == "quantity_produced_or_purchased":
                    if livelihood_strategy["strategy_type"] == LivelihoodStrategyType.CROP_PRODUCTION:
                        activity_attribute = "quantity_produced"
                    elif livelihood_strategy["strategy_type"] == LivelihoodStrategyType.PAYMENT_IN_KIND:
                        activity_attribute = "quantity_produced"
                    elif livelihood_strategy["strategy_type"] == LivelihoodStrategyType.FOOD_PURCHASE:
                        activity_attribute = "unit_multiple"
                    elif livelihood_strategy["strategy_type"] == LivelihoodStrategyType.RELIEF_GIFT_OTHER:
                        activity_attribute = "unit_multiple"
                    elif livelihood_strategy["strategy_type"] == LivelihoodStrategyType.OTHER_CASH_INCOME:
                        activity_attribute = "payment_per_time"
                    else:
                        errors.append(
                            "Invalid strategy_type %s for attribute %s from label '%s'"
                            % (strategy_type, activity_attribute, label)
                        )
                        activity_attribute = None

                # For Payment In Kind and Other Cash Income the attribute for payment_per_time sometimes uses a label
                # that normally matches the price attribute.
                if activity_attribute == "price":
                    if livelihood_strategy["strategy_type"] in (
                        LivelihoodStrategyType.PAYMENT_IN_KIND,
                        LivelihoodStrategyType.OTHER_CASH_INCOME,
                    ):
                        activity_attribute = "payment_per_time"

                # Some BSS incorrectly specify the product in the value columns instead of in the label column
                # Therefore, if we have specified the product__name as the attribute, check that the product
                # can be identified and is the same for all columns and then add it to the Livelihood Strategy.
                elif activity_attribute == "product__name":
                    product_name_df = pd.DataFrame(df.loc[row, "B":]).rename(columns={row: "product__name"})
                    product_name_df["product__name"] = product_name_df["product__name"].replace(["", 0], pd.NA)
                    if product_name_df["product__name"].dropna().nunique() > 0:
                        try:
                            product_name_df = classifiedproductlookup.do_lookup(
                                product_name_df, "product__name", "product_id"
                            )
                            if product_name_df["product_id"].nunique() > 1:
                                # Only log a warning, so that the code that checks for a valid product when
                                # the livelihood strategy is finalized can raise an error if necessary, depending
                                # on whether there are any summary livelihood activities.
                                context.log.warning(
                                    "Found multiple products %s on row %s for label '%s'"
                                    % (
                                        ", ".join(product_name_df["product__name"].dropna().astype(str).unique()),
                                        row,
                                        label,
                                    )
                                )
                            elif product_name_df["product_id"].nunique() == 1:
                                if not livelihood_strategy["product_id"]:
                                    livelihood_strategy["product_id"] = product_name_df["product_id"].dropna().iloc[0]
                                elif (
                                    livelihood_strategy["product_id"]
                                    and livelihood_strategy["product_id"]
                                    != product_name_df["product_id"].dropna().iloc[0]
                                ):
                                    # Include the header rows so that we can see which Wealth Groups are affected
                                    rows = df.index[:num_header_rows].tolist() + [row]
                                    errors.append(
                                        "Found different products %s and %s in label and other columns on row %s for label '%s':\n%s"
                                        % (
                                            livelihood_strategy["product_id"],
                                            product_name_df["product_id"].iloc[0],
                                            row,
                                            label,
                                            get_sample_data(df, rows).to_markdown(),
                                        )
                                    )

                        except ValueError:
                            if not livelihood_strategy["product_id"]:
                                # Include the header rows so that we can see which Wealth Groups are affected
                                rows = df.index[:num_header_rows].tolist() + [row]
                                errors.append(
                                    "Failed to identify product from %s on row %s for label '%s':\n%s"
                                    % (
                                        ", ".join(product_name_df["product__name"].dropna().astype(str).unique()),
                                        row,
                                        label,
                                        get_sample_data(df, rows).to_markdown(),
                                    )
                                )

                # Some BSS incorrectly specify the product in the label in column A, but not the attribute.
                # Therefore, we infer the missing attribute if possible.
                if not activity_attribute or (
                    activity_attribute == "product__name"
                    and (livelihood_strategy["product_id"] or livelihood_strategy["product_id_original"])
                ):
                    # Check the following row, and attempt to infer the attribute for this row
                    next_label_attributes = all_label_attributes.loc[row + 1].fillna("")
                    if next_label_attributes["attribute"] == "name_of_local_measure":
                        activity_attribute = "number_of_local_measures"
                    elif (
                        livelihood_strategy["strategy_type"] == LivelihoodStrategyType.OTHER_PURCHASE
                        and label_attributes["is_start"]
                        and next_label_attributes["is_start"]
                    ):
                        activity_attribute = "expenditure"
                    elif (
                        livelihood_strategy["strategy_type"] == LivelihoodStrategyType.CROP_PRODUCTION
                        and next_label_attributes["attribute"] == "price"
                    ):
                        activity_attribute = "quantity_sold"

                # Make sure we have an attribute!
                if not activity_attribute:
                    # We can ignore the values if they are all 0 or all 1, as they are typically just
                    # copy/paste errors from the previous row, or a note that data exists for the
                    # Livelihood Activity without containing any actual data.
                    values = df.loc[row, "B":].replace("", pd.NA).dropna().astype(str).str.strip().unique()
                    if values.size > 1 or values[0] not in ["0", "1"]:
                        # Include the header rows so that we can see which Wealth Groups are affected
                        rows = df.index[:num_header_rows].tolist() + [row]
                        errors.append(
                            "Found values %s without an identified attribute on row %s for label '%s':\n%s"
                            % (
                                ", ".join(values),
                                row,
                                label,
                                get_sample_data(df, rows).to_markdown(),
                            )
                        )

                # If the activity label that marks the start of a Livelihood Strategy is not
                # recognized by the get_label_attributes lookup, then repeated labels like
                # `kcals (%)` will appear to be duplicate attributes for the previous
                # LivelihoodStrategy. Therefore, if we have `allow_unrecognized_labels` we
                # need to ignore the duplicates, and if we don't we should raise an error.
                elif activity_attribute in livelihood_strategy["attribute_rows"]:
                    if allow_unrecognized_labels:
                        # Skip to the next row
                        continue
                    else:
                        errors.append(
                            "Found duplicate attribute '%s' for label '%s' in row %s that was already found in row %s for this LivelihoodStrategy"
                            % (
                                activity_attribute,
                                label,
                                row,
                                livelihood_strategy["attribute_rows"][activity_attribute],
                            )
                        )

                # Add the attribute to the LivelihoodStrategy.attribute_rows, assuming we have a strategy_type.
                # Some rows may have set attributes without setting a strategy_type, for example in the
                # Livelihood Summary section.
                elif strategy_type:
                    livelihood_strategy["attribute_rows"][activity_attribute] = row
                    # Assertion to prevent linting from complaining about possible None values
                    assert activity_field_names is not None, (
                        "Found activity_attribute %s from row %s, but there is no Livelihood Strategy and therefore no activity_field_names defined."
                        % (activity_attribute, row)
                    )
                    for i, value in enumerate(df.loc[row, "B":]):
                        # Some attributes are stored in LivelihoodActivity.extra rather than individual fields.
                        if activity_attribute not in activity_field_names:
                            if "extra" not in livelihood_activities_for_strategy[i]:
                                livelihood_activities_for_strategy[i]["extra"] = {}
                            livelihood_activities_for_strategy[i]["extra"][activity_attribute] = value
                        else:
                            livelihood_activities_for_strategy[i][activity_attribute] = value

        except Exception as e:
            if column:
                raise RuntimeError(
                    "Unhandled error in BSS %s processing cell '%s'!%s%s for label '%s'"
                    % (partition_key, worksheet_name, column, row, label)
                ) from e
            else:
                raise RuntimeError(
                    "Unhandled error in BSS %s processing row '%s'!%s with label '%s'"
                    % (partition_key, worksheet_name, row, label)
                ) from e

    result = {
        "LivelihoodStrategy": livelihood_strategies,
        "LivelihoodActivity": livelihood_activities,
    }
    metadata = {
        "num_livelihood_strategies": len(livelihood_strategies),
        "num_livelihood_activities": len(livelihood_activities),
        "num_unrecognized_labels": len(unrecognized_labels),
        "pct_rows_recognized": round(
            (
                1
                - len(df.iloc[num_header_rows:][df.iloc[num_header_rows:]["A"].isin(unrecognized_labels["label"])])
                / len(df.iloc[num_header_rows:])
            )
            * 100
        ),
        "preview": MetadataValue.md(f"```json\n{json.dumps(result, indent=4, ensure_ascii=False)}\n```"),
    }
    if not unrecognized_labels.empty:
        metadata["unrecognized_labels"] = MetadataValue.md(unrecognized_labels.to_markdown(index=False))

    if errors:
        if config.strict:
            raise RuntimeError(
                "Missing or inconsistent metadata in BSS %s worksheet '%s':\n%s"
                % (partition_key, worksheet_name, "\n".join(errors))
            )
        else:
            context.log.error(
                "Missing or inconsistent metadata in BSS %s worksheet '%s':\n%s"
                % (partition_key, worksheet_name, "\n".join(errors))
            )
            metadata["errors"] = MetadataValue.md(f'```text\n{"\n".join(errors)}\n```')

    return Output(
        result,
        metadata=metadata,
    )


def get_annotated_instances_from_dataframe(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    livelihood_activity_dataframe: pd.DataFrame,
    livelihood_summary_dataframe: pd.DataFrame,
    activity_type: str,
    num_header_rows: int,
) -> Output[dict]:
    """
    Get the LivelhoodStrategy and LivelihoodActivity instances from the BSS, annotated with completeness information.

    Completeness of the recognized detail livelihood activities is calculated as a percentage of the total income,
    expenditure and kcals_consumed reported in the livelihood summary section at the top of the Data worksheet.
    """
    # Find the metadata for this BSS
    partition_key = context.asset_partition_key_for_output()
    livelihood_zone_baseline = LivelihoodZoneBaseline.objects.get_by_natural_key(*partition_key.split("~")[1:])

    # Get the detail LivelihoodStrategy and LivelihoodActivity instances
    output = get_instances_from_dataframe(
        context,
        config,
        livelihood_activity_dataframe,
        livelihood_zone_baseline,
        activity_type,
        num_header_rows,
        partition_key,
    )

    if output.value["LivelihoodActivity"]:
        # Get the summary instances
        reported_summary_output = get_instances_from_dataframe(
            context,
            config,
            livelihood_summary_dataframe,
            livelihood_zone_baseline,
            ActivityLabel.LivelihoodActivityType.LIVELIHOOD_SUMMARY,
            # The summary section is on the Data worksheet, so has the same number of header rows
            # regardless of the activity_type
            len(HEADER_ROWS),
            partition_key,
        )

        # Annotate the output metadata with completeness information
        # Get the summary dataframe, grouped by strategy_type
        summary_df = pd.DataFrame(reported_summary_output.value["LivelihoodActivity"])
        for col in ["income", "expenditure", "kcals_consumed"]:
            summary_df[col] = pd.to_numeric(summary_df[col], errors="coerce").fillna(0)
        summary_df = (
            summary_df[["strategy_type", "income", "expenditure", "kcals_consumed"]].groupby("strategy_type").sum()
        )

        # Add the recognized Livelihood Activities, also grouped by strategy_type
        recognized_activities_df = pd.DataFrame(output.value["LivelihoodActivity"])
        for column in ["income", "expenditure", "kcals_consumed"]:
            if column in recognized_activities_df:
                recognized_activities_df[column] = pd.to_numeric(
                    recognized_activities_df[column], errors="coerce"
                ).fillna(0)
            else:
                recognized_activities_df[column] = 0
        summary_df = summary_df.join(
            recognized_activities_df[["strategy_type", "income", "expenditure", "kcals_consumed"]]
            .groupby("strategy_type")
            .sum(),
            on="strategy_type",
            lsuffix="_summary",
            rsuffix="_recognized",
        ).fillna(0)

        # Add a totals row at the end
        summary_df.loc["Total"] = summary_df.sum(numeric_only=True)

        # Add completeness percentages
        summary_df = summary_df.round(0)
        summary_df["income_completeness"] = summary_df.apply(
            lambda row: (
                round(row["income_recognized"] / row["income_summary"] * 100, 1)
                if row["income_summary"] > 0
                else pd.NA
            ),
            axis=1,
        )
        summary_df["expenditure_completeness"] = summary_df.apply(
            lambda row: (
                round(row["expenditure_recognized"] / row["expenditure_summary"] * 100, 1)
                if row["expenditure_summary"] > 0
                else pd.NA
            ),
            axis=1,
        )
        summary_df["kcals_consumed_completeness"] = summary_df.apply(
            lambda row: (
                round(row["kcals_consumed_recognized"] / row["kcals_consumed_summary"] * 100, 1)
                if row["kcals_consumed_summary"] > 0
                else pd.NA
            ),
            axis=1,
        )
        # Format the numbers as integers, for better display in the markdown table
        for column in ["income", "expenditure", "kcals_consumed"]:
            for source in ["recognized", "summary"]:
                summary_df[f"{column}_{source}"] = summary_df.apply(
                    lambda row: (
                        int(row[f"{column}_{source}"])
                        if (pd.notna(row[f"{column}_recognized"]) and row[f"{column}_recognized"] > 0)
                        or (pd.notna(row[f"{column}_summary"]) and row[f"{column}_summary"] > 0)
                        else pd.NA
                    ),
                    axis="columns",
                )

        # Transpose and reorder the columns and rows
        # Sort the rows so that Strategy Types appear in the same order as in the BSS
        ordered_strategy_types = ["LivestockProduction"] + [x for x in LivelihoodStrategyType] + ["Total"]
        summary_df["strategy_type"] = pd.Categorical(
            summary_df.reset_index(drop=False)["strategy_type"],
            categories=ordered_strategy_types,
            ordered=True,
        )
        summary_df = summary_df.reset_index(drop=True).sort_values(by="strategy_type")
        summary_df = summary_df[
            [
                "strategy_type",
                "kcals_consumed_recognized",
                "kcals_consumed_summary",
                "kcals_consumed_completeness",
                "income_recognized",
                "income_summary",
                "income_completeness",
                "expenditure_recognized",
                "expenditure_summary",
                "expenditure_completeness",
            ]
        ]
        summary_df = summary_df.set_index("strategy_type").transpose()

        # Add the completeness summary to the output metadata
        output.metadata["pct_kcals_consumed_recognized"] = float(
            summary_df.loc["kcals_consumed_completeness", "Total"]
        )
        output.metadata["pct_income_recognized"] = float(summary_df.loc["income_completeness", "Total"])
        output.metadata["pct_expenditure_recognized"] = float(summary_df.loc["expenditure_completeness", "Total"])
        output.metadata["completeness_summary"] = MetadataValue.md(
            summary_df.replace(pd.NA, None).to_markdown(floatfmt=",.0f")
        )

        # Move the preview and errors metadata item to the end of the dict
        if "errors" in output.metadata:
            output.metadata["errors"] = output.metadata.pop("errors")
        output.metadata["preview"] = output.metadata.pop("preview")

    return output


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def livelihood_activity_instances(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    livelihood_activity_dataframe: pd.DataFrame,
    livelihood_summary_dataframe: pd.DataFrame,
) -> Output[dict]:
    """
    LivelhoodStrategy and LivelihoodActivity instances extracted from the BSS.
    """
    return get_annotated_instances_from_dataframe(
        context,
        config,
        livelihood_activity_dataframe,
        livelihood_summary_dataframe,
        ActivityLabel.LivelihoodActivityType.LIVELIHOOD_ACTIVITY,
        len(HEADER_ROWS),
    )


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def livelihood_activity_valid_instances(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    livelihood_activity_instances: dict,
    wealth_characteristic_instances: dict,
) -> Output[dict]:
    """
    Valid LivelhoodStrategy and LivelihoodActivity instances from a BSS, ready to be loaded via a Django fixture.
    """
    partition_key = context.asset_partition_key_for_output()
    # Livelihood Activities depend on the Wealth Groups, so copy them from the wealth_characteristic_instances, making
    # sure that the WealthGroup is the first entry in the dict, so that the lookup keys have been created before
    # validate_instances processes the child model and needs them.
    if any(instances for instances in livelihood_activity_instances.values()):
        livelihood_activity_instances = {
            **{"WealthGroup": wealth_characteristic_instances["WealthGroup"]},
            **livelihood_activity_instances,
        }
    return validate_instances(context, config, livelihood_activity_instances, partition_key)


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def livelihood_activity_fixture(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    livelihood_activity_valid_instances: dict,
) -> Output[list[dict]]:
    """
    Django fixture for the Livelihood Activities from a BSS.
    """
    return get_fixture_from_instances(livelihood_activity_valid_instances)


@asset(partitions_def=bss_instances_partitions_def)
def imported_livelihood_activities(
    context: AssetExecutionContext,
    livelihood_activity_fixture,
) -> Output[None]:
    """
    Imported Django fixtures for a BSS, added to the Django database.
    """
    return import_fixture(livelihood_activity_fixture)
