from io import StringIO

import pandas as pd
from django.http import HttpResponse
from django.test import SimpleTestCase
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from common.models import Country
from common.renderers import FormattedCSVRenderer, HtmlTableRenderer

from .factories import CountryFactory


class RendererTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.existing_countries = Country.objects.count()
        cls.num_records = 5
        cls.data = [CountryFactory() for _ in range(cls.num_records)]

    def setUp(self):
        self.url = reverse("country-list")

    def test_json(self):
        response = self.client.get(self.url, {"format": "json"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records + self.existing_countries)

    def test_csv(self):
        response = self.client.get(self.url, {"format": "csv"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"][:8], "text/csv")
        try:
            content = "".join([s.decode("utf-8") for s in response.streaming_content])
        except AttributeError:
            content = response.content.decode("utf-8")
        df = pd.read_csv(StringIO(content)).fillna("")
        self.assertEqual(len(df), self.num_records + self.existing_countries)

    def test_html(self):
        response = self.client.get(self.url, {"format": "html"})
        self.assertEqual(response.status_code, 200)
        try:
            content = "".join([s.decode("utf-8") for s in response.streaming_content])
        except AttributeError:
            content = response.content
        df = pd.read_html(content)[0].fillna("")
        # Add 1 to self.num_records for the header row
        self.assertEqual(len(df), self.num_records + self.existing_countries + 1)

    def test_xml(self):
        response = self.client.get(self.url, {"format": "xml"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content)
        # No need to parse XML. Encoding is entirely done by package djangorestframework-xml, our code is not involved.


class MismatchedKeysRendererTestCase(SimpleTestCase):
    """
    Test that the tabular renderers align columns when rows have different keys.

    Serializers omit read-only fields whose dotted source can't be resolved, so
    rows in the same response don't necessarily have the same keys.
    """

    data = [
        {"id": 1, "strategy_type": "CropProduction", "season": 3, "season_name": "Main", "quantity": 10},
        {"id": 2, "strategy_type": "FoodPurchase", "quantity": 20},
        {"id": 3, "strategy_type": "OtherCashIncome", "quantity": 30, "extra_field": "x"},
    ]
    expected = pd.DataFrame(
        [
            [1, "CropProduction", "3", "Main", 10, ""],
            [2, "FoodPurchase", "", "", 20, ""],
            [3, "OtherCashIncome", "", "", 30, "x"],
        ],
        columns=["id", "strategy_type", "season", "season_name", "quantity", "extra_field"],
    )

    def test_csv(self):
        """
        Test that the CSV has a column for every key, and empty values for missing keys.
        """
        content = FormattedCSVRenderer().render(self.data, renderer_context={"response": HttpResponse()})
        content = content.decode("utf-8-sig")
        lines = content.splitlines()
        self.assertEqual(len(lines), 4)
        self.assertTrue(all(line.count(",") == 5 for line in lines))
        df = pd.read_csv(StringIO(content), dtype={"season": str, "season_name": str}).fillna("")
        pd.testing.assert_frame_equal(df, self.expected)

    def test_csv_empty(self):
        """
        Test that an empty dataset renders an empty CSV.
        """
        content = FormattedCSVRenderer().render([], renderer_context={"response": HttpResponse()})
        self.assertEqual(content.decode("utf-8-sig"), "")

    def test_html(self):
        """
        Test that the HTML table has a column for every key, and empty cells for missing keys.
        """
        content = HtmlTableRenderer().render(self.data).decode("utf-8")
        # The renderer's nested table markup means that pandas reads the header as a data row
        df = pd.read_html(StringIO(content), keep_default_na=False)[0].astype(str)
        self.assertEqual(df.iloc[0].tolist(), self.expected.columns.tolist())
        self.assertEqual(df.iloc[1:].values.tolist(), self.expected.astype(str).values.tolist())
