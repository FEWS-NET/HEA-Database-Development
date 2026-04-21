"""
Dagster assets related to Livelihood Product Category, read from the 'Exp factors' worksheet in a BSS starting around row 64.

Column A contains the label that matches the start of the relevant LivelihoodStrategy.
Column D contains the `percentage_allocation_to_basket`.
Column G contains the `basket` code.

An example of relevant rows from the worksheet:
|     | A                                                                      | B                    | C                     | D            | E            | F      | G                    |
|----:|:-----------------------------------------------------------------------|:---------------------|:----------------------|:-------------|:-------------|:-------|:---------------------|
|   1 |                                                                        |                      |                       |              |              |        |                      |
|   2 | EXPANDABILITY PARAMETERS                                               |                      |                       |              |              |        |                      |
|   3 |                                                                        |                      | MAXIMIUM (or MINIMUM) |              |              |        |                      |
|  64 | Expenditure                                                            |                      |                       |              |              |        |                      |
|  65 | Food Purchase                                                          |                      |                       |              |              |        | code for basket      |
|  66 | Maize: name of meas.                                                   | poor adj.for HH size |                       | 1            |              |        | 1                    |
|  67 | Millet: name of meas.                                                  | poor adj.for HH size |                       | 1            |              |        | 2                    |
|  68 | Sorghum: name of meas.                                                 | poor adj.for HH size |                       | 1            |              |        | 2                    |
|  69 | Rice: name of meas.                                                    | poor adj.for HH size |                       | 0.25         |              |        | 4                    |
|  70 | Cowpeas: name of meas.                                                 | poor adj.for HH size |                       | 0.75         |              |        | 2                    |
|  71 | Sweet potatoes: name of meas.                                          | poor adj.for HH size |                       | 0            |              |        | 4                    |
|  72 | Sugar: quantity (kg)                                                   | poor adj.for HH size |                       | 0.5          |              |        | 4                    |
|  73 | Meat : quantity (kg)                                                   | poor adj.for HH size |                       | 0            |              |        | 4                    |
|  74 | Veg oil + palm oil: quantity (kg)                                      | poor adj.for HH size |                       | 0.75         |              |        | 2                    |
|  75 | Wheat flour: quantity (kg)                                             | poor adj.for HH size |                       | 0            |              |        | 4                    |
|  76 | Other: Milk                                                            | poor adj.for HH size |                       | 0            |              |        | 4                    |
|  77 | Other purchase_2-5                                                     | poor adj.for HH size |                       | 0.5          |              |        | 2                    |
|  78 | Other items                                                            |                      |                       |              |              |        | code for basket      |
|  79 | Tea                                                                    | poor adj.for HH size |                       | 0            |              |        | 4                    |
|  80 | Salt                                                                   | poor adj.for HH size |                       | 1            |              |        | 3                    |
|  81 | Soap (bar, powder)                                                     | poor adj.for HH size |                       | 0.5          |              |        | 3                    |
|  82 | Cooking fuel                                                           | poor adj.for HH size |                       | 0.75         |              |        | 3                    |
|  83 | Grinding                                                               | poor adj.for HH size |                       | 0.75         |              |        | 3                    |
|  84 | Lighting                                                               | poor adj.for HH size |                       | 0.5          |              |        | 3                    |
|  85 | Utensils/pots/jerricans/blankets                                       | poor adj.for HH size |                       | 0            |              |        | 4                    |
|  86 | Clothing                                                               | poor adj.for HH size |                       | 0.5          |              |        | 4                    |
|  87 | Transport                                                              | WG specific          | 1                     | 1            | 1            | 1      | 4                    |
|  88 |                                                                        | WG specific          | 0                     | 0            | 0            | 0      | 4                    |
|  89 |                                                                        | poor adj.for HH size |                       | 0.5          |              |        | 4                    |
|  90 | Other items (inc. transport)                                           | poor adj.for HH size |                       | 0.5          |              |        | 4                    |
|  91 | Water                                                                  |                      |                       |              |              |        |                      |
|  92 |                                                                        | WG specific          | 1                     | 1            | 1            | 1      | 3                    |
|  93 |                                                                        | WG specific          | 1                     | 1            | 1            | 1      | 4                    |
|  94 | Social services                                                        |                      |                       |              |              |        |                      |
|  95 | School                                                                 | WG specific          | 1                     | 1            | 1            | 1      | 4                    |
|  96 | Medicine                                                               | WG specific          | 1                     | 1            | 1            | 1      | 4                    |
|  97 | Inputs                                                                 |                      |                       |              |              |        |                      |
|  98 | Animal drugs                                                           | WG specific          | 1                     | 1            | 1            | 1      | 4                    |
|  99 | Salt for animals                                                       | WG specific          | 1                     | 1            | 1            | 1      | 4                    |
| 100 | Ploughing                                                              | WG specific          | 1                     | 1            | 1            | 1      | 4                    |
| 101 | Seeds/tools                                                            | WG specific          | 1                     | 1            | 1            | 1      | 4                    |
| 102 | Fertilizer/pesticides                                                  | WG specific          | 1                     | 1            | 1            | 1      | 4                    |
| 103 | Irrigation costs                                                       | WG specific          | 1                     | 1            | 1            | 1      | 4                    |
| 104 | Labour                                                                 | WG specific          | 1                     | 1            | 1            | 1      | 4                    |
| 105 | Purchase of new animals                                                | WG specific          | 0                     | 0            | 0            | 0      | 4                    |
| 106 | Other essential livestock inputs                                       | WG specific          | 1                     | 1            | 1            | 1      | 4                    |
| 107 |                                                                        | WG specific          | 1                     | 1            | 1            | 1      | 4                    |
| 108 |                                                                        |                      |                       |              |              |        |                      |
"""  # NOQA: E501

import json
import os

import django
import pandas as pd
from dagster import AssetExecutionContext, MetadataValue, Output, asset

from ..configs import BSSMetadataConfig
from ..partitions import bss_instances_partitions_def
from .base import (
    get_bss_dataframe,
)
from .fixtures import get_fixture_from_instances, import_fixture, validate_instances

# set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hea.settings.production")

# Configure Django with our custom settings before importing any Django classes
django.setup()

from metadata.lookups import WealthGroupCategoryLookup  # NOQA: E402

HEADER_ROWS = [4]
WORKSHEET_NAME = "Exp factors"


@asset(partitions_def=bss_instances_partitions_def)
def livelihood_product_category_dataframe(config: BSSMetadataConfig, corrected_files) -> Output[pd.DataFrame]:
    """
    DataFrame of Livelihood Product Categories from a BSS
    """
    return get_bss_dataframe(
        config,
        corrected_files,
        WORKSHEET_NAME,
        start_strings=[
            "Food Purchase",
            "Staple purchase",
            "Achat aliments",
        ],
        header_rows=HEADER_ROWS,
        # Exp factors doesn't have summary columns, because it only contains Baseline-level reconciled data.
        end_col="G",
        num_summary_cols=0,
        fill_blank_rows=False,
    )


@asset(partitions_def=bss_instances_partitions_def)
def other_food_purchase_summ_dataframe(config: BSSMetadataConfig, corrected_files) -> Output[pd.DataFrame]:
    """
    DataFrame of Other Food Purchase details from the Summ worksheet in a BSS.

    Some BSSs summarize some of the Food Purchases into a single line in 'Exp factors'.
    The Other Food Purchase details section in the Summ contains the details of
    the Livelihood Activities that are being summarized.
    """
    try:
        return get_bss_dataframe(
            config,
            corrected_files,
            "Summ",
            start_strings=[
                "OTHER FOOD PURCHASE:",
            ],
            header_rows=[],
            end_col="Q",
            num_summary_cols=0,
            fill_blank_rows=False,
        )
    except ValueError:
        # There is no Other Food Purchase section in the Summ worksheet
        return Output(
            pd.DataFrame(),
            metadata={
                "row_count": 0,
                "message": "No 'Other Food Purchase' section found in the 'Summ' worksheet in this BSS",
            },
        )


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def livelihood_product_category_instances(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    livelihood_product_category_dataframe: pd.DataFrame,
    other_food_purchase_summ_dataframe: pd.DataFrame,
    livelihood_activity_instances: dict,
) -> Output[dict]:
    """
    LivelihoodProductCategory instances extracted from the BSS.
    """
    if livelihood_product_category_dataframe.empty:
        return Output({}, metadata={"message": "No 'Exp factors' worksheet found in this BSS"})

    # Find the metadata for this BSS
    partition_key = context.asset_partition_key_for_output()

    # Set the column headers from the first row so that we capture the Wealth Group Categories
    df = livelihood_product_category_dataframe
    wealthgroupcategorylookup = WealthGroupCategoryLookup()
    wealth_group_categories = []
    for x in df.iloc[0, 2:6]:
        wealth_group_category = wealthgroupcategorylookup.get(x)
        if not wealth_group_category:
            raise ValueError(f"Unrecognized wealth_group_category '{x}'")
        wealth_group_categories.append(wealth_group_category)
    df.columns = ["label", "description"] + wealth_group_categories + ["basket"]

    # Drop the old header row and the start row used to identify the range
    df = df.drop(df.index[0:2])

    # Save the index (which is the original row number) as a column, so that
    # we can alter the dataframe without losing the row number when troubleshooting.
    df = df.reset_index(names="row")

    # Replace old text basket names with the expected codes
    df["basket"] = df["basket"].replace(
        {
            "ess": 1,
            "mns": 2,
        },
    )

    # We only need to create Livelihood Product Category instances for rows that have a label and basket
    df["label"] = df["label"].where(df["label"] != "", pd.NA)
    df["basket"] = pd.to_numeric(df["basket"], errors="coerce")
    df = df.dropna(subset=["label", "basket"])

    # The values in the wealth group category columns are the percentage_allocation_to_basket and need to be numeric
    for wealth_group_category in wealth_group_categories:
        df[wealth_group_category] = pd.to_numeric(df[wealth_group_category], errors="coerce")

    # Build a map from the natural key to the corresponding activity_label
    # The label in 'Exp factors' matches the one from the row in the Data worksheet that starts the LivelihoodStrategy.
    livelihood_strategy_map = {
        tuple(livelihood_strategy["natural_key"]): livelihood_strategy["activity_label"]
        for livelihood_strategy in livelihood_activity_instances["LivelihoodStrategy"]
    }

    # Build a map from the label and the wealth_group_category to the corresponding BaselineLivelihoodActivity
    livelihood_activity_map = {}
    for livelihood_activity in livelihood_activity_instances["LivelihoodActivity"]:
        # We only want Baseline Livelihood Activities for the 'Exp factors' wealth groups
        if (
            livelihood_activity["wealth_group"][3] == ""  # Full name is empty, so a Baseline Livelihood Activity
            and livelihood_activity["wealth_group"][2] in wealth_group_categories
        ):
            livelihood_activity_map[
                (
                    livelihood_strategy_map[tuple(livelihood_activity["livelihood_strategy"])],
                    livelihood_activity["wealth_group"][2],
                )
            ] = livelihood_activity["natural_key"]

    # The data in `Exp factors` is pulled from the 'Summ' worksheet, and there is a special label `Other purchase_2-5`
    # which references a row in the Summ worksheet, typically row 531, which is calculated as the sum of multiple
    # LivelihoodActivities from the Data worksheet.  For example Summ!C531 has formula `=SUM(C1031,C1038,C1045,C1052,C1059)`
    # This section of Summ, headed OTHER FOOD PURCHASE copies the LivelihoodActivity values from Data for the rows to
    # be summarized.  We need to expand `Other purchase_2-5` to reference the actual LivelihoodStrategy labels.
    for label in ["Other purchase_2-5", "autres éléments non essentiels"]:
        if label in df["label"].tolist():
            if other_food_purchase_summ_dataframe.empty:
                raise ValueError(
                    f"'Exp factors' worksheet contains label '{label}' "
                    "but no 'OTHER FOOD PURCHASE:' section found in the 'Summ' worksheet"
                )
            other_purchase_basket_df = df[df["label"] == label].drop(columns=["label"])
            other_purchase_activity_df = other_food_purchase_summ_dataframe[
                other_food_purchase_summ_dataframe["A"].isin(livelihood_strategy_map.values())
            ]["A"].rename("label")
            df = pd.concat(
                [df, other_purchase_basket_df.merge(other_purchase_activity_df, how="cross")], ignore_index=True
            )
            df = df[df["label"] != label]

    livelihood_product_categories = []
    errors = []
    for i in df.index:
        try:
            label = df.loc[i, "label"]

            # Check that we found a Livelihood Strategy for this label
            # We don't want to iterate over the Wealth Groups if there are no Strategies
            if label not in livelihood_strategy_map.values():
                # There is no matching LivelihoodStrategy:
                #   * There is no reconciled expenditure, and therefore no LivelihoodStrategy,
                #     but the percentage_allocation_to_basket is set.
                #   * Old BSS, without a Graphs worksheet, don't have a direct link between
                #     the rows in the 'Exp factors' worksheet and the Livelihood Activities
                #     in the Data worksheet (via the Summ worksheet), so it isn't possible
                #     to match the Livelihood Activity instances to the basket.
                errors.append(f"No matching Livelihood Strategy for label '{label}' from row {df.loc[i, 'row']}")

            else:
                # Iterate over the Wealth Groups
                for wealth_group_category in wealth_group_categories:

                    # We only need to create a Baseline Product Category if there is a percentage_allocation_to_basket
                    if pd.notna(df.loc[i, wealth_group_category]):

                        try:
                            livelihood_activity = livelihood_activity_map[(label, wealth_group_category)]
                            livelihood_product_category = {
                                "baseline_livelihood_activity": livelihood_activity,
                                "basket": int(df.loc[i, "basket"]),
                                "percentage_allocation_to_basket": df.loc[i, wealth_group_category],
                                # Add the natural key to support lookups and foreign key validation
                                "natural_key": (
                                    livelihood_activity[:4]  # code, end_date, wealth_group_category, strategy_type
                                    + [int(df.loc[i, "basket"])]
                                    + livelihood_activity[4:7]  # product, season, additional_identifier
                                ),
                            }
                            livelihood_product_categories.append(livelihood_product_category)

                        except KeyError:
                            # There is no matching LivelihoodActivity:
                            #   * There is reconciled expenditure for some but not all Wealth Groups. There
                            #     will be a LivelihoodStrategy but no LivelihoodActivity for the rows without
                            #     reconciled expenditure.
                            errors.append(
                                f"No matching Livelihood Activity for label '{label}' for Wealth Group '{wealth_group_category}' from row {df.loc[i, 'row']}"
                            )

        except Exception as e:
            raise RuntimeError(
                "Unhandled error in BSS %s processing row '%s'!%s with label '%s'"
                % (partition_key, WORKSHEET_NAME, df.loc[i, "row"], label)
            ) from e

    result = {
        "LivelihoodProductCategory": livelihood_product_categories,
    }
    metadata = {
        "num_product_categories": len(livelihood_product_categories),
        "preview": MetadataValue.md(f"```json\n{json.dumps(result, indent=4, ensure_ascii=False)}\n```"),
    }
    if errors:
        context.log.warning(
            "Ignoring missing or inconsistent metadata in BSS %s:\n%s" % (partition_key, "\n".join(errors))
        )
        metadata["errors"] = MetadataValue.md(f'```text\n{"\n".join(errors)}\n```')
        # Move the preview metadata item to the end of the dict
        metadata["preview"] = metadata.pop("preview")
    return Output(
        result,
        metadata=metadata,
    )


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def livelihood_product_category_valid_instances(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    livelihood_product_category_instances: dict,
    wealth_characteristic_instances: dict,
    livelihood_activity_instances: dict,
) -> Output[dict]:
    """
    Valid LivelihoodProductCategory instances from a BSS, ready to be loaded via a Django fixture.
    """
    partition_key = context.asset_partition_key_for_output()
    # Livelihood Product Categories depend on Baseline Livelihood Activities which depend on the Wealth Groups, making
    # sure that the WealthGroup is the first entry in the dict, so that the lookup keys have been created before
    # validate_instances processes the child model and needs them.
    if "LivelihoodProductCategory" in livelihood_product_category_instances:
        # We only need the livelihood activity, strategy and wealth group
        # instances that match the baseline livelihood activities
        required_activities = [
            x["baseline_livelihood_activity"]
            for x in livelihood_product_category_instances["LivelihoodProductCategory"]
        ]
        required_strategies = [
            x["livelihood_strategy"]
            for x in livelihood_activity_instances["LivelihoodActivity"]
            if x["natural_key"] in required_activities
        ]
        required_wealth_groups = [
            x["wealth_group"]
            for x in livelihood_activity_instances["LivelihoodActivity"]
            if x["natural_key"] in required_activities
        ]
        livelihood_product_category_instances = {
            "WealthGroup": [
                x for x in wealth_characteristic_instances["WealthGroup"] if x["natural_key"] in required_wealth_groups
            ],
            "LivelihoodStrategy": [
                x
                for x in livelihood_activity_instances["LivelihoodStrategy"]
                if x["natural_key"] in required_strategies
            ],
            "LivelihoodActivity": [
                x
                for x in livelihood_activity_instances["LivelihoodActivity"]
                if x["natural_key"] in required_activities
            ],
            "LivelihoodProductCategory": livelihood_product_category_instances["LivelihoodProductCategory"],
        }
    return validate_instances(context, config, livelihood_product_category_instances, partition_key)


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def livelihood_product_category_fixture(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    livelihood_product_category_valid_instances: dict,
) -> Output[list[dict]]:
    """
    Django fixture for the Livelihood Product Categories from a BSS.
    """
    return get_fixture_from_instances(livelihood_product_category_valid_instances)


@asset(partitions_def=bss_instances_partitions_def)
def imported_livelihood_product_categories(
    context: AssetExecutionContext,
    livelihood_product_category_fixture,
) -> Output[None]:
    """
    Imported Django fixtures for a BSS, added to the Django database.
    """
    return import_fixture(livelihood_product_category_fixture)
