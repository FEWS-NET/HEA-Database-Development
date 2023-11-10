import json

from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from common.models import ClassifiedProduct, Country, Currency, UnitOfMeasure

from .factories import (
    ClassifiedProductFactory,
    CountryFactory,
    CurrencyFactory,
    UnitOfMeasureFactory,
    UserFactory,
)


class CountryViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.existing_countries = Country.objects.count()
        cls.country1 = CountryFactory()
        cls.country2 = CountryFactory()
        cls.country3 = CountryFactory()
        cls.country4 = CountryFactory()

    def setUp(self):
        self.url = reverse("country-list")

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 4 + self.existing_countries)

    def test_filter_by_single_country_code(self):
        response = self.client.get(self.url, {"country_code": self.country1.iso3166a2})
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 1)
        self.assertEqual(self.country1.iso3166a2, result[0]["iso3166a2"])

    def test_filter_by_multiple_country_codes(self):
        parameters = {"country_code": [self.country1.iso3166a2, self.country2.iso3166a2]}
        response = self.client.get(self.url, parameters)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(set(parameters["country_code"])), 2)
        self.assertEqual(len(result), 2)

    def test_filter_by_multiple_country_names(self):
        parameters = {"country": [self.country1.iso_en_name, self.country2.iso_en_name]}
        response = self.client.get(self.url, parameters)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(set(parameters["country"])), 2)
        self.assertEqual(len(result), 2)

    def test_filter_by_multiple_country_codes_and_names(self):
        parameters = {
            "country_code": [self.country1.iso3166a2, self.country2.iso3166a2],
            "country": [self.country2.iso_en_name, self.country4.iso_en_name],
        }
        response = self.client.get(self.url, parameters)
        self.assertEqual(len(set(parameters["country_code"])), 2)
        self.assertEqual(len(set(parameters["country"])), 2)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        # must return only one country which matches both of the specified criteria
        self.assertEqual(len(result), 1)

    def test_search_by_country_code(self):
        response = self.client.get(self.url, {"search": self.country1.iso3166a2})
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 1)

    def test_search_by_country_name(self):
        response = self.client.get(self.url, {"search": self.country1.iso_en_name})
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 1)


class CurrencyViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.existing_currencies = Currency.objects.all().count()
        cls.currency1 = CurrencyFactory()
        cls.currency2 = CurrencyFactory()
        cls.currency3 = CurrencyFactory()

    def setUp(self):
        self.url = reverse("currency-list")

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), self.existing_currencies + 3)

    def test_filter_by_single_currency_code(self):
        response = self.client.get(self.url, {"currency_code": self.currency1.iso4217a3})
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 1)
        self.assertEqual(self.currency1.iso4217a3, json.loads(response.content)[0]["iso4217a3"])

    def test_filter_by_multiple_currency_codes(self):
        parameters = {"currency_code": [self.currency1.iso4217a3, self.currency2.iso4217a3]}
        response = self.client.get(self.url, parameters)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(set(parameters["currency_code"])), 2)
        self.assertEqual(len(result), 2)


class UnitOfMeasureViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.existing_units = UnitOfMeasure.objects.all().count()
        cls.unit1 = UnitOfMeasureFactory(conversion=None)
        cls.unit2 = UnitOfMeasureFactory(conversion=None)
        cls.unit3 = UnitOfMeasureFactory(conversion=None)

        cls.unit4 = UnitOfMeasureFactory(unit_type=UnitOfMeasure.VOLUME, conversion=None)
        cls.unit5 = UnitOfMeasureFactory(unit_type=UnitOfMeasure.VOLUME, conversion=None)
        cls.unit6 = UnitOfMeasureFactory(unit_type=UnitOfMeasure.VOLUME, conversion=None)

    def setUp(self):
        self.url = reverse("unitofmeasure-list")

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), self.existing_units + 6)

    def test_list_returns_filtered_data_by_unit_type(self):
        response = self.client.get(self.url, {"unit_type": UnitOfMeasure.VOLUME})
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 3)


class ClassifiedProductViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.existing_products = ClassifiedProduct.objects.all().count()
        cls.product1 = ClassifiedProductFactory()
        cls.product2 = ClassifiedProductFactory()
        cls.superuser = UserFactory(is_superuser=True, is_staff=True, is_active=True)

    def setUp(self):
        self.url = reverse("classifiedproduct-list")

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), ClassifiedProduct.objects.count())

    def test_filter_by_cpcv2(self):
        response = self.client.get(self.url, {"cpcv2": self.product1.cpcv2})
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["cpcv2"], self.product1.cpcv2)

    def test_filter_by_description(self):
        response = self.client.get(self.url, {"description": self.product2.description})
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["description"], self.product2.description)

    def test_filter_by_common_name(self):
        response = self.client.get(self.url, {"common_name": self.product2.common_name})
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["common_name"], self.product2.common_name)

    def test_search_fields(self):
        response = self.client.get(self.url, {"search": "Product Description"})
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 2)
        response = self.client.get(self.url, {"search": self.product1.common_name})
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 1)
