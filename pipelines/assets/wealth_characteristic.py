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


@asset(partitions_def=bss_files_partitions_def)
def wealth_characteristic_dataframe(config: BSSMetadataConfig, corrected_files) -> Output[pd.DataFrame]:
    """
    DataFrame of Wealth Characteristic from a BSS

    Read from the 'WB' worksheet in the BSS.

    An example of relevant rows from the worksheet:
        |     | A                                              | B                   | C                                          | D                                          | E                                          | F                                          | G                |
        |----:|:-----------------------------------------------|:--------------------|:-------------------------------------------|:-------------------------------------------|:-------------------------------------------|:-------------------------------------------|:-----------------|
        |   1 | MALAWI HEA BASELINES 2015                      | Southern Lakeshore  | Southern Lakeshore                         |                                            |                                            |                                            |                  |
        |   2 |                                                |                     | Community interviews                       |                                            |                                            |                                            |                  |
        |   3 | WEALTH GROUP                                   |                     |                                            |                                            |                                            |                                            |                  |
        |   4 | District                                       | Salima and Mangochi | Salima                                     | Salima                                     | Salima                                     | Salima                                     | Dedza            |
        |   5 | Village                                        |                     | Mtika                                      | Pemba                                      | Ndembo                                     | Makanjira                                  | Kasakala         |
        |   6 | Interview number:                              |                     | 1                                          | 2                                          | 3                                          | 4                                          | 5                |
        |   7 | Interviewers                                   |                     | Kandiwo, Ethel, Fyawupi, Daniel, Chipiliro | Kandiwo, Ethel, Fyawupi, Daniel, Chipiliro | Kandiwo, Ethel, Fyawupi, Chipiliro, Daniel | Kandiwo, Ethel, Fyawupi, Chipiliro, Daniel | Chipiliro, Imran |
        |   8 | Wealth characteristics                         |                     |                                            |                                            |                                            |                                            |                  |
        |   9 | Wealth breakdown (% of households)             | VP                  | 36                                         | 35                                         | 52                                         | 43                                         | 41               |
        |  10 |                                                | P                   | 27                                         | 29                                         | 16                                         | 29                                         | 34               |
        |  11 |                                                | M                   | 29                                         | 23                                         | 23                                         | 20                                         | 18               |
        |  12 |                                                | B/O                 | 8                                          | 13                                         | 9                                          | 8                                          | 7                |
        |  13 |                                                |                     | 100                                        | 100                                        | 100                                        | 100                                        | 100              |
        |  14 | HH size                                        | VP                  | 8                                          | 8                                          | 7                                          | 8                                          | 7                |
        |  15 |                                                | P                   | 9                                          | 8                                          | 7                                          | 7                                          | 7                |
        |  16 |                                                | M                   | 10                                         | 5                                          | 7                                          | 6                                          | 7                |
        |  17 |                                                | B/O                 | 15                                         | 10                                         | 7                                          | 6                                          | 7                |
        |  18 | Land area owned (acres)                        | VP                  | 1.4                                        | 0.75                                       | 0.5                                        | 2                                          | 1                |
        |  19 |                                                | P                   | 1.4                                        | 0.75                                       | 1                                          | 2                                          | 1                |
        |  20 |                                                | M                   | 1.4                                        | 0.75                                       | 1.5                                        | 2                                          | 1                |
        |  21 |                                                | B/O                 | 1.4                                        | 0.75                                       | 2                                          | 2                                          | 2                |
        |  66 | Cattle: Oxen number owned                      | VP                  | 0                                          | 0                                          | 0                                          | 0                                          | 0                |
        |  67 |                                                | P                   | 0                                          | 0                                          | 0                                          | 0                                          | 0                |
        |  68 |                                                | M                   | 0                                          | 0                                          | 0                                          | 0                                          | 0                |
        |  69 |                                                | B/O                 | 0                                          | 0                                          | 0                                          | 0                                          | 0                |
        |  70 | Cattle: total owned at start of year           | VP                  | 0                                          | 0                                          | 0                                          | 0                                          | 0                |
        |  71 | adult females                                  | VP                  | 0                                          | 0                                          | 0                                          | 0                                          | 0                |
        |  72 | no.born during year                            | VP                  |                                            |                                            |                                            |                                            |                  |
        |  73 | no. sold                                       | VP                  |                                            |                                            |                                            |                                            |                  |
        |  74 | no. slaughtered                                | VP                  |                                            |                                            |                                            |                                            |                  |
        |  75 | no. died                                       | VP                  |                                            |                                            |                                            |                                            |                  |
        |  76 | no. bought                                     | VP                  |                                            |                                            |                                            |                                            |                  |
        |  77 | no. at end of reference year                   | VP                  |                                            |                                            |                                            |                                            |                  |
        |  78 | Cattle: total owned at start of year           | P                   | 0                                          | 0                                          | 0                                          | 0                                          | 0                |
        |  79 | adult females                                  | P                   | 0                                          | 0                                          | 0                                          | 0                                          | 0                |
        |  80 | no.born during year                            | P                   |                                            |                                            |                                            |                                            |                  |
        |  81 | no. sold                                       | P                   |                                            |                                            |                                            |                                            |                  |
        |  82 | no. slaughtered                                | P                   |                                            |                                            |                                            |                                            |                  |
        |  83 | no. died                                       | P                   |                                            |                                            |                                            |                                            |                  |
        |  84 | no. bought                                     | P                   |                                            |                                            |                                            |                                            |                  |
        |  85 | no. at end of reference year                   | P                   |                                            |                                            |                                            |                                            |                  |
        |  86 | Cattle: total owned at start of year           | M                   | 0                                          | 0                                          | 3                                          | 5                                          | 0                |
        |  87 | adult females                                  | M                   | 0                                          | 0                                          | 2                                          | 3                                          | 0                |
        |  88 | no.born during year                            | M                   |                                            |                                            |                                            |                                            |                  |
        |  89 | no. sold                                       | M                   |                                            |                                            |                                            |                                            |                  |
        |  90 | no. slaughtered                                | M                   |                                            |                                            |                                            |                                            |                  |
        |  91 | no. died                                       | M                   |                                            |                                            |                                            |                                            |                  |
        |  92 | no. bought                                     | M                   |                                            |                                            |                                            |                                            |                  |
        |  93 | no. at end of reference year                   | M                   |                                            |                                            |                                            |                                            |                  |
        |  94 | Cattle: total owned at start of year           | B/O                 | 15                                         | 9                                          | 30                                         | 18                                         | 3                |
        |  95 | adult females                                  | B/O                 | 13                                         | 6                                          | 24                                         | 14                                         | 2                |
        |  96 | no.born during year                            | B/O                 |                                            |                                            |                                            |                                            |                  |
        |  97 | no. sold                                       | B/O                 |                                            |                                            |                                            |                                            |                  |
        |  98 | no. slaughtered                                | B/O                 |                                            |                                            |                                            |                                            |                  |
        |  99 | no. died                                       | B/O                 |                                            |                                            |                                            |                                            |                  |
        | 100 | no. bought                                     | B/O                 |                                            |                                            |                                            |                                            |                  |
        | 101 | no. at end of reference year                   | B/O                 |                                            |                                            |                                            |                                            |                  |
        | 170 | Chicken number owned                           | VP                  | 6                                          | 8                                          | 1                                          | 3                                          | 3                |
        | 171 |                                                | P                   | 9                                          | 10                                         | 4                                          | 10                                         | 4                |
        | 172 |                                                | M                   | 13                                         | 10                                         | 10                                         | 30                                         | 6                |
        | 173 |                                                | B/O                 | 25                                         | 25                                         | 25                                         | 40                                         | 7                |
        | 186 | Main food crops                                | VP                  | 2                                          | 2                                          | 2                                          | 2                                          | 2                |
        | 187 |                                                | P                   | 2                                          | 2                                          | 2                                          | 2                                          | 2                |
        | 188 |                                                | M                   | 3                                          | 3                                          | 3                                          | 3                                          | 3                |
        | 189 |                                                | B/O                 | 3                                          | 3                                          | 3                                          | 3                                          | 3                |
        | 190 | Main cash crops                                | VP                  | 1                                          | 3                                          | 2                                          | 1                                          | 1                |
        | 191 |                                                | P                   | 2                                          | 3                                          | 2                                          | 1                                          | 1                |
        | 192 |                                                | M                   | 2                                          | 3                                          | 2                                          | 2                                          | 2                |
        | 193 |                                                | B/O                 | 2                                          | 3                                          | 2                                          | 2                                          | 2                |
        | 194 | Main source of cash income 1st                 | VP                  | Casual labour                              | Casual labour                              | Agric Labour                               | Agricultural Labour                        | Agric ganyu      |
        | 195 |                                                | P                   | agricultural labour                        | Casual labour                              | Handcrafts                                 | Agricultural Labour                        | Kabanza,         |
        | 196 |                                                | M                   | agricultural labour                        | small businesses                           | Crop sales                                 | Crop sales                                 | Kabaza business, |
        | 197 |                                                | B/O                 | Businesses                                 | crop sales                                 | Crop sales                                 | Fish sales                                 | Small business,  |
    """  # NOQA: E501
    df = pd.read_excel(corrected_files, "WB", header=None)
    # Use a 1-based index to match the Excel Row Number
    df.index += 1
    # Set the column names to match Excel
    df.columns = [get_column_letter(col + 1) for col in df.columns]

    # Find the column index of the last column that contains relevant data.
    # The final three relevant columns are Summary/From/To in Row 4. Find Summary because
    # it is less likely to give a false positive than the From or To, and then add 2.
    end_col = get_index(["Summary", "SYNTHÈSE", "RESUME"], df.loc[4], offset=2)

    # Find the row index of the start of the Wealth Characteristics
    start_row = get_index(
        ["Wealth characteristics", "Caractéristiques socio-économiques", "Caractéristiques de richesse"],
        df.loc[:, "A"],
        offset=1,
    )

    # Find the language based on the value in cell A3
    langs = {
        "wealth group": "en",
        "group de richesse": "fr",
        "groupe de richesse": "fr",
        "groupe socio-economique": "fr",
    }
    lang = langs[df.loc[3, "A"].strip().lower()]

    # Filter to just the Wealth Group header rows and the Wealth Characteristics
    # Filter to just the Wealth Group header rows and the Wealth Characteristics
    df = pd.concat([df.loc[3:5, :end_col], df.loc[start_row:, :end_col]])

    # Copy the wealth characteristic label from the previous cell for rows that are blank but have a wealth category.
    # Sometimes the wealth characteristic label is only filled in for the first wealth category. For example:
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
            df["A"].isna() & df["B"].notna(),
            pd.NA,
        )
        .ffill()
    )

    # Replace NaN with "" ready for Django
    df = df.fillna("")

    return Output(
        df,
        metadata={
            "worksheet": "WB",
            "lang": lang,
            "row_count": len(df),
            "datapoint_count": int(
                df.loc[:, "C":].apply(lambda row: sum((row != 0) & (row != "")), axis="columns").sum()
            ),
            "preview": MetadataValue.md(df.head(config.preview_rows).to_markdown()),
            "sample": MetadataValue.md(
                df[df.loc[:, "C":].apply(lambda row: sum((row != 0) & (row != "")), axis="columns") > 0]
                .sample(config.preview_rows)
                .to_markdown()
            ),
        },
    )


@asset(partitions_def=bss_files_partitions_def)
def wealth_characteristic_label_dataframe(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    wealth_characteristic_dataframe,
) -> Output[pd.DataFrame]:
    """
    Wealth Characteristic Label References
    """
    df = wealth_characteristic_dataframe.iloc[3:]  # Ignore the Wealth Group header rows
    instance = context.instance
    wealth_characteristic_dataframe_materialization = instance.get_event_records(
        event_records_filter=EventRecordsFilter(
            event_type=DagsterEventType.ASSET_MATERIALIZATION,
            asset_key=context.asset_key_for_input("wealth_characteristic_dataframe"),
            asset_partitions=[context.asset_partition_key_for_input("wealth_characteristic_dataframe")],
        ),
        limit=1,
    )[0].asset_materialization

    label_df = pd.DataFrame()
    label_df["wealth_characteristic_label"] = df["A"]
    label_df["wealth_category"] = df["B"]
    label_df["wealth_characteristic_label_lower"] = label_df["wealth_characteristic_label"].str.lower()
    label_df["filename"] = context.asset_partition_key_for_output()
    label_df["lang"] = wealth_characteristic_dataframe_materialization.metadata["lang"].text
    label_df["worksheet"] = wealth_characteristic_dataframe_materialization.metadata["worksheet"].text
    label_df["row_number"] = df.index
    label_df["datapoint_count"] = df.loc[:, "C":].apply(lambda row: sum((row != 0) & (row != "")), axis="columns")
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


@asset(required_resource_keys={"dataframe_csv_io_manager"})
def all_wealth_characteristic_labels_dataframe(
    config: BSSMetadataConfig, wealth_characteristic_label_dataframe: dict[str, pd.DataFrame]
) -> Output[pd.DataFrame]:
    """
    Combined dataframe of the wealth characteristic labels in use across all BSSs.
    """
    df = pd.concat(list(wealth_characteristic_label_dataframe.values()))
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
