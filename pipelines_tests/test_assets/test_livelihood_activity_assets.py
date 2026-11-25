import json
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
from django.test import TestCase

from baseline.tests.factories import LivelihoodZoneBaselineFactory
from common.models import ClassifiedProduct, UnitOfMeasure
from common.tests.factories import ClassifiedProductFactory, CountryFactory
from metadata.models import ActivityLabel
from metadata.tests.factories import SeasonFactory
from pipelines.assets.livelihood_activity import (
    _get_completeness_dataframe,
    _get_preview,
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
        # Each row records its BSS label, how it was recognized (the short regex template, or the ActivityLabel
        # status), and the attributes recognized from it.
        row_sources = strategies[0]["row_sources"]
        self.assertEqual(sorted(row_sources), [5, 6, 7, 8, 9])
        self.assertEqual(row_sources[5]["label"], "Labour migration: no. people per HH")
        self.assertTrue(row_sources[5]["source"].startswith("Regular Expression - "))
        self.assertIn("{product_season_pattern}", row_sources[5]["source"])
        self.assertEqual(row_sources[5]["attributes"]["product_id"], "S8512HA")
        self.assertTrue(row_sources[5]["attributes"]["is_start"])
        self.assertEqual(
            row_sources[8],
            {
                "label": "savings/remittance each time (per person)",
                "source": "Override",
                "attributes": {"attribute": "payment_per_time"},
            },
        )
        # The instances are saved by the json_io_manager
        json.dumps(row_sources)
        # times_per_year is calculated when the strategy is finished, which is the last row for the final strategy
        self.assertEqual(strategies[0]["attribute_rows"]["times_per_year"], 9)

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

    @patch("pipelines.assets.livelihood_activity.get_wealth_group_dataframe")
    def test_payment_in_kind_payment_product_from_start_label(self, mock_get_wealth_group_dataframe):
        """
        Test that a payment_product on the label that starts a PaymentInKind strategy is used for the activities.

        Mirrors ML02-TAR 'Data' rows 541-555, where 'Repas pris en exode: nbr. pers par Mènage' is followed only by
        'nbr. mois' and 'kcals (%)', so the start label is the only source of the payment_product. A subsequent
        payment_per_time row must still take precedence over the start label's payment_product.
        """
        livelihood_zone_baseline = LivelihoodZoneBaselineFactory()
        country = livelihood_zone_baseline.livelihood_zone.country
        for purpose in ["MilkProduction", "ButterProduction"]:
            SeasonFactory(country=country, purpose=purpose, aliases=["season 2"])
        labor_migration = ClassifiedProductFactory(cpc="S8512HA", kcals_per_unit=2100)
        casual_labor = ClassifiedProductFactory(cpc="S85HA")
        prepared_meals = ClassifiedProductFactory(cpc="P23997")
        # The test database may already contain R011, so make sure it has the alias used in the payment row.
        cereals = ClassifiedProductFactory(cpc="R011")
        cereals.aliases = ["céréale"]
        cereals.save()
        maize = ClassifiedProductFactory(cpc="R01122")
        for activity_label, product, payment_product, attribute in [
            ("travail: type", casual_labor, maize, "activity_notes"),
            ("repas pris en exode: nbr. pers par mènage", labor_migration, prepared_meals, "people_per_household"),
        ]:
            ActivityLabel.objects.create(
                activity_label=activity_label,
                activity_type=LIVELIHOOD_ACTIVITY,
                status=ActivityLabel.LabelStatus.OVERRIDE,
                is_start=True,
                product=product,
                payment_product=payment_product,
                attribute=attribute,
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
                    ("C", "VP", ""),
                ]
            ]
        )

        # The fourth header row is the household size (row 40 in the BSS).
        dataframe = pd.DataFrame(
            {
                "A": [
                    "",
                    "",
                    "",
                    "Taille du mènage",
                    "PAIEMENT EN NATURE:",
                    "Travail: type",
                    "no. personnes par ménage",
                    "nbr fois par mois",
                    "nbr. mois",
                    "paiement en kg par fois (céréale)",
                    "kcals (%)",
                    "Repas pris en exode: nbr. pers par Mènage",
                    "nbr. mois",
                    "kcals (%)",
                ],
                "B": ["", "", "", 6, "", "FFW", 2, 1, 1, 30, 0.047358, 0.5, 4, 0.027778],
                "C": ["", "", "", 6, "", "FFW", 2, 1, 1, 30, 0.035519, 1, 3, 0.041667],
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

        strategies = {strategy["product_id"]: strategy for strategy in output.value["LivelihoodStrategy"]}
        self.assertEqual(sorted(strategies), ["S8512HA", "S85HA"])
        for strategy in strategies.values():
            self.assertEqual(strategy["strategy_type"], "PaymentInKind")

        payment_products = {
            (activity["livelihood_strategy"][3], activity["bss_column"]): activity["payment_product_id"]
            for activity in output.value["LivelihoodActivity"]
        }
        self.assertEqual(
            payment_products,
            {
                # The subsequent payment_per_time row overrides the payment_product from the start label
                ("S85HA", "B"): "R011",
                ("S85HA", "C"): "R011",
                # There is no payment_per_time row, so the payment_product comes from the start label
                ("S8512HA", "B"): "P23997",
                ("S8512HA", "C"): "P23997",
            },
        )

    @patch("pipelines.assets.livelihood_activity.get_wealth_group_dataframe")
    def test_butter_kcals_moved_to_milk(self, mock_get_wealth_group_dataframe):
        """
        Test that the ButterProduction kcals move to the matching MilkProduction strategy, with their row sources.

        Mirrors ML05 'Data' rows 86-111, where kcals_consumed is calculated rather than read from a row, so its
        attribute row is the start of the next strategy and has no row source.
        """
        livelihood_zone_baseline = LivelihoodZoneBaselineFactory()
        country = livelihood_zone_baseline.livelihood_zone.country
        for purpose in ["MilkProduction", "ButterProduction"]:
            SeasonFactory(country=country, purpose=purpose, aliases=["season 1", "1st season"])
            SeasonFactory(country=country, purpose=purpose, aliases=["season 2", "2nd season"])
        # The migrations load P02211 (cow's milk) and P22241 (butter) without the aliases from the real database
        ClassifiedProduct.objects.filter(cpc="P02211").update(aliases=["cows' milk"])
        # The start of ButterProduction is only recognized via an Override, as it is in the BSS Labels workbook.
        ActivityLabel.objects.create(
            activity_label="% cows' milk sold",
            activity_type=LIVELIHOOD_ACTIVITY,
            status=ActivityLabel.LabelStatus.OVERRIDE,
            strategy_type="ButterProduction",
            is_start=True,
            product_id="P22241",
            season="season 1",
            attribute="percentage_milk_sold",
        )
        get_label_attributes.cache_clear()
        get_livelihood_activity_label_map.cache_clear()

        mock_get_wealth_group_dataframe.return_value = pd.DataFrame(
            [
                {
                    "bss_column": "B",
                    "wealth_group_category": "VP",
                    "community": "Community 1",
                    "natural_key": list(livelihood_zone_baseline.natural_key()) + ["VP", "Community 1"],
                }
            ]
        )
        dataframe = pd.DataFrame(
            {
                "A": [
                    "",
                    "",
                    "",
                    "HH size",
                    "Cows' milk",
                    "no. milking animals",
                    "season 1: lactation period (days)",
                    "total production (litres)",
                    "type of milk sold/other use (skim=0, whole=1)",
                    "% cows' milk sold",
                    "milk+ghee/butter kcals (%) - 1st season",
                    "milk+ghee/butter kcals (%) - 2nd season",
                ],
                "B": ["", "", "", 6, "", 2, 120, 240, 1, 0.5, 0.01, ""],
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

        milk_strategy = next(
            strategy
            for strategy in output.value["LivelihoodStrategy"]
            if strategy["strategy_type"] == "MilkProduction"
        )
        self.assertEqual(milk_strategy["attribute_rows"]["percentage_kcals"], 10)
        self.assertEqual(milk_strategy["attribute_rows"]["kcals_consumed"], 11)
        self.assertTrue(milk_strategy["row_sources"][10]["source"].startswith("Regular Expression - "))
        self.assertNotIn(11, milk_strategy["row_sources"])
        # Normalizing the type of milk keeps the row of its label
        self.assertEqual(milk_strategy["attribute_rows"]["type_of_milk_sold_or_other_uses"], 8)
        # type_of_milk_consumed is added when the MilkProduction strategy is finished, at the start of ButterProduction
        self.assertEqual(milk_strategy["attribute_rows"]["type_of_milk_consumed"], 9)
        milk_activity = next(
            activity
            for activity in output.value["LivelihoodActivity"]
            if activity["strategy_type"] == "MilkProduction"
        )
        self.assertEqual(milk_activity["percentage_kcals"], 0.01)
        self.assertAlmostEqual(milk_activity["kcals_consumed"], 0.01 * 2100 * 365 * 6)

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

    def test_get_all_label_attributes_uses_household_labor_provider_as_additional_identifier(self):
        """
        Labels containing a product and the household members doing the work use those members as the identifier.

        A BSS often contains several rowsets for the same product that differ only by household members, e.g.
        "Filles/garçons - construction" and "Femmes - construction" in BI02 Data2, so the household members must be
        part of the additional_identifier to keep the Livelihood Strategies unique.
        """
        construction = ClassifiedProductFactory(cpc="S54HA", aliases=["construction"])
        domestic_labor = ClassifiedProductFactory(cpc="S98HA", aliases=["travail domestique"])
        labels = pd.Series(
            [
                "Filles/garçons - construction",
                "Femmes - construction",
                "Construction - garçons/filles",
                "Femmes - travail domestique",
            ]
        )

        attributes_df = get_all_label_attributes(
            labels=labels,
            activity_type=ActivityLabel.LivelihoodActivityType.OTHER_CASH_INCOME,
            country_code=None,
            livelihood_zone_id=None,
        )

        self.assertEqual(
            list(attributes_df["product_id"]),
            [construction.pk, construction.pk, construction.pk, domestic_labor.pk],
        )
        self.assertEqual(
            list(attributes_df["additional_identifier"]),
            ["filles/garçons", "femmes", "garçons/filles", "femmes"],
        )
        self.assertEqual(list(attributes_df["household_labor_provider"]), ["children", "women", "children", "women"])
        self.assertTrue(attributes_df["is_start"].all())

    def test_get_all_label_attributes_household_labor_provider_keeps_product_prefix_recovery(self):
        construction = ClassifiedProductFactory(cpc="S54HA", aliases=["construction"])

        attributes_df = get_all_label_attributes(
            labels=pd.Series(["Femmes - construction - masonry"]),
            activity_type=ActivityLabel.LivelihoodActivityType.OTHER_CASH_INCOME,
            country_code=None,
            livelihood_zone_id=None,
        )

        self.assertEqual(attributes_df.loc[0, "product_id"], construction.pk)
        self.assertEqual(attributes_df.loc[0, "additional_identifier"], "femmes - masonry")
        self.assertEqual(attributes_df.loc[0, "household_labor_provider"], "women")

    def test_get_all_label_attributes_splits_trailing_season_from_product(self):
        """
        A season trailing the product in a label is split off, so both the product and the season are recognized.
        """
        # Use a CPC code that isn't in the reference data loaded by the migrations, so that the factory creates it
        # with the aliases we need, rather than returning the existing instance.
        product = ClassifiedProductFactory(
            cpc="R09999AR",
            common_name_en="Test groundnuts",
            description_en="Test groundnuts",
            aliases=["arachide"],
        )
        country = CountryFactory()
        season_a = SeasonFactory(
            country=country, name_en=f"{country.iso_en_ro_name}, Harvest A", aliases=["saison a"], purpose=""
        )
        season_b = SeasonFactory(
            country=country, name_en=f"{country.iso_en_ro_name}, Harvest B", aliases=["saison b"], purpose=""
        )

        attributes_df = get_all_label_attributes(
            labels=pd.Series(
                ["Arachide saison A", "Arachide saison B: nbr unités", "Arachide - saison A: kg produits"]
            ),
            activity_type=LIVELIHOOD_ACTIVITY,
            country_code=country.iso3166a2,
            livelihood_zone_id=None,
        )

        self.assertEqual(list(attributes_df["product_id"]), [product.pk, product.pk, product.pk])
        self.assertEqual(list(attributes_df["season"]), [season_a.name_en, season_b.name_en, season_a.name_en])
        self.assertEqual(
            list(attributes_df["attribute"]),
            ["income_expenditure_or_activity_notes", "number_of_local_measures", "quantity_produced"],
        )
        self.assertEqual(list(attributes_df["additional_identifier"]), ["", "", ""])

    def test_get_completeness_dataframe_with_no_rows(self):
        column = "income"
        summary_df = pd.DataFrame(
            columns=["strategy_type", "wealth_group_category", f"{column}_recognized", f"{column}_summary"]
        )

        result = _get_completeness_dataframe(summary_df, column)

        self.assertTrue(result.empty)
        self.assertEqual(result.index.names, ["strategy_type", "wealth_group_category"])
        self.assertEqual(list(result.columns), ["recognized", "summary", "unrecognized", "income_completeness"])


class GetPreviewTestCase(TestCase):
    """
    Tests for _get_preview, which limits the preview to the Baseline and first Community Livelihood Activities.
    """

    def test_preview_excludes_later_communities(self):
        """
        Instances for the Baseline and the first Community are kept, later Communities are dropped from every model.
        """
        activities = [
            {"wealth_group": ["ML03", "2020-09-30", "VP", full_name]} for full_name in ["", "Village A", "Village B"]
        ]
        instances = {
            "LivelihoodStrategy": [{"strategy_type": "MilkProduction"}],
            "LivelihoodActivity": activities,
            "MilkProduction": activities,
        }
        preview = json.loads(_get_preview(instances).value.removeprefix("```json\n").removesuffix("\n```"))
        self.assertEqual(preview["LivelihoodStrategy"], instances["LivelihoodStrategy"])
        for model_name in ["LivelihoodActivity", "MilkProduction"]:
            self.assertEqual([a["wealth_group"][3] for a in preview[model_name]], ["", "Village A"])
