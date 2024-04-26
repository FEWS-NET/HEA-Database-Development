"""
Dagster assets related to Wild Foods and Fishing Livelihood Activities, read from the 'Data3' worksheet in a BSS.

An example of relevant rows from the worksheet:
    |    | A                                       | B              | C              | D      | E              | F             | G        | H         | I              | J        |
    |---:|:----------------------------------------|:---------------|:---------------|:-------|:---------------|:--------------|:---------|:----------|:---------------|:---------|
    |  1 | WILD FOODS + FISHING                    |                |                |        |                |               |          |           |                |          |
    |  2 |                                         |                |                |        |                |               |          |           |                |          |
    |  3 | WEALTH GROUP                            | V.Poor         | V.Poor         | V.Poor | V.Poor         | V.Poor        | V.Poor   | V.Poor    | V.Poor         | V.Poor   |
    |  4 | District/Ward number                    | Salima         | Salima         | Salima | Salima         | Dedza         | Mangochi | Mangochi  | Mangochi       | Mangochi |
    |  5 | Village                                 | Mtika          | Pemba          | Ndembo | Makanjira      | Kasakala      | Kalanje  | Makanjira | Matekwe        | Chiwalo  |
    |  6 | Interview number                        | 1              | 2              | 3      | 4              | 5             | 6        | 7         | 8              | 9        |
    |  7 | HH size                                 | 6              | 10             | 6      | 9              | 7             | 5        | 7         | 6              | 5        |
    |  8 |                                         |                |                |        |                |               |          |           |                |          |
    |  9 | WILD FOODS                              |                |                |        |                |               |          |           |                |          |
    | 10 | Wild food type 1- Mphunga - kg gathered | 8.6            |                |        |                | 43            |          |           | 20             |          |
    | 11 | kcals per kg                            | 3540           | 3540           | 3540   | 3540           | 3550          | 3540     | 3540      | 3540           | 3540     |
    | 12 | sold/exchanged (kg)                     | 0              |                |        |                | 0             |          |           | 0              |          |
    | 13 | price (cash)                            |                |                |        |                |               |          |           |                |          |
    | 14 | income (cash)                           | 0              |                |        |                | 0             |          |           | 0              |          |
    | 15 | other use (kg)                          | 0              |                |        |                | 0             |          |           |                |          |
    | 16 | kcals (%)                               | 0.006619699935 |                |        |                | 0.02845028422 |          |           | 0.01539465101  |          |
    | 17 | Wild food type 2- Honey - kg gathered   |                |                |        |                |               |          |           | 1.8            |          |
    | 18 | kcals per kg                            | 2860           | 2860           | 2860   | 2860           |               | 2860     | 2860      | 2860           | 2860     |
    | 19 | sold/exchanged (kg)                     |                |                |        |                |               |          |           | 1.8            |          |
    | 20 | price (cash)                            |                |                |        |                |               |          |           | 1667           |          |
    | 21 | income (cash)                           |                |                |        |                |               |          |           | 3000.6         |          |
    | 22 | other use (kg)                          |                |                |        |                |               |          |           |                |          |
    | 23 | kcals (%)                               |                |                |        |                |               |          |           | 0              |          |
    | 24 | Wild food type 3 - kg gathered          |                |                |        |                |               |          |           |                |          |
    | 25 | kcals per kg                            |                |                |        |                |               |          |           |                |          |
    | 26 | sold/exchanged (kg)                     |                |                |        |                |               |          |           |                |          |
    | 27 | price (cash)                            |                |                |        |                |               |          |           |                |          |
    | 28 | income (cash)                           |                |                |        |                |               |          |           |                |          |
    | 29 | other use (kg)                          |                |                |        |                |               |          |           |                |          |
    | 30 | kcals (%)                               |                |                |        |                |               |          |           |                |          |
    | 45 | TOTAL WILD FOOD CASH INCOME             | 0              | 0              | 0      | 0              | 0             | 0        | 0         | 3000.6         | 0        |
    | 46 | TOTAL WILD FOOD KCALS (%)               | 0.006619699935 | 0              | 0      | 0              | 0.02845028422 | 0        | 0         | 0.01539465101  | 0        |
    | 47 |                                         |                |                |        |                |               |          |           |                |          |
    | 48 | FISHING                                 |                |                |        |                |               |          |           |                |          |
    | 49 | Fish type 1 (fresh) - kg gathered       | 44             | 45             |        | 70             | 64            |          |           | 47             |          |
    | 50 | kcals per kg                            | 950            | 950            | 950    | 950            | 950           | 950      | 950       | 950            | 950      |
    | 51 | sold/exchanged (kg)                     |                |                |        |                |               |          |           |                |          |
    | 52 | price (cash)                            |                |                |        |                |               |          |           |                |          |
    | 53 | income (cash)                           |                |                |        |                |               |          |           |                |          |
    | 54 | other use (kg)                          | 0              | 0              |        | 0              | 0             |          |           |                |          |
    | 55 | kcals (%)                               | 0.009088932377 | 0.005577299413 |        | 0.009639776763 | 0.01133165595 |          |           | 0.009708632311 |          |
    | 56 | Fish type 2 (dried) - kg gathered       |                |                |        |                |               |          |           |                |          |
    | 57 | kcals per kg                            | 3090           | 3090           | 3090   | 3090           | 3090          | 3090     | 3090      | 3090           | 3090     |
    | 58 | sold/exchanged (kg)                     |                |                |        |                |               |          |           |                |          |
    | 59 | price (cash)                            |                |                |        |                |               |          |           |                |          |
    | 60 | income (cash)                           |                |                |        |                |               |          |           |                |          |
    | 61 | other use (kg)                          |                |                |        |                |               |          |           |                |          |
    | 62 | kcals (%)                               |                |                |        |                |               |          |           |                |          |
    | 84 | TOTAL FISHING CASH INCOME               | 0              | 0              | 0      | 0              | 0             | 0        | 0         | 0              | 0        |
    | 85 | TOTAL FISHING KCALS (%)                 | 0.009088932377 | 0.005577299413 | 0      | 0.009639776763 | 0.01133165595 | 0        | 0         | 0.009708632311 | 0        |
"""  # NOQA: E501

import os

import django
import pandas as pd
from dagster import AssetExecutionContext, Output, asset

from ..configs import BSSMetadataConfig
from ..partitions import bss_instances_partitions_def
from .base import (
    get_all_bss_labels_dataframe,
    get_bss_dataframe,
    get_bss_label_dataframe,
    get_summary_bss_label_dataframe,
)
from .livelihood_activity import get_instances_from_dataframe

# set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hea.settings.production")

# Configure Django with our custom settings before importing any Django classes
django.setup()

from baseline.models import LivelihoodZoneBaseline  # NOQA: E402
from metadata.models import ActivityLabel  # NOQA: E402

# Indexes of header rows in the Data3 dataframe (wealth_group_category, district, village)
HEADER_ROWS = [3, 4, 5, 7]


@asset(partitions_def=bss_instances_partitions_def)
def wild_foods_dataframe(config: BSSMetadataConfig, corrected_files) -> Output[pd.DataFrame]:
    """
    DataFrame of Wild Food Gathering and Fishing Livelihood Activities from a BSS
    """
    return get_bss_dataframe(
        config,
        corrected_files,
        "Data3",
        start_strings=["WILD FOODS", "CUEILLETTE", "CUEILLETTE / CHASSE"],
        header_rows=HEADER_ROWS,
    )


@asset(partitions_def=bss_instances_partitions_def)
def wild_foods_label_dataframe(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    wild_foods_dataframe,
) -> Output[pd.DataFrame]:
    """
    Dataframe of Wild Food (Data3) Label References
    """
    return get_bss_label_dataframe(context, config, wild_foods_dataframe, "wild_foods_dataframe", len(HEADER_ROWS))


@asset(io_manager_key="dataframe_csv_io_manager")
def all_wild_foods_labels_dataframe(
    config: BSSMetadataConfig, wild_foods_label_dataframe: dict[str, pd.DataFrame]
) -> Output[pd.DataFrame]:
    """
    Combined dataframe of the wild food activity labels in use across all BSSs.
    """
    return get_all_bss_labels_dataframe(config, wild_foods_label_dataframe)


@asset(io_manager_key="dataframe_csv_io_manager")
def summary_wild_foods_labels_dataframe(
    config: BSSMetadataConfig, all_wild_foods_labels_dataframe: pd.DataFrame
) -> Output[pd.DataFrame]:
    """
    Summary of the wild food activity labels in use across all BSSs.
    """
    return get_summary_bss_label_dataframe(config, all_wild_foods_labels_dataframe)


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def wild_foods_instances(
    context: AssetExecutionContext,
    wild_foods_dataframe,
) -> Output[dict]:
    """
    LivelhoodStrategy and LivelihoodActivity instances extracted from the BSS.
    """
    partition_key = context.asset_partition_key_for_output()
    livelihood_zone_baseline = LivelihoodZoneBaseline.objects.get_by_natural_key(*partition_key.split("~")[1:])

    if wild_foods_dataframe.empty:
        output = {}

    output = get_instances_from_dataframe(
        context,
        wild_foods_dataframe,
        livelihood_zone_baseline,
        ActivityLabel.LivelihoodActivityType.WILD_FOODS,
        len(HEADER_ROWS),
        partition_key,
    )
    return output
