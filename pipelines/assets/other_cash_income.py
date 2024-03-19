"""
Dagster assets related to Other Cash Income Livelihood Activities, read from the 'Data2' worksheet in a BSS.

An example of relevant rows from the worksheet:
|    | A                                                      | B      | C      | D      | E         | F        | G        | H         | I        | J        |
|---:|:-------------------------------------------------------|:-------|:-------|:-------|:----------|:---------|:---------|:----------|:---------|:---------|
|  1 | OTHER CASH INCOME SOURCES                              |        |        |        |           |          |          |           |          |          |
|  2 |                                                        |        |        |        |           |          |          |           |          |          |
|  3 | WEALTH GROUP                                           | V.Poor | V.Poor | V.Poor | V.Poor    | V.Poor   | V.Poor   | V.Poor    | V.Poor   | V.Poor   |
|  4 | District/Ward number                                   | Salima | Salima | Salima | Salima    | Dedza    | Mangochi | Mangochi  | Mangochi | Mangochi |
|  5 | Village                                                | Mtika  | Pemba  | Ndembo | Makanjira | Kasakala | Kalanje  | Makanjira | Matekwe  | Chiwalo  |
|  6 | Interview number                                       | 1      | 2      | 3      | 4         | 5        | 6        | 7         | 8        | 9        |
|  7 |                                                        |        |        |        |           |          |          |           |          |          |
|  8 | AGRICULTURAL LABOUR INCOME - CULTIVATION (PRE-HARVEST) |        |        |        |           |          |          |           |          |          |
|  9 | Land preparation                                       |        |        |        |           |          |          |           |          |          |
| 10 | no. people per HH                                      |        | 1      | 2      | 2         |          | 1        |           | 1        | 1        |
| 11 | no. times per month                                    |        | 9      | 2      | 1         |          | 2        |           | 1        | 2        |
| 12 | no. months                                             |        | 2      | 2      | 4         |          | 2        |           | 2        | 1        |
| 13 | price per unit                                         |        | 1300   | 1200   | 4500      |          | 2000     |           | 3000     | 3000     |
| 14 | income                                                 |        | 23400  | 9600   | 36000     |          | 8000     |           | 6000     | 6000     |
| 15 | Planting                                               |        |        |        |           |          |          |           |          |          |
| 16 | no. people per HH                                      |        |        |        |           |          |          |           |          |          |
| 17 | no. times per month                                    |        |        |        |           |          |          |           |          |          |
| 18 | no. months                                             |        |        |        |           |          |          |           |          |          |
| 19 | price per unit                                         |        |        |        |           |          |          |           |          |          |
| 20 | income                                                 |        |        |        |           |          |          |           |          |          |
| 21 | Weeding                                                |        |        |        |           |          |          |           |          |          |
| 22 | no. people per HH                                      | 1      | 1      | 2      | 2         | 3        | 2        |           | 1        | 1        |
| 23 | no. times per month                                    | 1      | 13     | 4      | 1         | 1        | 2        |           | 2        | 1        |
| 24 | no. months                                             | 2      | 2      | 2      | 2         | 1        | 2        |           | 2        | 1        |
| 25 | price per unit                                         | 4000   | 1200   | 1200   | 6000      | 4000     | 1500     |           | 3500     | 3000     |
| 26 | income                                                 | 8000   | 31200  | 19200  | 24000     | 12000    | 12000    |           | 14000    | 3000     |
| 27 | Ploughing                                              |        |        |        |           |          |          |           |          |          |
| 28 | no. people per HH                                      |        |        |        |           |          |          |           |          |          |
| 29 | no. times per month                                    |        |        |        |           |          |          |           |          |          |
| 30 | no. months                                             |        |        |        |           |          |          |           |          |          |
| 31 | price per unit                                         |        |        |        |           |          |          |           |          |          |
| 32 | income                                                 |        |        |        |           |          |          |           |          |          |
"""  # NOQA: E501

import os

import django
import pandas as pd
from dagster import AssetExecutionContext, Output, asset

from ..configs import BSSMetadataConfig
from ..partitions import bss_files_partitions_def, bss_instances_partitions_def
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

from metadata.models import ActivityLabel  # NOQA: E402

# Indexes of header rows in the Data3 dataframe (wealth_group_category, district, village)
HEADER_ROWS = [3, 4, 5]


@asset(partitions_def=bss_files_partitions_def)
def other_cash_income_dataframe(config: BSSMetadataConfig, corrected_files) -> Output[pd.DataFrame]:
    """
    DataFrame of Other Cash Income Livelihood Activities from a BSS
    """
    return get_bss_dataframe(
        config,
        corrected_files,
        "Data2",
        start_strings=[
            "AGRICULTURAL LABOUR INCOME - CULTIVATION (PRE-HARVEST)",
            "PAIMENT EN NATURE",
            "REVENUS MAIN D'OEUVRE AGRICOLE (pre-récolte)",
            "REVENU DU TRAVAUX AGRICOLES - CULTIVATION",
            "REVENUS DU TRAVAUX AGRICOLES (Pré-récolte)",
        ],
    )


@asset(partitions_def=bss_files_partitions_def)
def other_cash_income_label_dataframe(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    other_cash_income_dataframe,
) -> Output[pd.DataFrame]:
    """
    Other Cash Income (Data2) Label References
    """
    return get_bss_label_dataframe(
        context, config, other_cash_income_dataframe, "other_cash_income_dataframe", len(HEADER_ROWS)
    )


@asset(io_manager_key="dataframe_csv_io_manager")
def all_other_cash_income_labels_dataframe(
    config: BSSMetadataConfig, other_cash_income_label_dataframe: dict[str, pd.DataFrame]
) -> Output[pd.DataFrame]:
    """
    Combined dataframe of the Other Cash Income activity labels in use across all BSSs.
    """
    return get_all_bss_labels_dataframe(config, other_cash_income_label_dataframe)


@asset(io_manager_key="dataframe_csv_io_manager")
def summary_other_cash_income_labels_dataframe(
    config: BSSMetadataConfig, all_other_cash_income_labels_dataframe: pd.DataFrame
) -> Output[pd.DataFrame]:
    """
    Summary of the Other Cash Income activity labels in use across all BSSs.
    """
    return get_summary_bss_label_dataframe(config, all_other_cash_income_labels_dataframe)


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def other_cash_income_instances(
    context: AssetExecutionContext,
    completed_bss_metadata,
    other_cash_income_dataframe,
) -> Output[dict]:
    """
    LivelhoodStrategy and LivelihoodActivity instances extracted from the BSS.
    """
    partition_key = context.asset_partition_key_for_output()
    # Find the metadata for this BSS
    partition_key = context.asset_partition_key_for_output()
    try:
        metadata = completed_bss_metadata[completed_bss_metadata["partition_key"] == partition_key].iloc[0]
    except IndexError:
        raise ValueError("No complete entry in the BSS Metadata worksheet for %s" % partition_key)

    if other_cash_income_dataframe.empty:
        raise ValueError("%s does not contain a Data2 worksheet" % partition_key)

    output = get_instances_from_dataframe(
        context,
        other_cash_income_dataframe,
        metadata,
        ActivityLabel.LivelihoodActivityType.OTHER_CASH_INCOME,
        len(HEADER_ROWS),
        partition_key,
    )
    return output
