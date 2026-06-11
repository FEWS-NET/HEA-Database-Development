"""
Dagster assets related to key parameters read from the key parameters analysis section of the Summ worksheet in a BSS.

The Key Parameters section is typically between rows 931 and 1025 of the Summ worksheet.

An example of relevant rows from the worksheet:
    |     | A                                                              | B   | C                       | D                       | E                       | F                     | G   | H                                                                        | I                      | J                     | K                      | L   | M                     | N                      |
    |----:|:---------------------------------------------------------------|:----|:------------------------|:------------------------|:------------------------|:----------------------|:----|:-------------------------------------------------------------------------|:-----------------------|:----------------------|:-----------------------|:----|:----------------------|:-----------------------|
    |   1 | HEA BASELINES NE NIGERIA                                       |     | Borno-Yobe-Bauchi Millet, Cowpeas, Groundnuts and Sesame Livelihood Zone    |                       |     | Borno-Yobe-Bauchi Millet, Cowpeas, Groundnuts and Sesame Livelihood Zone |                        |                       |                        |     |                       |                        |
    |   2 |                                                                |     | SUMMARY                 |                         |                         |                       |     | RESPONSE                                                                 |                        |                       |                        |     |                       |                        |
    |   3 | WEALTH GROUP                                                   |     | BASELINE                |                         |                         |                       |     | MAXIMIUM (or MINIMUM)                                                    |                        |                       |                        |     | EXPANDABILITY         |                        |
    |   4 |                                                                |     | Very Poor               | Poor                    | Middle                  | B/Off                 |     | Very Poor                                                                | Poor                   | Middle                | B/Off                  |     | Very Poor             | Poor                   |
    |   5 | Village/settlement                                             |     |                         |                         |                         |                       |     |                                                                          |                        |                       |                        |     |                       |                        |
    |   6 | Interview number                                               |     |                         |                         |                         |                       |     |                                                                          |                        |                       |                        |     |                       |                        |
    |   7 | Interviewers                                                   |     |                         |                         |                         |                       |     |                                                                          |                        |                       |                        |     |                       |                        |
    |   8 | Reference year                                                 |     |                         |                         |                         |                       |     |                                                                          |                        |                       |                        |     |                       |                        |
    |   9 | Currency                                                       |     | Naira                   | Naira                   | Naira                   | Naira                 |     | Cross-check of totals vs. Data sheet                                     |                        |                       |                        |     |                       |                        |
    | 931 | Key parameters analysis                                        |     |                         |                         |                         |                       |     |                                                                          |                        |                       |                        |     |                       |                        |
    | 932 | cut-off for significance (% kcals)                             |     | 0.05                    |                         |                         |                       |     |                                                                          |                        |                       |                        |     |                       |                        |
    | 933 |                                                                |     | VP                      | P                       | M                       | BO                    |     | VP                                                                       | P                      | M                     | BO                     |     |                       |                        |
    | 934 | cost of 100% kcals                                             |     | 407102.8443973635       | 523417.9427966102       | 639733.0411958569       | 930520.7871939737     |     |                                                                          |                        |                       |                        |     |                       |                        |
    | 935 |                                                                |     |                         |                         |                         |                       |     |                                                                          |                        |                       |                        |     | key parameter?        |                        |
    | 936 | CROPS:                                                         |     |                         |                         |                         |                       |     |                                                                          |                        |                       |                        |     | quant.                | price                  |
    | 937 | Green crops season 1 Season 1: no of months                    |     | 0                       | 0                       | 0                       | 0                     |     |                                                                          |                        |                       |                        |     |                       |                        |
    | 938 | Green crops season 2 Season 2: no of months                    |     | 0                       | 0                       | 0                       | 0                     |     |                                                                          |                        |                       |                        |     |                       |                        |
    | 939 | Maize: kg produced                                             |     | 0                       | 0                       | 0                       | 0                     |     | 0                                                                        | 0                      | 0                     | 0                      |     |                       |                        |
    | 940 | Rice - rainfed (paddy): kg produced                            |     | 0                       | 0                       | 0                       | 0.19558939736191064   |     | 0                                                                        | 0                      | 0                     | 0.19558939736191064    |     | yes                   | yes                    |
    | 941 | Rice - irrigated (paddy): kg produced                          |     | 0                       | 0                       | 0                       | 0                     |     | 0                                                                        | 0                      | 0                     | 0                      |     |                       |                        |
    | 942 | Wheat - irrigated: kg produced                                 |     | 0                       | 0                       | 0                       | 0                     |     | 0                                                                        | 0                      | 0                     | 0                      |     |                       |                        |
    | 943 | Sorghum: kg produced                                           |     | 0.172024974373311       | 0.20584184967746613     | 0.8336594911937378      | 1.0203644814090018    |     | 0.03868801266499331                                                      | 0.016717042509565013   | 0.3446750219244859    | 0.4696294870722799     |     | yes                   | yes                    |
    | 944 | Millet: kg produced                                            |     | 0.20296337713167462     | 0.228897586431833       | 0.7318982387475538      | 0.9146037181996086    |     | 0.02923094290243939                                                      | 0.02760700163008165    | 0.38406645300157      | 0.5168073691832024     |     | yes                   | yes                    |
    | 945 | Cowpeas: kg produced                                           |     | 0.06833380589031189     | 0.09697290037786516     | 0.2896138467999658      | 0.29555319326754326   |     | 0.050662873727967433                                                     | 0.07164446789813576    | 0.22509389186905202   | 0.22971007519839778    |     | yes                   | yes                    |
    | 946 | Groundnuts (dried): kg produced                                |     | 0.009235995404468244    | 0.062445662111119904    | 0.48641636424982376     | 0.37687617111023053   |     | 0.009235995404468244                                                     | 0.056570471852368      | 0.44315359961719614   | 0.3433561124018156     |     | yes                   | yes                    |
    | 947 | Soybeans: kg produced                                          |     | 0                       | 0                       | 0                       | 0                     |     | 0                                                                        | 0                      | 0                     | 0                      |     |                       |                        |
    | 948 | Sesame: no. local meas.                                        |     | 0                       | 0.03152356587517974     | 0.25498917438291047     | 0.25523341688710866   |     | 0                                                                        | 0.0319438800868488     | 0.25498917438291047   | 0.25523341688710866    |     | yes                   | yes                    |
    | 949 | Bambara nuts: no. local meas.                                  |     | 0                       | 0                       | 0.10121409373972998     | 0.06958468944606436   |     | 0                                                                        | 0                      | 0.10121409373972998   | 0.06958468944606436    |     | yes                   | yes                    |
    | 950 | Sweet potatoes: no. local meas.                                |     | 0                       | 0                       | 0.04501478961630541     | 0                     |     | 0                                                                        | 0                      | 0.04298668073888146   | 0                      |     |                       |                        |
    | 951 | Watermelon: no. local meas.                                    |     | 0                       | 0                       | 0.046894560806052504    | 0.12896004221664437   |     | 0                                                                        | 0                      | 0.046894560806052504  | 0.12896004221664437    |     | yes                   | yes                    |
    | 952 | Cassava (fresh): no. local meas.                               |     | 0                       | 0                       | 0                       | 0                     |     | 0                                                                        | 0                      | 0                     | 0                      |     |                       |                        |
    | 953 | Yams (fresh): no. local meas.                                  |     | 0                       | 0                       | 0                       | 0                     |     | 0                                                                        | 0                      | 0                     | 0                      |     |                       |                        |
    | 954 | Other crop: Cocoyams                                           |     | 0                       | 0                       | 0                       | 0                     |     | 0                                                                        | 0                      | 0                     | 0                      |     |                       |                        |
    | 955 | Other crop: Citrus fruits                                      |     | 0                       | 0                       | 0                       | 0                     |     | 0                                                                        | 0                      | 0                     | 0                      |     |                       |                        |
"""

import json
import os
import re
from collections import defaultdict

import django
import openpyxl
import pandas as pd
from dagster import AssetExecutionContext, MetadataValue, Output, asset

from ..configs import BSSMetadataConfig
from ..partitions import bss_instances_partitions_def
from .base import get_bss_dataframe
from .fixtures import validate_instances
from .livelihood_activity import get_all_label_attributes

# set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hea.settings.production")

# Configure Django with our custom settings before importing any Django classes
django.setup()

from pipelines.utils import (  # NOQA: E402
    get_cell_formula,
    get_formula_references,
)

from baseline.models import LivelihoodZoneBaseline  # NOQA: E402
from metadata.models import ActivityLabel  # NOQA: E402


def _get_grouped_detail_strategies(instances: dict, subtotal_field: str) -> dict[str, list[dict]]:
    grouped_strategies = defaultdict(list)
    for strategy in instances.get("LivelihoodStrategy", []):
        subtotal_label = strategy.get(subtotal_field)
        if subtotal_label:
            grouped_strategies[subtotal_label].append(strategy)
    return grouped_strategies


def _get_livelihood_activity_groups(
    livelihood_zone_baseline: LivelihoodZoneBaseline,
    livelihood_activity_dataframe: pd.DataFrame,
    other_cash_income_dataframe: pd.DataFrame,
    wild_foods_dataframe: pd.DataFrame,
) -> tuple[dict[str, dict], list[str]]:
    """
    Create a map of labels from the 'Data' worksheet ending in `see Data2` or `see Data3` to the subtotal rows in those worksheets.

    Returns a dictionary of groups and a list of errors encountered during processing.

    This map is created by reading the formulae from column B in the 'Data' worksheet to identify the source rows in
    the 'Data2' or 'Data3' worksheet. It uses openpyxl to read the original file to access the formulae.

    Note that because openpyxl can't read .xls files, and xlrd can't read formulae, this function only works
    for .xlsx files.
    """
    with livelihood_zone_baseline.bss.open() as original_file:
        try:
            original_workbook = openpyxl.load_workbook(original_file, data_only=False)
        except Exception:
            # Original file can't be read, so it is probably an unsupported format like .xls.
            return {}, []

    all_label_attributes = get_all_label_attributes(
        livelihood_activity_dataframe["A"],
        ActivityLabel.LivelihoodActivityType.LIVELIHOOD_ACTIVITY,
        livelihood_zone_baseline.livelihood_zone.country_id,
        livelihood_zone_baseline.livelihood_zone_id,
    )

    def finalize_group(group, row_errors):
        if not row_errors:
            groups[group["summary_label"]] = group
        else:
            errors.extend(row_errors)

    group = None
    group_errors = []
    groups = {}
    errors = []
    pattern = re.compile(
        r"^(?P<summary_label>.+?)[ -]*\(?see (?:worksheet )?+(?P<detail_sheet>Data ?[23])\)?$", re.IGNORECASE
    )
    for row in livelihood_activity_dataframe.index:
        label = (
            livelihood_activity_dataframe.loc[row, "A"].strip() if livelihood_activity_dataframe.loc[row, "A"] else ""
        )
        label_attributes = all_label_attributes.loc[row]
        match = pattern.match(label)
        if group and (label_attributes["is_start"] or match):
            # Finalize the previous group before starting a new one
            finalize_group(group, group_errors)
            group = None
            group_errors = []
        if match:
            # This is the start of a summary group that references a detail sheet.
            summary_label = label
            detail_sheet = match.group("detail_sheet").replace(" ", "")
            detail_dataframe = other_cash_income_dataframe if detail_sheet == "Data2" else wild_foods_dataframe
            group = {
                "summary_label": summary_label,
                "summary_row": row,
                "detail_sheet": detail_sheet,
            }
        elif group:
            # We are within a summary group, so look for rows for the summary attributes.
            attribute = label_attributes["attribute"]
            if attribute in ("income", "percentage_kcals"):
                # Find the referenced subtotal row from the formula in the summary row in the Data worksheet,
                # using the original workbook to access the actual formula.
                formula = get_cell_formula(original_workbook["Data"], f"B{row}")
                if not formula:
                    group_errors.append("No formula found in 'Data'!B%s for label '%s'" % (row, label))
                else:
                    references = get_formula_references(formula, default_sheet="Data")
                    for reference in references:
                        if reference["sheet"] == detail_sheet:
                            group[f"{attribute}_subtotal_row"] = reference["start_row"]
                            group[f"{attribute}_subtotal_label"] = detail_dataframe.loc[reference["start_row"], "A"]
                            break

                    if f"{attribute}_subtotal_row" not in group:
                        group_errors.append(
                            "Missing '%s' subtotal row in '%s' for '%s' from 'Data'!A%s"
                            % (attribute, detail_sheet, label, row)
                        )
                    if f"{attribute}_subtotal_label" not in group:
                        group_errors.append(
                            "Missing '%s' subtotal label in '%s' for '%s' from 'Data'!A%s"
                            % (attribute, detail_sheet, label, row)
                        )
        if group and row == livelihood_activity_dataframe.index[-1]:
            # Finalize the last group, if necessary.
            finalize_group(group, group_errors)

    return groups, errors


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def livelihood_activity_groups(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    livelihood_activity_dataframe: pd.DataFrame,
    other_cash_income_dataframe: pd.DataFrame,
    wild_foods_dataframe: pd.DataFrame,
) -> Output[dict]:
    """
    Map of Data worksheet labels ending in `see Data2` or `see Data3` to the subtotal rows in those worksheets.
    """
    partition_key = context.asset_partition_key_for_output()
    livelihood_zone_baseline = LivelihoodZoneBaseline.objects.get_by_natural_key(*partition_key.split("~")[1:])
    groups, errors = _get_livelihood_activity_groups(
        livelihood_zone_baseline,
        livelihood_activity_dataframe,
        other_cash_income_dataframe,
        wild_foods_dataframe,
    )

    metadata = {
        "num_groups": len(groups),
        "preview": MetadataValue.md(f"```json\n{json.dumps(groups, indent=4, ensure_ascii=False)}\n```"),
    }
    if errors:
        if config.strict:
            raise RuntimeError(
                "Unable to map livelihood activity groups in BSS %s:\n%s" % (partition_key, "\n".join(errors))
            )
        context.log.warning(
            "Unable to map livelihood activity groups in BSS %s:\n%s" % (partition_key, "\n".join(errors))
        )
        metadata["errors"] = MetadataValue.md(f'```text\n{"\n".join(errors)}\n```')

    return Output(groups, metadata=metadata)


@asset(partitions_def=bss_instances_partitions_def)
def key_parameter_dataframe(config: BSSMetadataConfig, corrected_files) -> Output[pd.DataFrame]:
    """
    DataFrame of key parameters from the Summ worksheet in a BSS.
    """
    return get_bss_dataframe(
        config,
        corrected_files,
        "Summ",
        start_strings=["Key parameters analysis", "Analyse des paramètres clés"],
        end_strings=None,
        header_rows=[],
        end_col="N",
        num_summary_cols=0,
        fill_blank_rows=False,
    )


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def key_parameter_instances(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    key_parameter_dataframe: pd.DataFrame,
    livelihood_activity_groups: dict,
    livelihood_activity_instances: dict,
    other_cash_income_instances: dict,
    wild_foods_instances: dict,
) -> Output[dict]:
    """
    KeyParameter instances extracted from the Summ worksheet in a BSS.
    """
    if key_parameter_dataframe.empty:
        return Output({}, metadata={"message": "No key parameter dataframe to parse"})

    partition_key = context.asset_partition_key_for_output()
    livelihood_strategy_map = {
        strategy["activity_label"]: [strategy]
        for strategy in livelihood_activity_instances.get("LivelihoodStrategy", [])
    }
    for group_label, group in livelihood_activity_groups.items():
        if group["detail_sheet"] == "Data2":
            livelihood_strategy_map[group_label] = [
                strategy
                for strategy in other_cash_income_instances.get("LivelihoodStrategy", [])
                if strategy.get("income_subtotal_label") == group.get("income_subtotal_label")
            ]
        elif group["detail_sheet"] == "Data3":
            livelihood_strategy_map[group_label] = [
                strategy
                for strategy in wild_foods_instances.get("LivelihoodStrategy", [])
                if (
                    (strategy.get("income_subtotal_label") == group.get("income_subtotal_label"))
                    or strategy.get("percentage_kcals_subtotal_label") == group.get("percentage_kcals_subtotal_label")
                )
            ]

    # Find the columns that contain monitor_quantity and monitor_price
    quantity_column = None
    price_column = None
    first_key_parameter_row = None
    quantity_headings = ["quantity", "quant."]
    price_headings = ["price", "prix"]
    for row in key_parameter_dataframe.index:
        for col in key_parameter_dataframe.columns:
            if key_parameter_dataframe.loc[row, col] in (quantity_headings):
                quantity_column = col
            if key_parameter_dataframe.loc[row, col] in (price_headings):
                price_column = col
        if quantity_column and price_column:
            first_key_parameter_row = row
            break
    if not quantity_column or not price_column:
        raise ValueError("Cannot identify Key Parameter quantity and price columns")

    key_parameters_by_natural_key = {}
    errors = []
    headings = ["key parameter?"] + quantity_headings + price_headings
    true_values = ["yes"]
    for row in key_parameter_dataframe.loc[first_key_parameter_row:].index:
        label = key_parameter_dataframe.loc[row, "A"].strip() if key_parameter_dataframe.loc[row, "A"] else ""
        monitor_quantity = key_parameter_dataframe.loc[row, quantity_column]
        monitor_price = key_parameter_dataframe.loc[row, price_column]

        # Ignore known heading rows
        if (monitor_quantity in headings or monitor_quantity == "") and (
            monitor_price in headings or monitor_price == ""
        ):
            continue
        elif monitor_quantity or monitor_price:

            # Normalize the values
            if monitor_quantity in true_values:
                monitor_quantity = True
            elif monitor_quantity:
                errors.append(
                    "Unrecognized quantity Key Parameter value '%s' at 'Summ'!%s%s"
                    % (monitor_quantity, quantity_column, row)
                )
                monitor_quantity = False
            if monitor_price in true_values:
                monitor_price = True
            elif monitor_price:
                errors.append(
                    "Unrecognized price Key Parameter value %s at 'Summ'!%s%s" % (monitor_price, price_column, row)
                )
                monitor_price = False

            # Find the Livelihood Strategies
            if monitor_quantity or monitor_price:
                if not label:
                    errors.append("No LivelihoodStrategy label for Key Parameter at 'Summ'!%s%s" % ("A", row))
                    continue
                livelihood_strategies = livelihood_strategy_map.get(label)

                if not livelihood_strategies:
                    errors.append(
                        "No matching LivelihoodStrategy for Key Parameter '%s' at 'Summ'!%s%s" % (label, "A", row)
                    )
                    continue

                for livelihood_strategy in livelihood_strategies:
                    natural_key = tuple(livelihood_strategy["natural_key"])
                    if natural_key not in key_parameters_by_natural_key:
                        key_parameters_by_natural_key[natural_key] = {
                            "livelihood_strategy": livelihood_strategy["natural_key"],
                            "monitor_quantity": False,
                            "monitor_price": False,
                            "natural_key": livelihood_strategy["natural_key"],
                            "bss_sheet": "Summ",
                            "bss_row": row,
                            "source_label": label,
                        }
                    key_parameters_by_natural_key[natural_key]["monitor_quantity"] = (
                        key_parameters_by_natural_key[natural_key]["monitor_quantity"] or monitor_quantity
                    )
                    key_parameters_by_natural_key[natural_key]["monitor_price"] = (
                        key_parameters_by_natural_key[natural_key]["monitor_price"] or monitor_price
                    )

    key_parameters = list(key_parameters_by_natural_key.values())

    metadata = {
        "num_key_parameters": len(key_parameters),
        "preview": MetadataValue.md(f"```json\n{json.dumps(key_parameters, indent=4, ensure_ascii=False)}\n```"),
    }
    if errors:
        if config.strict:
            raise RuntimeError("Unable to match key parameters in BSS %s:\n%s" % (partition_key, "\n".join(errors)))
        context.log.warning("Unable to match key parameters in BSS %s:\n%s" % (partition_key, "\n".join(errors)))
        metadata["errors"] = MetadataValue.md(f'```text\n{"\n".join(errors)}\n```')

    return Output({"KeyParameter": key_parameters}, metadata=metadata)


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def key_parameter_valid_instances(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    key_parameter_instances: dict,
    livelihood_activity_valid_instances: dict,
    other_cash_income_valid_instances: dict,
    wild_foods_valid_instances: dict,
) -> Output[dict]:
    """
    Valid KeyParameter instances from a BSS.
    """
    if not key_parameter_instances.get("KeyParameter"):
        return Output({}, metadata={"message": "No key parameter instances to validate"})

    partition_key = context.asset_partition_key_for_output()
    instances_to_validate = {
        "LivelihoodStrategy": (
            livelihood_activity_valid_instances.get("LivelihoodStrategy", [])
            + other_cash_income_valid_instances.get("LivelihoodStrategy", [])
            + wild_foods_valid_instances.get("LivelihoodStrategy", [])
        ),
        **key_parameter_instances,
    }
    return validate_instances(context, config, instances_to_validate, partition_key)
