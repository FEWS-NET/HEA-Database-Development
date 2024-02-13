import pandas as pd
from django.test import TestCase

from common.lookups import ClassifiedProductLookup

from .factories import ClassifiedProductFactory


class ClassifiedProductLookupTestCase(TestCase):
    def setUp(self):
        self.product = ClassifiedProductFactory()

        # Also create some other products with other names
        ClassifiedProductFactory.create_batch(5)

    def test_basic_lookup(self):
        df = pd.DataFrame({"product": [self.product.common_name_en]})
        result_df = ClassifiedProductLookup().do_lookup(df, "product", "cpc")
        self.assertTrue("cpc" in result_df.columns)
        self.assertEqual(len(result_df), 1)
        self.assertEqual(result_df["cpc"][0], self.product.pk)

    def test_ignore_unwanted_parents(self):
        ClassifiedProductFactory(cpc="R0151", description_en="Potatoes")
        # Create a child with a matching description, but different cpc
        product = ClassifiedProductFactory(cpc="R01510", description_en="Potatoes")
        product.common_name_en = "Potatoes"
        product.save()
        df = pd.DataFrame({"product": [product.common_name_en]})
        result_df = ClassifiedProductLookup().do_lookup(df, "product", "cpc")
        self.assertTrue("cpc" in result_df.columns)
        self.assertEqual(len(result_df), 1)
        self.assertEqual(result_df["cpc"][0], product.pk)

        # The child record doesn't could have the search term in a the common name instead of the description,
        # and the child doesn't need to be first child (with a 0 suffix). The child could have its own children,
        # that don't match the search term.
        ClassifiedProductFactory(cpc="R0141", description_en="Soya beans")
        ClassifiedProductFactory(cpc="R01411", description_en="Soya beans, seed for planting")
        product = ClassifiedProductFactory(cpc="R01412", description_en="Soya beans, other")
        product.common_name_en = "Soya beans"
        product.save()
        ClassifiedProductFactory(
            cpc="R01412HA", description_en="Soya beans, other, dry", common_name_en="Soya beans (dry)"
        )
        df = pd.DataFrame({"product": [product.common_name_en]})
        result_df = ClassifiedProductLookup().do_lookup(df, "product", "cpc")
        self.assertTrue("cpc" in result_df.columns)
        self.assertEqual(len(result_df), 1)
        self.assertEqual(result_df["cpc"][0], product.pk)
