import datetime
import json
import logging
import warnings
from io import StringIO

import pandas as pd
from bs4 import BeautifulSoup
from django.contrib.auth.models import User
from django.db.models import F
from django.urls import reverse
from rest_framework.test import APITestCase

from baseline.models import (
    LivelihoodActivity,
    LivelihoodZoneBaseline,
)
from common.fields import translation_fields
from common.tests.factories import ClassifiedProductFactory, CountryFactory
from metadata.models import LivelihoodActivityScenario
from metadata.tests.factories import (
    LivelihoodCategoryFactory,
    WealthCharacteristicFactory,
    WealthGroupCategoryFactory,
)

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

    def test_filter_by_country(self):
        country = CountryFactory(
            iso3166a2="AA",
            iso3166a3="AAA",
            iso3166n3=911,
            iso_en_ro_name="A Country",
            iso_en_name="AA Country",
            name="AA Country",
        )
        LivelihoodZoneFactory(country=country)
        response = self.client.get(self.url, {"country": country.iso3166a2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 1)
        response = self.client.get(self.url, {"country": country.iso_en_ro_name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)
        response = self.client.get(self.url, {"country": country.iso_en_name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)

    def test_pagination_for_browsable_api(self):
        LivelihoodZoneFactory.create_batch(100)
        response = self.client.get(self.url, {"format": "json"})
        self.assertEqual(response.status_code, 200)
        # Check that the response contains all 100 items (no pagination for JSON)
        self.assertEqual(len(response.data), 100 + self.num_records)

        response = self.client.get(self.url, {"format": "api"})
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, "html.parser")
        json_section = soup.find("pre", class_="content-holder")
        # Extract text and clean HTML tags to look for the JSON data inside
        raw_json_text = json_section.get_text()
        soup_cleaned = BeautifulSoup(raw_json_text, "html.parser")
        cleaned_json_text = soup_cleaned.get_text()
        json_data = json.loads(cleaned_json_text)
        # Check that the paginated response contains only 50 items
        self.assertEqual(len(json_data["results"]), 50)

    def test_json_pagination_with_page_size(self):
        LivelihoodZoneFactory.create_batch(100)
        response = self.client.get(self.url, {"format": "json"})
        self.assertEqual(response.status_code, 200)
        # Check that the response contains all 100 items (no pagination for JSON)
        self.assertEqual(len(response.data), 100 + self.num_records)
        # Check that the page_size for json format works
        response = self.client.get(self.url, {"format": "json", "page_size": 20})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 20)


class LivelihoodZoneBaselineViewSetTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5
        cls.data = [LivelihoodZoneBaselineFactory() for _ in range(cls.num_records)]
        cls.user = User.objects.create_superuser("test", "test@test.com", "password")
        cls.population_estimates = sorted(
            [record.population_estimate for record in LivelihoodZoneBaseline.objects.all()]
        )

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
        new_value = self.client.get(self.url_get(1)).json()["main_livelihood_category"]
        logging.disable(logging.CRITICAL)
        response = self.client.patch(self.url_get(0), {"main_livelihood_category": new_value})
        logging.disable(logging.NOTSET)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url_get(0))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertIn("main_livelihood_category", response.json())
        self.assertEqual(response.json()["main_livelihood_category"], new_value)

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

    def test_filter_by_country(self):
        country = CountryFactory(
            iso3166a2="AA",
            iso3166a3="AAA",
            iso3166n3=911,
            iso_en_ro_name="A Country",
            iso_en_name="AA Country",
            name="AA Country",
        )
        LivelihoodZoneBaselineFactory(livelihood_zone__country=country)
        response = self.client.get(self.url, {"country": country.iso3166a2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 1)
        response = self.client.get(self.url, {"country": country.iso_en_ro_name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)

    def test_population_estimate_range_filter(self):
        min_estimate = self.population_estimates[0]
        max_estimate = self.population_estimates[-1]

        # Test filtering with a range that should include all records
        response = self.client.get(
            self.url,
            {
                "population_estimate_min": min_estimate,
                "population_estimate_max": max_estimate,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), self.num_records)

        # Test filtering for subset of the records
        second_smallest = self.population_estimates[1]
        second_largest = self.population_estimates[3]
        response = self.client.get(
            self.url,
            {
                "population_estimate_min": second_smallest,
                "population_estimate_max": second_largest,
            },
        )
        self.assertEqual(response.status_code, 200)
        filtered_records = [_response["population_estimate"] for _response in response.data]
        self.assertTrue(all(second_smallest <= r <= second_largest for r in filtered_records))

        # Test filtering with a range that excludes all records
        response = self.client.get(
            self.url,
            {
                "population_estimate_min": max_estimate + 1,
                "population_estimate_max": max_estimate + 1000,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_filter_by_product(self):
        product = ClassifiedProductFactory(
            cpc="K0111",
            description_en="my product",
            common_name_en="common",
            kcals_per_unit=550,
            aliases=["test alias"],
        )
        ClassifiedProductFactory(cpc="K01111")
        baseline = LivelihoodZoneBaselineFactory()
        LivelihoodStrategyFactory(product=product, livelihood_zone_baseline=baseline)
        response = self.client.get(self.url, {"product": "K011"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 1)
        # filter by cpc
        response = self.client.get(self.url, {"product": "K0111"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 1)
        # filter by cpc startswith
        response = self.client.get(self.url, {"product": "K01111"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 0)
        # filter by description icontains
        response = self.client.get(self.url, {"product": "my"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)
        # filter by description
        response = self.client.get(self.url, {"product": "my product"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)
        # filter by alias
        response = self.client.get(self.url, {"product": "test"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)

    def test_filter_by_wealth_characteristic(self):
        baseline = LivelihoodZoneBaselineFactory()
        wealth_characteristic = WealthCharacteristicFactory()
        WealthGroupCharacteristicValueFactory(
            wealth_group__livelihood_zone_baseline=baseline, wealth_characteristic=wealth_characteristic
        )
        response = self.client.get(self.url, {"wealth_characteristic": wealth_characteristic.code})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)
        response = self.client.get(self.url, {"wealth_characteristic": wealth_characteristic.name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_as_of_date_filter_returns_valid_baselines(self):
        # Test that the as_of_date filter returns valid baselines as of the specified date.
        today = datetime.date.today()
        expired_baseline = LivelihoodZoneBaselineFactory(
            valid_from_date=today - datetime.timedelta(days=365),
            valid_to_date=today - datetime.timedelta(days=30),
        )
        current_baseline = LivelihoodZoneBaselineFactory(
            valid_from_date=today - datetime.timedelta(days=30),
            valid_to_date=today + datetime.timedelta(days=365),
        )
        # Test default behavior (as of today) - should exclude expired_baseline
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        baseline_ids = [b["id"] for b in response.json()]
        self.assertIn(current_baseline.id, baseline_ids)
        self.assertNotIn(expired_baseline.id, baseline_ids)

        # Test with a past date before the expired_baseline's valid_to_date
        past_date = today - datetime.timedelta(days=180)
        response = self.client.get(self.url, {"as_of_date": past_date.isoformat()})
        self.assertEqual(response.status_code, 200)
        baseline_ids = [b["id"] for b in response.json()]
        self.assertIn(expired_baseline.id, baseline_ids)
        self.assertIn(current_baseline.id, baseline_ids)

        # Test with a future date - expired_baseline should still be excluded
        future_date = today + datetime.timedelta(days=60)
        response = self.client.get(self.url, {"as_of_date": future_date.isoformat()})
        self.assertEqual(response.status_code, 200)
        baseline_ids = [b["id"] for b in response.json()]
        self.assertNotIn(expired_baseline.id, baseline_ids)
        self.assertIn(current_baseline.id, baseline_ids)

        # test as of date filter handles null dates
        baseline_no_from = LivelihoodZoneBaselineFactory(
            valid_from_date=None,
            valid_to_date=today + datetime.timedelta(days=365),
        )
        # Create a baseline with null valid_to_date (valid indefinitely)
        baseline_no_to = LivelihoodZoneBaselineFactory(
            valid_from_date=today - datetime.timedelta(days=365),
            valid_to_date=None,
        )
        # Create a baseline with both dates null (always valid)
        baseline_no_dates = LivelihoodZoneBaselineFactory(
            valid_from_date=None,
            valid_to_date=None,
        )
        # Test default behavior - all three should be returned
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        baseline_ids = [b["id"] for b in response.json()]
        self.assertIn(baseline_no_from.id, baseline_ids)
        self.assertIn(baseline_no_to.id, baseline_ids)
        self.assertIn(baseline_no_dates.id, baseline_ids)


class LivelihoodZoneBaselineFacetedSearchViewTestCase(APITestCase):
    def setUp(self):
        self.category1 = LivelihoodCategoryFactory()
        self.baseline1 = LivelihoodZoneBaselineFactory(main_livelihood_category=self.category1)
        self.baseline2 = LivelihoodZoneBaselineFactory(main_livelihood_category=self.category1)
        self.baseline3 = LivelihoodZoneBaselineFactory()
        self.product1 = ClassifiedProductFactory(
            cpc="K0111",
            description_en="my test",
            common_name_en="common",
            kcals_per_unit=550,
            aliases=["test alias"],
        )
        self.product2 = ClassifiedProductFactory(
            cpc="L0111",
            description_en="my mukera",
            common_name_en="common mukera",
            kcals_per_unit=550,
        )
        LivelihoodStrategyFactory(product=self.product1, livelihood_zone_baseline=self.baseline1)
        self.characteristic1 = WealthCharacteristicFactory(description_en="my test")
        self.characteristic2 = WealthCharacteristicFactory(description_en="my mukera", description_fr="my test")
        WealthGroupCharacteristicValueFactory(
            wealth_group__livelihood_zone_baseline=self.baseline1, wealth_characteristic=self.characteristic1
        )
        WealthGroupCharacteristicValueFactory(
            wealth_group__livelihood_zone_baseline=self.baseline2, wealth_characteristic=self.characteristic2
        )
        self.characteristic3 = WealthCharacteristicFactory()
        self.strategy = LivelihoodStrategyFactory(product=self.product1, livelihood_zone_baseline=self.baseline3)
        self.baseline = LivelihoodZoneBaselineFactory(main_livelihood_category=self.category1)
        self.url = reverse("livelihood-zone-baseline-faceted-search")

    def test_search_with_product(self):
        # Test when search matches entries
        response = self.client.get(self.url, {"search": self.product1.description_en, "language": "en"})
        self.assertEqual(response.status_code, 200)
        search_data = response.data
        self.assertEqual(len(search_data["products"]), 1)
        self.assertEqual(search_data["products"][0]["count"], 2)  # 2 zones have this product
        # confirm the product value is correct
        self.assertEqual(search_data["products"][0]["value"], self.product1.cpc)
        # Apply the filters to the baseline
        baseline_url = reverse("livelihoodzonebaseline-list")
        response = self.client.get(
            baseline_url,
            {search_data["products"][0]["filter"]: search_data["products"][0]["value"]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 2)
        data = json.loads(response.content)
        self.assertTrue(any(d["name"] == self.baseline1.name for d in data))
        self.assertTrue(any(d["name"] == self.baseline3.name for d in data))
        self.assertFalse(any(d["name"] == self.baseline2.name for d in data))

        response = self.client.get(
            baseline_url,
            {search_data["items"][0]["filter"]: search_data["items"][0]["value"]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 1)
        data = json.loads(response.content)
        self.assertTrue(any(d["name"] == self.baseline1.name for d in data))
        self.assertFalse(any(d["name"] == self.baseline2.name for d in data))
        self.assertFalse(any(d["name"] == self.baseline3.name for d in data))
        # Search by the second product
        response = self.client.get(
            self.url,
            {
                "search": self.product2.description_en,
            },
        )
        self.assertEqual(response.status_code, 200)
        search_data = response.data
        self.assertEqual(len(search_data["products"]), 0)

    def test_search_with_wealth_characterstics(self):
        # Test when search matches entries
        response = self.client.get(self.url, {"search": self.characteristic1.description_en})
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(len(data["items"]), 2)
        self.assertEqual(data["items"][0]["count"], 1)  # 1 zone for this characteristic
        self.assertEqual(data["items"][1]["count"], 1)  # 1 zone for this characteristic
        # Search by the second characteristic
        response = self.client.get(
            self.url,
            {
                "search": self.characteristic2.description_en,
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(len(data["items"]), 1)
        self.assertEqual(data["items"][0]["count"], 1)  # 1 zone for this characteristic
        # Search by the third characteristic
        response = self.client.get(
            self.url,
            {
                "search": self.characteristic3.description_en,
            },
        )
        data = response.data
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data["items"]), 0)


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
            "baseline_livelihood_activity",
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
            "percentage_allocation_to_basket",
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
                "baseline_livelihood_activity": self.data[0].baseline_livelihood_activity.pk,
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
            "community_full_name",
            "wealth_group_category",
            "wealth_group_category_name",
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
            "wealth_group_category_name",
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

    def test_filter_by_country(self):
        country = CountryFactory(
            iso3166a2="AA",
            iso3166a3="AAA",
            iso3166n3=911,
            iso_en_ro_name="A Country",
            iso_en_name="AA Country",
            name="AA Country",
        )
        BaselineWealthGroupFactory(livelihood_zone_baseline__livelihood_zone__country=country)
        response = self.client.get(self.url, {"country": country.iso3166a2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 1)
        response = self.client.get(self.url, {"country": country.iso_en_ro_name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)


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
            "community_full_name",
            "wealth_group_category",
            "wealth_group_category_name",
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

    def test_filter_by_country(self):
        country = CountryFactory(
            iso3166a2="AA",
            iso3166a3="AAA",
            iso3166n3=911,
            iso_en_ro_name="A Country",
            iso_en_name="AA Country",
            name="AA Country",
        )
        CommunityWealthGroupFactory(community__livelihood_zone_baseline__livelihood_zone__country=country)
        response = self.client.get(self.url, {"country": country.iso3166a2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 1)
        response = self.client.get(self.url, {"country": country.iso_en_ro_name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)


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
            "community_full_name",
            "wealth_group_category",
            "wealth_group_category_name",
            "wealth_group_category_description",
            "wealth_group_category_ordering",
            "wealth_characteristic",
            "wealth_characteristic_name",
            "wealth_characteristic_description",
            "wealth_characteristic_ordering",
            "variable_type",
            "characteristic_group",
            "product",
            "product_common_name",
            "unit_of_measure",
            "unit_of_measure_description",
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

    def test_filter_by_country(self):
        country = CountryFactory(
            iso3166a2="AA",
            iso3166a3="AAA",
            iso3166n3=911,
            iso_en_ro_name="A Country",
            iso_en_name="AA Country",
            name="AA Country",
        )
        WealthGroupCharacteristicValueFactory(wealth_group__livelihood_zone_baseline__livelihood_zone__country=country)
        response = self.client.get(self.url, {"country": country.iso3166a2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 1)
        response = self.client.get(self.url, {"country": country.iso_en_ro_name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)

    def test_filter_by_product(self):
        parent = ClassifiedProductFactory(cpc="K011")
        product = ClassifiedProductFactory(
            cpc="K0111",
            description_en="my product",
            common_name_en="common",
            kcals_per_unit=550,
            parent=parent,
            aliases=["test alias"],
        )
        ClassifiedProductFactory(cpc="K01111")
        characteristic1 = WealthCharacteristicFactory(
            code="IOO", description_en="item one ownership", has_product=True
        )
        WealthGroupCharacteristicValueFactory(wealth_characteristic=characteristic1, product=product)
        response = self.client.get(self.url, {"product": "K011"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 1)
        # filter by cpc
        response = self.client.get(self.url, {"product": "K0111"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 1)
        # filter by cpc startswith
        response = self.client.get(self.url, {"product": "K01111"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 0)
        # filter by description icontains
        response = self.client.get(self.url, {"product": "my"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)
        # filter by description
        response = self.client.get(self.url, {"product": "my product"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)
        # filter by alias
        response = self.client.get(self.url, {"product": "test"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)


class BaselineWealthGroupCharacteristicValueViewSetTestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.baseline = LivelihoodZoneBaselineFactory()

        cls.very_poor_wg = WealthGroupCategoryFactory(code="VP", name_en="Very Poor")
        cls.poor_wg = WealthGroupCategoryFactory(code="P", name_en="Poor")

        cls.baseline_wg_vp = BaselineWealthGroupFactory(
            livelihood_zone_baseline=cls.baseline,
            wealth_group_category=cls.very_poor_wg,
        )
        cls.baseline_wg_p = BaselineWealthGroupFactory(
            livelihood_zone_baseline=cls.baseline,
            wealth_group_category=cls.poor_wg,
        )

        # Create community wealth groups (should be excluded)
        cls.community = CommunityFactory(livelihood_zone_baseline=cls.baseline)
        cls.community_wg = CommunityWealthGroupFactory(
            livelihood_zone_baseline=cls.baseline,
            wealth_group_category=cls.very_poor_wg,
            community=cls.community,
        )
        # Create wealth characteristics
        cls.char_with_group = WealthCharacteristicFactory(
            code="household size",
            name_en="Household size",
            characteristic_group="Population",
        )
        cls.char_without_group = WealthCharacteristicFactory(
            code="other",
            name_en="Other characteristic",
            characteristic_group=None,
        )
        # Create characteristic values for baseline wealth groups (with values)
        cls.value_baseline_vp = WealthGroupCharacteristicValueFactory(
            wealth_group=cls.baseline_wg_vp,
            wealth_characteristic=cls.char_with_group,
            value=5,
            min_value=4,
            max_value=6,
        )
        cls.value_baseline_p = WealthGroupCharacteristicValueFactory(
            wealth_group=cls.baseline_wg_p,
            wealth_characteristic=cls.char_with_group,
            value=6,
            min_value=5,
            max_value=7,
        )

        # Create characteristic value for community wealth group (should be excluded)
        cls.value_community = WealthGroupCharacteristicValueFactory(
            wealth_group=cls.community_wg,
            wealth_characteristic=cls.char_with_group,
            value=3,
        )

    def setUp(self):
        self.url = reverse("baselinewealthgroupcharacteristicvalue-list")

    def test_only_baseline_wealth_groups_included(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        results = response.json()
        baseline_ids = {self.value_baseline_vp.id, self.value_baseline_p.id}
        returned_ids = {r["id"] for r in results}

        # All baseline records should be present
        self.assertTrue(baseline_ids.issubset(returned_ids))
        # Community record should not be present
        self.assertNotIn(self.value_community.id, returned_ids)

    def test_filter_by_livelihood_zone_baseline(self):
        # Create another baseline with its own data
        other_baseline = LivelihoodZoneBaselineFactory()
        other_wg = BaselineWealthGroupFactory(
            livelihood_zone_baseline=other_baseline,
            wealth_group_category=self.very_poor_wg,
        )
        WealthGroupCharacteristicValueFactory(
            wealth_group=other_wg,
            wealth_characteristic=self.char_with_group,
            value=10,
        )
        # Filter by our original baseline
        response = self.client.get(self.url, {"livelihood_zone_baseline": self.baseline.pk})
        self.assertEqual(response.status_code, 200)
        results = response.json()
        # Should only have our 2 original baseline records
        self.assertEqual(len([r for r in results if r["livelihood_zone_baseline"] == self.baseline.pk]), 2)

    def test_filter_has_value_true(self):
        # Create another baseline with its own data
        other_baseline = LivelihoodZoneBaselineFactory()
        other_wg = BaselineWealthGroupFactory(
            livelihood_zone_baseline=other_baseline,
            wealth_group_category=self.very_poor_wg,
        )
        WealthGroupCharacteristicValueFactory(
            wealth_group=other_wg,
            wealth_characteristic=self.char_with_group,
            value=0,
            min_value=None,
            max_value=None,
        )
        response = self.client.get(self.url, {"has_value": "true"})
        self.assertEqual(response.status_code, 200)
        results = response.json()
        # Should include records with values
        returned_ids = {r["id"] for r in results}
        self.assertIn(self.value_baseline_vp.id, returned_ids)
        self.assertIn(self.value_baseline_p.id, returned_ids)
        self.assertNotIn(other_baseline.id, returned_ids)

    def test_response_fields(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        results = response.json()
        if len(results) > 0:
            expected_fields = {
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
                "wealth_group_category",
                "wealth_group_category_name",
                "wealth_group_category_description",
                "wealth_group_category_ordering",
                "wealth_characteristic",
                "wealth_characteristic_name",
                "wealth_characteristic_description",
                "wealth_characteristic_ordering",
                "variable_type",
                "characteristic_group",
                "product",
                "product_common_name",
                "unit_of_measure",
                "unit_of_measure_description",
                "value",
                "min_value",
                "max_value",
            }
            self.assertEqual(set(results[0].keys()), expected_fields)


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

    def test_filter_by_country(self):
        country = CountryFactory(
            iso3166a2="AA",
            iso3166a3="AAA",
            iso3166n3=911,
            iso_en_ro_name="A Country",
            iso_en_name="AA Country",
            name="AA Country",
        )
        LivelihoodStrategyFactory(livelihood_zone_baseline__livelihood_zone__country=country)
        response = self.client.get(self.url, {"country": country.iso3166a2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 1)
        response = self.client.get(self.url, {"country": country.iso_en_ro_name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)

    def test_filter_by_product(self):
        parent = ClassifiedProductFactory(cpc="K011")
        product = ClassifiedProductFactory(
            cpc="K0111",
            description_en="my product",
            common_name_en="common",
            kcals_per_unit=550,
            parent=parent,
            aliases=["test alias"],
        )
        ClassifiedProductFactory(cpc="K01111")
        LivelihoodStrategyFactory(product=product)
        response = self.client.get(self.url, {"product": "K011"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 1)
        # filter by cpc
        response = self.client.get(self.url, {"product": "K0111"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 1)
        # filter by cpc startswith
        response = self.client.get(self.url, {"product": "K01111"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 0)
        # filter by description icontains
        response = self.client.get(self.url, {"product": "my"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)
        # filter by description
        response = self.client.get(self.url, {"product": "my product"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)
        # filter by alias
        response = self.client.get(self.url, {"product": "test"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)

    def test_filter_by_cpc(self):
        parent = ClassifiedProductFactory(cpc="K011")
        product = ClassifiedProductFactory(
            cpc="K0111",
            description_en="my product",
            common_name_en="common",
            kcals_per_unit=550,
            parent=parent,
        )
        ClassifiedProductFactory(cpc="K01111")
        LivelihoodStrategyFactory(product=product)
        # test filter by cpc exact match
        response = self.client.get(self.url, {"cpc": "K0111"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 1)
        # test filter by cpc startswith
        response = self.client.get(self.url, {"cpc": "K01"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 1)
        # test filter by cpc lowercase/case in-sensitive
        response = self.client.get(self.url, {"cpc": "k0111"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)
        # test filter by product not having a strategy
        response = self.client.get(self.url, {"cpc": "K01111"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 0)


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
            "community_full_name",
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

    def test_filter_by_country(self):
        country = CountryFactory(
            iso3166a2="AA",
            iso3166a3="AAA",
            iso3166n3=911,
            iso_en_ro_name="A Country",
            iso_en_name="AA Country",
            name="AA Country",
        )
        LivelihoodActivityFactory(livelihood_zone_baseline__livelihood_zone__country=country)
        response = self.client.get(self.url, {"country": country.iso3166a2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 1)
        response = self.client.get(self.url, {"country": country.iso_en_ro_name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)

    def test_filter_by_product(self):
        parent = ClassifiedProductFactory(cpc="K011")
        product = ClassifiedProductFactory(
            cpc="K0111",
            description_en="my product",
            common_name_en="common",
            kcals_per_unit=550,
            parent=parent,
            aliases=["test"],
        )
        LivelihoodActivityFactory(livelihood_strategy__product=product)
        response = self.client.get(self.url, {"product": "K011"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 1)
        # filter by cpc
        response = self.client.get(self.url, {"product": "K0111"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 1)
        # filter by cpc startswith
        response = self.client.get(self.url, {"product": "K01111"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 0)
        # filter by description icontains
        response = self.client.get(self.url, {"product": "my"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)
        # filter by description
        response = self.client.get(self.url, {"product": "my product"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)
        # filter by alias
        response = self.client.get(self.url, {"product": "test"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)

    def test_filter_by_cpc(self):
        parent = ClassifiedProductFactory(cpc="K011")
        product = ClassifiedProductFactory(
            cpc="K0111",
            description_en="my product",
            common_name_en="common",
            kcals_per_unit=550,
            parent=parent,
        )
        ClassifiedProductFactory(cpc="K01111")
        LivelihoodActivityFactory(livelihood_strategy__product=product)
        # test filter by cpc exact match
        response = self.client.get(self.url, {"cpc": "K0111"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 1)
        # test filter by cpc startswith
        response = self.client.get(self.url, {"cpc": "K01"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 1)
        # test filter by cpc lowercase/case in-sensitive
        response = self.client.get(self.url, {"cpc": "k0111"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)
        # test filter by product not having a strategy
        response = self.client.get(self.url, {"cpc": "K01111"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 0)


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

    def test_filter_by_country(self):
        country = CountryFactory(
            iso3166a2="AA",
            iso3166a3="AAA",
            iso3166n3=911,
            iso_en_ro_name="A Country",
            iso_en_name="AA Country",
            name="AA Country",
        )
        BaselineLivelihoodActivityFactory(livelihood_zone_baseline__livelihood_zone__country=country)
        response = self.client.get(self.url, {"country": country.iso3166a2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 1)
        response = self.client.get(self.url, {"country": country.iso_en_ro_name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)


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

    def test_filter_by_country(self):
        country = CountryFactory(
            iso3166a2="AA",
            iso3166a3="AAA",
            iso3166n3=911,
            iso_en_ro_name="A Country",
            iso_en_name="AA Country",
            name="AA Country",
        )
        ResponseLivelihoodActivityFactory(livelihood_zone_baseline__livelihood_zone__country=country)
        response = self.client.get(self.url, {"country": country.iso3166a2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content)), 1)
        response = self.client.get(self.url, {"country": country.iso_en_ro_name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(response.content.decode("utf-8"))), 1)


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
            "community_full_name",
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
            "community_full_name",
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
            "community_full_name",
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
                "price": self.data[0].price,
                "income": self.data[0].income,
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
            "community_full_name",
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
                "quantity_sold": self.data[0].quantity_sold,
                "price": self.data[0].price,
                "income": self.data[0].income,
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
            "community_full_name",
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
                "price": self.data[0].price,
                "income": self.data[0].income,
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
            "community_full_name",
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
                "quantity_purchased": self.data[0].quantity_purchased,
                "price": self.data[0].price,
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
            "community_full_name",
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
            "community_full_name",
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
                "price": self.data[0].price,
                "income": self.data[0].income,
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
            "community_full_name",
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
                "price": self.data[0].price,
                "income": self.data[0].income,
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
            "community_full_name",
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
                "price": self.data[0].price,
                "income": self.data[0].income,
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
            "community_full_name",
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
                "price": self.data[0].price,
                "income": self.data[0].income,
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
            "community_full_name",
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
                "price": self.data[0].price,
                "income": self.data[0].income,
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
            "community_full_name",
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
                "price": self.data[0].price,
                "expenditure": self.data[0].expenditure,
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


class LivelihoodActivitySummaryViewSetTestCase(APITestCase):
    PRODUCT_DEFINITIONS = (
        ("R01122", "Maize (corn), other", "Maize/corn grain"),
        ("R01142", "Sorghum, other", "Sorghum grain"),
        ("S86119", "Other support services to crop production", "Other cropping inputs"),
        ("S86121", "Farm animal husbandry services on inputs owned by others", "Livestock care"),
        ("S88537", "Stone cutting, shaping and finishing services", "Stone cutting"),
        ("P34510", "Wood charcoal", "Charcoal Sales"),
    )
    WEALTH_GROUP_CATEGORIES = {"VP": 1, "P": 2}

    @classmethod
    def setUpTestData(cls):
        for cpc, description_en, common_name_en in cls.PRODUCT_DEFINITIONS:
            product = ClassifiedProductFactory(
                cpc=cpc,
                description_en=f"{description_en} description",
                common_name_en=common_name_en,
            )
            for code in ["ML01", "ML02"]:
                zone = LivelihoodZoneFactory(code=code)
                for reference_year in [2011, 2025]:
                    baseline = LivelihoodZoneBaselineFactory(
                        livelihood_zone=zone, reference_year_end_date=datetime.date(reference_year, 9, 30)
                    )
                    # Create communities
                    for community_code in range(2):
                        community = CommunityFactory(
                            livelihood_zone_baseline=baseline, name=f"Community {community_code}"
                        )
                        # Create community wealth groups and activities
                        for wealth_category, wealth_group_category_ordering in cls.WEALTH_GROUP_CATEGORIES.items():
                            wealth_group = CommunityWealthGroupFactory(
                                livelihood_zone_baseline=baseline,
                                wealth_group_category__code=wealth_category,
                                wealth_group_category__ordering=wealth_group_category_ordering,
                                community=community,
                            )
                            cls._create_livelihood_activities(wealth_group, product)
                    # Create baseline wealth groups and activities
                    for wealth_category, wealth_group_category_ordering in cls.WEALTH_GROUP_CATEGORIES.items():
                        wealth_group = BaselineWealthGroupFactory(
                            livelihood_zone_baseline=baseline,
                            wealth_group_category__code=wealth_category,
                            wealth_group_category__ordering=wealth_group_category_ordering,
                        )
                        cls._create_livelihood_activities(wealth_group, product)
        activity_df = pd.DataFrame(
            LivelihoodActivity.objects.filter(
                livelihood_zone_baseline__livelihood_zone__code__in=["ML01", "ML02"],
                # The LivelihoodActivitySummaryViewSet only aggregates Baseline-level LivelihoodActivities.
                wealth_group__community__isnull=True,
            )
            .annotate(
                livelihood_zone=F("livelihood_zone_baseline__livelihood_zone__code"),
                livelihood_zone_baseline_name=F("livelihood_zone_baseline__name_en"),
                reference_year_end_date=F("livelihood_zone_baseline__reference_year_end_date"),
                product=F("livelihood_strategy__product__cpc"),
                wealth_group_category=F("wealth_group__wealth_group_category__code"),
                wealth_group_category_ordering=F("wealth_group__wealth_group_category__ordering"),
            )
            .values()
        )
        activity_df["livelihood_zone_baseline"] = activity_df["livelihood_zone_baseline_id"]
        activity_df["reference_year_end_date"] = activity_df["reference_year_end_date"].apply(lambda x: x.isoformat())
        cls.activity_df = activity_df
        cls.url = reverse("livelihoodactivitysummary-list")

    @classmethod
    def _create_livelihood_activities(cls, wealth_group, product):
        # Response Livelihood Activities are always Baseline-level
        scenarios = (
            LivelihoodActivityScenario.values if not wealth_group.community else [LivelihoodActivityScenario.BASELINE]
        )
        for scenario in scenarios:
            if product.cpc in ["R01122", "R01142"]:
                CropProductionFactory(
                    livelihood_zone_baseline=wealth_group.livelihood_zone_baseline,
                    wealth_group=wealth_group,
                    livelihood_strategy__product=product,
                    scenario=scenario,
                )
            elif product.cpc in ["S86119", "S86121"]:
                OtherPurchaseFactory(
                    livelihood_zone_baseline=wealth_group.livelihood_zone_baseline,
                    wealth_group=wealth_group,
                    livelihood_strategy__product=product,
                    scenario=scenario,
                )
            elif product.cpc in ["S88537", "P34510"]:
                OtherCashIncomeFactory(
                    livelihood_zone_baseline=wealth_group.livelihood_zone_baseline,
                    wealth_group=wealth_group,
                    livelihood_strategy__product=product,
                    scenario=scenario,
                )

    def test_summary_contains_all_rows(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), len(self.activity_df))

    def test_summary_uses_filters(self):
        response = self.client.get(self.url, {"scenario": LivelihoodActivityScenario.BASELINE})
        self.assertLess(
            len(self.activity_df[self.activity_df["scenario"] == LivelihoodActivityScenario.BASELINE]),
            len(self.activity_df),
        )
        self.assertGreaterEqual(
            len(self.activity_df[self.activity_df["scenario"] == LivelihoodActivityScenario.BASELINE]), 1
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(response.json()),
            len(self.activity_df[self.activity_df["scenario"] == LivelihoodActivityScenario.BASELINE]),
        )

    def test_summary_returns_row_aggregates_per_baseline_and_scenario(self):
        fields = ["livelihood_zone", "reference_year_end_date", "scenario"]
        expected = self.activity_df.groupby(fields).agg(
            kcals_consumed=("kcals_consumed", "sum"),
            income=("income", "sum"),
            expenditure=("expenditure", "sum"),
            percentage_kcals=("percentage_kcals", "sum"),
        )
        response = self.client.get(self.url, {"fields": ",".join(fields)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), len(expected))
        for row in response.json():
            expected_row = expected.loc[*[row[field] for field in fields]]
            self.assertEqual(row["kcals_consumed_sum_row"], expected_row["kcals_consumed"])
            self.assertEqual(row["income_sum_row"], expected_row["income"])
            self.assertEqual(row["expenditure_sum_row"], expected_row["expenditure"])
            self.assertAlmostEqual(row["percentage_kcals_sum_row"], expected_row["percentage_kcals"])
            self.assertNotIn("kcals_consumed_sum_slice", row)
            self.assertNotIn("income_sum_slice", row)
            self.assertNotIn("expenditure_sum_slice", row)
            self.assertNotIn("kcals_consumed_sum_slice_percentage_of_row", row)
            self.assertNotIn("income_sum_slice_percentage_of_row", row)
            self.assertNotIn("expenditure_sum_slice_percentage_of_row", row)

    def check_row_against_expected_slices(self, row, fields, expected, expected_slice):
        expected_row = expected.loc[*[row[field] for field in fields]]
        try:
            expected_slice_row = expected_slice.loc[*[row[field] for field in fields]]
        except KeyError:
            expected_slice_row = {
                "kcals_consumed": 0,
                "income": 0,
                "expenditure": 0,
                "percentage_kcals": 0,
            }
        self.assertEqual(
            row["kcals_consumed_sum_row"], expected_row["kcals_consumed"], "Mismatch in kcals_consumed_sum_row"
        )
        self.assertEqual(row["income_sum_row"], expected_row["income"], "Mismatch in income_sum_row")
        self.assertEqual(row["expenditure_sum_row"], expected_row["expenditure"], "Mismatch in expenditure_sum_row")
        self.assertAlmostEqual(
            row["percentage_kcals_sum_row"],
            expected_row["percentage_kcals"],
            msg="Mismatch in percentage_kcals_sum_row",
        )
        self.assertEqual(
            row["kcals_consumed_sum_slice"],
            expected_slice_row["kcals_consumed"],
            "Mismatch in kcals_consumed_sum_slice",
        )
        self.assertEqual(row["income_sum_slice"], expected_slice_row["income"], "Mismatch in income_sum_slice")
        self.assertEqual(
            row["expenditure_sum_slice"],
            expected_slice_row["expenditure"],
            "Mismatch in expenditure_sum_slice",
        )
        if expected_row["kcals_consumed"] == 0:
            self.assertEqual(row["kcals_consumed_sum_slice_percentage_of_row"], 0)
        else:
            self.assertAlmostEqual(
                row["kcals_consumed_sum_slice_percentage_of_row"],
                (expected_slice_row["kcals_consumed"] / expected_row["kcals_consumed"]) * 100,
            )
        if expected_row["income"] == 0:
            self.assertEqual(row["income_sum_slice_percentage_of_row"], 0)
        else:
            self.assertAlmostEqual(
                row["income_sum_slice_percentage_of_row"],
                (expected_slice_row["income"] / expected_row["income"]) * 100,
            )
        if expected_row["expenditure"] == 0:
            self.assertEqual(row["expenditure_sum_slice_percentage_of_row"], 0)
        else:
            self.assertAlmostEqual(
                row["expenditure_sum_slice_percentage_of_row"],
                (expected_slice_row["expenditure"] / expected_row["expenditure"]) * 100,
            )

    def test_summary_supports_product_slices(self):
        fields = ["livelihood_zone_baseline", "scenario"]
        expected = self.activity_df.groupby(fields).agg(
            kcals_consumed=("kcals_consumed", "sum"),
            income=("income", "sum"),
            expenditure=("expenditure", "sum"),
            percentage_kcals=("percentage_kcals", "sum"),
        )
        expected_slice = (
            self.activity_df[self.activity_df["product"] == "R01122"]
            .groupby(fields)
            .agg(
                kcals_consumed=("kcals_consumed", "sum"),
                income=("income", "sum"),
                expenditure=("expenditure", "sum"),
                percentage_kcals=("percentage_kcals", "sum"),
            )
        )
        response = self.client.get(self.url, {"fields": ",".join(fields), "slice_by_product": "R01122"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), len(expected))
        for row in response.json():
            with self.subTest(row=row):
                self.check_row_against_expected_slices(row, fields, expected, expected_slice)

    def test_summary_supports_strategy_type_slices(self):
        fields = ["livelihood_zone_baseline", "scenario"]
        expected = self.activity_df.groupby(fields).agg(
            kcals_consumed=("kcals_consumed", "sum"),
            income=("income", "sum"),
            expenditure=("expenditure", "sum"),
            percentage_kcals=("percentage_kcals", "sum"),
        )
        expected_slice = (
            self.activity_df[self.activity_df["strategy_type"] == "CropProduction"]
            .groupby(fields)
            .agg(
                kcals_consumed=("kcals_consumed", "sum"),
                income=("income", "sum"),
                expenditure=("expenditure", "sum"),
                percentage_kcals=("percentage_kcals", "sum"),
            )
        )
        response = self.client.get(self.url, {"fields": ",".join(fields), "slice_by_strategy_type": "CropProduction"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), len(expected))
        for row in response.json():
            with self.subTest(row=row):
                self.check_row_against_expected_slices(row, fields, expected, expected_slice)

    def test_ordering(self):
        fields = ["wealth_group_category_ordering", "strategy_type", "reference_year_end_date"]
        expected = (
            self.activity_df.groupby(fields)
            .size()
            .reset_index()[fields]
            .sort_values(
                by=["wealth_group_category_ordering", "strategy_type", "reference_year_end_date"],
                ascending=[True, True, False],
            )
            .to_dict("records")
        )
        response = self.client.get(
            self.url,
            {
                "fields": ",".join(fields),
                "ordering": "wealth_group_category_ordering,strategy_type,-reference_year_end_date",
            },
        )
        self.assertEqual(response.status_code, 200)
        response_rows = [{field: row[field] for field in fields} for row in response.json()]
        self.assertEqual(response_rows, expected)

    def test_summary_supports_combined_product_and_strategy_type_slices(self):
        fields = ["livelihood_zone_baseline", "scenario"]
        expected = self.activity_df.groupby(fields).agg(
            kcals_consumed=("kcals_consumed", "sum"),
            income=("income", "sum"),
            expenditure=("expenditure", "sum"),
            percentage_kcals=("percentage_kcals", "sum"),
        )
        expected_slice = (
            self.activity_df[
                (self.activity_df["product"] == "R01122") & (self.activity_df["strategy_type"] == "CropProduction")
            ]
            .groupby(fields)
            .agg(
                kcals_consumed=("kcals_consumed", "sum"),
                income=("income", "sum"),
                expenditure=("expenditure", "sum"),
                percentage_kcals=("percentage_kcals", "sum"),
            )
        )
        response = self.client.get(
            self.url,
            {"fields": ",".join(fields), "slice_by_product": "R01122", "slice_by_strategy_type": "CropProduction"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), len(expected))
        for row in response.json():
            with self.subTest(row=row):
                self.check_row_against_expected_slices(row, fields, expected, expected_slice)

    def test_min_max_row_filter(self):
        fields = ["livelihood_zone_baseline", "scenario", "wealth_group_category"]
        expected = self.activity_df.groupby(fields).agg(
            kcals_consumed=("kcals_consumed", "sum"),
            income=("income", "sum"),
            expenditure=("expenditure", "sum"),
            percentage_kcals=("percentage_kcals", "sum"),
        )
        target_row = expected[expected["kcals_consumed"] > 0].sample(n=1).iloc[0]
        min_value = target_row["kcals_consumed"] - 1
        max_value = target_row["kcals_consumed"] + 1
        matched_rows = expected[
            (expected["kcals_consumed"] >= min_value) & (expected["kcals_consumed"] <= max_value)
        ].reset_index()
        response = self.client.get(
            self.url,
            {
                "fields": ",".join(fields),
                "min_kcals_consumed_sum_row": min_value,
                "max_kcals_consumed_sum_row": max_value,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), len(matched_rows))
        for row in response.json():
            self.assertIn(row["livelihood_zone_baseline"], list(matched_rows["livelihood_zone_baseline"]))
            self.assertIn(row["scenario"], list(matched_rows["scenario"]))
            self.assertIn(row["kcals_consumed_sum_row"], list(matched_rows["kcals_consumed"]))

    def test_min_max_slice_filter(self):
        fields = ["livelihood_zone_baseline", "scenario", "wealth_group_category"]
        expected_slice = (
            self.activity_df[
                (self.activity_df["product"] == "R01122") & (self.activity_df["strategy_type"] == "CropProduction")
            ]
            .groupby(fields)
            .agg(
                kcals_consumed=("kcals_consumed", "sum"),
                income=("income", "sum"),
                expenditure=("expenditure", "sum"),
                percentage_kcals=("percentage_kcals", "sum"),
            )
        )
        target_row = expected_slice[expected_slice["income"] > 0].sample(n=1).iloc[0]
        min_value = target_row["income"] - 1
        max_value = target_row["income"] + 1
        matched_rows = expected_slice[
            (expected_slice["income"] >= min_value) & (expected_slice["income"] <= max_value)
        ].reset_index()
        response = self.client.get(
            self.url,
            {
                "fields": ",".join(fields),
                "slice_by_product": "R01122",
                "slice_by_strategy_type": "CropProduction",
                "min_income_sum_slice": min_value,
                "max_income_sum_slice": max_value,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), len(matched_rows))
        for row in response.json():
            self.assertIn(row["livelihood_zone_baseline"], list(matched_rows["livelihood_zone_baseline"]))
            self.assertIn(row["scenario"], list(matched_rows["scenario"]))
            self.assertIn(row["income_sum_slice"], list(matched_rows["income"]))

    def test_min_only_slice_filter(self):
        fields = ["livelihood_zone_baseline", "scenario", "wealth_group_category"]
        expected_slice = (
            self.activity_df[
                (self.activity_df["product"] == "R01122") & (self.activity_df["strategy_type"] == "CropProduction")
            ]
            .groupby(fields)
            .agg(
                kcals_consumed=("kcals_consumed", "sum"),
                income=("income", "sum"),
                expenditure=("expenditure", "sum"),
                percentage_kcals=("percentage_kcals", "sum"),
            )
        )
        target_row = expected_slice[expected_slice["income"] > 0].sample(n=1).iloc[0]
        min_value = target_row["income"] - 1
        matched_rows = expected_slice[(expected_slice["income"] >= min_value)].reset_index()
        response = self.client.get(
            self.url,
            {
                "fields": ",".join(fields),
                "slice_by_product": "R01122",
                "slice_by_strategy_type": "CropProduction",
                "min_income_sum_slice": min_value,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), len(matched_rows))
        for row in response.json():
            self.assertIn(row["livelihood_zone_baseline"], list(matched_rows["livelihood_zone_baseline"]))
            self.assertIn(row["scenario"], list(matched_rows["scenario"]))
            self.assertIn(row["income_sum_slice"], list(matched_rows["income"]))

    def test_min_max_percentage_filter(self):
        fields = ["livelihood_zone_baseline", "scenario", "wealth_group_category"]
        expected = self.activity_df.groupby(fields).agg(
            kcals_consumed=("kcals_consumed", "sum"),
            income=("income", "sum"),
            expenditure=("expenditure", "sum"),
            percentage_kcals=("percentage_kcals", "sum"),
        )
        expected_slice = (
            self.activity_df[
                (self.activity_df["product"] == "R01122") & (self.activity_df["strategy_type"] == "CropProduction")
            ]
            .groupby(fields)
            .agg(
                kcals_consumed=("kcals_consumed", "sum"),
                income=("income", "sum"),
                expenditure=("expenditure", "sum"),
                percentage_kcals=("percentage_kcals", "sum"),
            )
        )
        expected_slice["total_income"] = expected.loc[expected_slice.index]["income"]
        expected_slice["percentage_income"] = (
            expected_slice["income"] / expected.loc[expected_slice.index]["income"] * 100
        )
        target_row = expected_slice[expected_slice["percentage_income"] > 0].sample(n=1).iloc[0]
        min_value = target_row["percentage_income"] - 1
        max_value = target_row["percentage_income"] + 1
        matched_rows = expected_slice[
            (expected_slice["percentage_income"] >= min_value) & (expected_slice["percentage_income"] <= max_value)
        ].reset_index()
        response = self.client.get(
            self.url,
            {
                "fields": ",".join(fields),
                "slice_by_product": "R01122",
                "slice_by_strategy_type": "CropProduction",
                "min_income_sum_slice_percentage_of_row": min_value,
                "max_income_sum_slice_percentage_of_row": max_value,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), len(matched_rows))
        for row in response.json():
            self.assertIn(row["livelihood_zone_baseline"], list(matched_rows["livelihood_zone_baseline"]))
            self.assertIn(row["scenario"], list(matched_rows["scenario"]))
            self.assertIn(row["income_sum_slice"], list(matched_rows["income"]))
            self.assertIn(row["income_sum_row"], list(matched_rows["total_income"]))

    def test_incorrect_use_of_slice_filters_is_ignored(self):
        response = self.client.get(
            self.url,
            {
                "fields": "livelihood_zone_baseline,scenario",
                "min_income_sum_slice_percentage_of_row": 50,
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_slices_require_matching_product_and_strategy(self):
        response = self.client.get(
            self.url,
            {
                "fields": "livelihood_zone_baseline,scenario",
                "slice_by_product": "R01122",
                "slice_by_strategy_type": "OtherCashIncome",
            },
        )
        self.assertEqual(response.status_code, 200)
        for row in response.json():
            self.assertEqual(row["kcals_consumed_sum_slice"], 0)
            self.assertEqual(row["kcals_consumed_sum_slice_percentage_of_row"], 0)
            self.assertEqual(row["income_sum_slice"], 0)
            self.assertEqual(row["income_sum_slice_percentage_of_row"], 0)
            self.assertEqual(row["expenditure_sum_slice"], 0)
            self.assertEqual(row["expenditure_sum_slice_percentage_of_row"], 0)

    def test_baseline_explorer_example(self):
        response = self.client.get(
            self.url,
            {
                "fields": "livelihood_zone_baseline,livelihood_zone_baseline_name,livelihood_zone,wealth_group_category,country",
                "min_kcals_consumed_sum_slice_percentage_of_row": 1,
                "slice_by_product": "R01122",
            },
        )
        self.assertEqual(response.status_code, 200)


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
