import json

from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from metadata.test.factories import (
    HazardCategoryFactory,
    LivelihoodCategoryFactory,
    SeasonalActivityTypeFactory,
    SeasonFactory,
    WealthCategoryFactory,
    WealthCharacteristicFactory,
)


class DimensionViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.livelihoodcategory1 = LivelihoodCategoryFactory()
        cls.livelihoodcategory2 = LivelihoodCategoryFactory()
        cls.livelihoodcategory3 = LivelihoodCategoryFactory()

        cls.hazardcategory1 = HazardCategoryFactory()
        cls.hazardcategory2 = HazardCategoryFactory()

        cls.wealthcategory1 = WealthCategoryFactory()
        cls.wealthcategory2 = WealthCategoryFactory()
        cls.wealthcategory3 = WealthCategoryFactory()

        cls.seasonalactivitytype1 = SeasonalActivityTypeFactory()
        cls.seasonalactivitytype2 = SeasonalActivityTypeFactory()

        cls.wealthcharacteristic1 = WealthCharacteristicFactory()
        cls.wealthcharacteristic2 = WealthCharacteristicFactory()
        cls.wealthcharacteristic3 = WealthCharacteristicFactory()

    def setUp(self) -> None:
        self.livelihoodcategory_url = reverse("livelihoodcategory-list")
        self.hazardcategory_url = reverse("hazardcategory-list")
        self.wealthcategory_url = reverse("wealthcategory-list")
        self.seasonalactivitytype_url = reverse("seasonalactivitytype-list")
        self.wealthcharacteristic_url = reverse("wealthcharacteristic-list")

    # LivelihoodCategory Tests
    def test_livelihoodcategory_list_returns_all_records(self):
        response = self.client.get(self.livelihoodcategory_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

    def test_livelihoodcategory_search_by_code(self):
        response = self.client.get(self.livelihoodcategory_url, {"search": self.livelihoodcategory2.code})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(self.livelihoodcategory2.code, json.loads(response.content)[0]["code"])

    def test_livelihoodcategory_search_by_name(self):
        response = self.client.get(self.livelihoodcategory_url, {"search": self.livelihoodcategory3.name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(self.livelihoodcategory3.code, json.loads(response.content)[0]["code"])

    def test_livelihoodcategory_filter_by_name(self):
        response = self.client.get(self.livelihoodcategory_url, {"name": self.livelihoodcategory1.name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(self.livelihoodcategory1.code, json.loads(response.content)[0]["code"])

    # HazardCategory Tests
    def test_hazardcategory_list_returns_all_records(self):
        response = self.client.get(self.hazardcategory_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_hazardcategory_search_by_code(self):
        response = self.client.get(self.hazardcategory_url, {"search": self.hazardcategory1.code})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(self.hazardcategory1.code, json.loads(response.content)[0]["code"])

    def test_hazardcategory_search_by_name(self):
        response = self.client.get(self.hazardcategory_url, {"search": self.hazardcategory2.name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(self.hazardcategory2.code, json.loads(response.content)[0]["code"])

    def test_hazardcategory_filter_by_name(self):
        response = self.client.get(self.hazardcategory_url, {"name": self.hazardcategory2.name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(self.hazardcategory2.code, json.loads(response.content)[0]["code"])

    # WealthCategory Tests
    def test_wealthcategory_list_returns_all_records(self):
        response = self.client.get(self.wealthcategory_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

    def test_wealthcategory_search_by_code(self):
        response = self.client.get(self.wealthcategory_url, {"search": self.wealthcategory1.code})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(self.wealthcategory1.code, json.loads(response.content)[0]["code"])

    def test_wealthcategory_search_by_name(self):
        response = self.client.get(self.wealthcategory_url, {"search": self.wealthcategory2.name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(self.wealthcategory2.code, json.loads(response.content)[0]["code"])

    def test_wealthcategory_filter_by_name(self):
        response = self.client.get(self.wealthcategory_url, {"name": self.wealthcategory3.name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(self.wealthcategory3.code, json.loads(response.content)[0]["code"])

    # SeasonalActivityType Tests
    def test_seasonalactivitytype_list_returns_all_records(self):
        response = self.client.get(self.seasonalactivitytype_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_seasonalactivitytype_search_by_code(self):
        response = self.client.get(self.seasonalactivitytype_url, {"search": self.seasonalactivitytype1.code})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(self.seasonalactivitytype1.code, json.loads(response.content)[0]["code"])

    def test_seasonalactivitytype_search_by_name(self):
        response = self.client.get(self.seasonalactivitytype_url, {"search": self.seasonalactivitytype2.name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(self.seasonalactivitytype2.code, json.loads(response.content)[0]["code"])

    def test_seasonalactivitytype_filter_by_name(self):
        response = self.client.get(self.seasonalactivitytype_url, {"name": self.seasonalactivitytype1.name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(self.seasonalactivitytype1.code, json.loads(response.content)[0]["code"])

    def test_seasonalactivitytype_filter_by_activity_category(self):
        response = self.client.get(
            self.seasonalactivitytype_url, {"activity_category": self.seasonalactivitytype1.activity_category}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(self.seasonalactivitytype1.code, json.loads(response.content)[0]["code"])

    # WealthCharacteristic Tests
    def test_wealthcharacteristic_list_returns_all_records(self):
        response = self.client.get(self.wealthcharacteristic_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

    def test_wealthcharacteristic_search_by_code(self):
        response = self.client.get(self.wealthcharacteristic_url, {"search": self.wealthcharacteristic1.code})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(self.wealthcharacteristic1.code, json.loads(response.content)[0]["code"])

    def test_wealthcharacteristic_search_by_name(self):
        response = self.client.get(self.wealthcharacteristic_url, {"search": self.wealthcharacteristic2.name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(self.wealthcharacteristic2.code, json.loads(response.content)[0]["code"])

    def test_wealthcharacteristic_filter_by_name(self):
        response = self.client.get(self.wealthcharacteristic_url, {"name": self.wealthcharacteristic3.name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(self.wealthcharacteristic3.code, json.loads(response.content)[0]["code"])

    def test_wealthcharacteristic_filter_by_variable_type(self):
        response = self.client.get(
            self.wealthcharacteristic_url, {"variable_type": self.wealthcharacteristic1.variable_type}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(self.wealthcharacteristic1.code, json.loads(response.content)[0]["code"])


class SeasonViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.season1 = SeasonFactory()
        cls.season2 = SeasonFactory()
        cls.season3 = SeasonFactory()

    def setUp(self) -> None:
        self.url = reverse("season-list")

    def test_season_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

    def test_season_filter_by_country(self):
        response = self.client.get(self.url, {"country": self.season1.country.iso3166a2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(self.season1.name, json.loads(response.content)[0]["name"])

    def test_season_search_by_name(self):
        response = self.client.get(self.url, {"search": self.season1.name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(self.season1.name, json.loads(response.content)[0]["name"])

    def test_season_filter_by_season_type(self):
        response = self.client.get(self.url, {"season_type": self.season3.season_type})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(self.season3.name, json.loads(response.content)[0]["name"])
