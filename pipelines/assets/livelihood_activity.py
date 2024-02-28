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

import json
import os
import warnings
from typing import Any

import django
import pandas as pd
from dagster import AssetExecutionContext, MetadataValue, Output, asset

from ..utils import class_from_name
from .base import (
    BSSMetadataConfig,
    bss_files_partitions_def,
    bss_instances_partitions_def,
    get_all_bss_labels_dataframe,
    get_bss_dataframe,
    get_bss_label_dataframe,
    get_summary_bss_label_dataframe,
)

# set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hea.settings.production")

# Configure Django with our custom settings before importing any Django classes
django.setup()

from baseline.models import MilkProduction  # NOQA: E402
from metadata.lookups import SeasonNameLookup, WealthGroupCategoryLookup  # NOQA: E402
from metadata.models import ActivityLabel, LivelihoodActivityScenario  # NOQA: E402

# Indexes of header rows in the Data3 dataframe (wealth_group_category, district, village, household size)
# The household size is included in the header rows because it is used to calculate the kcals_consumed
HEADER_ROWS = [3, 4, 5, 40]


@asset(partitions_def=bss_files_partitions_def)
def livelihood_activity_dataframe(config: BSSMetadataConfig, corrected_files) -> Output[pd.DataFrame]:
    """
    DataFrame of Livelihood Activities from a BSS
    """
    return get_bss_dataframe(
        config,
        corrected_files,
        "Data",
        start_strings=["LIVESTOCK PRODUCTION:", "production animale:"],
        end_strings=["income minus expenditure", "Revenus moins dépenses", "Revenu moins dépense"],
        header_rows=HEADER_ROWS,
    )


@asset(partitions_def=bss_files_partitions_def)
def livelihood_activity_label_dataframe(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    livelihood_activity_dataframe,
) -> Output[pd.DataFrame]:
    """
    Dataframe of Livelihood Activity Label References
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
    return get_summary_bss_label_dataframe(config, all_livelihood_activity_labels_dataframe)


def get_instances_from_dataframe(
    df: pd.DataFrame, metadata: dict[str:Any], activity_type: str, num_header_rows: int, partition_key: str
) -> Output[dict]:
    """
    LivelhoodStrategy and LivelihoodActivity instances extracted from the BSS from the Data, Data2 or Data3 worksheets.
    """
    # Save the natural key to the livelihood zone baseline for later use.
    livelihoodzonebaseline = [metadata["code"], metadata["reference_year_end_date"]]

    # Prepare the lookups, so they cache the individual results
    seasonnamelookup = SeasonNameLookup()
    wealthgroupcategorylookup = WealthGroupCategoryLookup()
    label_map = {
        instance.pop("activity_label").lower(): instance
        for instance in ActivityLabel.objects.filter(activity_type=activity_type).values(
            "activity_label",
            "strategy_type",
            "is_start",
            "product_id",
            "unit_of_measure_id",
            "season",
            "additional_identifier",
            "attribute",
        )
    }

    # The LivelihoodActivity is the intersection of a LivelihoodStrategy and a WealthGroup,
    # so build a list of the natural keys for the WealthGroup for each column, based on the
    # Wealth Group Category from Row 3 and the Community Full Name from Rows 4 and 5.
    # In the Summary columns, typically the Wealth Group Category is in Row 4 rather than Row 3.
    wealth_groups = []
    for column in df.loc[3:5, "B":]:
        wealth_groups.append(
            livelihoodzonebaseline
            + [
                wealthgroupcategorylookup.get(df.loc[3, column]) or wealthgroupcategorylookup.get(df.loc[4, column]),
                (
                    ""
                    if wealthgroupcategorylookup.get(df.loc[4, column])
                    else ", ".join([df.loc[5, column], df.loc[4, column]])
                ),
            ]
        )

    # Check that we recognize all of the activity labels
    allow_unrecognized_labels = True
    unrecognized_labels = (
        df.iloc[num_header_rows:][
            ~df.iloc[num_header_rows:]["A"].str.strip().str.lower().isin(label_map)
            & (df.iloc[num_header_rows:]["A"].str.strip() != "")
        ]
        .groupby("A")
        .apply(lambda x: ", ".join(x.index.astype(str)))
    )
    if unrecognized_labels.empty:
        unrecognized_labels = pd.DataFrame(columns=["label", "rows"])
    else:
        unrecognized_labels = unrecognized_labels.reset_index()
        unrecognized_labels.columns = ["label", "rows"]
        message = "Unrecognized activity labels:\n\n" + unrecognized_labels.to_markdown(index=False)
        if allow_unrecognized_labels:
            warnings.warn(message)
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
            label = df.loc[row, "A"].strip().lower()
            if not label:
                # Ignore blank rows
                continue
            # Get the attributes, taking a copy so that we can pop() some attributes without altering the original
            attributes = label_map.get(label, {}).copy()
            if not any(attributes.values()):
                # Ignore rows that don't contain any relevant data (or which aren't in the label_map)
                continue
            # Headings like CROP PRODUCTION: set the strategy type for subsequent rows.
            # Some attributes imply specific strategy types, such as MilkProduction, MeatProduction or LivestockSales
            if attributes["strategy_type"]:
                strategy_type = attributes.pop("strategy_type")
                # Get the valid fields names so we can determine if the attribute is stored in LivelihoodActivity.extra
                model = class_from_name(f"baseline.models.{strategy_type}")
                activity_field_names = [field.name for field in model._meta.concrete_fields]
                # Also include values that point directly to the primary key of related objects
                activity_field_names += [
                    field.get_attname()
                    for field in model._meta.concrete_fields
                    if field.get_attname() not in activity_field_names
                ]

            if not strategy_type:
                raise ValueError("Found attributes %s from row %s without a strategy_type set" % (attributes, row))

            if attributes["is_start"]:
                # We are starting a new livelihood activity, so append the previous livelihood strategy
                # to the list, provided that it has at least one Livelihood Activity where there is some income,
                # expediture or consumption. This excludes empty activities that only contain attributes for,
                # for example, 'type_of_milk_sold_or_other_uses'
                non_empty_livelihood_activities = [
                    livelihood_activity
                    for livelihood_activity in livelihood_activities_for_strategy
                    if any(
                        (
                            field in livelihood_activity
                            and (livelihood_activity[field] or livelihood_activity[field] == 0)
                        )
                        for field in ["income", "expenditure", "kcals_consumed", "percentage_kcals"]
                    )
                ]

                if non_empty_livelihood_activities:
                    # Finalize the livelihood strategy and activities, making various adjustments for quirks in the BSS

                    # Copy the product_id for MilkProduction and ButterProduction the previous livelihood strategy if
                    # necessary.
                    if livelihood_strategy["strategy_type"] in ["MilkProduction", "ButterProduction"] and (
                        "product_id" not in livelihood_strategy or not livelihood_strategy["product_id"]
                    ):
                        if (
                            livelihood_strategy["season"] == "Season 2"
                            and previous_livelihood_strategy
                            and previous_livelihood_strategy["product_id"]
                        ):
                            livelihood_strategy["product_id"] = previous_livelihood_strategy["product_id"]
                        else:
                            raise ValueError(
                                "Cannot determine product_id for %s %s on row %s"
                                % (livelihood_strategy["strategy_type"], livelihood_strategy["activity_label"], row)
                            )

                    # Copy the milking_animals for camels and cattle from the previous livelihood activities if
                    # necessary.
                    if (
                        livelihood_strategy["strategy_type"] == "MilkProduction"
                        and livelihood_strategy["season"] == "Season 2"
                        and previous_livelihood_activities_for_strategy
                        and "milking_animals" in previous_livelihood_strategy["attribute_rows"]
                        and "milking_animals" not in livelihood_strategy["attribute_rows"]
                    ):
                        for i in range(len(previous_livelihood_activities_for_strategy)):
                            if "milking_animals" in previous_livelihood_activities_for_strategy[i]:
                                livelihood_activities_for_strategy[i]["milking_animals"] = (
                                    previous_livelihood_activities_for_strategy[i]["milking_animals"]
                                )

                    # Calculated kcals_consumed if the livelihood activity only contains the percentage_kcals.
                    # This is typical for ButterProduction. Derive it by multiplying percentage_kcals by:
                    #   2100 (kcals per person per day) * 365 (days per year) * average_household_size (from Row 40)
                    if (
                        "percentage_kcals" in livelihood_strategy["attribute_rows"]
                        and "kcals_consumed" not in livelihood_strategy["attribute_rows"]
                    ):
                        for i, livelihood_activity in enumerate(livelihood_activities_for_strategy):
                            # The household size will always be the 4th header row in the dataframe, even though the
                            # original row number (which is the index) will be different between the Data and Data3
                            # worksheets
                            household_size = df.iloc[3, i + 1]
                            livelihood_activity["kcals_consumed"] = (
                                livelihood_activity["percentage_kcals"] * 2100 * 365 * household_size
                                if livelihood_activity["percentage_kcals"] and household_size
                                else ""
                            )

                    # Normalize the `type_of_milk_sold_or_other_uses`, e.g. from `type of milk sold/other use (skim=0, whole=1)`  # NOQA: E501
                    if "type_of_milk_sold_or_other_uses" in livelihood_strategy["attribute_rows"]:
                        for livelihood_activity in livelihood_activities_for_strategy:
                            livelihood_activity["type_of_milk_sold_or_other_uses"] = (
                                MilkProduction.MilkType.WHOLE
                                if livelihood_activity["type_of_milk_sold_or_other_uses"]
                                else MilkProduction.MilkType.SKIM
                            )
                    # Lookup the season name from the alias used in the BSS to create the natural key
                    livelihood_strategy["season"] = (
                        [seasonnamelookup.get(livelihood_strategy["season"], country_id=metadata["country_id"])]
                        if livelihood_strategy["season"]
                        else None
                    )

                    # Add the natural keys for the livelihood strategy to the activities.
                    # This is the last step so that we are sure that the attributes in the livelihood_strategy are
                    # final. For example, the Season 1, etc. alias has been replaced with the real natural key.
                    for i, livelihood_activity in enumerate(livelihood_activities_for_strategy):
                        livelihood_activity["livelihood_strategy"] = livelihoodzonebaseline + [
                            livelihood_strategy["strategy_type"],
                            livelihood_strategy["season"][0] if livelihood_strategy["season"] else "",
                            livelihood_strategy["product_id"] if livelihood_strategy["product_id"] else "",
                            livelihood_strategy["additional_identifier"],
                        ]

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

                # Initialize the new livelihood strategy
                livelihood_strategy = {
                    "livelihood_zone_baseline": livelihoodzonebaseline,
                    "strategy_type": strategy_type,
                    "season": attributes.get("season", None),
                    "product_id": attributes.get("product_id", None),
                    "unit_of_measure_id": attributes.get("unit_of_measure_id", None),
                    "currency_id": metadata["currency_id"],
                    "additional_identifier": attributes.get("additional_identifier", None),
                    # Save the row, label and attribute/row map, to aid trouble-shooting
                    "row": row,
                    "activity_label": label,
                    "attribute_rows": {},
                }

                # Initialize the list of livelihood activities for the new livelihood strategy
                livelihood_activities_for_strategy = [
                    {
                        "livelihood_zone_baseline": livelihoodzonebaseline,
                        "strategy_type": livelihood_strategy["strategy_type"],
                        "scenario": LivelihoodActivityScenario.BASELINE,
                        "wealth_group": wealth_groups[i],
                        # Include the column and row to aid trouble-shooting
                        "bss_sheet": "Data",
                        "bss_column": df.columns[i + 1],
                        "bss_row": row,
                        "activity_label": label,
                    }
                    for i in range(len(df.loc[row, "B":]))
                ]

            else:

                # We are not starting a new Livelihood Strategy, but there may be
                # additional attributes that need to be added to the current one.
                if not livelihood_strategy:
                    raise ValueError(
                        "Found additional attributes %s from row %s without an existing LivelihoodStrategy"
                        % (attributes, row)
                    )

                # Only update expected keys, and only if we found a value for that attribute.
                for key, value in attributes.items():
                    if key in livelihood_strategy and value:
                        if not livelihood_strategy[key]:
                            livelihood_strategy[key] = value

                        # If this attribute is already set for the `livelihood_strategy`, then the value should be the
                        # same. For example, we may detect the unit of measure multiple times for a single
                        # `livelihood_strateg`:
                        #     Maize rainfed: kg produced
                        #     sold/exchanged (kg)
                        #     other use (kg)
                        # But if we receive different values for the same attribute, it probably indicates a metadata
                        # inconsistency for that attribute (or possibly a failure to recognize the start of the next
                        # Livelihood Strategy
                        elif livelihood_strategy[key] != value:
                            raise ValueError(
                                "Found duplicate value %s from row %s for existing attribute %s with value %s"
                                % (value, row, key, livelihood_strategy[key])
                            )

            # When we get the values for the LivelihoodActivity records, we just want the actual attribute
            # that the values in the row are for
            attribute = attributes["attribute"]
            # Update the LivelihoodActivity records
            if any(value for value in df.loc[row, "B":].astype(str).str.strip()):
                # Make sure we have an attribute!
                if not attribute:
                    raise ValueError(
                        "Found values in row %s for label '%s' without an identified attribute:\n%s"
                        % (row, label, df.loc[row, "B":].replace("", pd.NA).dropna().transpose().to_markdown())
                    )
                # If the activity label that marks the start of a Livelihood Strategy is not in the
                # `ActivityLabel.objects.all()`, and hence not in the  `activity_label_map`, then repeated
                # labels like `kcals (%)` will appear to be duplicate attributes for the previous
                # `1ivelihood_strategy`. Therefore, if we have `allow_unrecognized_labels` we need to ignore
                # the duplicates, but if we don't, we should raise an error.
                elif attribute in livelihood_strategy["attribute_rows"]:
                    if allow_unrecognized_labels:
                        # Skip to the next row
                        continue
                    else:
                        raise ValueError(
                            "Found duplicate value %s from row %s for existing attribute %s with value %s"
                            % (value, row, key, livelihood_strategy[key])
                        )

                # Add the attribute to the LivelihoodStrategy.attribute_rows
                livelihood_strategy["attribute_rows"][attribute] = row
                for i, value in enumerate(df.loc[row, "B":]):
                    # Some attributes are stored in LivelihoodActivity.extra rather than individual fields.
                    if attribute not in activity_field_names:
                        if "extra" not in livelihood_activities_for_strategy[i]:
                            livelihood_activities_for_strategy[i]["extra"] = {}
                        livelihood_activities_for_strategy[i]["extra"][attribute] = value
                    else:
                        livelihood_activities_for_strategy[i][attribute] = value

        except Exception as e:
            if column:
                raise RuntimeError(
                    "Unhandled error in %s processing cell 'Data'!%s%s for label '%s'"
                    % (partition_key, column, row, label)
                ) from e
            else:
                raise RuntimeError(
                    "Unhandled error in %s processing row 'Data'!%s with label '%s'" % (partition_key, row, label)
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
        "preview": MetadataValue.md(f"```json\n{json.dumps(result, indent=4)}\n```"),
    }
    if not unrecognized_labels.empty:
        metadata["unrecognized_labels"] = MetadataValue.md(unrecognized_labels.to_markdown(index=False))

    return Output(
        result,
        metadata=metadata,
    )


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def livelihood_activity_instances(
    context: AssetExecutionContext,
    completed_bss_metadata,
    livelihood_activity_dataframe,
) -> Output[dict]:
    """
    LivelhoodStrategy and LivelihoodActivity instances extracted from the BSS.
    """
    # Find the metadata for this BSS
    partition_key = context.asset_partition_key_for_output()
    try:
        metadata = completed_bss_metadata[completed_bss_metadata["partition_key"] == partition_key].iloc[0]
    except IndexError:
        raise ValueError("No complete entry in the BSS Metadata worksheet for %s" % partition_key)
    output = get_instances_from_dataframe(
        livelihood_activity_dataframe,
        metadata,
        ActivityLabel.LivelihoodActivityType.LIVELIHOOD_ACTIVITY,
        len(HEADER_ROWS),
        partition_key,
    )
    return output
