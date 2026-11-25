import datetime

from django.test import SimpleTestCase

from pipelines.assets.error_report import get_error_report, get_error_rows
from pipelines.utils import get_errors_metadata


class GetErrorRowsTestCase(SimpleTestCase):
    """
    Tests for get_error_rows, which turns the `errors` metadata from an asset into rows for the error report.
    """

    def test_errors_metadata_round_trip(self):
        """
        Multi-line errors are split correctly, and the worksheet, column and row are found from each message.
        """
        errors = [
            "Failed to identify product from Maize on row 112 for label 'maize':\n"
            "|    | A     | B  |\n"
            "|---:|:------|:---|\n"
            "|  3 | label | VP |",
            "Invalid strategy_type X for attribute income from label 'sales' on row 45",
            # A label containing a newline, which would look like a separate error without the indentation
            "Invalid strategy_type X for attribute income from label 'goat\nsales' on row 46",
            "No formula found in 'Data'!B77 for label 'kcals'",
            "Missing WealthGroup for LivelihoodActivity:\n"
            '{\n    "bss_sheet": "Data3",\n    "bss_column": "F",\n    "bss_row": 66\n}',
            "=SUM(A1:A2) is not a valid label",
        ]
        errors_text = get_errors_metadata(errors).value

        rows = get_error_rows("wild_foods_instances", "ML~ML05~2018-09-30", "run-1", 0.0, errors_text)

        self.assertEqual(
            [(row["worksheet"], row["column"], row["row"]) for row in rows],
            [
                ("Data3", None, 112),  # Default worksheet for the asset
                ("Data3", None, 45),
                ("Data3", None, 46),
                ("Data", "B", 77),  # Worksheet from the cell reference
                ("Data3", "F", 66),  # Location from the JSON dump of the instance
                (None, None, None),
            ],
        )
        self.assertEqual(rows[0]["error"], "Failed to identify product from Maize on row 112 for label 'maize':")
        # The indentation added by get_errors_metadata is removed from the details
        self.assertEqual(rows[0]["details"], errors[0].split("\n", 1)[1])
        self.assertEqual(rows[1]["details"], "")
        # Text from the BSS is not written to Excel as an active formula
        self.assertEqual(rows[5]["error"], "'=SUM(A1:A2) is not a valid label")
        self.assertEqual(
            {key: rows[0][key] for key in ["country", "livelihood_zone", "reference_year_end_date", "partition_key"]},
            {
                "country": "ML",
                "livelihood_zone": "ML05",
                "reference_year_end_date": "2018-09-30",
                "partition_key": "ML~ML05~2018-09-30",
            },
        )
        self.assertEqual(rows[0]["materialized_at"], datetime.datetime(1970, 1, 1))


class GetErrorReportTestCase(SimpleTestCase):
    """
    Tests for get_error_report, which builds the worksheets for the error report from the error rows.
    """

    def get_rows(self, asset_name: str, partition_key: str, timestamp: float, errors: list[str]) -> list[dict]:
        """
        Return the error report rows for the `errors` metadata from one materialization.
        """
        return get_error_rows(asset_name, partition_key, "run-1", timestamp, get_errors_metadata(errors).value)

    def test_summaries_count_bss_rows_by_error_type(self):
        """
        Errors are grouped by type across BSSs, counted once per BSS row, and knock-on errors aren't counted.
        """
        rows = self.get_rows(
            "livelihood_activity_valid_instances",
            "ML~ML05~2018-09-30",
            0.0,
            [
                # The same problem in two Wealth Group columns of one BSS row
                "Expenditure for a Food Purchase must be quantity purchased multiplied by price for FoodPurchase 1 "
                "from 'Data'!C10 with natural key ['ML05', '2018-09-30', 'VP', 'FoodPurchase', 'R01122', '', '', '']",
                "Expenditure for a Food Purchase must be quantity purchased multiplied by price for FoodPurchase 2 "
                "from 'Data'!D10 with natural key ['ML05', '2018-09-30', 'P', 'FoodPurchase', 'R01122', '', '', '']",
                # A parent record with an error, and the knock-on error for its child record
                "Invalid expenditure value kg: “kg” value must be a float. for LivelihoodActivity 3 from 'Data'!C12",
                "Unrecognized 'livelihoodactivity_ptr' foreign key ('ML05', '2018-09-30', 'VP') for FoodPurchase 3 "
                "from 'Data'!C12.",
            ],
        )
        rows += self.get_rows(
            "livelihood_activity_valid_instances",
            "NE~NE01~2019-09-30",
            86400.0,
            [
                "Expenditure for a Food Purchase must be quantity purchased multiplied by price for FoodPurchase 7 "
                "from 'Data'!E20 with natural key ['NE01', '2019-09-30', 'VP', 'FoodPurchase', 'R01122', '', '', '']",
            ],
        )
        # The LivelihoodStrategy is not validated by this asset, so this is not a knock-on error
        rows += self.get_rows(
            "key_parameter_valid_instances",
            "ML~ML05~2018-09-30",
            0.0,
            [
                "Unrecognized 'livelihood_strategy' foreign key ('ML05', '2018-09-30', 'OtherCashIncome') for KeyParameter 1 "
                "from 'Summ'!50:50 with natural key ['ML05', '2018-09-30', 'OtherCashIncome']"
            ],
        )

        sheets = get_error_report(rows)

        self.assertEqual(list(sheets), ["Summary by Error Type", "Summary by Asset", "Summary by BSS", "Errors"])
        errors = sheets["Errors"]
        self.assertEqual(
            errors.loc[errors["is_knock_on"], "error_type"].tolist(),
            ["Unrecognized 'livelihoodactivity_ptr' foreign key … for FoodPurchase from …."],
        )

        error_types = sheets["Summary by Error Type"].set_index("error_type")
        self.assertEqual(
            error_types.loc[
                "Expenditure for a Food Purchase must be quantity purchased multiplied by price for FoodPurchase from …",
                ["num_bss", "num_countries", "num_bss_rows", "num_errors", "assets"],
            ].tolist(),
            [2, 2, 2, 3, "livelihood_activity_valid_instances"],
        )
        # The error type with the most BSSs is first
        self.assertEqual(sheets["Summary by Error Type"]["num_bss"].iloc[0], 2)
        self.assertEqual(len(error_types), 3)

        assets = sheets["Summary by Asset"].set_index("asset_name")
        self.assertEqual(
            assets.loc[
                "livelihood_activity_valid_instances",
                ["num_partitions", "num_bss_rows", "num_errors", "num_knock_on_errors"],
            ].tolist(),
            [2, 3, 5, 1],
        )
        self.assertEqual(
            assets.loc["livelihood_activity_valid_instances", "oldest_materialized_at"], datetime.datetime(1970, 1, 1)
        )

        bss = sheets["Summary by BSS"].set_index("partition_key")
        self.assertEqual(bss.loc["ML~ML05~2018-09-30", "num_bss_rows"], 3)
        self.assertEqual(bss.loc["ML~ML05~2018-09-30", "livelihood_activity_valid_instances"], 2)
        self.assertEqual(bss.loc["NE~NE01~2019-09-30", "num_bss_rows"], 1)

    def test_no_errors(self):
        """
        The report can be created when there aren't any errors.
        """
        sheets = get_error_report([])

        for sheet in sheets.values():
            self.assertTrue(sheet.empty)
