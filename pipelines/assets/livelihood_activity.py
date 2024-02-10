import json
import os
import warnings

import django
import pandas as pd
from dagster import (
    AssetExecutionContext,
    DagsterEventType,
    EventRecordsFilter,
    MetadataValue,
    Output,
    asset,
)
from openpyxl.utils import get_column_letter

from ..utils import get_index
from .baseline import BSSMetadataConfig, bss_files_partitions_def

# set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hea.settings.production")

# Configure Django with our custom settings before importing any Django classes
django.setup()

from metadata.lookups import SeasonNameLookup, WealthGroupCategoryLookup  # NOQA: E402
from metadata.models import ActivityLabel, LivelihoodActivityScenario  # NOQA: E402


@asset(partitions_def=bss_files_partitions_def)
def livelihood_activity_dataframe(config: BSSMetadataConfig, corrected_files) -> Output[pd.DataFrame]:
    """
    DataFrame of Livelihood Activities from a BSS

    Read from the 'Data' worksheet in the BSS.

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
    df = pd.read_excel(corrected_files, "Data", header=None)
    # Use a 1-based index to match the Excel Row Number
    df.index += 1
    # Set the column names to match Excel
    df.columns = [get_column_letter(col + 1) for col in df.columns]

    # Find the last column before the summary column, which is in row 2
    end_col = get_index(["Summary", "SYNTHÈSE", "RESUME"], df.loc[2], offset=-1)

    # There will also be one summary column for each wealth category, which are in row 3
    num_wealth_categories = df.loc[3, "B":end_col].dropna().nunique()
    end_col = df.columns[df.columns.get_loc(end_col) + num_wealth_categories]

    # Find the row index of the start of the Livelihood Activities
    start_row = get_index(["LIVESTOCK PRODUCTION:", "production animale:"], df.loc[:, "A"])

    # Find the row index of the end of the Livelihood Activities
    end_row = get_index(
        ["income minus expenditure", "Revenus moins dépenses", "Revenu moins dépense"],
        df.loc[start_row:, "A"],
        offset=-1,
    )

    # Find the language based on the value in cell A3
    langs = {
        "wealth group": "en",
        "group de richesse": "fr",
        "groupe de richesse": "fr",
        "groupe socio-economique": "fr",
    }
    lang = langs[df.loc[3, "A"].strip().lower()]

    # Filter to just the Wealth Group header rows (including household size from row 40) and the Livelihood Activities
    df = pd.concat([df.loc[3:5, :end_col], df.loc[[40], :end_col], df.loc[start_row:end_row, :end_col]])

    # Replace NaN with "" ready for Django
    df = df.fillna("")

    return Output(
        df,
        metadata={
            "worksheet": "Data",
            "lang": lang,
            "row_count": len(df),
            "datapoint_count": int(
                df.loc[:, "B":].apply(lambda row: sum((row != 0) & (row != "")), axis="columns").sum()
            ),
            "preview": MetadataValue.md(df.head(config.preview_rows).to_markdown()),
            "sample": MetadataValue.md(
                df[df.loc[:, "B":].apply(lambda row: sum((row != 0) & (row != "")), axis="columns") > 0]
                .sample(config.preview_rows)
                .to_markdown()
            ),
        },
    )


@asset(partitions_def=bss_files_partitions_def)
def activity_label_dataframe(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    livelihood_activity_dataframe,
) -> Output[pd.DataFrame]:
    """
    Activity Label References
    """
    df = livelihood_activity_dataframe.iloc[3:]  # Ignore the Wealth Group header rows
    instance = context.instance
    livelihood_activity_dataframe_materialization = instance.get_event_records(
        event_records_filter=EventRecordsFilter(
            event_type=DagsterEventType.ASSET_MATERIALIZATION,
            asset_key=context.asset_key_for_input("livelihood_activity_dataframe"),
            asset_partitions=[context.asset_partition_key_for_input("livelihood_activity_dataframe")],
        ),
        limit=1,
    )[0].asset_materialization

    label_df = pd.DataFrame()
    label_df["activity_label"] = df["A"]
    label_df["activity_label_lower"] = label_df["activity_label"].str.lower()
    label_df["filename"] = context.asset_partition_key_for_output()
    label_df["lang"] = livelihood_activity_dataframe_materialization.metadata["lang"].text
    label_df["worksheet"] = livelihood_activity_dataframe_materialization.metadata["worksheet"].text
    label_df["row_number"] = df.index
    label_df["datapoint_count"] = df.loc[:, "B":].apply(lambda row: sum((row != 0) & (row != "")), axis="columns")
    return Output(
        label_df,
        metadata={
            "num_labels": len(label_df),
            "num_datapoints": int(label_df["datapoint_count"].sum()),
            "preview": MetadataValue.md(label_df.head(config.preview_rows).to_markdown()),
            "sample": MetadataValue.md(
                label_df[label_df["datapoint_count"] > 0].sample(config.preview_rows).to_markdown()
            ),
        },
    )


@asset(io_manager_key="dataframe_csv_io_manager")
def all_activity_labels_dataframe(
    config: BSSMetadataConfig, activity_label_dataframe: dict[str, pd.DataFrame]
) -> Output[pd.DataFrame]:
    """
    Combined dataframe of the activity labels in use across all BSSs.
    """
    df = pd.concat(list(activity_label_dataframe.values()))
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


@asset(partitions_def=bss_files_partitions_def, io_manager_key="json_io_manager")
def livelihood_activity_fixture(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    completed_bss_metadata,
    livelihood_activity_dataframe,
) -> Output[dict]:
    """
    Django fixtures for the LivelihoodStrategy and LivelihoodActivity records in the BSS.
    """
    # Find the metadata for this BSS
    partition_key = context.asset_partition_key_for_output()
    try:
        metadata = completed_bss_metadata[completed_bss_metadata["bss_path"].str.startswith(partition_key)].iloc[0]
    except IndexError:
        raise ValueError("No complete entry in the BSS Metadata worksheet for %s" % partition_key)
    livelihoodzonebaseline = [metadata["code"], metadata["reference_year_end_date"]]

    df = livelihood_activity_dataframe
    header_rows = 4  # wealth group category, district, village, household size

    # Prepare the lookups, so they cache the individual results
    seasonnamelookup = SeasonNameLookup()
    wealthgroupcategorylookup = WealthGroupCategoryLookup()
    label_map = {
        instance.pop("activity_label").lower(): instance
        for instance in ActivityLabel.objects.values(
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
        df.iloc[header_rows:][
            ~df.iloc[header_rows:]["A"].str.lower().isin(label_map) & (df.iloc[header_rows:]["A"].str.strip() != "")
        ]
        .groupby("A")
        .apply(lambda x: ", ".join(x.index.astype(str)))
        .reset_index()
    )
    unrecognized_labels.columns = ["label", "rows"]
    if not unrecognized_labels.empty:
        message = "Unrecognized activity labels:\n\n" + unrecognized_labels.to_markdown()
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
    livelihood_strategy = None
    livelihood_strategies = []
    livelihood_activities = []
    livelihood_activities_for_strategy = []
    for row in df.iloc[header_rows:].index:  # Ignore the Wealth Group header rows
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
            if attributes.pop("is_start"):
                # We are starting a new livelihood activity, so append the previous livelihood strategy
                # to the list, provided that it has at least one Livelihood Activity where there is some income,
                # expediture or consumption. This excludes empty activities that only contain attributes for,
                # for example, 'type_of_milk_sold_or_other_uses'
                non_empty_livelihood_actities = [
                    livelihood_activity
                    for livelihood_activity in livelihood_activities_for_strategy
                    if any(
                        (field in livelihood_activity and livelihood_activity[field])
                        for field in ["income", "expenditure", "kcals_consumed", "percentage_kcals"]
                    )
                ]

                if non_empty_livelihood_actities:

                    # Lookup the season name from the alias used in the BSS to create the natural key
                    livelihood_strategy["season"] = (
                        [seasonnamelookup.get(livelihood_strategy["season"], country_id=metadata["country_id"])]
                        if livelihood_strategy["season"]
                        else None
                    )

                    # Add the natural keys for the livelihood_zone_baseline, livelihood strategy and the wealth group
                    # to the activities. Note that we have to enumerate livelihood_activities_for_strategy rather than
                    # non_empty_livelihood_actities so we set the correct wealth_group for each livelihood_activity.
                    for i, livelihood_activity in enumerate(livelihood_activities_for_strategy):
                        livelihood_activity["livelihood_strategy"] = livelihoodzonebaseline + [
                            livelihood_strategy["strategy_type"],
                            livelihood_strategy["season"][0] if livelihood_strategy["season"] else "",
                            livelihood_strategy["product_id"] if livelihood_strategy["product_id"] else "",
                            livelihood_strategy["additional_identifier"],
                        ]
                        livelihood_activity["livelihood_zone_baseline"] = livelihoodzonebaseline
                        livelihood_activity["strategy_type"] = livelihood_strategy["strategy_type"]
                        livelihood_activity["scenario"] = LivelihoodActivityScenario.BASELINE
                        livelihood_activity["wealth_group"] = wealth_groups[i]

                    # Append the stategies and activities to the lists of instances to create.
                    livelihood_strategies.append(livelihood_strategy)
                    livelihood_activities += non_empty_livelihood_actities

                # Now that we have saved the previous livelihood strategy and activities, we can start a new one.

                # There are cases where attributes get copied to the new livelihood strategy,
                # notably the product_id for MilkProduction and ButterProduction for camels and cattle.
                if (
                    strategy_type in ["MilkProduction", "ButterProduction"]
                    and livelihood_strategy
                    and livelihood_strategy["product_id"]
                    and not attributes["product_id"]
                    and attributes["season"] == "Season 2"
                ):
                    attributes["product_id"] = livelihood_strategy["product_id"]

                # Initialize the new livelihood strategy from the attributes
                livelihood_strategy = {
                    k: v
                    for k, v in attributes.items()
                    if k
                    in [
                        "product_id",
                        "unit_of_measure_id",
                        "season",
                        "additional_identifier",
                    ]
                }
                # Set the strategy type from the current group
                livelihood_strategy["strategy_type"] = strategy_type
                # Set the currency from metadata
                livelihood_strategy["currency_id"] = metadata["currency_id"]
                # Set the natural key to the livelihood zone baseline
                livelihood_strategy["livelihood_zone_baseline"] = livelihoodzonebaseline
                # Save the starting row for this Strategy, to aid trouble-shooting
                livelihood_strategy["row"] = row

                # There are cases where attributes get copied to the new livelihood activities,
                # notably milking_animals for camels and cattle.
                if (
                    strategy_type == "MilkProduction"
                    and livelihood_activities_for_strategy
                    and "milking_animals" in livelihood_activities_for_strategy[0]
                    and attributes["attribute"] != "milking_animals"
                ):
                    livelihood_activities_for_strategy = [
                        {
                            "milking_animals": livelihood_activity["milking_animals"],
                            "column": livelihood_activity["column"],
                            "row": row,
                        }
                        for livelihood_activity in livelihood_activities_for_strategy
                    ]
                else:
                    # Initialize the list of livelihood activities for the new livelihood strategy
                    livelihood_activities_for_strategy = []
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
                        elif livelihood_strategy[key] != value:
                            raise ValueError(
                                "Found duplicate value %s from row %s for existing attribute %s with value %s"
                                % (value, row, key, livelihood_strategy[key])
                            )

            # When we get the values for the LivelihoodActivity records, we just want the actual attribute
            # that the values in the row are for
            attribute = attributes["attribute"]
            # Create the LivelihoodActivity records
            if any(value for value in df.loc[row, "B":]):
                # Default the list of livelihood activities for this strategy if necessary
                if not livelihood_activities_for_strategy:
                    livelihood_activities_for_strategy = []
                    for i, value in enumerate(df.loc[row, "B":]):
                        # Save the column and row, to aid trouble-shooting
                        # We need col_index + 1 to get the letter, and the enumerate is already starting from col B
                        column = get_column_letter(i + 2)
                        livelihood_activity = {attribute: value}
                        livelihood_activity["column"] = column
                        livelihood_activity["row"] = row

                        livelihood_activities_for_strategy.append(livelihood_activity)
                    column = None
                # Ignore duplicate attributes, which occur when we don't recognize the activity label that indicates
                # the start of the LivelihoodStrategy that follows the current LivelihoodStrategy.
                elif attribute not in livelihood_activities_for_strategy[0]:
                    for i, value in enumerate(df.loc[row, "B":]):
                        # Save the column and row, to aid trouble-shooting
                        # We need col_index + 1 to get the letter, and the enumerate is already starting from col B
                        column = get_column_letter(i + 2)
                        livelihood_activities_for_strategy[i][attribute] = value
                        # The BSS does not store the kcals_consumed for ButterProduction, only the percentage_kcals,
                        # so derive it by multiplying by:
                        # 2100 (kcals per person per day) * 365 (days per year) * average_household_size (from Row 40)
                        if strategy_type == "ButterProduction" and attribute == "percentage_kcals":
                            livelihood_activities_for_strategy[i]["kcals_consumed"] = (
                                value * 2100 * 365 * df.loc[40, df.columns[i + 1]] if value else ""
                            )
                    column = None
        except Exception as e:
            if column:
                raise RuntimeError("Unhandled error processing cell %s%s" % (column, row)) from e
            else:
                raise RuntimeError("Unhandled error processing row %s" % row) from e

    result = {
        "LivelihoodStrategy": livelihood_strategies,
        "LivelihoodActivity": livelihood_activities,
    }
    metadata = {
        "num_livelihood_strategies": len(livelihood_strategies),
        "num_livelihood_activities": len(livelihood_activities),
        "num_unrecognized_labels": len(unrecognized_labels),
        "preview": MetadataValue.md(f"```json\n{json.dumps(result, indent=4)}\n```"),
    }
    if not unrecognized_labels.empty:
        metadata["unrecognized_labels"] = MetadataValue.md(unrecognized_labels.to_markdown())

    return Output(
        result,
        metadata=metadata,
    )
