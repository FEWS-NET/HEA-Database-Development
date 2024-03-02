import re
from datetime import datetime

from bs4 import BeautifulSoup
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import activate

from baseline.admin import (
    CommunityCropProductionAdmin,
    CommunityLivestockAdmin,
    LivelihoodActivityAdmin,
    WealthGroupAdmin,
)
from baseline.models import (
    CommunityCropProduction,
    CommunityLivestock,
    LivelihoodActivity,
    LivelihoodActivityScenario,
    LivelihoodZoneBaseline,
    WealthGroup,
)
from baseline.tests.factories import (
    ButterProductionFactory,
    CommunityCropProductionFactory,
    CommunityFactory,
    CommunityLivestockFactory,
    CropProductionFactory,
    FoodPurchaseFactory,
    LivelihoodActivityFactory,
    LivelihoodStrategyFactory,
    LivelihoodZoneBaselineFactory,
    LivelihoodZoneFactory,
    LivestockSaleFactory,
    MeatProductionFactory,
    MilkProductionFactory,
    SourceOrganizationFactory,
    WealthGroupCharacteristicValueFactory,
    WealthGroupFactory,
)
from common.tests.factories import ClassifiedProductFactory
from metadata.models import LivelihoodStrategyType
from metadata.tests.factories import (
    LivelihoodCategoryFactory,
    SeasonFactory,
    WealthGroupCategoryFactory,
)


class SourceOrganizationAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username="admin", password="admin", email="admin@hea.org")
        cls.source_organization1 = SourceOrganizationFactory()
        cls.source_organization2 = SourceOrganizationFactory()
        activate("en")
        cls.url = reverse("admin:baseline_sourceorganization_changelist")

    def setUp(self):
        self.client.login(username="admin", password="admin")

    def test_sourceorganization_admin_changelists(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.source_organization1.name)

    def test_sourceorganization_search_fields(self):
        response = self.client.get(
            self.url,
            {"q": self.source_organization1.name},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.source_organization1.name)
        self.assertNotContains(response, self.source_organization2.name)


class CommunityAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username="admin", password="admin", email="admin@hea.org")
        cls.community1 = CommunityFactory(name="Dobley", full_name="Dobley, Kasungu")
        cls.community2 = CommunityFactory(name="Zukeyla", full_name="Zukeyla, Kasungu")
        activate("en")
        cls.url = reverse("admin:baseline_community_changelist")

    def setUp(self):
        self.client.login(username="admin", password="admin")

    def test_community_changelists(self):
        response = self.client.get(reverse("admin:baseline_community_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.community1.name)

    def test_community_search_fields(self):
        response = self.client.get(
            self.url,
            {"q": self.community1.name},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.community1.full_name)
        self.assertNotContains(response, self.community2.full_name)


class LivelihoodZoneAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username="admin", password="admin", email="admin@hea.org")
        cls.livelihood_zone1 = LivelihoodZoneFactory()
        cls.livelihood_zone2 = LivelihoodZoneFactory()
        activate("en")
        cls.url = reverse("admin:baseline_livelihoodzone_changelist")

    def setUp(self):
        self.client.login(username="admin", password="admin")

    def test_livelihoodzone_changelists(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.livelihood_zone1.name)

    def test_search_livelihood_zone(self):
        response = self.client.get(
            self.url,
            {"q": self.livelihood_zone2.name_en},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.livelihood_zone2.name)
        self.assertNotContains(response, self.livelihood_zone1.name)

    def test_filter_livelihood_zone(self):
        response = self.client.get(
            self.url,
            {"country": self.livelihood_zone1.country.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.livelihood_zone1.name)
        self.assertNotContains(response, self.livelihood_zone2.name)


class LivelihoodZoneBaselineAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username="admin", password="admin", email="admin@hea.org")
        cls.source_organization1 = SourceOrganizationFactory()
        cls.livelihood_zone_baseline1 = LivelihoodZoneBaselineFactory(
            source_organization=cls.source_organization1,
            reference_year_start_date=datetime(2015, 5, 1),
            reference_year_end_date=datetime(2016, 4, 30),
        )
        cls.livelihood_zone_baseline2 = LivelihoodZoneBaselineFactory()
        activate("en")
        cls.url = reverse("admin:baseline_livelihoodzonebaseline_changelist")

    def setUp(self):
        self.client.login(username="admin", password="admin")

    def test_livelihoodzonebaseline_changelists(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.livelihood_zone_baseline1.livelihood_zone.code)

    def test_search_livelihood_zone_baseline_fields(self):
        response = self.client.get(
            self.url,
            {"q": self.livelihood_zone_baseline1.livelihood_zone.name_en},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.livelihood_zone_baseline1.livelihood_zone)
        self.assertNotContains(response, self.livelihood_zone_baseline2.livelihood_zone)

        response = self.client.get(
            self.url,
            {"q": self.livelihood_zone_baseline2.livelihood_zone.name},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.livelihood_zone_baseline2.livelihood_zone)
        self.assertNotContains(response, self.livelihood_zone_baseline1.livelihood_zone)

    def test_livelihood_zone_baseline_list_filter(self):
        response = self.client.get(
            self.url,
            {"source_organization__id__exact": self.livelihood_zone_baseline1.source_organization.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.livelihood_zone_baseline1.source_organization.name)
        self.assertNotContains(response, self.livelihood_zone_baseline2.livelihood_zone)

    def test_livelihood_zone_baseline_date_hierarchy(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.livelihood_zone_baseline1.reference_year_start_date.year)
        self.assertContains(response, self.livelihood_zone_baseline2.reference_year_start_date.year)

    def test_create_livelihood_zone_baseline(self):
        bss = SimpleUploadedFile("test_bss.xlsx", b"Baseline content placeholder, just to be used for testing ...")
        livelihood_zone = LivelihoodZoneFactory(name_en="New Test Zone")
        current_count = LivelihoodZoneBaseline.objects.all().count()
        data = {
            "name_en": f"{livelihood_zone.code} Baseline",
            "description": f"{livelihood_zone.code} Baseline description",
            "livelihood_zone": livelihood_zone.pk,
            "main_livelihood_category": LivelihoodCategoryFactory().pk,
            "source_organization": SourceOrganizationFactory().pk,
            "bss": bss,
            "reference_year_start_date": "2023-01-01",
            "reference_year_end_date": "2023-12-31",
            "valid_from_date": "2023-01-01",
            "valid_to_date": "2033-12-31",
            "population_source": "New Test Source",
            "population_estimate": 15000,
        }
        response = self.client.post(reverse("admin:baseline_livelihoodzonebaseline_add"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(LivelihoodZoneBaseline.objects.all().count(), current_count + 1)
        self.assertTrue(LivelihoodZoneBaseline.objects.filter(livelihood_zone=livelihood_zone).exists())


class LivelihoodStrategyAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username="admin", password="admin", email="admin@hea.org")
        cls.strategy1 = LivelihoodStrategyFactory(
            livelihood_zone_baseline=LivelihoodZoneBaselineFactory(),
            strategy_type=LivelihoodStrategyType.MILK_PRODUCTION,
        )
        cls.strategy2 = LivelihoodStrategyFactory(
            livelihood_zone_baseline=LivelihoodZoneBaselineFactory(),
            strategy_type=LivelihoodStrategyType.CROP_PRODUCTION,
        )
        activate("en")
        cls.url = reverse("admin:baseline_livelihoodstrategy_changelist")

    def setUp(self):
        self.client.login(username="admin", password="admin")

    def test_livelihoodstrategy_changelists(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.strategy1.strategy_type)

    def test_livelihoodstrategy_search_fields(self):
        response = self.client.get(
            self.url,
            {"q": self.strategy1.livelihood_zone_baseline.livelihood_zone.name_en},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.strategy1.product.cpc)
        self.assertNotContains(response, self.strategy2.product.cpc)

    def test_livelihoodstrategy_list_filter(self):
        response = self.client.get(
            self.url,
            {"strategy_type": self.strategy2.strategy_type},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.strategy2.product.cpc)
        self.assertNotContains(response, self.strategy1.product.cpc)


class WealthGroupAdminTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username="admin", password="admin", email="admin@hea.org")
        cls.wealth_group1 = WealthGroupFactory()
        cls.url = "admin:baseline_wealthgroup_change"
        cls.site = AdminSite()
        activate("en")

    def setUp(self):
        self.client.login(username="admin", password="admin")

    def test_wealth_group_admin_display(self):
        response = self.client.get(reverse(self.url, args=[self.wealth_group1.pk]))

        # Ensure that the response contains the fields we expect
        self.assertContains(response, "community")
        self.assertContains(response, "wealth_group_category")
        self.assertContains(response, "percentage_of_households")
        # Using BeautifulSoup test that response content on html controls are populated as expected
        soup = BeautifulSoup(response.content, "html.parser")

        livelihood_zone_baseline = soup.find("select", {"id": "id_livelihood_zone_baseline"})
        selected_livelihood_zone_baseline = livelihood_zone_baseline.find("option", selected=True)
        self.assertEqual(
            int(selected_livelihood_zone_baseline["value"]), self.wealth_group1.livelihood_zone_baseline.pk
        )

        self.assertEqual(
            int(soup.find("input", {"id": "id_percentage_of_households"})["value"]),
            self.wealth_group1.percentage_of_households,
        )

    def test_wealth_group_admin_save_model(self):
        community = CommunityFactory()
        self.assertEqual(WealthGroup.objects.filter(community=community).count(), 0)
        wealth_group = WealthGroup(
            **{
                "livelihood_zone_baseline": LivelihoodZoneBaselineFactory(),
                "community": community,
                "wealth_group_category": WealthGroupCategoryFactory(),
                "percentage_of_households": 30,
                "average_household_size": 7,
            }
        )

        url = "admin:baseline_wealthgroup_add"
        request = self.client.get(reverse(url))

        admin_instance = WealthGroupAdmin(model=WealthGroup, admin_site=self.site)
        admin_instance.save_model(request, wealth_group, None, None)

        self.assertEqual(WealthGroup.objects.filter(community=community).count(), 1)
        saved_wealth_group = WealthGroup.objects.get(community=community)
        self.assertEqual(saved_wealth_group.percentage_of_households, wealth_group.percentage_of_households)

    def test_wealth_characteristic_inline_admin_display(self):
        wealth_group_characteristic_value = WealthGroupCharacteristicValueFactory(
            wealth_group=self.wealth_group1, value=2.5, min_value=2, max_value=4
        )

        response = self.client.get(reverse(self.url, args=[self.wealth_group1.pk]))
        self.assertContains(response, "Wealth Characteristic")

        soup = BeautifulSoup(response.content, "html.parser")

        wealth_group_characteristic1 = soup.find(
            "select", {"id": "id_wealthgroupcharacteristicvalue_set-0-wealth_characteristic"}
        )
        wealth_group_characteristic1 = wealth_group_characteristic1.find("option", selected=True)
        self.assertEqual(
            wealth_group_characteristic1["value"], wealth_group_characteristic_value.wealth_characteristic_id
        )
        value = re.sub(r"[\n\r\t]", "", soup.select("#id_wealthgroupcharacteristicvalue_set-0-value")[0].text)
        min_value = re.sub(r"[\n\r\t]", "", soup.select("#id_wealthgroupcharacteristicvalue_set-0-min_value")[0].text)
        max_value = re.sub(r"[\n\r\t]", "", soup.select("#id_wealthgroupcharacteristicvalue_set-0-max_value")[0].text)
        self.assertEqual(float(value), wealth_group_characteristic_value.value)
        self.assertEqual(float(min_value), wealth_group_characteristic_value.min_value)
        self.assertEqual(float(max_value), wealth_group_characteristic_value.max_value)

    def test_milk_production_inline_admin_display(self):
        milk_production = MilkProductionFactory(wealth_group=self.wealth_group1)

        response = self.client.get(reverse(self.url, args=[self.wealth_group1.pk]))
        self.assertContains(response, "Milk Production")

        # Ensure that the response contains the fields from MilkProductionInlineAdmin
        self.assertContains(response, "milking_animals")
        self.assertContains(response, "lactation_days")
        self.assertContains(response, "daily_production")

        soup = BeautifulSoup(response.content, "html.parser")

        milk_production_strategy_select = soup.find("select", {"id": "id_milkproduction_set-0-livelihood_strategy"})
        milk_production_strategy_select = milk_production_strategy_select.find("option", selected=True)
        self.assertEqual(int(milk_production_strategy_select["value"]), milk_production.livelihood_strategy.pk)

        self.assertEqual(
            int(soup.find("input", {"id": "id_milkproduction_set-0-milking_animals"})["value"]),
            milk_production.milking_animals,
        )
        self.assertEqual(
            int(soup.find("input", {"id": "id_milkproduction_set-0-lactation_days"})["value"]),
            milk_production.lactation_days,
        )
        self.assertEqual(
            int(soup.find("input", {"id": "id_milkproduction_set-0-daily_production"})["value"]),
            milk_production.daily_production,
        )

    def test_butter_production_inline_admin_display(self):
        butter_production = ButterProductionFactory(wealth_group=self.wealth_group1)

        response = self.client.get(reverse(self.url, args=[self.wealth_group1.pk]))
        self.assertContains(response, "Butter Production")
        soup = BeautifulSoup(response.content, "html.parser")

        butter_production_strategy_select = soup.find(
            "select", {"id": "id_butterproduction_set-0-livelihood_strategy"}
        )
        butter_production_strategy_select = butter_production_strategy_select.find("option", selected=True)
        self.assertEqual(int(butter_production_strategy_select["value"]), butter_production.livelihood_strategy.pk)
        butterproduction_set_scenario = soup.find("select", {"id": "id_butterproduction_set-0-scenario"}).find(
            "option", selected=True
        )
        self.assertEqual(butterproduction_set_scenario["value"], butter_production.scenario)

    def test_meat_production_inline_admin_display(self):
        meat_production = MeatProductionFactory(wealth_group=self.wealth_group1)
        response = self.client.get(reverse(self.url, args=[self.wealth_group1.pk]))
        self.assertContains(response, "Meat Production")
        soup = BeautifulSoup(response.content, "html.parser")

        meat_production_strategy_select = soup.find("select", {"id": "id_meatproduction_set-0-livelihood_strategy"})
        meat_production_strategy_select = meat_production_strategy_select.find("option", selected=True)
        self.assertEqual(int(meat_production_strategy_select["value"]), meat_production.livelihood_strategy.pk)

        meatproduction_set_scenario = soup.find("select", {"id": "id_meatproduction_set-0-scenario"}).find(
            "option", selected=True
        )
        self.assertEqual(meatproduction_set_scenario["value"], meat_production.scenario)
        # Ensure that the response contains the fields from MeatProductionInlineAdmin
        self.assertContains(response, "animals_slaughtered")
        self.assertContains(response, "animals_slaughtered")

    def test_livestock_sales_inline_admin_display(self):
        livestock_sales = LivestockSaleFactory(wealth_group=self.wealth_group1)

        self.site.register(WealthGroup, WealthGroupAdmin)
        url = reverse(self.url, args=[self.wealth_group1.pk])
        response = self.client.get(url)

        self.assertContains(response, "Livestock Sale")

        soup = BeautifulSoup(response.content, "html.parser")

        livestock_sales_strategy_select = soup.find("select", {"id": "id_livestocksale_set-0-livelihood_strategy"})
        livestock_sales_strategy_select = livestock_sales_strategy_select.find("option", selected=True)
        self.assertEqual(int(livestock_sales_strategy_select["value"]), livestock_sales.livelihood_strategy.pk)

    def test_crop_production_inline_admin_display(self):
        crop_production = CropProductionFactory(wealth_group=self.wealth_group1)

        self.site.register(WealthGroup, WealthGroupAdmin)
        url = reverse(self.url, args=[self.wealth_group1.pk])
        response = self.client.get(url)

        self.assertContains(response, "Crop Production")

        soup = BeautifulSoup(response.content, "html.parser")

        crop_production_strategy_select = soup.find("select", {"id": "id_cropproduction_set-0-livelihood_strategy"})
        crop_production_strategy_select = crop_production_strategy_select.find("option", selected=True)
        self.assertEqual(int(crop_production_strategy_select["value"]), crop_production.livelihood_strategy.pk)

    def test_food_purchase_production_inline_admin_display(self):
        food_purchase = FoodPurchaseFactory(wealth_group=self.wealth_group1)

        self.site.register(WealthGroup, WealthGroupAdmin)
        url = reverse(self.url, args=[self.wealth_group1.pk])
        response = self.client.get(url)

        self.assertContains(response, "Food Purchase")
        self.assertContains(response, "unit_multiple")
        self.assertContains(response, "times_per_month")
        self.assertContains(response, "months_per_year")

        soup = BeautifulSoup(response.content, "html.parser")

        food_purchase_strategy_select = soup.find("select", {"id": "id_foodpurchase_set-0-livelihood_strategy"})
        food_purchase_strategy_select = food_purchase_strategy_select.find("option", selected=True)
        self.assertEqual(int(food_purchase_strategy_select["value"]), food_purchase.livelihood_strategy.pk)

        self.assertEqual(
            float(soup.find("input", {"id": "id_foodpurchase_set-0-unit_multiple"})["value"]),
            food_purchase.unit_multiple,
        )
        self.assertEqual(
            float(soup.find("input", {"id": "id_foodpurchase_set-0-times_per_month"})["value"]),
            food_purchase.times_per_month,
        )
        self.assertEqual(
            float(soup.find("input", {"id": "id_foodpurchase_set-0-months_per_year"})["value"]),
            food_purchase.months_per_year,
        )


class CommunityCropProductionAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username="admin", password="admin", email="admin@hea.org")
        cls.url = "admin:baseline_communitycropproduction_changelist"
        cls.community1 = CommunityFactory(name="Test Community")
        cls.season1 = SeasonFactory()
        cls.cropproduction1 = CommunityCropProductionFactory(community__name=cls.community1, season__name_en="SeasonQ")
        cls.cropproduction2 = CommunityCropProductionFactory()
        cls.cropproduction3 = CommunityCropProductionFactory()
        cls.site = AdminSite()

        activate("en")

    def setUp(self):
        self.client.login(username="admin", password="admin")
        self.admin = CommunityCropProductionAdmin(model=CommunityCropProduction, admin_site=self.site)

    def test_fields(self):
        fields = [
            "community",
            "crop",
            "crop_purpose",
            "season",
            "yield_with_inputs",
            "yield_without_inputs",
            "seed_requirement",
            "crop_unit_of_measure",
            "land_unit_of_measure",
        ]
        self.assertEqual(list(self.admin.fields), fields)
        list_display = [
            "community",
            "crop",
            "season",
            "yield_with_inputs",
            "yield_without_inputs",
            "crop_unit_of_measure",
            "land_unit_of_measure",
        ]
        self.assertEqual(list(self.admin.list_display), list_display)

    def test_list_community_crop_production(self):
        response = self.client.get(reverse(self.url))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cropproduction1.community.full_name)
        self.assertContains(response, self.cropproduction2.crop)
        self.assertContains(response, self.cropproduction2.yield_with_inputs)
        self.assertContains(response, self.cropproduction2.yield_without_inputs)

    def test_search_fields(self):
        # Also confirms *translation_fields() is working correctly
        search_fields = (
            "crop__description_en",
            "crop__description_fr",
            "crop__description_ar",
            "crop__description_es",
            "crop__description_pt",
            "crop_purpose",
            "season__name_en",
            "season__name_fr",
            "season__name_ar",
            "season__name_es",
            "season__name_pt",
        )
        self.assertCountEqual(
            self.admin.search_fields,
            search_fields,
            "CommunityCropProductionAdmin: "
            f"Fields expected: {search_fields}. Fields found: {self.admin.search_fields}.",
        )
        response = self.client.get(reverse(self.url), {"q": self.cropproduction1.crop.description})
        self.assertEqual(response.status_code, 200)
        # Parse the HTML content of the response
        soup = BeautifulSoup(response.content, "html.parser")

        # Find the table rows in the result set
        table_rows = soup.find_all("tr")
        self.assertEqual(len(table_rows), 2)
        # Check that the table rows only contain the filtered results
        self.assertIn(str(self.cropproduction1.crop), table_rows[1].get_text())
        self.assertNotIn(str(self.cropproduction2.crop), table_rows[1].get_text())

    def test_filter_community_crop_production(self):
        response = self.client.get(
            reverse(self.url), {"community__full_name": self.cropproduction1.community.full_name}
        )
        self.assertEqual(response.status_code, 200)

        # Parse the HTML content of the response
        soup = BeautifulSoup(response.content, "html.parser")

        # Find the table rows in the result set
        table_rows = soup.find_all("tr")
        self.assertEqual(len(table_rows), 2)
        # Check that the table rows only contain the filtered results
        self.assertIn(str(self.cropproduction1.crop), table_rows[1].get_text())
        self.assertNotIn(str(self.cropproduction2.crop), table_rows[1].get_text())


class CommunityLivestockAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username="admin", password="admin", email="admin@hea.org")
        cls.url = "admin:baseline_communitylivestock_changelist"
        cls.community1 = CommunityFactory(name="Test Community")
        cls.livestockproduction1 = CommunityLivestockFactory(
            community=cls.community1, livestock=ClassifiedProductFactory(cpc="L021001")
        )
        cls.livestockproduction2 = CommunityLivestockFactory(livestock=ClassifiedProductFactory(cpc="L021002"))
        cls.site = AdminSite()
        activate("en")

    def setUp(self):
        self.client.login(username="admin", password="admin")
        self.admin = CommunityLivestockAdmin(model=CommunityLivestock, admin_site=self.site)

    def test_fields(self):
        fields = [
            "community",
            "livestock",
            "birth_interval",
            "wet_season_lactation_period",
            "wet_season_milk_production",
            "dry_season_lactation_period",
            "dry_season_milk_production",
            "age_at_sale",
            "additional_attributes",
        ]
        self.assertEqual(list(self.admin.fields), fields)
        list_display = [
            "community",
            "livestock",
            "wet_season_milk_production",
            "dry_season_milk_production",
        ]
        self.assertEqual(list(self.admin.list_display), list_display)

    def test_list_community_livestock(self):
        response = self.client.get(reverse(self.url))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.livestockproduction1.community.full_name)
        self.assertContains(response, self.livestockproduction2.livestock)
        self.assertContains(response, self.livestockproduction2.wet_season_milk_production)
        self.assertContains(response, self.livestockproduction2.dry_season_milk_production)

    def test_filter_community_livestock(self):
        response = self.client.get(
            reverse(self.url), {"community__full_name": self.livestockproduction1.community.full_name}
        )
        self.assertEqual(response.status_code, 200)

        # Parse the HTML content of the response
        soup = BeautifulSoup(response.content, "html.parser")

        # Find the table rows in the result set
        table_rows = soup.find_all("tr")
        self.assertEqual(len(table_rows), 2)

        # Check that the table rows only contain the filtered results
        self.assertIn(str(self.livestockproduction1.livestock), table_rows[1].get_text())
        self.assertNotIn(str(self.livestockproduction2.livestock), table_rows[1].get_text())


class LivelihoodActivityAdminTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username="admin", password="password", email="admin@hea.org")
        cls.livelihood_zone_baseline1 = LivelihoodZoneBaselineFactory()
        cls.livelihood_zone_baseline2 = LivelihoodZoneBaselineFactory()
        cls.livelihood_strategy1 = LivelihoodStrategyFactory(
            livelihood_zone_baseline=cls.livelihood_zone_baseline1,
            strategy_type=LivelihoodStrategyType.MILK_PRODUCTION,
        )
        cls.livelihood_strategy2 = LivelihoodStrategyFactory(
            livelihood_zone_baseline=cls.livelihood_zone_baseline2, strategy_type=LivelihoodStrategyType.FISHING
        )
        cls.activity1 = LivelihoodActivityFactory(
            livelihood_strategy=cls.livelihood_strategy1,
            strategy_type=LivelihoodStrategyType.MILK_PRODUCTION,
            livelihood_zone_baseline=cls.livelihood_zone_baseline1,
            wealth_group__livelihood_zone_baseline=cls.livelihood_zone_baseline1,
            scenario=LivelihoodActivityScenario.BASELINE,
        )
        cls.activity2 = LivelihoodActivityFactory(
            livelihood_strategy=cls.livelihood_strategy2,
            strategy_type=LivelihoodStrategyType.FISHING,
            livelihood_zone_baseline=cls.livelihood_zone_baseline2,
            wealth_group__livelihood_zone_baseline=cls.livelihood_zone_baseline2,
            scenario=LivelihoodActivityScenario.BASELINE,
        )
        cls.activity3 = LivelihoodActivityFactory(
            livelihood_strategy=cls.livelihood_strategy2,
            strategy_type=LivelihoodStrategyType.FISHING,
            livelihood_zone_baseline=cls.livelihood_zone_baseline2,
            wealth_group__livelihood_zone_baseline=cls.livelihood_zone_baseline2,
            scenario=LivelihoodActivityScenario.RESPONSE,
        )
        cls.site = AdminSite()
        activate("en")

    def setUp(self):
        self.client.login(username="admin", password="password")

    def test_search(self):
        url = reverse("admin:baseline_livelihoodactivity_changelist") + "?q=" + self.livelihood_strategy1.strategy_type
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, "html.parser")
        result_list = soup.find(id="result_list")
        result_list_str = str(result_list)
        self.assertIn(self.livelihood_strategy1.strategy_type, result_list_str)
        self.assertNotIn(self.livelihood_strategy2.strategy_type, result_list_str)

        url = (
            reverse("admin:baseline_livelihoodactivity_changelist")
            + "?q="
            + self.livelihood_strategy1.additional_identifier
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, "html.parser")
        result_list = soup.find(id="result_list")
        result_list_str = str(result_list)
        self.assertIn(self.livelihood_strategy1.strategy_type, result_list_str)
        self.assertNotIn(self.livelihood_strategy2.strategy_type, result_list_str)

    def test_get_product_common_name(self):
        modeladmin = LivelihoodActivityAdmin(LivelihoodActivity, self.site)
        self.assertEqual(
            modeladmin.get_product_common_name(self.activity1), self.livelihood_strategy1.product.common_name
        )

    def test_get_season_name(self):
        modeladmin = LivelihoodActivityAdmin(LivelihoodActivity, self.site)
        self.assertEqual(modeladmin.get_season_name(self.activity2), self.livelihood_strategy2.season.name)

    def test_get_country_name(self):
        modeladmin = LivelihoodActivityAdmin(LivelihoodActivity, self.site)
        self.assertEqual(
            modeladmin.get_country_name(self.activity1), self.livelihood_zone_baseline1.livelihood_zone.country.name
        )

    def test_filter(self):
        url = (
            reverse("admin:baseline_livelihoodactivity_changelist")
            + "?strategy_type="
            + self.livelihood_strategy1.strategy_type
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_filters(self):
        base_url = reverse("admin:baseline_livelihoodactivity_changelist")
        country_name = self.livelihood_zone_baseline1.livelihood_zone.country.name
        filters = {
            "strategy_type": self.livelihood_strategy1.strategy_type,
            "scenario": self.activity3.scenario,
            "livelihood_strategy__product__cpc": self.livelihood_strategy1.product.cpc,
            "livelihood_strategy__season__id__exact": self.livelihood_strategy2.season.pk,  # This will be an int
            "livelihood_zone_baseline__livelihood_zone__country__name": country_name,
        }

        for filter_name, filter_value in filters.items():
            with self.subTest(filter=filter_name):
                query_string = f"?{filter_name}={filter_value}"
                response = self.client.get(base_url + query_string)
                self.assertEqual(response.status_code, 200)

                soup = BeautifulSoup(response.content, "html.parser")
                result_list = soup.find(id="result_list")
                result_list_str = str(result_list)

                self.assertIn(str(filter_value), result_list_str)
