"""
Status reporting for partitioned Dagster pipelines.

A pipeline is monitored by adding `pipeline_status` metadata to its terminal asset, for example:

    @asset(
        partitions_def=bss_instances_partitions_def,
        metadata={"pipeline_status": {"label": "BSS import", "group_label": "Country", "group_separator": "~"}},
    )
    def imported_baseline(...):

The pipeline consists of the terminal asset and all the upstream assets that share its partitions definition.
`group_label` and `group_separator` are optional: if they are present then partitions are grouped by the part of
the partition key before the first `group_separator`, e.g. the country for `Mali~ML02~2020-06-30`.

Dagster marks every asset downstream of a failed step as failed too, so the useful information for each
partition is the root failure: the failed assets that do not have a failed parent.
"""

import datetime
import os
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from urllib.parse import quote

import pandas as pd
from dagster import AssetKey, AssetRecordsFilter, DagsterInstance, PartitionsDefinition
from dagster._core.definitions.assets.graph.base_asset_graph import BaseAssetGraph

METADATA_KEY = "pipeline_status"


class AssetStatus(StrEnum):
    """
    Status of a single asset partition, matching the statuses shown in the Dagster UI.
    """

    MATERIALIZED = "Materialized"
    FAILED = "Failed"
    IN_PROGRESS = "In Progress"
    MISSING = "Missing"


class PartitionStatus(StrEnum):
    """
    Overall status of a partition across all the assets in the pipeline.
    """

    COMPLETE = "Complete"
    FAILED = "Failed"
    IN_PROGRESS = "In Progress"
    INCOMPLETE = "Incomplete"
    NOT_STARTED = "Not Started"


# Colors from the Dagster UI light theme (accent-green, accent-red, accent-blue and core-gray200)
STATUS_COLORS = {
    AssetStatus.MATERIALIZED: "#2ECC81",
    AssetStatus.FAILED: "#C72A1C",
    AssetStatus.IN_PROGRESS: "#4F43DD",
    AssetStatus.MISSING: "#C2C7D0",
}


@dataclass(frozen=True)
class MonitoredPipeline:
    """
    A partitioned pipeline, defined by its terminal asset, whose status can be monitored.
    """

    terminal_asset_key: AssetKey
    label: str
    partitions_def: PartitionsDefinition
    asset_keys: list[AssetKey]
    dependencies: dict[str, list[str]] = field(repr=False)
    group_label: str | None = None
    group_separator: str | None = None

    @property
    def slug(self) -> str:
        """
        Return an identifier for the pipeline that is safe to use as a single url path segment.
        """
        return "__".join(self.terminal_asset_key.path)

    @property
    def terminal_asset(self) -> str:
        """
        Return the user string for the terminal asset key, e.g. `imported_baseline`.
        """
        return self.terminal_asset_key.to_user_string()

    def get_group(self, partition_key: str) -> str:
        """
        Return the group for a partition key, or an empty string if the pipeline does not group partitions.
        """
        if not self.group_separator or self.group_separator not in partition_key:
            return ""
        return partition_key.split(self.group_separator)[0]

    def get_partition_keys(self, instance: DagsterInstance) -> list[str]:
        """
        Return all the partition keys for the pipeline, for both dynamic and static or time window partitions.
        """
        return sorted(self.partitions_def.get_partition_keys(dynamic_partitions_store=instance))


def get_upstream_asset_keys(asset_graph: BaseAssetGraph, terminal_asset_key: AssetKey) -> list[AssetKey]:
    """
    Return the terminal asset and all its upstream assets that share its partitions definition, in dependency order.

    The search stops at assets with a different partitions definition, so unpartitioned metadata assets, and assets
    upstream of them, are excluded.
    """
    partitions_def = asset_graph.get(terminal_asset_key).partitions_def
    upstream = {terminal_asset_key}
    pending = [terminal_asset_key]
    while pending:
        for parent_key in asset_graph.get(pending.pop()).parent_keys:
            if parent_key not in upstream and asset_graph.get(parent_key).partitions_def == partitions_def:
                upstream.add(parent_key)
                pending.append(parent_key)
    return [asset_key for asset_key in asset_graph.toposorted_asset_keys if asset_key in upstream]


def get_dependencies(asset_graph: BaseAssetGraph, asset_keys: Iterable[AssetKey]) -> dict[str, list[str]]:
    """
    Return the parents of each asset in `asset_keys`, restricted to parents that are also in `asset_keys`.

    Keys and values are user strings, e.g. `corrected_files`, to match the status DataFrame.
    """
    asset_keys = list(asset_keys)
    return {
        asset_key.to_user_string(): [
            parent_key.to_user_string()
            for parent_key in asset_keys
            if parent_key in asset_graph.get(asset_key).parent_keys
        ]
        for asset_key in asset_keys
    }


def get_monitored_pipeline(asset_graph: BaseAssetGraph, terminal_asset_key: AssetKey) -> MonitoredPipeline:
    """
    Return the monitored pipeline for a terminal asset, using the `pipeline_status` metadata on the asset.
    """
    asset_node = asset_graph.get(terminal_asset_key)
    if asset_node.partitions_def is None:
        raise ValueError(f"Asset {terminal_asset_key.to_user_string()} must be partitioned to monitor its status")
    config = asset_node.metadata.get(METADATA_KEY) or {}
    # Metadata may be normalized to a JsonMetadataValue, depending on how the asset was defined
    config = getattr(config, "value", config)
    asset_keys = get_upstream_asset_keys(asset_graph, terminal_asset_key)
    return MonitoredPipeline(
        terminal_asset_key=terminal_asset_key,
        label=config.get("label", terminal_asset_key.to_user_string()),
        partitions_def=asset_node.partitions_def,
        asset_keys=asset_keys,
        dependencies=get_dependencies(asset_graph, asset_keys),
        group_label=config.get("group_label"),
        group_separator=config.get("group_separator"),
    )


def get_monitored_pipelines(asset_graph: BaseAssetGraph) -> list[MonitoredPipeline]:
    """
    Return the monitored pipelines for all the assets with `pipeline_status` metadata, ordered by label, ignoring case.
    """
    pipelines = [
        get_monitored_pipeline(asset_graph, asset_key)
        for asset_key in asset_graph.toposorted_asset_keys
        if METADATA_KEY in asset_graph.get(asset_key).metadata
    ]
    return sorted(pipelines, key=lambda pipeline: pipeline.label.casefold())


def get_asset_status_dataframe(
    instance: DagsterInstance, pipeline: MonitoredPipeline, partition_keys: list[str] | None = None
) -> pd.DataFrame:
    """
    Return a DataFrame with one row per partition and asset, containing the latest status of that asset partition.

    Includes all the partitions for the pipeline unless a list of `partition_keys` is supplied.
    Columns are `partition_key`, `group`, `asset_key` and `status`.
    """
    if partition_keys is None:
        partition_keys = pipeline.get_partition_keys(instance)
    rows = []
    for asset_key in pipeline.asset_keys:
        statuses = instance.get_status_by_partition(asset_key, partition_keys, pipeline.partitions_def) or {}
        for partition_key in partition_keys:
            status = statuses.get(partition_key)
            rows.append(
                {
                    "partition_key": partition_key,
                    "group": pipeline.get_group(partition_key),
                    "asset_key": asset_key.to_user_string(),
                    "status": AssetStatus[status.value] if status else AssetStatus.MISSING,
                }
            )
    return pd.DataFrame(rows, columns=["partition_key", "group", "asset_key", "status"])


def get_root_failures(statuses: dict[str, AssetStatus], dependencies: dict[str, list[str]]) -> list[str]:
    """
    Return the failed assets for a single partition that don't have a failed parent, in dependency order.

    These are the assets where the pipeline actually failed, rather than ones that failed because an upstream
    asset failed.
    """
    return [
        asset_key
        for asset_key, parents in dependencies.items()
        if statuses.get(asset_key) == AssetStatus.FAILED
        and not any(statuses.get(parent) == AssetStatus.FAILED for parent in parents)
    ]


def get_partition_status(statuses: dict[str, AssetStatus], terminal_asset: str) -> PartitionStatus:
    """
    Return the overall status of a single partition from the statuses of the assets in the pipeline.
    """
    values = set(statuses.values())
    if AssetStatus.IN_PROGRESS in values:
        return PartitionStatus.IN_PROGRESS
    if AssetStatus.FAILED in values:
        return PartitionStatus.FAILED
    if statuses.get(terminal_asset) == AssetStatus.MATERIALIZED:
        return PartitionStatus.COMPLETE
    if values <= {AssetStatus.MISSING}:
        return PartitionStatus.NOT_STARTED
    return PartitionStatus.INCOMPLETE


def get_partition_summary_dataframe(status_df: pd.DataFrame, pipeline: MonitoredPipeline) -> pd.DataFrame:
    """
    Return a DataFrame with one row per partition summarizing the status of the pipeline for that partition.

    Columns are `partition_key`, `group`, `status`, `root_failures` and `materialized_count`.
    """
    rows = []
    for (partition_key, group), partition_df in status_df.groupby(["partition_key", "group"], sort=True):
        statuses = dict(zip(partition_df["asset_key"], partition_df["status"]))
        rows.append(
            {
                "partition_key": partition_key,
                "group": group,
                "status": get_partition_status(statuses, pipeline.terminal_asset),
                "root_failures": get_root_failures(statuses, pipeline.dependencies),
                "materialized_count": sum(status == AssetStatus.MATERIALIZED for status in statuses.values()),
            }
        )
    return pd.DataFrame(rows, columns=["partition_key", "group", "status", "root_failures", "materialized_count"])


def get_asset_partition_details(
    instance: DagsterInstance, pipeline: MonitoredPipeline, partition_key: str
) -> dict[str, dict]:
    """
    Return the latest materialization and latest run for each asset in the pipeline for a single partition.

    The latest planned run is the run that most recently attempted the asset, so for a failed asset it is the run
    that contains the failure.
    """
    details = {}
    for asset_key in pipeline.asset_keys:
        records = instance.fetch_materializations(
            AssetRecordsFilter(asset_key=asset_key, asset_partitions=[partition_key]), limit=1
        ).records
        planned = instance.get_latest_planned_materialization_info(asset_key, partition_key)
        details[asset_key.to_user_string()] = {
            "last_materialized": (
                datetime.datetime.fromtimestamp(records[0].timestamp, tz=datetime.timezone.utc) if records else None
            ),
            "last_materialized_run_id": records[0].run_id if records else None,
            "latest_run_id": planned.run_id if planned else None,
        }
    return details


def get_dagster_url(path: str) -> str:
    """
    Return the url for a page in the Dagster UI, served through the Django proxy.
    """
    return f"/{os.environ.get('DAGSTER_WEBSERVER_PREFIX', 'pipelines')}/{path}"


def get_dagster_asset_partition_url(asset_key: str, partition_key: str) -> str:
    """
    Return the url for the partitions view of an asset in the Dagster UI, with the partition selected.

    `asset_key` is a user string, so prefixed asset keys like `drc_price/normalized` keep their `/` separators.
    """
    return get_dagster_url(
        f"assets/{quote(asset_key, safe='/')}?view=partitions&partition={quote(partition_key, safe='')}"
    )


def get_dagster_run_url(run_id: str) -> str:
    """
    Return the url for a run in the Dagster UI.
    """
    return get_dagster_url(f"runs/{run_id}")
