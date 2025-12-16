import importlib
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
    UserProfileFactory,
)


class CountryViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.existing_countries = Country.objects.count()
        cls.country1 = CountryFactory()
        cls.country2 = CountryFactory()
        cls.country3 = CountryFactory()
        cls.country4 = CountryFactory()

        # import baseline factory to avoid circular depdnecies
        module = importlib.import_module("baseline.tests.factories")
        WealthGroupFactory = getattr(module, "WealthGroupFactory")

        cls.wealth_group1 = WealthGroupFactory(livelihood_zone_baseline__livelihood_zone__country=cls.country1)

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

    def test_filter_by_has_wealthgroups(self):
        # test by has_wealthgroups set to true
        filter_data = {"has_wealthgroups": True}
        response = self.client.get(self.url, filter_data)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 1)
        self.assertEqual(self.country1.name, result[0]["name"])
        self.assertEqual(self.wealth_group1.livelihood_zone_baseline.livelihood_zone.country, self.country1)

        # test by has_wealthgroups set to false
        filter_data = {"has_wealthgroups": False}
        response = self.client.get(self.url, filter_data)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertNotIn(self.country1.iso3166a2, result)


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
        cls.existing_volume_units = UnitOfMeasure.objects.filter(unit_type=UnitOfMeasure.VOLUME).count()
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
        self.assertEqual(len(result), self.existing_volume_units + 3)


class ClassifiedProductViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.existing_products = ClassifiedProduct.objects.all().count()
        cls.product1 = ClassifiedProductFactory()
        cls.product2 = ClassifiedProductFactory()
        cls.superuser = UserFactory(is_superuser=True, is_staff=True, is_active=True)

        cls.country_a = CountryFactory(
            iso3166a2="AA",
            iso3166a3="AAA",
            iso3166n3=911,
            iso_en_ro_name="A Country",
            iso_en_name="AA Country",
            name="AA Country",
        )
        cls.country_b = CountryFactory(
            iso3166a2="BB",
            iso3166a3="BBB",
            iso3166n3=912,
            iso_en_ro_name="B Country",
            iso_en_name="BB Country",
            name="BB Country",
        )

        # import baseline factory to avoid circular depdnecies
        module = importlib.import_module("baseline.tests.factories")
        WealthGroupFactory = getattr(module, "WealthGroupFactory")
        LivelihoodStrategyFactory = getattr(module, "LivelihoodStrategyFactory")
        LivelihoodZoneBaselineFactory = getattr(module, "LivelihoodZoneBaselineFactory")

        livelihood_zone_baseline = LivelihoodZoneBaselineFactory(livelihood_zone__country=cls.country_a)
        WealthGroupFactory(livelihood_zone_baseline=livelihood_zone_baseline)
        cls.livelihood_strategy1 = LivelihoodStrategyFactory(
            livelihood_zone_baseline=livelihood_zone_baseline, product=cls.product1
        )

    def setUp(self):
        self.url = reverse("classifiedproduct-list")

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), ClassifiedProduct.objects.count())

    def test_filter_by_cpc(self):
        response = self.client.get(self.url, {"cpc": self.product1.cpc})
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["cpc"], self.product1.cpc)

    def test_filter_by_description(self):
        response = self.client.get(self.url, {"description_en": self.product2.description})
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["description"], self.product2.description)

    def test_filter_by_common_name(self):
        response = self.client.get(self.url, {"common_name_en": self.product2.common_name})
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["common_name"], self.product2.common_name)
        self.assertEqual(result[0]["display_name"], self.product2.display_name())

    def test_search_fields(self):
        response = self.client.get(self.url, {"search": "Product Description"})
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 2)
        response = self.client.get(self.url, {"search": self.product1.common_name})
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 1)

    def test_filter_by_has_wealthgroups(self):
        # test by has_wealthgroups set to true
        filter_data = {"has_wealthgroups": True}
        response = self.client.get(self.url, filter_data)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 1)
        self.assertEqual(self.product1.cpc, result[0]["cpc"])
        self.assertEqual(self.livelihood_strategy1.product, self.product1)

        # test by has_wealthgroups set to false
        filter_data = {"has_wealthgroups": False}
        response = self.client.get(self.url, filter_data)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertNotIn(self.product1.cpc, result)

    def test_filter_by_country(self):
        # test filter by country
        filter_data = {"country": self.country_a.iso3166a2}
        response = self.client.get(self.url, filter_data)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 1)
        self.assertEqual(self.product1.cpc, result[0]["cpc"])

        filter_data = {"country": self.country_b.iso3166a2}
        response = self.client.get(self.url, filter_data)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 0)

        filter_data = {"country": self.country_a.iso3166a2.lower()}
        response = self.client.get(self.url, filter_data)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 1)
        self.assertEqual(self.product1.cpc, result[0]["cpc"])


class UserViewSetTestCase(APITestCase):
    def setUp(self):
        self.user = UserFactory(username="testuser", password="password123", first_name="Test", last_name="User")
        self.client.force_authenticate(user=self.user)
        self.url = reverse("user-list")

    def test_get_current_user(self):
        response = self.client.get(f"{self.url}current/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["username"], self.user.username)

    def test_search_users(self):
        UserFactory(username="searchuser", password="password123", first_name="Search", last_name="User")
        response = self.client.get(self.url, {"search": "Search"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["first_name"], "Search")


class UserProfileViewSetTestCase(APITestCase):
    def setUp(self):
        self.user = UserFactory(username="testuser", password="password123")
        self.profile = UserProfileFactory(user=self.user)
        self.client.force_authenticate(user=self.user)
        self.url = reverse("userprofile-list")

    def test_get_current_profile(self):
        response = self.client.get(f"{self.url}current/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"], self.user.id)

    def test_superuser_access_profiles(self):
        superuser = UserFactory(username="admin", password="password123", is_superuser=True)
        self.client.force_authenticate(user=superuser)
        response = self.client.get(f"{self.url}{self.profile.user.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["user"], self.user.id)

    def test_queryset_filters(self):
        other_user = UserFactory(username="otheruser", password="password123")
        UserProfileFactory(user=other_user)

        # Current user profile only
        response = self.client.get(f"{self.url}?pk=current")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["user"], self.user.id)

        # Superuser access to all profiles
        superuser = UserFactory(username="admin", password="password123", is_superuser=True)
        self.client.force_authenticate(user=superuser)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 2)
