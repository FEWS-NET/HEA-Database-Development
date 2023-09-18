import re
from datetime import datetime

from bs4 import BeautifulSoup
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import activate

from baseline.admin import CommunityCropProductionAdmin, WealthGroupAdmin
from baseline.models import CommunityCropProduction, LivelihoodZoneBaseline, WealthGroup
from metadata.tests.factories import (
    LivelihoodCategoryFactory,
    SeasonFactory,
    WealthCategoryFactory,
)

from .factories import (
    ButterProductionFactory,
    CommunityCropProductionFactory,
    CommunityFactory,
    LivelihoodStrategyFactory,
    LivelihoodZoneBaselineFactory,
    LivelihoodZoneFactory,
    MeatProductionFactory,
    MilkProductionFactory,
    SourceOrganizationFactory,
    WealthGroupCharacteristicValueFactory,
    WealthGroupFactory,
)


class BaselineAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username="admin", password="admin", email="admin@hea.org")
        cls.source_organization1 = SourceOrganizationFactory()
        cls.source_organization2 = SourceOrganizationFactory()
        cls.livelihood_zone = LivelihoodZoneFactory()
        cls.livelihood_zone_baseline1 = LivelihoodZoneBaselineFactory(
            source_organization=cls.source_organization1,
            reference_year_start_date=datetime(2015, 5, 1),
            reference_year_end_date=datetime(2016, 4, 30),
        )
        cls.livelihood_zone_baseline2 = LivelihoodZoneBaselineFactory()
        cls.community = CommunityFactory()
        cls.livelihood_strategy = LivelihoodStrategyFactory()
        cls.site = AdminSite()
        activate("en")

    def setUp(self):
        self.client.login(username="admin", password="admin")

    def test_admin_changelists(self):
        response = self.client.get(reverse("admin:baseline_sourceorganization_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.source_organization1.name)

        response = self.client.get(reverse("admin:baseline_livelihoodzone_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.livelihood_zone.name)

        response = self.client.get(reverse("admin:baseline_livelihoodzonebaseline_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.livelihood_zone_baseline1.livelihood_zone.name)

        response = self.client.get(reverse("admin:baseline_community_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.community.name)

        response = self.client.get(reverse("admin:baseline_livelihoodstrategy_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.livelihood_strategy.strategy_type)

    def test_search_livelihood_zone_baseline_fields(self):
        response = self.client.get(
            reverse("admin:baseline_livelihoodzonebaseline_changelist"),
            {"q": self.livelihood_zone_baseline1.livelihood_zone.name},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.livelihood_zone_baseline1.livelihood_zone)
        self.assertNotContains(response, self.livelihood_zone_baseline2.livelihood_zone)

        response = self.client.get(
            reverse("admin:baseline_livelihoodzonebaseline_changelist"),
            {"q": self.livelihood_zone_baseline2.livelihood_zone.name},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.livelihood_zone_baseline2.livelihood_zone)
        self.assertNotContains(response, self.livelihood_zone_baseline1.livelihood_zone)

    def test_livelihood_zone_baseline_list_filter(self):
        response = self.client.get(
            reverse("admin:baseline_livelihoodzonebaseline_changelist"),
            {"source_organization__id__exact": self.livelihood_zone_baseline1.source_organization.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.livelihood_zone_baseline1.source_organization.name)
        self.assertNotContains(response, self.livelihood_zone_baseline2.livelihood_zone)

    def test_livelihood_zone_baseline_date_hierarchy(self):
        response = self.client.get(reverse("admin:baseline_livelihoodzonebaseline_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.livelihood_zone_baseline1.reference_year_start_date.year)
        self.assertContains(response, self.livelihood_zone_baseline2.reference_year_start_date.year)

    def test_create_livelihood_zone_baseline(self):
        bss = SimpleUploadedFile("test_bss.xlsx", b"Baseline content placeholder, just to be used for testing ...")
        livelihood_zone = LivelihoodZoneFactory(name="New Test Zone")
        current_count = LivelihoodZoneBaseline.objects.all().count()
        data = {
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
        self.assertContains(response, "wealth_category")
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
                "wealth_category": WealthCategoryFactory(),
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
        """ """
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


class CommunityCropProductionAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username="admin", password="admin", email="admin@hea.org")
        cls.url = "admin:baseline_communitycropproduction_changelist"
        cls.community1 = CommunityFactory(name="Test Community")
        cls.season1 = SeasonFactory()
        cls.community_cropproduction1 = CommunityCropProductionFactory(
            community__name=cls.community1, season__name="SeasonQ"
        )
        cls.community_cropproduction2 = CommunityCropProductionFactory()
        cls.community_cropproduction3 = CommunityCropProductionFactory()
        cls.site = AdminSite()
        activate("en")

    def setUp(self):
        self.client.login(username="admin", password="admin")

    def test_fields(self):
        fields = [
            "community",
            "crop",
            "crop_purpose",
            "season",
            "yield_with_inputs",
            "yield_without_inputs",
            "seed_requirement",
            "unit_of_measure",
        ]
        self.assertEqual(list(self.admin.fields), fields)
        list_display = ["community", "crop", "season", "yield_with_inputs", "yield_without_inputs", "unit_of_measure"]
        self.assertEqual(list(self.admin.list_display), list_display)

    def test_search_fields(self):
        search_fields = (
            "crop__description",
            "crop_purpose",
            "season__name",
        )
        admin = CommunityCropProductionAdmin(CommunityCropProduction, admin_site=self.site)
        self.assertTrue(all(element in admin.search_fields for element in search_fields))
        response = self.client.get(reverse(self.url), {"q": self.community_cropproduction1.crop.description})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.community_cropproduction1.crop.description)
        self.assertNotContains(response, self.community_cropproduction2.crop.description)
