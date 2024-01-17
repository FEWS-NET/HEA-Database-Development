from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from metadata.admin import (
    HazardCategoryAdmin,
    MarketAdmin,
    SeasonalActivityTypeAdmin,
    WealthCharacteristicAdmin,
    WealthGroupCategoryAdmin,
)
from metadata.models import (
    HazardCategory,
    Market,
    SeasonalActivityType,
    WealthCharacteristic,
    WealthGroupCategory,
)

from .factories import (
    HazardCategoryFactory,
    MarketFactory,
    SeasonalActivityTypeFactory,
    SeasonFactory,
    WealthCharacteristicFactory,
    WealthGroupCategoryFactory,
)


class ReferenceDataAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(username="admin", password="admin", email="admin@hea.org")

        cls.wealth_category1 = WealthGroupCategoryFactory(code="TP", name_en="Très Pauvre", aliases=["vp", "tp"])
        cls.wealth_category2 = WealthGroupCategoryFactory(code="MV", name_en="Mieux vaut", aliases=["b/o"])
        cls.wealth_characteristic1 = WealthCharacteristicFactory(
            code="area cultivated (acres)",
            name_en="Land area cultivated (acres)",
            aliases=["land area cultivated (acres)"],
        )
        cls.wealth_characteristic2 = WealthCharacteristicFactory(
            code="fruit tree",
            name_en="Fruit Tree",
            aliases=["fruit trees", "other (fruit tree)"],
        )

        cls.seasonal_activity_type1 = SeasonalActivityTypeFactory(
            code="LP", name_en="land preparation", description_en="Preparation of land for crop", aliases=["Land prep"]
        )
        cls.seasonal_activity_type2 = SeasonalActivityTypeFactory(
            code="P", name_en="planting", description_en="planting", aliases=["seeding"]
        )
        cls.market1 = MarketFactory(name_en="Waamo market", aliases=["wa`mo"])
        cls.market2 = MarketFactory(name_en="Farjano maret", aliases=["franjo"])
        cls.hazard_category1 = HazardCategoryFactory(name_en="Drought", description_en="Drought")
        cls.hazard_category2 = HazardCategoryFactory(name_en="Frost", description_en="Frost")

    def setUp(self):
        self.client.force_login(self.superuser)
        self.site = AdminSite()

    def tearDown(self):
        # Ref: https://docs.djangoproject.com/en/4.2/topics/testing/tools/#setting-the-language
        translation.activate(settings.LANGUAGE_CODE)

    def test_common_admin_functionality(self):
        # Test common admin functionality for all child model admins
        models = [
            (WealthCharacteristic, WealthCharacteristicAdmin),
            (SeasonalActivityType, SeasonalActivityTypeAdmin),
            (WealthGroupCategory, WealthGroupCategoryAdmin),
            (Market, MarketAdmin),
            (HazardCategory, HazardCategoryAdmin),
        ]

        for model, admin_class in models:
            with self.subTest(model=model):
                url = reverse(f"admin:metadata_{model._meta.model_name}_changelist")
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "name")
                self.assertContains(response, "description")

    def test_search_by_name_description_aliases(self):
        # Test search by name, description, and aliases for all child model admins
        models = [
            WealthCharacteristic,
            SeasonalActivityType,
            WealthGroupCategory,
            Market,
            HazardCategory,
        ]

        for model in models:
            for code, _ in settings.LANGUAGES:
                with self.subTest(model=model, language=code):
                    url = reverse(f"admin:metadata_{model._meta.model_name}_changelist")
                    if "wealthcharacteristic" in url:
                        response = self.client.get(url, {"q": self.wealth_characteristic1.name})
                        self.assertContains(response, self.wealth_characteristic1.name)
                        self.assertNotContains(response, self.wealth_characteristic2.name)
                        response = self.client.get(url, {"q": self.wealth_characteristic2.aliases})
                        self.assertContains(response, self.wealth_characteristic2.name)
                        self.assertNotContains(response, self.wealth_characteristic1.name)

                    elif "seasonalactivitytype" in url:
                        response = self.client.get(url, {"q": self.seasonal_activity_type1.name})
                        self.assertContains(response, self.seasonal_activity_type1.name)
                        self.assertNotContains(response, self.seasonal_activity_type2.name)
                        response = self.client.get(url, {"q": self.seasonal_activity_type2.aliases})
                        self.assertContains(response, self.seasonal_activity_type2.name)
                        self.assertNotContains(response, self.seasonal_activity_type1.name)

                    elif "market" in url:
                        response = self.client.get(url, {"q": self.market1.name})
                        self.assertContains(response, self.market1.name)
                        self.assertNotContains(response, self.market2.name)
                        response = self.client.get(url, {"q": self.market2.aliases})
                        self.assertContains(response, self.market2.name)
                        self.assertNotContains(response, self.market1.name)

                    elif "WealthGroupCategory" in url:
                        response = self.client.get(url, {"q": self.wealth_category1.name})
                        self.assertContains(response, self.wealth_category1.name)
                        self.assertNotContains(response, self.wealth_category2.name)
                        response = self.client.get(url, {"q": self.wealth_category2.aliases})
                        self.assertContains(response, self.wealth_category2.name)
                        self.assertNotContains(response, self.wealth_category1.name)

                    elif "hazardcategory" in url:
                        response = self.client.get(url, {"q": self.hazard_category1.name})
                        self.assertContains(response, self.hazard_category1.name)
                        self.assertNotContains(response, self.hazard_category2.name)
                        response = self.client.get(url, {"q": self.hazard_category2.description})
                        self.assertContains(response, self.hazard_category2.name)
                        self.assertNotContains(response, self.hazard_category1.name)

    def test_filter_by_variable_type(self):
        # Test filter by variable_type for WealthCharacteristic
        url = reverse("admin:metadata_wealthcharacteristic_changelist")
        response = self.client.get(url, {"variable_type": self.wealth_characteristic1.variable_type})
        self.assertContains(response, self.wealth_characteristic1.name)
        self.assertNotContains(response, self.wealth_characteristic2.name)
        response = self.client.get(url, {"variable_type": self.wealth_characteristic2.variable_type})
        self.assertContains(response, self.wealth_characteristic2.name)
        self.assertNotContains(response, self.wealth_characteristic1.name)

    def test_filter_by_country(self):
        # Test filter by country for Market
        self.site.register(Market, MarketAdmin)
        url = reverse("admin:metadata_market_changelist")
        response = self.client.get(url, {"country": self.market1.country.iso3166a2})
        self.assertContains(response, self.market1.name)
        self.assertNotContains(response, self.market2.name)


class SeasonAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(username="admin", password="admin", email="admin@hea.org")

        cls.season1 = SeasonFactory()
        cls.season2 = SeasonFactory()

    def setUp(self):
        self.client.force_login(self.superuser)
        self.site = AdminSite()
        translation.activate("en")

    def test_list_display(self):
        url = reverse("admin:metadata_season_changelist")
        response = self.client.get(url)
        self.assertContains(response, "country")
        self.assertContains(response, "name")
        self.assertContains(response, "season_type")
        self.assertContains(response, "start")
        self.assertContains(response, "end")

    def test_search_fields(self):
        url = reverse("admin:metadata_season_changelist")
        response = self.client.get(url, {"q": self.season1.name})
        self.assertContains(response, self.season1.name)
        self.assertNotContains(response, self.season2.name)

    def test_list_filter(self):
        url = reverse("admin:metadata_season_changelist")
        response = self.client.get(url, {"season_type": self.season1.season_type})
        self.assertContains(response, self.season1.name)
        self.assertNotContains(response, self.season2.name)
