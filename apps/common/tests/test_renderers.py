from io import StringIO

import pandas as pd
from django.http import HttpResponse
from django.test import SimpleTestCase
from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory, APITestCase

from common.models import Country
from common.renderers import FormattedCSVRenderer, HtmlTableRenderer, get_fieldnames

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


class ExampleSerializer(serializers.Serializer):
    """
    Serializer with a write-only field, used to test the column order from a view's serializer.
    """

    id = serializers.IntegerField()
    season = serializers.IntegerField(read_only=True)
    password = serializers.CharField(write_only=True)
    quantity = serializers.IntegerField()


class GetFieldnamesTestCase(SimpleTestCase):
    """
    Test that get_fieldnames uses the serializer fields, and falls back to the keys in the data.
    """

    def get_renderer_context(self, status_code: int = 200) -> dict:
        """
        Return a renderer_context for a view that uses ExampleSerializer.
        """
        view = GenericAPIView(serializer_class=ExampleSerializer, format_kwarg=None)
        view.request = Request(APIRequestFactory().get("/"))
        return {"view": view, "response": HttpResponse(status=status_code)}

    def test_serializer_fields(self):
        """
        Test that the columns are the readable serializer fields, followed by any other keys in the data.
        """
        data = [{"quantity": 1, "id": 1}, {"id": 2, "quantity": 2, "aggregate": 3}]
        self.assertEqual(get_fieldnames(data, self.get_renderer_context()), ["id", "season", "quantity", "aggregate"])

    def test_serializer_fields_without_data(self):
        """
        Test that the columns are the serializer fields when there are no rows.
        """
        self.assertEqual(get_fieldnames([], self.get_renderer_context()), ["id", "season", "quantity"])

    def test_error_response(self):
        """
        Test that the columns are the keys in the data for an error response.
        """
        data = [{"detail": "Not found."}]
        self.assertEqual(get_fieldnames(data, self.get_renderer_context(404)), ["detail"])

    def test_data_not_from_serializer(self):
        """
        Test that the columns are the keys in the data if they don't match the serializer, e.g. for a paginated response.
        """
        data = [{"count": 1, "next": None, "previous": None, "results": []}]
        self.assertEqual(get_fieldnames(data, self.get_renderer_context()), ["count", "next", "previous", "results"])

    def test_no_view(self):
        """
        Test that the columns are the keys from all the rows if there is no view.
        """
        data = [{"id": 1}, {"id": 2, "quantity": 2}]
        self.assertEqual(get_fieldnames(data, {}), ["id", "quantity"])
        self.assertEqual(get_fieldnames(data), ["id", "quantity"])
