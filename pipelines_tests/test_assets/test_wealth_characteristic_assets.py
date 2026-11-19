from unittest.mock import Mock, patch

import pandas as pd
from django.test import TestCase

from baseline.tests.factories import LivelihoodZoneBaselineFactory
from metadata.lookups import WealthCharacteristicLookup
from metadata.models import WealthCharacteristicLabel
from metadata.tests.factories import (
    WealthCharacteristicFactory,
    WealthGroupCategoryFactory,
)
from pipelines.assets.wealth_characteristic import (
    WB_NOISE_LABEL_PATTERNS,
    get_wealth_characteristic_attributes,
    get_wealth_characteristic_label_map,
    is_ignored_wealth_characteristic_label,
    wealth_characteristic_instances,
)


class WBNoiseLabelPatternsTestCase(TestCase):
    """
    Tests for the explanatory notes in Column A of the WB worksheet that are treated as blank cells.
    """

    def is_noise(self, labels: list[str]) -> list[bool]:
        """
        Apply WB_NOISE_LABEL_PATTERNS to the labels in the same way as get_bss_dataframe.
        """
        noise_pattern = "|".join(f"(?:{pattern})" for pattern in WB_NOISE_LABEL_PATTERNS)
        return pd.Series(labels).str.strip().str.fullmatch(noise_pattern, case=False, na=False).tolist()

    def test_noise_labels_are_ignored(self):
        """
        Explanatory notes referring to the TSS or to other forms are recognized as noise.
        """
        labels = [
            "TSS ligne 27",
            'TSS ligne 3=""',
            'TSS ligne 4=""',
            "tss ligne",
            "Voir TSS ligne 12 et 13",
            "TSS line 5",
            "TSS row 27",
            "F3 pas F4 (pas TSS)",
            "F3 seulement (pas sur TSS)",
            " F3 seulement (pas sur TSS) ",
            "CL only (not in TSS)",
            "Wealth characteristics",
        ]
        self.assertEqual(self.is_noise(labels), [True] * len(labels))

    def test_real_labels_are_not_ignored(self):
        """
        Genuine wealth characteristic labels are not treated as noise.
        """
        labels = [
            "Taille du ménage",
            "Superficie cultivée (ha)",
            "Vaches: nombre possédé au début de l'année",
            "HH size",
            "F3 seulement",
        ]
        self.assertEqual(self.is_noise(labels), [False] * len(labels))


class WealthCharacteristicInstancesTestCase(TestCase):

    def test_get_wealth_characteristic_attributes_matches_characteristic_alias(self):
        """
        Labels can match aliases on simple WealthCharacteristic records directly.
        """
        WealthCharacteristicFactory(
            code="household size",
            aliases=["HH size"],
            has_product=False,
            has_unit_of_measure=False,
        )
        WealthCharacteristicFactory(
            code="adult females",
            name_en="Adult females",
            variable_type="float",
            aliases=["number of adult females", "no. adult females"],
            has_product=True,
            has_unit_of_measure=False,
        )
        lookup = WealthCharacteristicLookup()

        attributes = get_wealth_characteristic_attributes("hh size", {}, lookup)
        self.assertEqual(attributes["wealth_characteristic_id"], "household size")
        self.assertIsNone(attributes["product_id"])
        self.assertIsNone(attributes["unit_of_measure_id"])
        self.assertEqual(attributes["wealth_characteristic__has_product"], False)

        attributes = get_wealth_characteristic_attributes("no. adult females", {}, lookup)
        self.assertEqual(attributes["wealth_characteristic_id"], "adult females")
        self.assertIsNone(attributes["product_id"])
        self.assertIsNone(attributes["unit_of_measure_id"])
        self.assertEqual(attributes["wealth_characteristic__has_product"], True)

    def test_get_wealth_characteristic_attributes_prefers_configured_label(self):
        """
        WealthCharacteristicLabel metadata overrides a possible direct match.
        """
        lookup = Mock()
        label_attributes = {
            "status": WealthCharacteristicLabel.LabelStatus.IGNORE,
            "wealth_characteristic_id": None,
        }

        attributes = get_wealth_characteristic_attributes("ignore me", {"ignore me": label_attributes}, lookup)

        self.assertEqual(attributes, label_attributes)
        self.assertIsNot(attributes, label_attributes)
        lookup.get.assert_not_called()

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
    def test_wealth_characteristic_instances_matches_alias_and_skips_ignored_rows_with_data(
        self, mock_get_wealth_group_dataframe
    ):
        livelihood_zone_baseline = LivelihoodZoneBaselineFactory()
        WealthGroupCategoryFactory(code="VP", name_en="Very Poor", aliases=["vp"])
        household_size = WealthCharacteristicFactory(
            code="household size",
            name_en="Household size",
            variable_type="float",
            aliases=["HH size", "Ignore me"],
            has_product=False,
            has_unit_of_measure=False,
        )
        WealthCharacteristicLabel.objects.create(
            wealth_characteristic_label="Ignore me",
            status=WealthCharacteristicLabel.LabelStatus.IGNORE,
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
        self.assertEqual(
            output.value["WealthGroupCharacteristicValue"][0]["wealth_characteristic_id"], household_size.pk
        )
        self.assertEqual(output.value["WealthGroupCharacteristicValue"][0]["bss_row"], 4)

    @patch("pipelines.assets.wealth_characteristic.get_wealth_group_dataframe")
    def test_wealth_characteristic_instances_creates_baseline_group_for_category_missing_from_first_community(
        self, mock_get_wealth_group_dataframe
    ):
        livelihood_zone_baseline = LivelihoodZoneBaselineFactory()
        WealthGroupCategoryFactory(code="VP", name_en="Very Poor", aliases=["vp"])
        WealthGroupCategoryFactory(code="P", name_en="Poor", aliases=["p"])
        characteristic = WealthCharacteristicFactory(code="household size", has_product=False)

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

        baseline_key = [
            livelihood_zone_baseline.livelihood_zone_id,
            livelihood_zone_baseline.reference_year_end_date.isoformat(),
        ]

        def community_key(name):
            return (
                livelihood_zone_baseline.livelihood_zone_id,
                livelihood_zone_baseline.reference_year_end_date.isoformat(),
                name,
            )

        # Community 1 (the first column, "C") only has a "VP" Wealth Group interview column, while Community 2
        # has both "VP" (column "D") and "P" (column "E") Wealth Group interview columns.
        mock_get_wealth_group_dataframe.side_effect = [
            pd.DataFrame(
                [
                    {
                        "bss_column": "C",
                        "wealth_group_category_original": "VP",
                        "wealth_group_category": "VP",
                        "livelihood_zone_baseline": baseline_key,
                        "community": community_key("Community 1"),
                        "district": "District 1",
                        "name": "Community 1",
                        "full_name": "Community 1",
                        "natural_key": baseline_key + ["VP", "Community 1"],
                    },
                    {
                        "bss_column": "D",
                        "wealth_group_category_original": "VP",
                        "wealth_group_category": "VP",
                        "livelihood_zone_baseline": baseline_key,
                        "community": community_key("Community 2"),
                        "district": "District 2",
                        "name": "Community 2",
                        "full_name": "Community 2",
                        "natural_key": baseline_key + ["VP", "Community 2"],
                    },
                    {
                        "bss_column": "E",
                        "wealth_group_category_original": "P",
                        "wealth_group_category": "P",
                        "livelihood_zone_baseline": baseline_key,
                        "community": community_key("Community 2"),
                        "district": "District 2",
                        "name": "Community 2",
                        "full_name": "Community 2",
                        "natural_key": baseline_key + ["P", "Community 2"],
                    },
                ]
            ),
            pd.DataFrame(
                [
                    {"bss_column": "B", "full_name": "Community 1", "wealth_group_category": "VP"},
                    {"bss_column": "C", "full_name": "Community 2", "wealth_group_category": "VP"},
                    {"bss_column": "D", "full_name": "Community 2", "wealth_group_category": "P"},
                ]
            ),
        ]

        wealth_characteristic_dataframe = pd.DataFrame(
            {
                "A": ["", "", "", "HH size", "HH size"],
                "B": ["", "", "", "VP", "P"],
                "C": ["", "", "", 8, ""],
                "D": ["", "", "", 8, 7],
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

        baseline_categories = {
            wealth_group["wealth_group_category"]
            for wealth_group in output.value["WealthGroup"]
            if wealth_group["community"] is None
        }
        self.assertEqual(baseline_categories, {"VP", "P"})
