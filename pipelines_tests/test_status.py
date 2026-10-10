import dagster as dg
from django.test import SimpleTestCase

from pipelines import defs
from pipelines.status import (
    AssetStatus,
    PartitionStatus,
    get_asset_partition_details,
    get_asset_status_dataframe,
    get_dagster_asset_partition_url,
    get_monitored_pipeline,
    get_monitored_pipelines,
    get_partition_status,
    get_partition_summary_dataframe,
    get_root_failures,
    get_upstream_asset_keys,
)

partitions_def = dg.DynamicPartitionsDefinition(name="test_bss_instances")
daily_partitions_def = dg.DailyPartitionsDefinition(start_date="2024-01-01", end_date="2024-01-04")


@dg.asset
def unpartitioned(context: dg.AssetExecutionContext) -> int:
    """
    Unpartitioned asset upstream of the test pipeline.
    """
    return 1


@dg.asset(partitions_def=partitions_def, deps=[unpartitioned])
def start(context: dg.AssetExecutionContext) -> int:
    """
    First asset in the test pipeline.
    """
    return 1


@dg.asset(partitions_def=partitions_def)
def left(context: dg.AssetExecutionContext, start: int) -> int:
    """
    Asset on the left branch of the test pipeline, which fails for partitions ending in `left`.
    """
    if context.partition_key.endswith("left"):
        raise ValueError("Left failed")
    return start


@dg.asset(partitions_def=partitions_def)
def right(context: dg.AssetExecutionContext, start: int) -> int:
    """
    Asset on the right branch of the test pipeline.
    """
    return start


@dg.asset(partitions_def=partitions_def)
def joined(context: dg.AssetExecutionContext, left: int, right: int) -> int:
    """
    Asset that joins the left and right branches of the test pipeline.
    """
    return left + right


@dg.asset(
    partitions_def=partitions_def,
    metadata={"pipeline_status": {"label": "Test pipeline", "group_label": "Country", "group_separator": "~"}},
)
def end(context: dg.AssetExecutionContext, joined: int) -> int:
    """
    Terminal asset of the test pipeline.
    """
    return joined


@dg.asset(partitions_def=partitions_def)
def after(context: dg.AssetExecutionContext, end: int) -> int:
    """
    Asset downstream of the terminal asset of the test pipeline.
    """
    return end


@dg.asset(partitions_def=daily_partitions_def, key_prefix="daily")
def extracted(context: dg.AssetExecutionContext) -> int:
    """
    First asset in the daily test pipeline, with a prefixed asset key.
    """
    return 1


@dg.asset(partitions_def=daily_partitions_def, key_prefix="daily", metadata={"pipeline_status": {}})
def loaded(context: dg.AssetExecutionContext, extracted: int) -> int:
    """
    Terminal asset of the daily test pipeline, without a label or grouping.
    """
    return extracted


test_assets = [unpartitioned, start, left, right, joined, end, after]
test_asset_graph = dg.Definitions(assets=[*test_assets, extracted, loaded]).resolve_asset_graph()


class MonitoredPipelineTestCase(SimpleTestCase):
    """
    Tests for identifying the monitored pipelines and their assets.
    """

    def test_get_monitored_pipelines(self):
        """
        Pipelines are found from the assets with pipeline_status metadata, and ordered by label, ignoring case.
        """
        pipelines = get_monitored_pipelines(test_asset_graph)
        self.assertEqual([pipeline.label for pipeline in pipelines], ["daily/loaded", "Test pipeline"])

    def test_get_upstream_asset_keys(self):
        """
        The pipeline contains the upstream assets with the same partitions definition, in dependency order.
        """
        asset_keys = get_upstream_asset_keys(test_asset_graph, dg.AssetKey("end"))
        self.assertEqual(asset_keys[0], dg.AssetKey("start"))
        self.assertEqual(asset_keys[-1], dg.AssetKey("end"))
        self.assertCountEqual(asset_keys, [dg.AssetKey(key) for key in ["start", "left", "right", "joined", "end"]])

    def test_get_monitored_pipeline(self):
        """
        The pipeline uses the label and grouping from the metadata, and dependencies within the pipeline.
        """
        pipeline = get_monitored_pipeline(test_asset_graph, dg.AssetKey("end"))
        self.assertEqual(pipeline.label, "Test pipeline")
        self.assertEqual(pipeline.slug, "end")
        self.assertEqual(pipeline.group_label, "Country")
        self.assertEqual(pipeline.get_group("Mali~ML01~2020-01-01"), "Mali")
        self.assertEqual(pipeline.dependencies["start"], [])
        self.assertCountEqual(pipeline.dependencies["joined"], ["left", "right"])

    def test_get_monitored_pipeline_without_config(self):
        """
        A pipeline with empty metadata is labelled with the terminal asset, and doesn't group partitions.
        """
        pipeline = get_monitored_pipeline(test_asset_graph, dg.AssetKey(["daily", "loaded"]))
        self.assertEqual(pipeline.label, "daily/loaded")
        self.assertEqual(pipeline.slug, "daily__loaded")
        self.assertEqual(pipeline.asset_keys, [dg.AssetKey(["daily", "extracted"]), dg.AssetKey(["daily", "loaded"])])
        self.assertEqual(pipeline.get_group("2024-01-01"), "")

    def test_unpartitioned_asset_cannot_be_monitored(self):
        """
        Unpartitioned assets cannot be monitored.
        """
        with self.assertRaises(ValueError):
            get_monitored_pipeline(test_asset_graph, dg.AssetKey("unpartitioned"))

    def test_bss_pipeline(self):
        """
        The BSS import pipeline runs from corrected_files to imported_baseline via consolidated_fixture.
        """
        pipeline = get_monitored_pipeline(defs.resolve_asset_graph(), dg.AssetKey("imported_baseline"))
        self.assertEqual(pipeline.asset_keys[0], dg.AssetKey("corrected_files"))
        self.assertEqual(pipeline.asset_keys[-1], dg.AssetKey("imported_baseline"))
        self.assertIn(dg.AssetKey("consolidated_fixture"), pipeline.asset_keys)
        self.assertNotIn(dg.AssetKey("bss_metadata"), pipeline.asset_keys)
        self.assertEqual(pipeline.get_group("Mali~ML02~2020-06-30"), "Mali")

    def test_dagster_asset_partition_url(self):
        """
        Prefixed asset keys keep their separators, and partition keys are fully encoded.
        """
        self.assertEqual(
            get_dagster_asset_partition_url("daily/loaded", "Mali/a b.xlsx"),
            "/pipelines/assets/daily/loaded?view=partitions&partition=Mali%2Fa%20b.xlsx",
        )


class RootFailuresTestCase(SimpleTestCase):
    """
    Tests for finding the assets where a partition actually failed.
    """

    dependencies = {"start": [], "left": ["start"], "right": ["start"], "joined": ["left", "right"], "end": ["joined"]}

    def test_downstream_failures_are_not_root_failures(self):
        """
        Assets that failed because a parent failed are not root failures.
        """
        statuses = {
            "start": AssetStatus.MATERIALIZED,
            "left": AssetStatus.FAILED,
            "right": AssetStatus.MATERIALIZED,
            "joined": AssetStatus.FAILED,
            "end": AssetStatus.FAILED,
        }
        self.assertEqual(get_root_failures(statuses, self.dependencies), ["left"])
        self.assertEqual(get_partition_status(statuses, "end"), PartitionStatus.FAILED)

    def test_multiple_root_failures(self):
        """
        Failures on parallel branches are both root failures.
        """
        statuses = {
            "start": AssetStatus.MATERIALIZED,
            "left": AssetStatus.FAILED,
            "right": AssetStatus.FAILED,
            "joined": AssetStatus.FAILED,
            "end": AssetStatus.FAILED,
        }
        self.assertEqual(get_root_failures(statuses, self.dependencies), ["left", "right"])

    def test_failure_with_missing_parent_is_a_root_failure(self):
        """
        A failed asset whose parent is missing, rather than failed, is a root failure.
        """
        statuses = {
            "start": AssetStatus.MISSING,
            "left": AssetStatus.FAILED,
            "right": AssetStatus.MISSING,
            "joined": AssetStatus.MISSING,
            "end": AssetStatus.MISSING,
        }
        self.assertEqual(get_root_failures(statuses, self.dependencies), ["left"])

    def test_get_partition_status(self):
        """
        The partition status summarizes the asset statuses, with in progress taking precedence.
        """
        materialized = {asset_key: AssetStatus.MATERIALIZED for asset_key in self.dependencies}
        missing = {asset_key: AssetStatus.MISSING for asset_key in self.dependencies}
        self.assertEqual(get_partition_status(materialized, "end"), PartitionStatus.COMPLETE)
        self.assertEqual(get_partition_status(missing, "end"), PartitionStatus.NOT_STARTED)
        self.assertEqual(
            get_partition_status({**missing, "start": AssetStatus.MATERIALIZED}, "end"), PartitionStatus.INCOMPLETE
        )
        self.assertEqual(
            get_partition_status({**missing, "start": AssetStatus.IN_PROGRESS, "left": AssetStatus.FAILED}, "end"),
            PartitionStatus.IN_PROGRESS,
        )


class AssetStatusDataFrameTestCase(SimpleTestCase):
    """
    Tests for reading asset status from a Dagster instance.
    """

    partition_keys = ["Mali~ML01~2020-01-01~ok", "Mali~ML02~2020-01-01~left", "Niger~NE01~2020-01-01~none"]

    @classmethod
    def setUpClass(cls):
        """
        Materialize the test assets into an ephemeral Dagster instance.
        """
        super().setUpClass()
        cls.instance = dg.DagsterInstance.ephemeral()
        cls.instance.add_dynamic_partitions(partitions_def.name, cls.partition_keys)
        for partition_key in cls.partition_keys[:2]:
            dg.materialize(test_assets, partition_key=partition_key, instance=cls.instance, raise_on_error=False)
        dg.materialize([extracted, loaded], partition_key="2024-01-02", instance=cls.instance)
        cls.pipeline = get_monitored_pipeline(test_asset_graph, dg.AssetKey("end"))
        cls.status_df = get_asset_status_dataframe(cls.instance, cls.pipeline)

    @classmethod
    def tearDownClass(cls):
        """
        Dispose of the ephemeral Dagster instance.
        """
        cls.instance.dispose()
        super().tearDownClass()

    def test_get_asset_status_dataframe(self):
        """
        The DataFrame contains the status of each pipeline asset for every partition.
        """
        self.assertEqual(len(self.status_df), len(self.partition_keys) * len(self.pipeline.asset_keys))
        statuses = self.status_df.set_index(["partition_key", "asset_key"])["status"]
        self.assertEqual(statuses[("Mali~ML01~2020-01-01~ok", "end")], AssetStatus.MATERIALIZED)
        self.assertEqual(statuses[("Mali~ML02~2020-01-01~left", "right")], AssetStatus.MATERIALIZED)
        self.assertEqual(statuses[("Mali~ML02~2020-01-01~left", "left")], AssetStatus.FAILED)
        self.assertEqual(statuses[("Niger~NE01~2020-01-01~none", "start")], AssetStatus.MISSING)
        self.assertEqual(
            set(self.status_df[self.status_df["partition_key"].str.startswith("Niger")]["group"]), {"Niger"}
        )

    def test_get_asset_status_dataframe_for_time_window_partitions(self):
        """
        Pipelines with time window partitions include every partition in the window.
        """
        pipeline = get_monitored_pipeline(test_asset_graph, dg.AssetKey(["daily", "loaded"]))
        status_df = get_asset_status_dataframe(self.instance, pipeline)
        summary_df = get_partition_summary_dataframe(status_df, pipeline).set_index("partition_key")
        self.assertEqual(list(summary_df.index), ["2024-01-01", "2024-01-02", "2024-01-03"])
        self.assertEqual(summary_df.loc["2024-01-02", "status"], PartitionStatus.COMPLETE)
        self.assertEqual(summary_df.loc["2024-01-01", "status"], PartitionStatus.NOT_STARTED)

    def test_get_asset_status_dataframe_for_selected_partitions(self):
        """
        The DataFrame can be restricted to selected partitions.
        """
        status_df = get_asset_status_dataframe(
            self.instance, self.pipeline, partition_keys=["Mali~ML01~2020-01-01~ok"]
        )
        self.assertEqual(set(status_df["partition_key"]), {"Mali~ML01~2020-01-01~ok"})

    def test_get_partition_summary_dataframe(self):
        """
        The summary identifies the overall status and root failures for each partition.
        """
        summary_df = get_partition_summary_dataframe(self.status_df, self.pipeline).set_index("partition_key")
        self.assertEqual(summary_df.loc["Mali~ML01~2020-01-01~ok", "status"], PartitionStatus.COMPLETE)
        self.assertEqual(
            summary_df.loc["Mali~ML01~2020-01-01~ok", "materialized_count"], len(self.pipeline.asset_keys)
        )
        self.assertEqual(summary_df.loc["Mali~ML02~2020-01-01~left", "status"], PartitionStatus.FAILED)
        self.assertEqual(summary_df.loc["Mali~ML02~2020-01-01~left", "root_failures"], ["left"])
        self.assertEqual(summary_df.loc["Niger~NE01~2020-01-01~none", "status"], PartitionStatus.NOT_STARTED)

    def test_get_asset_partition_details(self):
        """
        The details include the latest materialization and the run that most recently attempted each asset.
        """
        details = get_asset_partition_details(self.instance, self.pipeline, "Mali~ML02~2020-01-01~left")
        self.assertIsNotNone(details["right"]["last_materialized"])
        self.assertEqual(details["right"]["last_materialized_run_id"], details["right"]["latest_run_id"])
        self.assertIsNone(details["left"]["last_materialized"])
        self.assertIsNotNone(details["left"]["latest_run_id"])
