import importlib
import json

from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from metadata.models import (
    HazardCategory,
    LivelihoodCategory,
    SeasonalActivityType,
    WealthCharacteristic,
    WealthGroupCategory,
)

from .factories import (
    HazardCategoryFactory,
    LivelihoodCategoryFactory,
    SeasonalActivityTypeFactory,
    SeasonFactory,
    WealthCharacteristicFactory,
    WealthGroupCategoryFactory,
)


class ReferenceDataViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.livelihoodcategory1 = LivelihoodCategoryFactory()
        cls.livelihoodcategory2 = LivelihoodCategoryFactory()
        cls.livelihoodcategory3 = LivelihoodCategoryFactory()

        cls.hazardcategory1 = HazardCategoryFactory()
        cls.hazardcategory2 = HazardCategoryFactory()

        cls.WealthGroupCategory1 = WealthGroupCategoryFactory()
        cls.WealthGroupCategory2 = WealthGroupCategoryFactory()
        cls.WealthGroupCategory3 = WealthGroupCategoryFactory()

        cls.seasonalactivitytype1 = SeasonalActivityTypeFactory()
        cls.seasonalactivitytype2 = SeasonalActivityTypeFactory()

        cls.wealthcharacteristic1 = WealthCharacteristicFactory()
        cls.wealthcharacteristic2 = WealthCharacteristicFactory()
        cls.wealthcharacteristic3 = WealthCharacteristicFactory()

    def setUp(self) -> None:
        self.livelihoodcategory_url = reverse("livelihoodcategory-list")
        self.hazardcategory_url = reverse("hazardcategory-list")
        self.wealthgroupcategory_url = reverse("wealthgroupcategory-list")
        self.seasonalactivitytype_url = reverse("seasonalactivitytype-list")
        self.wealthcharacteristic_url = reverse("wealthcharacteristic-list")

    def test_list_returns_all_records(self, filter_data = {}):
        # LivelihoodCategory
        response = self.client.get(self.livelihoodcategory_url)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 3)

        # HazardCategory
        response = self.client.get(self.hazardcategory_url)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 2)

        # WealthGroupCategory
        filter_data = {"has_wealthgroups": "all"}
        response = self.client.get(self.wealthgroupcategory_url, filter_data)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 3)

        # SeasonalActivityType
        response = self.client.get(self.seasonalactivitytype_url)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 2)

        # WealthCharacteristic
        response = self.client.get(self.wealthcharacteristic_url)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 3)

    def _test_search_by_code(self, model_cls, filter_data = {}):
        # Test search by code for each model
        url = reverse(f"{model_cls._meta.model_name}-list")
        # Sort queryset, so that test results are deterministic and don't depend on random ordering of query results.
        # WealthGroupCategoryFactory has single character codes, eg, P, which intermittently match other instances.
        # Likewise "Poor" matches "Very Poor". Max code is "VP" so shouldn't match other instances or fields, and
        # because the test is now deterministic, this will reliably fail if a factory change breaks this assumption.
        sought_instance = model_cls.objects.order_by("-code").first()
        search_filter =  {"search": sought_instance.code, ** filter_data}
        response = self.client.get(url, search_filter)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(len(result), 1, f"Code {sought_instance.code}")
        self.assertEqual(sought_instance.code, result[0]["code"])

    def _test_search_by_name(self, model_cls, filter_data = {}):
        # Test search by name for each model
        url = reverse(f"{model_cls._meta.model_name}-list")
        sought_instance = model_cls.objects.order_by("-code").first()
        search_filter =  {"search": sought_instance.name_pt, ** filter_data}
        response = self.client.get(url, search_filter)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(len(result), 1)
        self.assertEqual(sought_instance.code, result[0]["code"])

    def _test_filter_by_name(self, model_cls, filter_data = {}):
        # Test filter by name for each model
        url = reverse(f"{model_cls._meta.model_name}-list")
        sought_instance = model_cls.objects.order_by("-code").first()
        search_filter =  {"search": sought_instance.name_pt, ** filter_data}
        response = self.client.get(url, search_filter)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(len(result), 1)
        self.assertEqual(sought_instance.code, result[0]["code"])

    def test_search_and_filter(self):
        models_to_test = [
            LivelihoodCategory,
            HazardCategory,
            WealthGroupCategory,
            SeasonalActivityType,
            WealthCharacteristic,
        ]

        for model_cls in models_to_test:
            filter_data = {}
            if model_cls == WealthGroupCategory:
                filter_data = {"has_wealthgroups": "all"}
            with self.subTest(model=model_cls):
                self._test_search_by_code(model_cls, filter_data)
                self._test_search_by_name(model_cls, filter_data)
                self._test_filter_by_name(model_cls, filter_data)

    def test_seasonalactivitytype_filter_by_activity_category(self):
        response = self.client.get(
            self.seasonalactivitytype_url, {"activity_category": self.seasonalactivitytype1.activity_category}
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 1)
        self.assertEqual(self.seasonalactivitytype1.code, result[0]["code"])

    def test_wealthcharacteristic_filter_by_variable_type(self):
        response = self.client.get(
            self.wealthcharacteristic_url, {"variable_type": self.wealthcharacteristic1.variable_type}
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 1)
        self.assertEqual(self.wealthcharacteristic1.code, result[0]["code"])


class SeasonViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.season1 = SeasonFactory()
        cls.season2 = SeasonFactory()
        cls.season3 = SeasonFactory(start=200, end=260)

    def setUp(self) -> None:
        self.url = reverse("season-list")

    def test_season_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 3)

    def test_season_filter_by_country(self):
        response = self.client.get(self.url, {"country": self.season1.country.iso3166a2})
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 1)
        self.assertEqual(self.season1.name, result[0]["name"])

    def test_season_search_by_name(self):
        response = self.client.get(self.url, {"search": self.season1.name})
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 1)
        self.assertEqual(self.season1.name, result[0]["name"])

    def test_season_filter_by_season_type(self):
        response = self.client.get(self.url, {"season_type": self.season3.season_type})
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 1)
        self.assertEqual(self.season3.name, result[0]["name"])

    def test_start_month_and_end_month_fields(self):
        response = self.client.get(f"{self.url}{self.season3.pk}/")
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertTrue(len(result), 1)
        self.assertEqual(self.season3.name, result["name"])
        # start date of 200 corresponds to July (7) and 260 is Sept (9)
        self.assertIn("start_month", result)
        self.assertIn("end_month", result)
        self.assertEqual(result["start_month"], 7)
        self.assertEqual(result["end_month"], 9)


class WealthGroupCategoryTestCase(APITestCase):
    def setUp(self):
        self.url = reverse("wealthgroupcategory-list")
        # Create categories
        self.cat_with_groups = WealthGroupCategoryFactory()
        self.cat_without_groups = WealthGroupCategoryFactory()

        # import baseline factory to avoid circular depdnecies
        module = importlib.import_module("baseline.tests.factories")
        WealthGroupFactory = getattr(module, "WealthGroupFactory")

        WealthGroupFactory(wealth_group_category=self.cat_with_groups)

    def test_filter_by_has_wealthgroups(self):
        # test by has_wealthgroups set to true
        filter_data = {"has_wealthgroups": "true"}
        response = self.client.get(self.url, filter_data)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 1)
        self.assertEqual(self.cat_with_groups.name, result[0]["name"])

        # test by has_wealthgroups set to false
        filter_data = {"has_wealthgroups": "false"}
        response = self.client.get(self.url, filter_data)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 1)
        self.assertEqual(self.cat_without_groups.name, result[0]["name"])

        # test by has_wealthgroups set to all
        filter_data = {"has_wealthgroups": "all"}
        response = self.client.get(self.url, filter_data)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 2)

        # test by has_wealthgroups set empty value for default filter
        filter_data = {"has_wealthgroups": ""}
        response = self.client.get(self.url, filter_data)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(result), 1)
        self.assertEqual(self.cat_with_groups.name, result[0]["name"])
