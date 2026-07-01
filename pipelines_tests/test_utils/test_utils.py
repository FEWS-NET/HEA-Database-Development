import pandas as pd
from django.test import TestCase
from pipelines.utils import get_formula_references, prepare_lookup


class PrepareLookupTestCase(TestCase):

    def test_prepare_lookup_with_premitive_type_input(self):
        # empty string
        result = prepare_lookup("")
        self.assertEqual(result, "")

        # a simple string
        result = prepare_lookup("nbr Mois")
        self.assertEqual(result, "nbr mois")

        # an int
        result = prepare_lookup(0)
        self.assertEqual(result, "0")

        # a float
        result = prepare_lookup(7.55)
        self.assertEqual(result, "7.55")

        # a simple string with spaces
        result = prepare_lookup(" nbr Mois ")
        self.assertEqual(result, "nbr mois")

        # string with multiple internal spaces
        result = prepare_lookup("Autre    revenu  (ex. crédit)")
        self.assertEqual(result, "autre revenu (ex. crédit)")

    def test_prepare_lookup_with_list_input(self):
        # list with single element
        result = prepare_lookup(["water"])
        self.assertIsInstance(result, pd.Series)
        self.assertEqual(result[0], "water")

        # list with multiple elements
        result = prepare_lookup(["Water", "inputs", "Social serv."])
        self.assertIsInstance(result, pd.Series)
        pd.testing.assert_series_equal(result, pd.Series(["water", "inputs", "social serv."], name=0))

    def test_prepare_lookup_with_series_input(self):
        # simple series
        data = pd.Series(["Camel number owned", "Cattle number owned"])
        result = prepare_lookup(data)
        self.assertIsInstance(result, pd.Series)
        pd.testing.assert_series_equal(result, pd.Series(["camel number owned", "cattle number owned"], name=0))

        # test with irrigular spaces in elements
        data = pd.Series(["Camel number   owned ", "  cattle number  Owned"])
        result = prepare_lookup(data)
        pd.testing.assert_series_equal(result, pd.Series(["camel number owned", "cattle number owned"], name=0))

        # test with numeric elemnts
        data = pd.Series([123, 456])
        result = prepare_lookup(data)
        pd.testing.assert_series_equal(result, pd.Series(["123", "456"], name=0))

    def test_prepare_lookup_with_dataframe_input(self):
        # single column dataframe
        data = pd.DataFrame({"lables": ["Livestock products"]})
        result = prepare_lookup(data)
        self.assertIsInstance(result, pd.DataFrame)
        pd.testing.assert_frame_equal(result, pd.DataFrame({"lables": ["livestock products"]}))

        # multiple columns dataframe
        data = pd.DataFrame({"lables": ["Livestock products"], "another": ["Payment  in kind  "]})
        result = prepare_lookup(data)
        assert isinstance(result, pd.DataFrame)
        expected = pd.DataFrame({"lables": ["livestock products"], "another": ["payment in kind"]})
        pd.testing.assert_frame_equal(result, expected)

        # numeric values
        data = pd.DataFrame({"column1": [123, 456], "column2": [78.9, 1011.12]})
        result = prepare_lookup(data)
        expected = pd.DataFrame({"column1": ["123", "456"], "column2": ["78.9", "1011.12"]})
        pd.testing.assert_frame_equal(result, expected)

        # empty df
        data = pd.DataFrame()
        result = prepare_lookup(data)
        self.assertIsInstance(result, pd.DataFrame)
        self.assertTrue(result.empty)

        # test that datafarme preserves structure
        data = pd.DataFrame(
            {
                "label": ["Cowpeas: kg produced", "Sorghum: kg produced"],
                "product": ["Cowpeas", "Sorghum"],
                "unit": ["kg", "kg"],
            }
        )
        result = prepare_lookup(data)
        self.assertEqual(result.shape, data.shape)
        self.assertEqual(list(result.columns), list(data.columns))

    def test_prepare_lookup_with_special_characters(self):
        result = prepare_lookup("Autre nourriture: Poisson 2(sec)!@#$%")
        self.assertEqual(result, "autre nourriture: poisson 2(sec)!@#$%")
        # with tabs
        result = prepare_lookup("Autre nourriture: \tPoisson")
        self.assertEqual(result, "autre nourriture: poisson")
        # some unicode characters
        result = prepare_lookup("Revenu (Espèces)")
        self.assertEqual(result, "revenu (espèces)")


class GetFormulaReferencesTestCase(TestCase):

    def test_single_cell_reference(self):
        self.assertEqual(
            get_formula_references('=IF(Data2!B39=0,"",Data2!B39)'),
            [
                {
                    "sheet": "Data2",
                    "start_coordinate": "B39",
                    "start_col": "B",
                    "start_row": 39,
                    "end_coordinate": "B39",
                    "end_col": "B",
                    "end_row": 39,
                    "is_range": False,
                }
            ],
        )

    def test_range_and_quoted_sheet_reference(self):
        self.assertEqual(
            get_formula_references("=SUM('Data 3'!$C$45:$K$45)"),
            [
                {
                    "sheet": "Data 3",
                    "start_coordinate": "C45",
                    "start_col": "C",
                    "start_row": 45,
                    "end_coordinate": "K45",
                    "end_col": "K",
                    "end_row": 45,
                    "is_range": True,
                }
            ],
        )

    def test_default_sheet_reference(self):
        self.assertEqual(
            get_formula_references("=SUM(B39:K39)", default_sheet="Data"),
            [
                {
                    "sheet": "Data",
                    "start_coordinate": "B39",
                    "start_col": "B",
                    "start_row": 39,
                    "end_coordinate": "K39",
                    "end_col": "K",
                    "end_row": 39,
                    "is_range": True,
                }
            ],
        )
