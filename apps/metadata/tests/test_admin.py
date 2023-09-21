from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import activate

from metadata.admin import (
    HazardCategoryAdmin,
    MarketAdmin,
    SeasonalActivityTypeAdmin,
    WealthCategoryAdmin,
    WealthCharacteristicAdmin,
)
from metadata.models import (
    HazardCategory,
    Market,
    SeasonalActivityType,
    WealthCategory,
    WealthCharacteristic,
)

from .factories import (
    HazardCategoryFactory,
    MarketFactory,
    SeasonalActivityTypeFactory,
    SeasonFactory,
    WealthCategoryFactory,
    WealthCharacteristicFactory,
)


class ReferenceDataAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.superuser = User.objects.create_superuser(username="admin", password="admin", email="admin@hea.org")

        cls.wealth_category1 = WealthCategoryFactory(code="TP", name="Très Pauvre", aliases=["vp", "tp"])
        cls.wealth_category2 = WealthCategoryFactory(code="MV", name="Mieux vaut", aliases=["b/o"])
        cls.wealth_characteristic1 = WealthCharacteristicFactory(
            code="area cultivated (acres)",
            name="Land area cultivated (acres)",
            aliases=["land area cultivated (acres)"],
        )
        cls.wealth_characteristic2 = WealthCharacteristicFactory(
            code="fruit tree",
            name="Fruit Tree",
            aliases=["fruit trees", "other (fruit tree)"],
        )

        cls.seasonal_activity_type1 = SeasonalActivityTypeFactory(
            code="LP", name="land preparation", description="Preparation of land for crop", aliases=["Land prep"]
        )
        cls.seasonal_activity_type2 = SeasonalActivityTypeFactory(
            code="P", name="planting", description="planting", aliases=["seeding"]
        )
        cls.market1 = MarketFactory(name="Waamo market", aliases=["wa`mo"])
        cls.market2 = MarketFactory(name="Farjano maret", aliases=["franjo"])
        cls.hazard_category1 = HazardCategoryFactory(name="Drought", description="Drought")
        cls.hazard_category2 = HazardCategoryFactory(name="Frost", description="Frost")

    def setUp(self):
        self.client.force_login(self.superuser)
        self.site = AdminSite()
        activate("en")

    def test_common_admin_functionality(self):
        # Test common admin functionality for all child model admins
        models = [
            (WealthCharacteristic, WealthCharacteristicAdmin),
            (SeasonalActivityType, SeasonalActivityTypeAdmin),
            (WealthCategory, WealthCategoryAdmin),
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
            WealthCategory,
            Market,
            HazardCategory,
        ]

        for model in models:
            with self.subTest(model=model):
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

                elif "wealthcategory" in url:
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
        activate("en")

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
