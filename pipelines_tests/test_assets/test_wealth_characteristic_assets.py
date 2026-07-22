from unittest.mock import Mock, patch

import pandas as pd
from django.test import TestCase

from baseline.tests.factories import LivelihoodZoneBaselineFactory
from metadata.models import WealthCharacteristicLabel
from metadata.tests.factories import (
    WealthCharacteristicFactory,
    WealthGroupCategoryFactory,
)
from pipelines.assets.wealth_characteristic import (
    get_wealth_characteristic_label_map,
    is_ignored_wealth_characteristic_label,
    wealth_characteristic_instances,
)


class WealthCharacteristicInstancesTestCase(TestCase):

    def test_get_wealth_characteristic_label_map_marks_ignore_labels_as_ignored(self):
        WealthCharacteristicLabel.objects.create(
            wealth_characteristic_label="Ignore me",
            status=WealthCharacteristicLabel.LabelStatus.IGNORE,
        )

        attributes = get_wealth_characteristic_label_map()["ignore me"]

        self.assertTrue(is_ignored_wealth_characteristic_label(attributes))
        self.assertEqual(attributes["status"], WealthCharacteristicLabel.LabelStatus.IGNORE)
        self.assertIsNone(attributes["wealth_characteristic_id"])

    @patch("pipelines.assets.wealth_characteristic.get_wealth_group_dataframe")
    def test_wealth_characteristic_instances_skips_ignored_rows_with_data(self, mock_get_wealth_group_dataframe):
        livelihood_zone_baseline = LivelihoodZoneBaselineFactory()
        WealthGroupCategoryFactory(code="VP", name_en="Very Poor", aliases=["vp"])
        characteristic = WealthCharacteristicFactory(code="household size", has_product=False)

        WealthCharacteristicLabel.objects.create(
            wealth_characteristic_label="Ignore me",
            status=WealthCharacteristicLabel.LabelStatus.IGNORE,
        )
        WealthCharacteristicLabel.objects.create(
            wealth_characteristic_label="HH size",
            status=WealthCharacteristicLabel.LabelStatus.COMPLETE,
            wealth_characteristic=characteristic,
        )

        partition_key = (
            f"TEST~{livelihood_zone_baseline.livelihood_zone_id}~"
            f"{livelihood_zone_baseline.reference_year_end_date.isoformat()}"
        )
        context = Mock()
        context.asset_partition_key_for_output.return_value = partition_key

        community_key = (
            livelihood_zone_baseline.livelihood_zone_id,
            livelihood_zone_baseline.reference_year_end_date.isoformat(),
            "Community 1",
        )
        baseline_key = [
            livelihood_zone_baseline.livelihood_zone_id,
            livelihood_zone_baseline.reference_year_end_date.isoformat(),
        ]
        mock_get_wealth_group_dataframe.side_effect = [
            pd.DataFrame(
                [
                    {
                        "bss_column": "C",
                        "wealth_group_category_original": "VP",
                        "wealth_group_category": "VP",
                        "livelihood_zone_baseline": baseline_key,
                        "community": community_key,
                        "district": "District 1",
                        "name": "Community 1",
                        "full_name": "Community 1",
                        "natural_key": baseline_key + ["VP", "Community 1"],
                    }
                ]
            ),
            pd.DataFrame(
                [
                    {
                        "bss_column": "B",
                        "full_name": "Community 1",
                        "wealth_group_category": "VP",
                    }
                ]
            ),
        ]

        wealth_characteristic_dataframe = pd.DataFrame(
            {
                "A": ["", "", "", "Ignore me", "HH size"],
                "B": ["", "", "", "VP", "VP"],
                "C": ["", "", "", 123, 8],
                "D": ["", "", "", "", ""],
                "E": ["", "", "", "", ""],
            }
        )
        livelihood_summary_dataframe = pd.DataFrame(
            {
                "A": ["h1", "h2", "h3", "h4", "h5", "h6"],
                "B": ["", "", "", 0, 0, 0],
            },
            index=[3, 4, 5, 6, 7, 8],
        )
        livelihood_summary_dataframe.loc[6, "A"] = "Total food"
        livelihood_summary_dataframe.loc[7, "A"] = "Total income"
        livelihood_summary_dataframe.loc[8, "A"] = "Total expenditure"

        output = wealth_characteristic_instances.node_def.compute_fn.decorated_fn(
            context=context,
            config=Mock(),
            wealth_characteristic_dataframe=wealth_characteristic_dataframe,
            livelihood_summary_dataframe=livelihood_summary_dataframe,
        )

        self.assertEqual(output.metadata["num_unrecognized_labels"].value, 0)
        self.assertEqual(output.metadata["num_wealth_group_characteristic_values"].value, 1)
        self.assertEqual(output.metadata["pct_rows_recognized"].value, 100)
        self.assertEqual(len(output.value["WealthGroupCharacteristicValue"]), 1)
        self.assertEqual(output.value["WealthGroupCharacteristicValue"][0]["bss_row"], 4)
