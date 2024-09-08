import logging
import warnings
from io import StringIO

import pandas as pd
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase

from common.fields import translation_fields

from .factories import (
    BaselineLivelihoodActivityFactory,
    BaselineWealthGroupFactory,
    ButterProductionFactory,
    CommunityCropProductionFactory,
    CommunityFactory,
    CommunityLivestockFactory,
    CommunityWealthGroupFactory,
    CopingStrategyFactory,
    CropProductionFactory,
    EventFactory,
    ExpandabilityFactorFactory,
    FishingFactory,
    FoodPurchaseFactory,
    HazardFactory,
    HuntingFactory,
    LivelihoodActivityFactory,
    LivelihoodProductCategoryFactory,
    LivelihoodStrategyFactory,
    LivelihoodZoneBaselineFactory,
    LivelihoodZoneFactory,
    LivestockSaleFactory,
    MarketPriceFactory,
    MeatProductionFactory,
    MilkProductionFactory,
    OtherCashIncomeFactory,
    OtherPurchaseFactory,
    PaymentInKindFactory,
    ReliefGiftOtherFactory,
    ResponseLivelihoodActivityFactory,
    SeasonalActivityFactory,
    SeasonalActivityOccurrenceFactory,
    SeasonalProductionPerformanceFactory,
    SourceOrganizationFactory,
    WealthGroupCharacteristicValueFactory,
    WealthGroupFactory,
    WildFoodGatheringFactory,
)

warnings.filterwarnings("error", r"Forbidden: .*")


class SourceOrganizationViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [SourceOrganizationFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("sourceorganization-list")
        self.url_get = lambda n: reverse("sourceorganization-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        # assertCountEqual checks elements match in any order
        expected_fields = (
            "id",
            "name",
            "full_name",
            "description",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"SourceOrganization: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["name"] + "X"
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"name": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("name", response.json())
        self.assertEqual(response.json()["name"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "name": self.data[0].name,
                "full_name": self.data[0].full_name,
                "description": self.data[0].description,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].name,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].name + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class LivelihoodZoneViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [LivelihoodZoneFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("livelihoodzone-list")
        self.url_get = lambda n: reverse("livelihoodzone-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "code",
            "alternate_code",
            "name",
            "description",
            "country",
            "country_name",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"LivelihoodZone: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"modified": self.data[1].modified})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "code": self.data[0].code,
                "name": self.data[0].name,
                "description": self.data[0].description,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].code,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].code + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class LivelihoodZoneBaselineViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [LivelihoodZoneBaselineFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("livelihoodzonebaseline-list")
        self.url_get = lambda n: reverse("livelihoodzonebaseline-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "name",
            "description",
            "source_organization",
            "source_organization_name",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "geography",
            "main_livelihood_category",
            "bss",
            "bss_language",
            *translation_fields("profile_report"),
            "reference_year_start_date",
            "reference_year_end_date",
            "valid_from_date",
            "valid_to_date",
            "population_source",
            "population_estimate",
            "currency",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            "LivelihoodZoneBaseline: "
            f"Fields expected: {expected_fields}. "
            f"Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["geography"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"geography": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("geography", response.json())
        self.assertEqual(response.json()["geography"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "population_source": self.data[0].population_source,
                "population_estimate": self.data[0].population_estimate,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        baseline = LivelihoodZoneBaselineFactory(population_source="Government statistics agency")
        response = self.client.get(
            self.url,
            {
                "search": baseline.population_source,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["population_source"], baseline.population_source)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].population_source + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)

    def test_geojson_format(self):
        response = self.client.get(self.url, {"format": "geojson"})
        self.assertEqual(response.status_code, 200)
        # Ensure Content-Type is 'application/geo+json'
        self.assertEqual(response["Content-Type"], "application/geo+json")

        json_response = response.json()
        self.assertEqual(json_response["type"], "FeatureCollection")
        # Check if 'features' is present in the response
        self.assertIn("features", json_response)

        self.assertEqual(len(json_response["features"]), self.num_records)
        feature = json_response["features"][0]
        self.assertIn("geometry", feature)
        self.assertIn("properties", feature)


class LivelihoodProductCategoryViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [LivelihoodProductCategoryFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("livelihoodproductcategory-list")
        self.url_get = lambda n: reverse("livelihoodproductcategory-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "product",
            "product_common_name",
            "product_description",
            "basket",
            "basket_name",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            "LivelihoodProductCategory: "
            f"Fields expected: {expected_fields}. "
            f"Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["basket"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"basket": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("basket", response.json())
        self.assertEqual(response.json()["basket"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "livelihood_zone_baseline": self.data[0].livelihood_zone_baseline.pk,
                "product": self.data[0].product.pk,
                "basket": self.data[0].basket,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

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
        self.assertEqual(len(df), self.num_records + 1)


class CommunityViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [CommunityFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("community-list")
        self.url_get = lambda n: reverse("community-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "code",
            "name",
            "full_name",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country_code",
            "livelihood_zone_country_name",
            "geography",
            "aliases",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"Community: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["code"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"code": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("code", response.json())
        self.assertEqual(response.json()["code"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "name": self.data[0].name,
                "full_name": self.data[0].full_name,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].code,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].code + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class WealthGroupViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [WealthGroupFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("wealthgroup-list")
        self.url_get = lambda n: reverse("wealthgroup-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country_code",
            "livelihood_zone_country_name",
            "community",
            "community_name",
            "wealth_group_category",
            "percentage_of_households",
            "average_household_size",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"WealthGroup: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["percentage_of_households"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"percentage_of_households": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("percentage_of_households", response.json())
        self.assertEqual(response.json()["percentage_of_households"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "livelihood_zone_baseline": self.data[0].livelihood_zone_baseline.pk,
                "community": self.data[0].community.pk,
                "wealth_group_category": self.data[0].wealth_group_category.pk,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

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
        self.assertEqual(len(df), self.num_records + 1)


class BaselineWealthGroupViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [BaselineWealthGroupFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("baselinewealthgroup-list")
        self.url_get = lambda n: reverse("baselinewealthgroup-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country_code",
            "livelihood_zone_country_name",
            "wealth_group_category",
            "percentage_of_households",
            "average_household_size",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"BaselineWealthGroup: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["percentage_of_households"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"percentage_of_households": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("percentage_of_households", response.json())
        self.assertEqual(response.json()["percentage_of_households"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "livelihood_zone_baseline": self.data[0].livelihood_zone_baseline.pk,
                "wealth_group_category": self.data[0].wealth_group_category.pk,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

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
        self.assertEqual(len(df), self.num_records + 1)


class CommunityWealthGroupViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [CommunityWealthGroupFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("communitywealthgroup-list")
        self.url_get = lambda n: reverse("communitywealthgroup-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country_code",
            "livelihood_zone_country_name",
            "community",
            "community_name",
            "wealth_group_category",
            "percentage_of_households",
            "average_household_size",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            "CommunityWealthGroup: "
            f"Fields expected: {expected_fields}. "
            f"Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["percentage_of_households"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"percentage_of_households": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("percentage_of_households", response.json())
        self.assertEqual(response.json()["percentage_of_households"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "livelihood_zone_baseline": self.data[0].livelihood_zone_baseline.pk,
                "wealth_group_category": self.data[0].wealth_group_category.pk,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

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
        self.assertEqual(len(df), self.num_records + 1)


class WealthGroupCharacteristicValueViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [WealthGroupCharacteristicValueFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("wealthgroupcharacteristicvalue-list")
        self.url_get = lambda n: reverse("wealthgroupcharacteristicvalue-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "wealth_group",
            "wealth_group_label",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country_code",
            "livelihood_zone_country_name",
            "community",
            "community_name",
            "wealth_group_category",
            "wealth_group_category_name",
            "wealth_group_category_description",
            "wealth_characteristic",
            "wealth_characteristic_name",
            "wealth_characteristic_description",
            "value",
            "min_value",
            "max_value",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            "WealthGroupCharacteristicValue: "
            f"Fields expected: {expected_fields}. "
            f"Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch_validation(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(0)).json()["max_value"] + 0.1
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"value": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 400)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(0)).json()["min_value"] + 0.1
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"value": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("value", response.json())
        self.assertEqual(response.json()["value"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "wealth_group": self.data[0].wealth_group.pk,
                "wealth_characteristic": self.data[0].wealth_characteristic.pk,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

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
        self.assertEqual(len(df), self.num_records + 1)


class LivelihoodStrategyViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [LivelihoodStrategyFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("livelihoodstrategy-list")
        self.url_get = lambda n: reverse("livelihoodstrategy-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "strategy_type",
            "strategy_type_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_description",
            "currency",
            "additional_identifier",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"LivelihoodStrategy: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["strategy_type"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"strategy_type": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("strategy_type", response.json())
        self.assertEqual(response.json()["strategy_type"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "additional_identifier": self.data[0].additional_identifier,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].strategy_type,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].strategy_type + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class LivelihoodActivityViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [LivelihoodActivityFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("livelihoodactivity-list")
        self.url_get = lambda n: reverse("livelihoodactivity-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "livelihood_strategy",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "strategy_type",
            "strategy_type_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_description",
            "currency",
            "additional_identifier",
            "scenario",
            "scenario_label",
            "wealth_group",
            "wealth_group_label",
            "community",
            "community_name",
            "wealth_group_category",
            "wealth_group_category_name",
            "wealth_group_category_description",
            "wealth_group_percentage_of_households",
            "wealth_group_average_household_size",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "household_labor_provider",
            "household_labor_provider_label",
            "extra",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"LivelihoodActivity: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )
        self.assertEqual(response.json()["extra"], self.data[0].extra)

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["scenario"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"scenario": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("scenario", response.json())
        self.assertEqual(response.json()["scenario"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "quantity_produced": self.data[0].quantity_produced,
                "quantity_sold": self.data[0].quantity_sold,
                "quantity_other_uses": self.data[0].quantity_other_uses,
                "quantity_consumed": self.data[0].quantity_consumed,
                "price": self.data[0].price,
                "income": self.data[0].income,
                "expenditure": self.data[0].expenditure,
                "kcals_consumed": self.data[0].kcals_consumed,
                "percentage_kcals": self.data[0].percentage_kcals,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class BaselineLivelihoodActivityViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [BaselineLivelihoodActivityFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("baselinelivelihoodactivity-list")
        self.url_get = lambda n: reverse("baselinelivelihoodactivity-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "livelihood_strategy",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "strategy_type",
            "strategy_type_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_description",
            "currency",
            "additional_identifier",
            "household_labor_provider",
            "household_labor_provider_label",
            "scenario",
            "scenario_label",
            "wealth_group",
            "wealth_group_label",
            "community",
            "community_name",
            "wealth_group_category",
            "wealth_group_category_name",
            "wealth_group_category_description",
            "wealth_group_percentage_of_households",
            "wealth_group_average_household_size",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "extra",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            "BaselineLivelihoodActivity: "
            f"Fields expected: {expected_fields}. "
            f"Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["scenario"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"scenario": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("scenario", response.json())
        self.assertEqual(response.json()["scenario"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "quantity_produced": self.data[0].quantity_produced,
                "quantity_sold": self.data[0].quantity_sold,
                "quantity_other_uses": self.data[0].quantity_other_uses,
                "quantity_consumed": self.data[0].quantity_consumed,
                "price": self.data[0].price,
                "income": self.data[0].income,
                "expenditure": self.data[0].expenditure,
                "kcals_consumed": self.data[0].kcals_consumed,
                "percentage_kcals": self.data[0].percentage_kcals,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class ResponseLivelihoodActivityViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [ResponseLivelihoodActivityFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("responselivelihoodactivity-list")
        self.url_get = lambda n: reverse("responselivelihoodactivity-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "livelihood_strategy",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "strategy_type",
            "strategy_type_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_description",
            "currency",
            "additional_identifier",
            "household_labor_provider",
            "household_labor_provider_label",
            "scenario",
            "scenario_label",
            "wealth_group",
            "wealth_group_label",
            "community",
            "community_name",
            "wealth_group_category",
            "wealth_group_category_name",
            "wealth_group_category_description",
            "wealth_group_percentage_of_households",
            "wealth_group_average_household_size",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "extra",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            "ResponseLivelihoodActivity: "
            f"Fields expected: {expected_fields}. "
            f"Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["scenario"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"scenario": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("scenario", response.json())
        self.assertEqual(response.json()["scenario"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "quantity_produced": self.data[0].quantity_produced,
                "quantity_sold": self.data[0].quantity_sold,
                "quantity_other_uses": self.data[0].quantity_other_uses,
                "quantity_consumed": self.data[0].quantity_consumed,
                "price": self.data[0].price,
                "income": self.data[0].income,
                "expenditure": self.data[0].expenditure,
                "kcals_consumed": self.data[0].kcals_consumed,
                "percentage_kcals": self.data[0].percentage_kcals,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].strategy_type,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].strategy_type + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class MilkProductionViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [MilkProductionFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("milkproduction-list")
        self.url_get = lambda n: reverse("milkproduction-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "livelihood_strategy",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "strategy_type",
            "strategy_type_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_description",
            "currency",
            "additional_identifier",
            "household_labor_provider",
            "household_labor_provider_label",
            "scenario",
            "scenario_label",
            "wealth_group",
            "wealth_group_label",
            "community",
            "community_name",
            "wealth_group_category",
            "wealth_group_category_name",
            "wealth_group_category_description",
            "wealth_group_percentage_of_households",
            "wealth_group_average_household_size",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "milking_animals",
            "lactation_days",
            "daily_production",
            "type_of_milk_sold_or_other_uses",
            "extra",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"MilkProduction: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["scenario"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"scenario": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("scenario", response.json())
        self.assertEqual(response.json()["scenario"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "quantity_produced": self.data[0].quantity_produced,
                "quantity_sold": self.data[0].quantity_sold,
                "quantity_other_uses": self.data[0].quantity_other_uses,
                "quantity_consumed": self.data[0].quantity_consumed,
                "price": self.data[0].price,
                "income": self.data[0].income,
                "expenditure": self.data[0].expenditure,
                "kcals_consumed": self.data[0].kcals_consumed,
                "percentage_kcals": self.data[0].percentage_kcals,
                "milking_animals": self.data[0].milking_animals,
                "lactation_days": self.data[0].lactation_days,
                "daily_production": self.data[0].daily_production,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class ButterProductionViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [ButterProductionFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("butterproduction-list")
        self.url_get = lambda n: reverse("butterproduction-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "livelihood_strategy",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "strategy_type",
            "strategy_type_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_description",
            "currency",
            "additional_identifier",
            "household_labor_provider",
            "household_labor_provider_label",
            "scenario",
            "scenario_label",
            "wealth_group",
            "wealth_group_label",
            "community",
            "community_name",
            "wealth_group_category",
            "wealth_group_category_name",
            "wealth_group_category_description",
            "wealth_group_percentage_of_households",
            "wealth_group_average_household_size",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "extra",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"ButterProduction: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["scenario"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"scenario": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("scenario", response.json())
        self.assertEqual(response.json()["scenario"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "quantity_produced": self.data[0].quantity_produced,
                "quantity_sold": self.data[0].quantity_sold,
                "quantity_other_uses": self.data[0].quantity_other_uses,
                "quantity_consumed": self.data[0].quantity_consumed,
                "price": self.data[0].price,
                "income": self.data[0].income,
                "expenditure": self.data[0].expenditure,
                "kcals_consumed": self.data[0].kcals_consumed,
                "percentage_kcals": self.data[0].percentage_kcals,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class MeatProductionViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [MeatProductionFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("meatproduction-list")
        self.url_get = lambda n: reverse("meatproduction-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "livelihood_strategy",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "strategy_type",
            "strategy_type_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_description",
            "currency",
            "additional_identifier",
            "household_labor_provider",
            "household_labor_provider_label",
            "scenario",
            "scenario_label",
            "wealth_group",
            "wealth_group_label",
            "community",
            "community_name",
            "wealth_group_category",
            "wealth_group_category_name",
            "wealth_group_category_description",
            "wealth_group_percentage_of_households",
            "wealth_group_average_household_size",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "animals_slaughtered",
            "carcass_weight",
            "extra",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"MeatProduction: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["scenario"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"scenario": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("scenario", response.json())
        self.assertEqual(response.json()["scenario"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "quantity_produced": self.data[0].quantity_produced,
                "quantity_sold": self.data[0].quantity_sold,
                "quantity_other_uses": self.data[0].quantity_other_uses,
                "quantity_consumed": self.data[0].quantity_consumed,
                "price": self.data[0].price,
                "income": self.data[0].income,
                "expenditure": self.data[0].expenditure,
                "kcals_consumed": self.data[0].kcals_consumed,
                "percentage_kcals": self.data[0].percentage_kcals,
                "animals_slaughtered": self.data[0].animals_slaughtered,
                "carcass_weight": self.data[0].carcass_weight,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class LivestockSalesViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [LivestockSaleFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("livestocksale-list")
        self.url_get = lambda n: reverse("livestocksale-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "livelihood_strategy",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "strategy_type",
            "strategy_type_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_description",
            "currency",
            "additional_identifier",
            "household_labor_provider",
            "household_labor_provider_label",
            "scenario",
            "scenario_label",
            "wealth_group",
            "wealth_group_label",
            "community",
            "community_name",
            "wealth_group_category",
            "wealth_group_category_name",
            "wealth_group_category_description",
            "wealth_group_percentage_of_households",
            "wealth_group_average_household_size",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "extra",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"LivestockSales: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["scenario"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"scenario": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("scenario", response.json())
        self.assertEqual(response.json()["scenario"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "quantity_produced": self.data[0].quantity_produced,
                "quantity_sold": self.data[0].quantity_sold,
                "quantity_other_uses": self.data[0].quantity_other_uses,
                "quantity_consumed": self.data[0].quantity_consumed,
                "price": self.data[0].price,
                "income": self.data[0].income,
                "expenditure": self.data[0].expenditure,
                "kcals_consumed": self.data[0].kcals_consumed,
                "percentage_kcals": self.data[0].percentage_kcals,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class CropProductionViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [CropProductionFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("cropproduction-list")
        self.url_get = lambda n: reverse("cropproduction-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "livelihood_strategy",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "strategy_type",
            "strategy_type_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_description",
            "currency",
            "additional_identifier",
            "household_labor_provider",
            "household_labor_provider_label",
            "scenario",
            "scenario_label",
            "wealth_group",
            "wealth_group_label",
            "community",
            "community_name",
            "wealth_group_category",
            "wealth_group_category_name",
            "wealth_group_category_description",
            "wealth_group_percentage_of_households",
            "wealth_group_average_household_size",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "extra",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"CropProduction: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["scenario"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"scenario": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("scenario", response.json())
        self.assertEqual(response.json()["scenario"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "quantity_produced": self.data[0].quantity_produced,
                "quantity_sold": self.data[0].quantity_sold,
                "quantity_other_uses": self.data[0].quantity_other_uses,
                "quantity_consumed": self.data[0].quantity_consumed,
                "price": self.data[0].price,
                "income": self.data[0].income,
                "expenditure": self.data[0].expenditure,
                "kcals_consumed": self.data[0].kcals_consumed,
                "percentage_kcals": self.data[0].percentage_kcals,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class FoodPurchaseViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [FoodPurchaseFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("foodpurchase-list")
        self.url_get = lambda n: reverse("foodpurchase-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "livelihood_strategy",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "strategy_type",
            "strategy_type_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_description",
            "currency",
            "additional_identifier",
            "household_labor_provider",
            "household_labor_provider_label",
            "scenario",
            "scenario_label",
            "wealth_group",
            "wealth_group_label",
            "community",
            "community_name",
            "wealth_group_category",
            "wealth_group_category_name",
            "wealth_group_category_description",
            "wealth_group_percentage_of_households",
            "wealth_group_average_household_size",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "unit_multiple",
            "months_per_year",
            "times_per_month",
            "times_per_year",
            "extra",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"FoodPurchase: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["scenario"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"scenario": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("scenario", response.json())
        self.assertEqual(response.json()["scenario"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "quantity_produced": self.data[0].quantity_produced,
                "quantity_consumed": self.data[0].quantity_consumed,
                "price": self.data[0].price,
                "income": self.data[0].income,
                "expenditure": self.data[0].expenditure,
                "kcals_consumed": self.data[0].kcals_consumed,
                "percentage_kcals": self.data[0].percentage_kcals,
                "unit_multiple": self.data[0].unit_multiple,
                "times_per_year": self.data[0].times_per_year,
                "times_per_month": self.data[0].times_per_month,
                "months_per_year": self.data[0].months_per_year,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class PaymentInKindViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [PaymentInKindFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("paymentinkind-list")
        self.url_get = lambda n: reverse("paymentinkind-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "livelihood_strategy",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "strategy_type",
            "strategy_type_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_description",
            "currency",
            "additional_identifier",
            "household_labor_provider",
            "household_labor_provider_label",
            "scenario",
            "scenario_label",
            "wealth_group",
            "wealth_group_label",
            "community",
            "community_name",
            "wealth_group_category",
            "wealth_group_category_name",
            "wealth_group_category_description",
            "wealth_group_percentage_of_households",
            "wealth_group_average_household_size",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "payment_per_time",
            "people_per_household",
            "times_per_month",
            "months_per_year",
            "extra",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"PaymentInKind: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["scenario"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"scenario": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("scenario", response.json())
        self.assertEqual(response.json()["scenario"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "quantity_produced": self.data[0].quantity_produced,
                "quantity_sold": self.data[0].quantity_sold,
                "quantity_other_uses": self.data[0].quantity_other_uses,
                "quantity_consumed": self.data[0].quantity_consumed,
                "price": self.data[0].price,
                "income": self.data[0].income,
                "expenditure": self.data[0].expenditure,
                "kcals_consumed": self.data[0].kcals_consumed,
                "percentage_kcals": self.data[0].percentage_kcals,
                "payment_per_time": self.data[0].payment_per_time,
                "people_per_household": self.data[0].people_per_household,
                "times_per_month": self.data[0].times_per_month,
                "months_per_year": self.data[0].months_per_year,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class ReliefGiftsOtherViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [ReliefGiftOtherFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("reliefgiftother-list")
        self.url_get = lambda n: reverse("reliefgiftother-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "livelihood_strategy",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "strategy_type",
            "strategy_type_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_description",
            "currency",
            "additional_identifier",
            "household_labor_provider",
            "household_labor_provider_label",
            "scenario",
            "scenario_label",
            "wealth_group",
            "wealth_group_label",
            "community",
            "community_name",
            "wealth_group_category",
            "wealth_group_category_name",
            "wealth_group_category_description",
            "wealth_group_percentage_of_households",
            "wealth_group_average_household_size",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "unit_multiple",
            "months_per_year",
            "times_per_month",
            "times_per_year",
            "extra",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"ReliefGiftsOther: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["scenario"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"scenario": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("scenario", response.json())
        self.assertEqual(response.json()["scenario"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "quantity_produced": self.data[0].quantity_produced,
                "quantity_consumed": self.data[0].quantity_consumed,
                "price": self.data[0].price,
                "income": self.data[0].income,
                "expenditure": self.data[0].expenditure,
                "kcals_consumed": self.data[0].kcals_consumed,
                "percentage_kcals": self.data[0].percentage_kcals,
                "unit_multiple": self.data[0].unit_multiple,
                "times_per_year": self.data[0].times_per_year,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class FishingViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [FishingFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("fishing-list")
        self.url_get = lambda n: reverse("fishing-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "livelihood_strategy",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "strategy_type",
            "strategy_type_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_description",
            "currency",
            "additional_identifier",
            "household_labor_provider",
            "household_labor_provider_label",
            "scenario",
            "scenario_label",
            "wealth_group",
            "wealth_group_label",
            "community",
            "community_name",
            "wealth_group_category",
            "wealth_group_category_name",
            "wealth_group_category_description",
            "wealth_group_percentage_of_households",
            "wealth_group_average_household_size",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "extra",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"Fishing: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["scenario"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"scenario": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("scenario", response.json())
        self.assertEqual(response.json()["scenario"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "quantity_produced": self.data[0].quantity_produced,
                "quantity_sold": self.data[0].quantity_sold,
                "quantity_other_uses": self.data[0].quantity_other_uses,
                "quantity_consumed": self.data[0].quantity_consumed,
                "price": self.data[0].price,
                "income": self.data[0].income,
                "expenditure": self.data[0].expenditure,
                "kcals_consumed": self.data[0].kcals_consumed,
                "percentage_kcals": self.data[0].percentage_kcals,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class HuntingViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [HuntingFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("hunting-list")
        self.url_get = lambda n: reverse("hunting-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "livelihood_strategy",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "strategy_type",
            "strategy_type_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_description",
            "currency",
            "additional_identifier",
            "household_labor_provider",
            "household_labor_provider_label",
            "scenario",
            "scenario_label",
            "wealth_group",
            "wealth_group_label",
            "community",
            "community_name",
            "wealth_group_category",
            "wealth_group_category_name",
            "wealth_group_category_description",
            "wealth_group_percentage_of_households",
            "wealth_group_average_household_size",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "extra",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"Hunting: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["scenario"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"scenario": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("scenario", response.json())
        self.assertEqual(response.json()["scenario"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "quantity_produced": self.data[0].quantity_produced,
                "quantity_sold": self.data[0].quantity_sold,
                "quantity_other_uses": self.data[0].quantity_other_uses,
                "quantity_consumed": self.data[0].quantity_consumed,
                "price": self.data[0].price,
                "income": self.data[0].income,
                "expenditure": self.data[0].expenditure,
                "kcals_consumed": self.data[0].kcals_consumed,
                "percentage_kcals": self.data[0].percentage_kcals,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class WildFoodGatheringViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [WildFoodGatheringFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("wildfoodgathering-list")
        self.url_get = lambda n: reverse("wildfoodgathering-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "livelihood_strategy",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "strategy_type",
            "strategy_type_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_description",
            "currency",
            "additional_identifier",
            "household_labor_provider",
            "household_labor_provider_label",
            "scenario",
            "scenario_label",
            "wealth_group",
            "wealth_group_label",
            "community",
            "community_name",
            "wealth_group_category",
            "wealth_group_category_name",
            "wealth_group_category_description",
            "wealth_group_percentage_of_households",
            "wealth_group_average_household_size",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "extra",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"WildFoodGathering: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["scenario"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"scenario": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("scenario", response.json())
        self.assertEqual(response.json()["scenario"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "quantity_produced": self.data[0].quantity_produced,
                "quantity_sold": self.data[0].quantity_sold,
                "quantity_other_uses": self.data[0].quantity_other_uses,
                "quantity_consumed": self.data[0].quantity_consumed,
                "price": self.data[0].price,
                "income": self.data[0].income,
                "expenditure": self.data[0].expenditure,
                "kcals_consumed": self.data[0].kcals_consumed,
                "percentage_kcals": self.data[0].percentage_kcals,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class OtherCashIncomeViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [OtherCashIncomeFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("othercashincome-list")
        self.url_get = lambda n: reverse("othercashincome-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "livelihood_strategy",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "strategy_type",
            "strategy_type_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_description",
            "currency",
            "additional_identifier",
            "household_labor_provider",
            "household_labor_provider_label",
            "scenario",
            "scenario_label",
            "wealth_group",
            "wealth_group_label",
            "community",
            "community_name",
            "wealth_group_category",
            "wealth_group_category_name",
            "wealth_group_category_description",
            "wealth_group_percentage_of_households",
            "wealth_group_average_household_size",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "payment_per_time",
            "people_per_household",
            "times_per_month",
            "months_per_year",
            "times_per_year",
            "extra",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"OtherCashIncome: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["scenario"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"scenario": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("scenario", response.json())
        self.assertEqual(response.json()["scenario"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "quantity_produced": self.data[0].quantity_produced,
                "quantity_sold": self.data[0].quantity_sold,
                "quantity_other_uses": self.data[0].quantity_other_uses,
                "quantity_consumed": self.data[0].quantity_consumed,
                "price": self.data[0].price,
                "income": self.data[0].income,
                "expenditure": self.data[0].expenditure,
                "kcals_consumed": self.data[0].kcals_consumed,
                "percentage_kcals": self.data[0].percentage_kcals,
                "payment_per_time": self.data[0].payment_per_time,
                "people_per_household": self.data[0].people_per_household,
                "times_per_month": self.data[0].times_per_month,
                "months_per_year": self.data[0].months_per_year,
                "times_per_year": self.data[0].times_per_year,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class OtherPurchasesViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [OtherPurchaseFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("otherpurchase-list")
        self.url_get = lambda n: reverse("otherpurchase-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "livelihood_strategy",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "strategy_type",
            "strategy_type_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_description",
            "currency",
            "additional_identifier",
            "household_labor_provider",
            "household_labor_provider_label",
            "scenario",
            "scenario_label",
            "wealth_group",
            "wealth_group_label",
            "community",
            "community_name",
            "wealth_group_category",
            "wealth_group_category_name",
            "wealth_group_category_description",
            "wealth_group_percentage_of_households",
            "wealth_group_average_household_size",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "unit_multiple",
            "times_per_month",
            "months_per_year",
            "extra",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"OtherPurchases: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["scenario"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"scenario": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("scenario", response.json())
        self.assertEqual(response.json()["scenario"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "quantity_produced": self.data[0].quantity_produced,
                "quantity_sold": self.data[0].quantity_sold,
                "quantity_other_uses": self.data[0].quantity_other_uses,
                "quantity_consumed": self.data[0].quantity_consumed,
                "price": self.data[0].price,
                "income": self.data[0].income,
                "expenditure": self.data[0].expenditure,
                "kcals_consumed": self.data[0].kcals_consumed,
                "percentage_kcals": self.data[0].percentage_kcals,
                "unit_multiple": self.data[0].unit_multiple,
                "times_per_month": self.data[0].times_per_month,
                "months_per_year": self.data[0].months_per_year,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].scenario + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class SeasonalActivityViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [SeasonalActivityFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("seasonalactivity-list")
        self.url_get = lambda n: reverse("seasonalactivity-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "seasonal_activity_type",
            "seasonal_activity_type_name",
            "seasonal_activity_type_description",
            "activity_category",
            "activity_category_label",
            "product",
            "product_common_name",
            "product_description",
            "additional_identifier",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"SeasonalActivity: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "livelihood_zone_baseline": self.data[0].livelihood_zone_baseline.pk,
                "seasonal_activity_type": self.data[0].seasonal_activity_type.pk,
                "product": self.data[0].product.pk,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

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
        self.assertEqual(len(df), self.num_records + 1)


class SeasonalActivityOccurrenceViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [SeasonalActivityOccurrenceFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("seasonalactivityoccurrence-list")
        self.url_get = lambda n: reverse("seasonalactivityoccurrence-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "seasonal_activity",
            "seasonal_activity_type",
            "seasonal_activity_type_name",
            "seasonal_activity_type_description",
            "activity_category",
            "activity_category_label",
            "product",
            "product_common_name",
            "product_description",
            "additional_identifier",
            "community",
            "community_name",
            "start",
            "end",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            "SeasonalActivityOccurrence: "
            f"Fields expected: {expected_fields}. "
            f"Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["start"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"start": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("start", response.json())
        self.assertEqual(response.json()["start"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "start": self.data[0].start,
                "end": self.data[0].end,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

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
        self.assertEqual(len(df), self.num_records + 1)


class CommunityCropProductionViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [CommunityCropProductionFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("communitycropproduction-list")
        self.url_get = lambda n: reverse("communitycropproduction-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "community",
            "community_name",
            "crop",
            "crop_common_name",
            "crop_description",
            "crop_purpose",
            "crop_purpose_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "yield_with_inputs",
            "yield_without_inputs",
            "seed_requirement",
            "crop_unit_of_measure",
            "crop_unit_of_measure_description",
            "land_unit_of_measure",
            "land_unit_of_measure_description",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            "CommunityCropProduction: "
            f"Fields expected: {expected_fields}. "
            f"Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["crop_purpose"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"crop_purpose": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("crop_purpose", response.json())
        self.assertEqual(response.json()["crop_purpose"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "yield_with_inputs": self.data[0].yield_with_inputs,
                "yield_without_inputs": self.data[0].yield_without_inputs,
                "seed_requirement": self.data[0].seed_requirement,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].crop_purpose,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].crop_purpose + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class CommunityLivestockViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [CommunityLivestockFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("communitylivestock-list")
        self.url_get = lambda n: reverse("communitylivestock-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "community",
            "community_name",
            "livestock",
            "livestock_common_name",
            "livestock_description",
            "birth_interval",
            "wet_season_lactation_period",
            "wet_season_milk_production",
            "dry_season_lactation_period",
            "dry_season_milk_production",
            "age_at_sale",
            "additional_attributes",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"CommunityLivestock: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["birth_interval"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"birth_interval": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("birth_interval", response.json())
        self.assertEqual(response.json()["birth_interval"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "birth_interval": self.data[0].birth_interval,
                "wet_season_lactation_period": self.data[0].wet_season_lactation_period,
                "wet_season_milk_production": self.data[0].wet_season_milk_production,
                "dry_season_lactation_period": self.data[0].dry_season_lactation_period,
                "dry_season_milk_production": self.data[0].dry_season_milk_production,
                "age_at_sale": self.data[0].age_at_sale,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

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
        self.assertEqual(len(df), self.num_records + 1)


class MarketPriceViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [MarketPriceFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("marketprice-list")
        self.url_get = lambda n: reverse("marketprice-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "community",
            "community_name",
            "market",
            "market_name",
            "market_description",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_description",
            "currency",
            "description",
            "low_price_start",
            "low_price_end",
            "low_price",
            "high_price_start",
            "high_price_end",
            "high_price",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"MarketPrice: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["description"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"description": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("description", response.json())
        self.assertEqual(response.json()["description"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "description": self.data[0].description,
                "low_price_start": self.data[0].low_price_start,
                "low_price_end": self.data[0].low_price_end,
                "low_price": self.data[0].low_price,
                "high_price_start": self.data[0].high_price_start,
                "high_price_end": self.data[0].high_price_end,
                "high_price": self.data[0].high_price,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].description,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].description + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class SeasonalProductionPerformanceViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [SeasonalProductionPerformanceFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("seasonalproductionperformance-list")
        self.url_get = lambda n: reverse("seasonalproductionperformance-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "community",
            "community_name",
            "performance_year_start_date",
            "performance_year_end_date",
            "seasonal_performance",
            "seasonal_performance_label",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            "SeasonalProductionPerformance: "
            f"Fields expected: {expected_fields}. "
            f"Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["performance_year_start_date"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"performance_year_start_date": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("performance_year_start_date", response.json())
        self.assertEqual(response.json()["performance_year_start_date"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {"id": self.data[0].id, "seasonal_performance": self.data[0].seasonal_performance},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_filter_by_seasonal_performance(self):
        response = self.client.get(
            self.url,
            {
                "seasonal_performance": self.data[0].seasonal_performance,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["seasonal_performance"], int(self.data[0].seasonal_performance))

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
        self.assertEqual(len(df), self.num_records + 1)


class HazardViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [HazardFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("hazard-list")
        self.url_get = lambda n: reverse("hazard-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "community",
            "community_name",
            "chronic_or_periodic",
            "chronic_or_periodic_label",
            "ranking",
            "ranking_label",
            "hazard_category",
            "hazard_category_name",
            "hazard_category_description",
            "description",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"Hazard: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["chronic_or_periodic"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"chronic_or_periodic": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("chronic_or_periodic", response.json())
        self.assertEqual(response.json()["chronic_or_periodic"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "description": self.data[0].description,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].chronic_or_periodic,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].chronic_or_periodic + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class EventViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [EventFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("event-list")
        self.url_get = lambda n: reverse("event-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "community",
            "community_name",
            "event_year_start_date",
            "event_year_end_date",
            "description",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"Event: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"created": self.data[1].created})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["event_year_start_date"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"event_year_start_date": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("event_year_start_date", response.json())
        self.assertEqual(response.json()["event_year_start_date"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "description": self.data[0].description,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].description,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].description + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class ExpandabilityFactorViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [ExpandabilityFactorFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("expandabilityfactor-list")
        self.url_get = lambda n: reverse("expandabilityfactor-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone_name",
            "livelihood_zone",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "community",
            "community_name",
            "livelihood_strategy",
            "strategy_type",
            "strategy_type_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_description",
            "currency",
            "additional_identifier",
            "wealth_group",
            "wealth_group_label",
            "wealth_group_category",
            "wealth_group_category_name",
            "wealth_group_category_description",
            "wealth_group_percentage_of_households",
            "wealth_group_average_household_size",
            "percentage_produced",
            "percentage_sold",
            "percentage_other_uses",
            "percentage_expenditure",
            "percentage_consumed",
            "percentage_income",
            "remark",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"ExpandabilityFactor: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"remark": self.data[1].remark})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["percentage_produced"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"percentage_produced": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("percentage_produced", response.json())
        self.assertEqual(response.json()["percentage_produced"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "percentage_produced": self.data[0].percentage_produced,
                "percentage_sold": self.data[0].percentage_sold,
                "percentage_other_uses": self.data[0].percentage_other_uses,
                "percentage_consumed": self.data[0].percentage_consumed,
                "percentage_income": self.data[0].percentage_income,
                "percentage_expenditure": self.data[0].percentage_expenditure,
                "remark": self.data[0].remark,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].remark,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].remark + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)


class CopingStrategyViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [CopingStrategyFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")

    def setUp(self):
        self.url = reverse("copingstrategy-list")
        self.url_get = lambda n: reverse("copingstrategy-detail", args=(self.data[n].pk,))

    def test_get_record(self):
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        expected_fields = (
            "id",
            "community",
            "community_name",
            "leaders",
            "wealth_group",
            "wealth_group_label",
            "wealth_group_category",
            "wealth_group_category_name",
            "wealth_group_category_description",
            "wealth_group_percentage_of_households",
            "wealth_group_average_household_size",
            "livelihood_strategy",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "strategy_type",
            "strategy_type_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_description",
            "currency",
            "additional_identifier",
            "strategy",
            "strategy_label",
            "by_value",
        )
        self.assertCountEqual(
            response.json().keys(),
            expected_fields,
            f"CopingStrategy: Fields expected: {expected_fields}. Fields found: {response.json().keys()}.",
        )

    def test_patch_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"leaders": self.data[1].leaders})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_delete_requires_authentication(self):
        logging.disable(logging.CRITICAL)
        response = self.client.delete(self.url_get(0))
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 403)

    def test_patch(self):
        self.client.force_login(self.user)
        new_value = self.client.get(self.url_get(1)).json()["leaders"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"leaders": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("leaders", response.json())
        self.assertEqual(response.json()["leaders"], new_value)

    def test_list_returns_all_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), self.num_records)

    def test_list_returns_filtered_data(self):
        response = self.client.get(
            self.url,
            {
                "id": self.data[0].id,
                "leaders": self.data[0].leaders,
                "by_value": self.data[0].by_value,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_search(self):
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].leaders,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.json()), 0)
        self.assertLess(len(response.json()), self.num_records)
        response = self.client.get(
            self.url,
            {
                "search": self.data[0].leaders + "xyz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

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
        self.assertEqual(len(df), self.num_records + 1)
