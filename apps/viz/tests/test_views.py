import pickle
import tempfile
from io import BytesIO
from pathlib import Path
from urllib.parse import urlencode

import dagster as dg
import openpyxl
from django.test import TestCase
from django.urls import reverse
from openpyxl.styles import Font

from baseline.tests.factories import LivelihoodZoneBaselineFactory
from common.tests.factories import UserFactory
from pipelines.partitions import bss_instances_partitions_def


def get_workbook_content(value: int) -> bytes:
    """
    Return an .xlsx workbook with a WB worksheet and a Data worksheet that has `value` in B3 and a formula in C3.

    The Data worksheet also has a formatted but empty cell in F10, so that it has trailing empty rows and columns.
    """
    workbook = openpyxl.Workbook()
    workbook.active.title = "WB"
    workbook["WB"]["A1"] = "Wealth group"
    worksheet = workbook.create_sheet("Data")
    worksheet["A1"] = "Livelihood activity"
    worksheet["B3"] = value
    worksheet["C3"] = "=B3*2"
    worksheet["F10"].font = Font(bold=True)
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


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
            with self.subTest(url=url), self.assertLogs("django.request", level="WARNING"):
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
        with self.assertLogs("django.request", level="WARNING"):
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
        self.assertEqual(
            response.context["bss_viewer_url"],
            f"{reverse('viz:bss_viewer')}?{urlencode({'partition_key': self.started_partition})}",
        )

    def test_pipeline_status_partition_not_found(self):
        """
        Partitions that don't exist return a 404.
        """
        self.client.force_login(self.user)
        with self.assertLogs("django.request", level="WARNING"):
            response = self.client.get(
                reverse("viz:pipeline_status_partition", args=[self.pipeline, "Mali~XX99~2020-01-01"])
            )
        self.assertEqual(response.status_code, 404)


class BSSViewerViewTestCase(TestCase):
    """
    Tests for the BSS viewer, using a temporary Dagster instance.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Create a baseline with an original BSS, a user with access to the Dagster UI and a user without it.
        """
        cls.user = UserFactory()
        cls.user_without_permission = UserFactory(is_superuser=False)
        cls.livelihood_zone_baseline = LivelihoodZoneBaselineFactory(bss__data=get_workbook_content(2))
        livelihood_zone = cls.livelihood_zone_baseline.livelihood_zone
        cls.partition_key = (
            f"{livelihood_zone.country.iso_en_ro_proper}~{livelihood_zone.code}~"
            f"{cls.livelihood_zone_baseline.reference_year_end_date.isoformat()}"
        )
        cls.url = reverse("viz:bss_viewer")

    def setUp(self):
        """
        Create a temporary Dagster instance containing the partition for the baseline.
        """
        instance_context = dg.instance_for_test()
        self.instance = instance_context.__enter__()
        self.addCleanup(instance_context.__exit__, None, None, None)
        self.instance.add_dynamic_partitions(bss_instances_partitions_def.name, [self.partition_key])
        self.client.force_login(self.user)

    def test_bss_viewer_requires_permission(self):
        """
        Users without permission to access the Dagster UI cannot see the BSS viewer.
        """
        self.client.force_login(self.user_without_permission)
        with self.assertLogs("django.request", level="WARNING"):
            response = self.client.get(self.url, {"partition_key": self.partition_key})
        self.assertEqual(response.status_code, 403)

    def test_bss_viewer_without_baseline(self):
        """
        The viewer lists the baselines until one is selected.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["partition_keys"], [self.partition_key])
        self.assertNotIn("rows", response.context)

    def test_bss_viewer_values(self):
        """
        The viewer shows the saved values from the Data worksheet by default, without trailing empty cells.
        """
        response = self.client.get(self.url, {"partition_key": self.partition_key})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["sheet_names"], ["WB", "Data"])
        self.assertEqual(response.context["sheet_name"], "Data")
        # openpyxl doesn't save calculated values, so the formula in C3 has no saved value
        self.assertEqual(response.context["columns"], ["A", "B"])
        self.assertEqual(response.context["rows"], [["Livelihood activity", ""], ["", ""], ["", "2"]])

    def test_bss_viewer_formulas(self):
        """
        The viewer shows the formulas instead of the values for cells that have one.
        """
        response = self.client.get(self.url, {"partition_key": self.partition_key, "formulas": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["columns"], ["A", "B", "C"])
        self.assertEqual(response.context["rows"][2], ["", "2", "=B3*2"])
        self.assertContains(response, "<td>=B3*2</td>", html=True)

    def test_bss_viewer_sheet(self):
        """
        The viewer shows the requested worksheet.
        """
        response = self.client.get(self.url, {"partition_key": self.partition_key, "sheet": "WB"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["sheet_name"], "WB")
        self.assertEqual(response.context["rows"], [["Wealth group"]])

    def test_bss_viewer_corrected(self):
        """
        The viewer shows the corrected BSS from the latest materialization of the corrected_files asset.
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corrected_files.pickle"
            path.write_bytes(pickle.dumps(BytesIO(get_workbook_content(3))))
            self.instance.report_runless_asset_event(
                dg.AssetMaterialization(
                    asset_key="corrected_files",
                    partition=self.partition_key,
                    metadata={"path": dg.MetadataValue.path(str(path))},
                )
            )
            response = self.client.get(self.url, {"partition_key": self.partition_key, "file": "corrected"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["rows"][2], ["", "3"])

    def test_bss_viewer_corrected_not_materialized(self):
        """
        The viewer explains that the corrected BSS is missing if the corrected_files asset hasn't been materialized.
        """
        response = self.client.get(self.url, {"partition_key": self.partition_key, "file": "corrected"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The corrected file has not been materialized for this baseline.")

    def test_bss_viewer_partition_not_found(self):
        """
        Partitions that don't exist return a 404.
        """
        with self.assertLogs("django.request", level="WARNING"):
            response = self.client.get(self.url, {"partition_key": "Mali~XX99~2020-01-01"})
        self.assertEqual(response.status_code, 404)
