import pandas as pd
from django.test import TestCase

from common.tests.factories import CountryFactory
from metadata.lookups import SeasonLookup, SeasonNameLookup
from metadata.models import LivelihoodStrategyType

from .factories import SeasonFactory


class SeasonLookupTestCase(TestCase):
    def setUp(self):
        self.country = CountryFactory()

        # season with "Season 1" as an alias but no purpose
        self.season1_no_purpose = SeasonFactory(
            country=self.country,
            name_en="Generic First Season",
            aliases=["Season 1"],
            purpose=None,
        )

        # MilkProduction purpose with "Season 1" as an alias
        self.season1_milk = SeasonFactory(
            country=self.country,
            name_en="Milk Production First Season",
            aliases=["Season 1"],
            purpose=LivelihoodStrategyType.MILK_PRODUCTION,
        )

        # CropProduction purpose with "Season 1" as an alias
        self.season1_crop = SeasonFactory(
            country=self.country,
            name_en="Crop Production First Season",
            aliases=["Season 1"],
            purpose=LivelihoodStrategyType.CROP_PRODUCTION,
        )

    def test_lookup_without_purpose(self):
        # when no purpose is provided, should match only seasons with null purpose
        df = pd.DataFrame(
            {
                "season": ["Season 1"],
                "country_id": [self.country.iso3166a2],
            }
        )
        result_df = SeasonLookup().do_lookup(df, "season", "season_id")
        self.assertTrue("season_id" in result_df.columns)
        self.assertEqual(len(result_df), 1)
        self.assertEqual(result_df["season_id"][0], self.season1_no_purpose.id)

    def test_lookup_with_matching_purpose(self):
        # test when purpose is provided and matches a season's purpose
        df = pd.DataFrame(
            {
                "season": ["Season 1"],
                "country_id": [self.country.iso3166a2],
                "purpose": [LivelihoodStrategyType.MILK_PRODUCTION],
            }
        )
        result_df = SeasonLookup().do_lookup(df, "season", "season_id")
        self.assertTrue("season_id" in result_df.columns)
        self.assertEqual(len(result_df), 1)
        self.assertEqual(result_df["season_id"][0], self.season1_milk.id)

    def test_lookup_with_strategy_type_alias(self):
        # test when strategy_type is provided and matches a season's purpose
        df = pd.DataFrame(
            {
                "season": ["Season 1"],
                "country_id": [self.country.iso3166a2],
                "strategy_type": [LivelihoodStrategyType.MILK_PRODUCTION],
            }
        )
        result_df = SeasonLookup().do_lookup(df, "season", "season_id")
        self.assertTrue("season_id" in result_df.columns)
        self.assertEqual(len(result_df), 1)
        self.assertEqual(result_df["season_id"][0], self.season1_milk.id)

    def test_lookup_with_non_matching_purpose_falls_back(self):
        # test when purpose doesn't match any season's purpose, should fall back Seasons with null purpose
        df = pd.DataFrame(
            {
                "season": ["Season 1"],
                "country_id": [self.country.iso3166a2],
                "purpose": [LivelihoodStrategyType.LIVESTOCK_SALE],
            }
        )
        result_df = SeasonLookup().do_lookup(df, "season", "season_id")
        self.assertTrue("season_id" in result_df.columns)
        self.assertEqual(len(result_df), 1)
        self.assertEqual(result_df["season_id"][0], self.season1_no_purpose.id)

    def test_season_name_lookup_with_purpose(self):
        df = pd.DataFrame(
            {
                "season": ["Season 1"],
                "country_id": [self.country.iso3166a2],
                "purpose": [LivelihoodStrategyType.MILK_PRODUCTION],
            }
        )
        result_df = SeasonNameLookup().do_lookup(df, "season", "season_name")
        self.assertTrue("season_name" in result_df.columns)
        self.assertEqual(len(result_df), 1)
        self.assertEqual(result_df["season_name"][0], self.season1_milk.name_en)

    def test_lookup_raises_error_with_duplicate_null_purpose(self):
        # test when multiple seasons have null purpose and same alias, should raise error
        SeasonFactory(
            country=self.country,
            name_en="Another Generic First Season",
            aliases=["Season 1"],
            purpose=None,
        )

        df = pd.DataFrame(
            {
                "season": ["Season 1"],
                "country_id": [self.country.iso3166a2],
            }
        )

        with self.assertRaises(ValueError) as context:
            SeasonLookup().do_lookup(df, "season", "season_id")

        self.assertIn("found multiple Season matches", str(context.exception))

    def test_lookup_raises_error_with_duplicate_same_purpose(self):
        # test when multiple seasons have same purpose and same alias, should raise error
        SeasonFactory(
            country=self.country,
            name_en="Another Milk Production Season",
            aliases=["Season 1"],
            purpose=LivelihoodStrategyType.MILK_PRODUCTION,
        )

        df = pd.DataFrame(
            {
                "season": ["Season 1"],
                "country_id": [self.country.iso3166a2],
                "purpose": [LivelihoodStrategyType.MILK_PRODUCTION],
            }
        )

        with self.assertRaises(ValueError) as context:
            SeasonLookup().do_lookup(df, "season", "season_id")

        self.assertIn("found multiple Season matches", str(context.exception))
