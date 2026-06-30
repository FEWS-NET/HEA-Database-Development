from unittest.mock import patch

import pandas as pd
from django.test import TestCase
from pipelines.assets.baseline import get_wealth_group_dataframe

from baseline.tests.factories import LivelihoodZoneBaselineFactory
from metadata.tests.factories import WealthGroupCategoryFactory


class GetWealthGroupDataframeTestCase(TestCase):
    """
    Tests for parsing Wealth Group columns from BSS worksheets.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Create shared database records used by all tests in this class.
        """
        cls.livelihood_zone_baseline = LivelihoodZoneBaselineFactory()
        cls.very_poor = WealthGroupCategoryFactory(code="VP", name_en="Very Poor")

    def test_summ_worksheet_without_column_b_uses_first_value_column_and_skips_community_lookup(self):
        """
        Summ parsing should use the first non-label column and avoid community lookups
        when every parsed full_name is blank.
        """
        # Summ response dataframes may not include column B.
        df = pd.DataFrame(
            {
                "A": ["", "", "", "", "", ""],
                "C": ["", "", "", "Baseline", "Very Poor", ""],
            }
        )

        with patch("pipelines.assets.baseline.CommunityLookup") as community_lookup_cls:
            wealth_group_df = get_wealth_group_dataframe(
                df=df,
                livelihood_zone_baseline=self.livelihood_zone_baseline,
                worksheet_name="Summ",
                partition_key="XX~LZ01~2026-12-31",
            )

        community_lookup_cls.assert_not_called()
        self.assertEqual("C", wealth_group_df.loc[0, "bss_column"])
        self.assertEqual("VP", wealth_group_df.loc[0, "wealth_group_category"])
        self.assertIsNone(wealth_group_df.loc[0, "community"])
        self.assertEqual("", wealth_group_df.loc[0, "full_name"])
        self.assertEqual("VP", wealth_group_df.loc[0, "natural_key"][2])
        self.assertEqual("", wealth_group_df.loc[0, "natural_key"][3])
