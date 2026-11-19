import json
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
from django.test import TestCase

from baseline.tests.factories import LivelihoodZoneBaselineFactory
from common.models import UnitOfMeasure
from common.tests.factories import ClassifiedProductFactory, CountryFactory
from metadata.models import ActivityLabel
from metadata.tests.factories import SeasonFactory
from pipelines.assets.livelihood_activity import (
    _get_completeness_dataframe,
    get_all_label_attributes,
    get_instances_from_dataframe,
    get_label_attributes,
    get_livelihood_activity_label_map,
    get_livelihood_activity_regexes,
)

LIVELIHOOD_ACTIVITY = ActivityLabel.LivelihoodActivityType.LIVELIHOOD_ACTIVITY


class GetActivityLabelAttributesTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Make sure that Litre has the necessary aliases for the regular expression tests.
        UnitOfMeasure.objects.update_or_create(
            abbreviation="L",
            defaults={
                "name": "litre",
                "category": "Volume",
                "aliases": ["l", "litre", "liter", "1 litre", "1 liter", "litres", "liters"],
            },
        )

    def setUp(self):
        """
        Clear cached label and regex lookups so test order does not affect unit matching.
        """
        get_label_attributes.cache_clear()
        get_livelihood_activity_label_map.cache_clear()
        get_livelihood_activity_regexes.cache_clear()

    def test_livelihood_activity_regexes(self):
        # Fetch the list of labels to test and the expected attributes
        with open(Path(__file__).parent / "test_livelihood_activity_regexes.json") as f:
            expected = json.load(f)

        for label, expected_attributes in expected.items():
            with self.subTest(label=label):
                attributes = {
                    k: v for k, v in get_label_attributes(label, LIVELIHOOD_ACTIVITY).items() if not pd.isna(v)
                }
                self.assertGreaterEqual(
                    len(attributes.keys()),
                    1,
                    f"No pattern matched '{label}'",
                )
                found_attributes = {k: v for k, v in attributes.items() if k in expected_attributes}
                self.assertEqual(
                    found_attributes,
                    expected_attributes,
                    f"Attributes from {attributes['notes']} did not match the expected attributes for '{label}'",
                )
                unwanted_attributes = {
                    k: v
                    for k, v in attributes.items()
                    if k not in expected_attributes and k not in ["activity_label", "status", "notes"]
                }

                self.assertFalse(
                    any([bool(v) for k, v in unwanted_attributes.items()]),
                    msg=f"Extra attributes {({k: v for k, v in unwanted_attributes.items() if v})} from {attributes['notes']} found for '{label}'",
                )

    def test_activity_label_override(self):
        label = "riz - kg produits"
        expected_regex_attributes = {
            "activity_label": label,
            "is_start": True,
            "product_id": "riz",
            "unit_of_measure_id": "kg",
            "attribute": "quantity_produced",
        }
        # Test that the regular expression matches the label and returns the expected attributes
        regex_attributes = {k: v for k, v in get_label_attributes(label, LIVELIHOOD_ACTIVITY).items()}
        self.assertDictEqual(
            expected_regex_attributes,
            {k: v for k, v in regex_attributes.items() if k in expected_regex_attributes},
        )
        # Now create an ActivityLabel instance with status=OVERRIDE for the same label but different attributes
        expected_override_attributes = {
            "activity_label": label,
            "is_start": False,
            "product_id": "R01132",
            "season": "season 1",
        }
        ActivityLabel.objects.create(
            status=ActivityLabel.LabelStatus.OVERRIDE,
            activity_type=LIVELIHOOD_ACTIVITY,
            **expected_override_attributes,
        )
        # Clear the cache of label attributes
        get_label_attributes.cache_clear()
        get_livelihood_activity_label_map.cache_clear()
        # Test that the override attributes are returned instead of the regex attributes
        override_attributes = {k: v for k, v in get_label_attributes(label, LIVELIHOOD_ACTIVITY).items()}
        self.assertDictEqual(
            expected_override_attributes,
            {k: v for k, v in override_attributes.items() if k in expected_override_attributes},
        )
        # Test that additional attributes set in the regex instance are ignored when using the override
        self.assertEqual(None, override_attributes["unit_of_measure_id"])
        # Update the ActivityLabel instance to make it use the regex again
        ActivityLabel.objects.filter(activity_label=label, activity_type=LIVELIHOOD_ACTIVITY).update(
            status=ActivityLabel.LabelStatus.REGULAR_EXPRESSION
        )
        # Clear the cache of label attributes
        get_label_attributes.cache_clear()
        get_livelihood_activity_label_map.cache_clear()
        # Test that the regex attributes are returned again
        regex_attributes = {k: v for k, v in get_label_attributes(label, LIVELIHOOD_ACTIVITY).items()}
        self.assertDictEqual(
            expected_regex_attributes,
            {k: v for k, v in regex_attributes.items() if k in expected_regex_attributes},
        )
        # Test that additional attributes set in the ActivityLabel instance are ignored when using the regex
        self.assertEqual(None, regex_attributes["season"])

    def test_activity_label_ignore_takes_priority_over_regex(self):
        label = "riz - kg produits"
        ActivityLabel.objects.create(
            activity_label=label,
            activity_type=LIVELIHOOD_ACTIVITY,
            status=ActivityLabel.LabelStatus.IGNORE,
        )

        get_label_attributes.cache_clear()
        get_livelihood_activity_label_map.cache_clear()

        ignored_attributes = {k: v for k, v in get_label_attributes(label, LIVELIHOOD_ACTIVITY).items()}

        self.assertEqual(ignored_attributes["activity_label"], label)
        self.assertEqual(ignored_attributes["status"], ActivityLabel.LabelStatus.IGNORE)
        self.assertEqual(ignored_attributes["strategy_type"], "")
        self.assertIsNone(ignored_attributes["unit_of_measure_id"])

    @patch("pipelines.assets.livelihood_activity.get_wealth_group_dataframe")
    def test_get_instances_from_dataframe_skips_ignored_rows_with_data(self, mock_get_wealth_group_dataframe):
        livelihood_zone_baseline = LivelihoodZoneBaselineFactory()
        country = livelihood_zone_baseline.livelihood_zone.country
        for purpose in ["MilkProduction", "ButterProduction"]:
            SeasonFactory(
                country=country,
                purpose=purpose,
                aliases=["season 2"],
            )

        label = "riz - kg produits"
        ActivityLabel.objects.create(
            activity_label=label,
            activity_type=LIVELIHOOD_ACTIVITY,
            status=ActivityLabel.LabelStatus.IGNORE,
        )

        mock_get_wealth_group_dataframe.return_value = pd.DataFrame(
            [{"bss_column": "B", "wealth_group_category": "VP", "community": "Community 1"}]
        )

        dataframe = pd.DataFrame(
            {
                "A": ["", "", "", "", label],
                "B": ["", "", "", "", 123],
            }
        )

        output = get_instances_from_dataframe(
            context=Mock(),
            config=Mock(strict=False),
            df=dataframe,
            livelihood_zone_baseline=livelihood_zone_baseline,
            activity_type=LIVELIHOOD_ACTIVITY,
            num_header_rows=4,
            partition_key="TEST001",
        )

        self.assertEqual(output.value["LivelihoodStrategy"], [])
        self.assertEqual(output.value["LivelihoodActivity"], [])
        self.assertEqual(output.metadata["num_livelihood_strategies"].value, 0)
        self.assertEqual(output.metadata["num_livelihood_activities"].value, 0)
        self.assertEqual(output.metadata["num_unrecognized_labels"].value, 0)
        self.assertEqual(output.metadata["pct_rows_recognized"].value, 100.0)

    @patch("pipelines.assets.livelihood_activity.get_wealth_group_dataframe")
    def test_labor_migration_times_per_year_derived_from_income(self, mock_get_wealth_group_dataframe):
        livelihood_zone_baseline = LivelihoodZoneBaselineFactory()
        country = livelihood_zone_baseline.livelihood_zone.country
        for purpose in ["MilkProduction", "ButterProduction"]:
            SeasonFactory(country=country, purpose=purpose, aliases=["season 2"])
        ClassifiedProductFactory(cpc="S8512HA", kcals_per_unit=2100, aliases=["labour migration"])
        # The payment_per_time label is only recognized via an Override, as it is in the BSS Labels workbook.
        ActivityLabel.objects.create(
            activity_label="savings/remittance each time (per person)",
            activity_type=LIVELIHOOD_ACTIVITY,
            status=ActivityLabel.LabelStatus.OVERRIDE,
            is_start=False,
            attribute="payment_per_time",
        )
        get_label_attributes.cache_clear()
        get_livelihood_activity_label_map.cache_clear()

        baseline_key = list(livelihood_zone_baseline.natural_key())
        mock_get_wealth_group_dataframe.return_value = pd.DataFrame(
            [
                {
                    "bss_column": bss_column,
                    "wealth_group_category": wealth_group_category,
                    "community": community or None,  # Summary columns have no Community
                    "natural_key": baseline_key + [wealth_group_category, community],
                }
                for bss_column, wealth_group_category, community in [
                    ("B", "VP", "Community 1"),
                    ("C", "P-F", "Community 2"),
                    ("D", "P", "Community 3"),
                    ("E", "VP", ""),
                ]
            ]
        )

        # Mirrors NG04 'Data' rows 632-638: the fourth header row is the household size (row 40 in the BSS).
        dataframe = pd.DataFrame(
            {
                "A": [
                    "",
                    "",
                    "",
                    "HH size",
                    "Other cash income:",
                    "Labour migration: no. people per HH",
                    "no. months",
                    "kcals (%)",
                    "savings/remittance each time (per person)",
                    "income",
                ],
                # 'Data'!H632: paid once in 2 months away
                "B": ["", "", "", 7, "", 1, 2, 0.02380952381, 7000, 7000],
                # 'Data'!Q632: paid twice in 1 month away
                "C": ["", "", "", 6, "", 1, 1, 0.01388888889, 15000, 30000],
                # No income recorded, so fall back to once per month away
                "D": ["", "", "", 6, "", 1, 2, 0.02380952381, 5000, ""],
                # 'Data'!BE632: summary column, paid once per month away
                "E": ["", "", "", 7, "", 1, 3, 0.03571428571, 36000, 108000],
            }
        )

        output = get_instances_from_dataframe(
            context=Mock(),
            config=Mock(strict=False),
            df=dataframe,
            livelihood_zone_baseline=livelihood_zone_baseline,
            activity_type=LIVELIHOOD_ACTIVITY,
            num_header_rows=4,
            partition_key="TEST001",
        )

        strategies = output.value["LivelihoodStrategy"]
        self.assertEqual(len(strategies), 1)
        self.assertEqual(strategies[0]["strategy_type"], "OtherCashIncome")
        self.assertEqual(strategies[0]["product_id"], "S8512HA")

        activities = {activity["bss_column"]: activity for activity in output.value["LivelihoodActivity"]}
        self.assertEqual(sorted(activities), ["B", "C", "D", "E"])
        expected_times_per_year = {"B": 1, "C": 2, "D": 2, "E": 3}
        for column, expected in expected_times_per_year.items():
            self.assertAlmostEqual(activities[column]["times_per_year"], expected, msg=f"Column {column}")
        # The derived times_per_year must satisfy the OtherCashIncome income validation
        for column in ["B", "C", "E"]:
            activity = activities[column]
            self.assertAlmostEqual(
                activity["income"],
                activity["payment_per_time"] * activity["people_per_household"] * activity["times_per_year"],
                msg=f"Column {column}",
            )

    def test_zone_specific_season_alias(self):
        country = CountryFactory()
        livelihood_zone_id = f"{country.iso3166a2}04"

        general_season = SeasonFactory(
            country=country,
            name_en=f"{country.iso_en_ro_name}, Harvest",
            aliases=["season 1"],
            purpose=None,
        )
        zone_specific_season = SeasonFactory(
            country=country,
            name_en=f"{country.iso_en_ro_name}, Southern Unimodal, Harvest",
            aliases=[f"season 1 ({livelihood_zone_id.lower()})"],
            purpose=None,
        )

        # Test that the zone-specific season alias is matched when looking up attributes for that Zone.
        attributes_df = get_all_label_attributes(
            labels=pd.Series(["season 1: lactation period (days)"]),
            activity_type=LIVELIHOOD_ACTIVITY,
            country_code=country.iso3166a2,
            livelihood_zone_id=livelihood_zone_id,
        )
        self.assertEqual(attributes_df.loc[0, "season"], zone_specific_season.name_en)

        # Test that the general season alias is matched when looking up attributes for a different Zone.
        livelihood_zone_id = f"{country.iso3166a2}05"
        attributes_df = get_all_label_attributes(
            labels=pd.Series(["season 1: lactation period (days)"]),
            activity_type=LIVELIHOOD_ACTIVITY,
            country_code=country.iso3166a2,
            livelihood_zone_id=livelihood_zone_id,
        )
        self.assertEqual(attributes_df.loc[0, "season"], general_season.name_en)

    def test_get_all_label_attributes_includes_lookup_product_debug_fields(self):
        product = ClassifiedProductFactory(
            cpc="S86119HC",
            common_name_en="Land preparation labor",
            description_en="Land preparation labor",
            aliases=["land prep/ploughing"],
        )

        attributes_df = get_all_label_attributes(
            labels=pd.Series([product.common_name_en]),
            activity_type=LIVELIHOOD_ACTIVITY,
            country_code=None,
            livelihood_zone_id=None,
        )

        self.assertEqual(attributes_df.loc[0, "product_id"], product.pk)
        self.assertEqual(attributes_df.loc[0, "product_common_name_en"], product.common_name_en)

    def test_get_all_label_attributes_matches_product_prefix_and_keeps_full_label(self):
        product = ClassifiedProductFactory(
            cpc="R0132",
            common_name_en="Citrus fruits",
            description_en="Citrus fruits",
        )

        full_label = "Citrus fruits - orange/mandarine"
        attributes_df = get_all_label_attributes(
            labels=pd.Series([full_label]),
            activity_type=LIVELIHOOD_ACTIVITY,
            country_code=None,
            livelihood_zone_id=None,
        )

        self.assertEqual(attributes_df.loc[0, "product_id"], product.pk)
        self.assertEqual(attributes_df.loc[0, "activity_label"], full_label)
        self.assertEqual(attributes_df.loc[0, "additional_identifier"], full_label)
        self.assertEqual(attributes_df.loc[0, "product_common_name_en"], product.common_name_en)

    def test_get_completeness_dataframe_with_no_rows(self):
        column = "income"
        summary_df = pd.DataFrame(
            columns=["strategy_type", "wealth_group_category", f"{column}_recognized", f"{column}_summary"]
        )

        result = _get_completeness_dataframe(summary_df, column)

        self.assertTrue(result.empty)
        self.assertEqual(result.index.names, ["strategy_type", "wealth_group_category"])
        self.assertEqual(list(result.columns), ["recognized", "summary", "unrecognized", "income_completeness"])
