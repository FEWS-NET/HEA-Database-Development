from io import StringIO

import pandas as pd
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from .factories import CountryFactory


class RendererTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [CountryFactory() for _ in range(cls.num_records)]

    def setUp(self):
        self.url = reverse("country-list")

    def test_json(self):
        response = self.client.get(self.url, {"format": "json"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_csv(self):
        response = self.client.get(self.url, {"format": "csv"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"][:8], "text/csv")
        try:
            content = "".join([s.decode("utf-8") for s in response.streaming_content])
        except AttributeError:
            content = response.content.decode("utf-8")
        df = pd.read_csv(StringIO(content)).fillna("")
        self.assertEqual(len(df), self.num_records)

    def test_html(self):
        response = self.client.get(self.url, {"format": "html"})
        self.assertEqual(response.status_code, 200)
        try:
            content = "".join([s.decode("utf-8") for s in response.streaming_content])
        except AttributeError:
            content = response.content
        df = pd.read_html(content)[0].fillna("")
        # Add 1 to self.num_records for the header row
        self.assertEqual(len(df), self.num_records + 1)

    def test_xml(self):
        response = self.client.get(self.url, {"format": "xml"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.content)
        # No need to parse XML. Encoding is entirely done by package djangorestframework-xml, our code is not involved.
