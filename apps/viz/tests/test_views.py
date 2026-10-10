import dagster as dg
from django.test import TestCase
from django.urls import reverse

from common.tests.factories import UserFactory
from pipelines.partitions import bss_instances_partitions_def


class PipelineStatusViewTestCase(TestCase):
    """
    Tests for the pipeline status views for the BSS import pipeline, using a temporary Dagster instance.
    """

    pipeline = "imported_baseline"
    complete_partition = "Mali~ML01~2020-01-01"
    started_partition = "Niger~NE01~2021-01-01"

    @classmethod
    def setUpTestData(cls):
        """
        Create a user with access to the Dagster UI and a user without it.
        """
        cls.user = UserFactory()
        cls.user_without_permission = UserFactory(is_superuser=False)

    def setUp(self):
        """
        Create a temporary Dagster instance with one complete partition and one partially materialized partition.
        """
        instance_context = dg.instance_for_test()
        instance = instance_context.__enter__()
        self.addCleanup(instance_context.__exit__, None, None, None)

        from pipelines import defs
        from pipelines.status import get_upstream_asset_keys

        asset_keys = get_upstream_asset_keys(defs.resolve_asset_graph(), dg.AssetKey(self.pipeline))
        instance.add_dynamic_partitions(
            bss_instances_partitions_def.name, [self.complete_partition, self.started_partition]
        )
        for asset_key in asset_keys:
            instance.report_runless_asset_event(
                dg.AssetMaterialization(asset_key=asset_key, partition=self.complete_partition)
            )
        instance.report_runless_asset_event(
            dg.AssetMaterialization(asset_key=asset_keys[0], partition=self.started_partition)
        )

    def test_pipeline_status_requires_login(self):
        """
        Anonymous users are redirected to the login page.
        """
        response = self.client.get(reverse("viz:pipeline_status_index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response["Location"])

    def test_pipeline_status_requires_permission(self):
        """
        Users without permission to access the Dagster UI cannot see the pipeline status.
        """
        self.client.force_login(self.user_without_permission)
        for url in [
            reverse("viz:pipeline_status_index"),
            reverse("viz:pipeline_status", args=[self.pipeline]),
            reverse("viz:pipeline_status_partition", args=[self.pipeline, self.complete_partition]),
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

    def test_pipeline_status_index(self):
        """
        The index lists the monitored pipelines with the number of partitions in each status.
        """
        self.client.force_login(self.user)
        response = self.client.get(reverse("viz:pipeline_status_index"))
        self.assertEqual(response.status_code, 200)
        pipelines = {pipeline["terminal_asset"]: pipeline for pipeline in response.context["pipelines"]}
        self.assertEqual(pipelines[self.pipeline]["label"], "BSS import")
        self.assertEqual(pipelines[self.pipeline]["partition_count"], 2)
        self.assertEqual(pipelines[self.pipeline]["url"], reverse("viz:pipeline_status", args=[self.pipeline]))

    def test_pipeline_status(self):
        """
        The pipeline status shows each partition, its overall status and the heatmap.
        """
        self.client.force_login(self.user)
        response = self.client.get(reverse("viz:pipeline_status", args=[self.pipeline]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["partition_count"], 2)
        status_counts = {item["status"]: item["count"] for item in response.context["status_counts"]}
        self.assertEqual(status_counts["Complete"], 1)
        self.assertEqual(status_counts["Incomplete"], 1)
        self.assertEqual(response.context["failures"], [])
        self.assertEqual(
            response.context["heatmap"]["data"][0]["y"], [self.complete_partition, self.started_partition]
        )
        self.assertEqual(response.context["groups"], ["Mali", "Niger"])
        self.assertContains(response, '<label for="id_group">Country</label>', html=True)

    def test_pipeline_status_filtered_by_group(self):
        """
        The pipeline status can be filtered by group, i.e. country for the BSS import pipeline.
        """
        self.client.force_login(self.user)
        response = self.client.get(reverse("viz:pipeline_status", args=[self.pipeline]), {"group": "Niger"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["partition_count"], 1)
        self.assertEqual(response.context["heatmap"]["data"][0]["y"], [self.started_partition])

    def test_pipeline_not_found(self):
        """
        Assets that aren't monitored return a 404.
        """
        self.client.force_login(self.user)
        response = self.client.get(reverse("viz:pipeline_status", args=["consolidated_fixture"]))
        self.assertEqual(response.status_code, 404)

    def test_pipeline_status_partition(self):
        """
        The partition view shows the status of each asset in the pipeline.
        """
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("viz:pipeline_status_partition", args=[self.pipeline, self.started_partition])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["partition_status"], "Incomplete")
        assets = response.context["assets"]
        self.assertEqual(assets[0]["asset_key"], "corrected_files")
        self.assertEqual(assets[0]["status"], "Materialized")
        self.assertIsNotNone(assets[0]["last_materialized"])
        self.assertEqual(assets[-1]["asset_key"], "imported_baseline")
        self.assertEqual(assets[-1]["status"], "Missing")
        self.assertContains(response, "<svg")

    def test_pipeline_status_partition_not_found(self):
        """
        Partitions that don't exist return a 404.
        """
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("viz:pipeline_status_partition", args=[self.pipeline, "Mali~XX99~2020-01-01"])
        )
        self.assertEqual(response.status_code, 404)
