import datetime
from collections import defaultdict

import dagster as dg
import numpy as np
import pandas as pd
from dagster import AssetRecordsFilter, DagsterInstance
from pipelines import defs
from pipelines.partitions import bss_instances_partitions_def

# pd.set_option("future.no_silent_downcasting", True)


def get_dagster_instance():
    # Connect to Dagster instance
    instance = DagsterInstance.get()
    return instance


def get_partion_status_dataframe():
    instance = get_dagster_instance()
    partition_keys = instance.get_dynamic_partitions("bss_instances")
    # Build dataframe of status per (partition, asset)
    df = pd.DataFrame(columns=["asset_key", "partition_key", "status"])
    for asset_def in defs.assets:
        print(f"Processing asset: {asset_def.key.to_user_string()}; partitions_def: {asset_def.partitions_def}")

        # Filter for assets that match the target partitions definition
        if asset_def.partitions_def == bss_instances_partitions_def:

            # 1. Batch fetch run history for all relevant partitions of this asset
            run_info_records = instance.fetch_materializations(
                records_filter=AssetRecordsFilter(
                    asset_key=asset_def.key,
                    asset_partitions=partition_keys,
                ),
                limit=10000,  # Use a limit large enough for all expected records
            ).records

            # 2. Process these records into a lookup dictionary for quick access
            run_info_lookup = {}
            partitions_run_data = defaultdict(list)
            for record in run_info_records:
                partition_key = record.event_log_entry.dagster_event.partition
                if partition_key:
                    partitions_run_data[partition_key].append(record)

            for partition_key, records_list in partitions_run_data.items():
                if records_list:
                    # Find the most recent record to get the last run date
                    last_record = max(records_list, key=lambda r: r.timestamp)
                    run_info_lookup[partition_key] = {
                        "run_count": len(records_list),
                        "last_run_date": datetime.datetime.fromtimestamp(last_record.timestamp),
                    }

            # 3. Get the latest status for each partition
            statuses = instance.get_status_by_partition(
                asset_key=asset_def.key,
                partition_keys=partition_keys,
                partitions_def=bss_instances_partitions_def,
            )

            # 4. Build the DataFrame, combining status with the run info lookup
            if statuses:
                df = pd.concat(
                    [
                        df,
                        pd.DataFrame(
                            [
                                {
                                    "asset_key": asset_def.key.to_user_string(),
                                    "partition_key": k,
                                    "status": str(v).split(".")[1].title() if v else "Missing",
                                    # Safely look up the run count and last run date
                                    "run_count": run_info_lookup.get(k, {}).get("run_count", 0),
                                    "last_run_date": run_info_lookup.get(k, {}).get("last_run_date", None),
                                }
                                for k, v in statuses.items()
                            ]
                        ),
                    ],
                    ignore_index=True,
                )

    df["country"] = df["partition_key"].apply(lambda x: x.split("~")[0] if pd.notna(x) else None)
    return df


def get_metadata(instance, asset_key, asset_partition):
    """
    Fetch materialization metadata for a given asset and partition.
    """
    materialization = instance.get_event_records(
        event_records_filter=dg.EventRecordsFilter(
            event_type=dg.DagsterEventType.ASSET_MATERIALIZATION,
            asset_key=dg.AssetKey([asset_key]),
            asset_partitions=[asset_partition],
        ),
        limit=1,
    )
    if materialization:
        metadata = materialization[0].asset_materialization.metadata
        return metadata

    return None


def extract_pct_rows_recognized(metadata):
    """
    Extract pct_rows_recognized value from metadata dict.
    """
    if metadata and "pct_rows_recognized" in metadata:
        pct_value = metadata["pct_rows_recognized"]
        if hasattr(pct_value, "value"):
            return pct_value.value
        else:
            return pct_value
    return None


def create_metadata_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a new dataframe focused on materialization metadata for heatmap visualization.
    """
    new_data = []
    instance = get_dagster_instance()
    for idx, row in df.iterrows():
        asset_key = row["asset_key"]
        partition_key = row["partition_key"]
        status = row["status"]

        try:
            # Get metadata
            metadata = get_metadata(instance, asset_key, partition_key)
            pct_value = extract_pct_rows_recognized(metadata)

            new_data.append(
                {
                    "asset_key": asset_key,
                    "partition_key": partition_key,
                    "status": status,
                    "pct_rows_recognized": pct_value,
                }
            )

            print(f"Processed {asset_key} - {partition_key}: {pct_value}")

        except Exception as e:
            print(f"Error processing {asset_key} - {partition_key}: {str(e)}")
            # Still add row but with NaN for pct_rows_recognized
            new_data.append(
                {
                    "asset_key": asset_key,
                    "partition_key": partition_key,
                    "status": status,
                    "pct_rows_recognized": np.nan,
                }
            )

    return pd.DataFrame(new_data)
