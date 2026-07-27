import re
from datetime import datetime

from bs4 import BeautifulSoup
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse
from django.utils.translation import activate

from baseline.admin import (
    CommunityCropProductionAdmin,
    CommunityLivestockAdmin,
    CopingStrategyAdmin,
    EventAdmin,
    ExpandabilityFactorAdmin,
    HazardAdmin,
    KeyParameterAdmin,
    LivelihoodActivityAdmin,
    LivelihoodStrategyAdmin,
    LivelihoodZoneBaselineAdmin,
    LivelihoodZoneBaselineCorrectionInlineAdmin,
    MarketPriceAdmin,
    SeasonalActivityAdmin,
    SeasonalActivityOccurrenceAdmin,
    SeasonalProductionPerformanceAdmin,
    WealthGroupAdmin,
    WealthGroupCharacteristicValueAdmin,
)
from baseline.models import (
    CommunityCropProduction,
    CommunityLivestock,
    KeyParameter,
    LivelihoodActivity,
    LivelihoodActivityScenario,
    LivelihoodProductCategory,
    LivelihoodZoneBaseline,
    LivelihoodZoneBaselineCorrection,
    WealthGroup,
)
from baseline.tests.factories import (
    BaselineWealthGroupFactory,
    ButterProductionFactory,
    CommunityCropProductionFactory,
    CommunityFactory,
    CommunityLivestockFactory,
    CropProductionFactory,
    FoodPurchaseFactory,
    KeyParameterFactory,
    LivelihoodActivityFactory,
    LivelihoodProductCategoryFactory,
    LivelihoodStrategyFactory,
    LivelihoodZoneBaselineFactory,
    LivelihoodZoneFactory,
    LivestockSaleFactory,
    MeatProductionFactory,
    MilkProductionFactory,
    SourceOrganizationFactory,
    WealthCharacteristicFactory,
    WealthGroupCharacteristicValueFactory,
    WealthGroupFactory,
)
from common.tests.factories import (
    ClassifiedProductFactory,
    CurrencyFactory,
    UnitOfMeasureFactory,
)
from metadata.models import LivelihoodStrategyType, WealthGroupCategory
from metadata.tests.factories import (
    LivelihoodSystemFactory,
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
        cls.baseline_with_poor_main_staple = LivelihoodZoneBaselineFactory()
        cls.poor_wealth_group = BaselineWealthGroupFactory(
            livelihood_zone_baseline=cls.baseline_with_poor_main_staple,
            wealth_group_category__code=WealthGroupCategory.POOR,
            average_household_size=5,
        )
        cls.poor_main_staple_activity = FoodPurchaseFactory(
            livelihood_zone_baseline=cls.baseline_with_poor_main_staple,
            wealth_group=cls.poor_wealth_group,
            extra={"product__kcals_per_unit": 100},
        )
        cls.poor_other_food_activity = FoodPurchaseFactory(
            livelihood_zone_baseline=cls.baseline_with_poor_main_staple,
            wealth_group=cls.poor_wealth_group,
        )
        LivelihoodProductCategoryFactory(
            baseline_livelihood_activity=cls.poor_main_staple_activity,
            basket=LivelihoodProductCategory.ProductBasket.MAIN_STAPLE,
            percentage_allocation_to_basket=1,
        )
        LivelihoodProductCategoryFactory(
            baseline_livelihood_activity=cls.poor_other_food_activity,
            basket=LivelihoodProductCategory.ProductBasket.SURVIVAL_OTHER_FOOD,
            percentage_allocation_to_basket=0.25,
        )
        cls.poor_non_food_activity = FoodPurchaseFactory(
            livelihood_zone_baseline=cls.baseline_with_poor_main_staple,
            wealth_group=cls.poor_wealth_group,
        )
        LivelihoodProductCategoryFactory(
            baseline_livelihood_activity=cls.poor_non_food_activity,
            basket=LivelihoodProductCategory.ProductBasket.SURVIVAL_NON_FOOD,
            percentage_allocation_to_basket=0.2,
        )
        cls.baseline_with_poor_main_staple.save()
        activate("en")
        cls.url = reverse("admin:baseline_livelihoodzonebaseline_changelist")
        cls.site = AdminSite()

    def setUp(self):
        self.client.login(username="admin", password="admin")

    def test_livelihoodzonebaseline_changelists(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.livelihood_zone_baseline1.livelihood_zone.code)

    def test_change_form_displays_bss_metadata_in_additional_section(self):
        response = self.client.get(
            reverse(
                "admin:baseline_livelihoodzonebaseline_change",
                args=[self.livelihood_zone_baseline1.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, "html.parser")
        additional = soup.find("h2", string="Additional").find_parent("fieldset")
        self.assertIsNotNone(additional.select_one(".field-bss_content_hash"))
        self.assertIsNotNone(additional.select_one(".field-bss_uploaded_datetime"))
        self.assertIsNotNone(additional.select_one(".field-bss_size"))
        self.assertEqual(
            additional.select_one(".field-bss_content_hash label").get_text(strip=True),
            "BSS Content Hash:",
        )
        self.assertIn(
            self.livelihood_zone_baseline1.bss_uploaded_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            additional.select_one(".field-bss_uploaded_datetime").get_text(),
        )
        self.assertIn(
            f"{self.livelihood_zone_baseline1.bss_size:,} bytes",
            additional.select_one(".field-bss_size").get_text(),
        )

    def test_correction_inline_eager_loads_natural_key_relations(self):
        correction = LivelihoodZoneBaselineCorrection.objects.create(
            livelihood_zone_baseline=self.livelihood_zone_baseline1,
            worksheet_name=LivelihoodZoneBaselineCorrection.WorksheetName.DATA,
            cell_range="A1",
            previous_value="old",
            value="new",
            author=User.objects.get(username="admin"),
            comment="Corrected value",
        )
        request = RequestFactory().get("/")
        request.user = User.objects.get(username="admin")
        inline = LivelihoodZoneBaselineCorrectionInlineAdmin(LivelihoodZoneBaseline, self.site)
        loaded_correction = inline.get_queryset(request).get(pk=correction.pk)

        with self.assertNumQueries(0):
            loaded_correction.natural_key()
            str(loaded_correction)

    def test_correction_inline_reuses_author_choices(self):
        author = User.objects.get(username="admin")
        for cell_range in ("A1", "A2"):
            LivelihoodZoneBaselineCorrection.objects.create(
                livelihood_zone_baseline=self.livelihood_zone_baseline1,
                worksheet_name=LivelihoodZoneBaselineCorrection.WorksheetName.DATA,
                cell_range=cell_range,
                previous_value="old",
                value="new",
                author=author,
                comment="Corrected value",
            )
        request = RequestFactory().get("/")
        request.user = author
        inline = LivelihoodZoneBaselineCorrectionInlineAdmin(LivelihoodZoneBaseline, self.site)
        formset_class = inline.get_formset(request, obj=self.livelihood_zone_baseline1)
        queryset = inline.get_queryset(request).filter(livelihood_zone_baseline=self.livelihood_zone_baseline1)
        forms = formset_class(instance=self.livelihood_zone_baseline1, queryset=queryset).forms

        choices = forms[0].fields["author"].choices
        self.assertEqual(choices, forms[1].fields["author"].choices)
        with self.assertNumQueries(0):
            str(forms[0]["author"])
            str(forms[1]["author"])

    def test_search_livelihood_zone_baseline_fields(self):
        response = self.client.get(
            self.url,
            {"q": self.livelihood_zone_baseline1.name_en},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.livelihood_zone_baseline1.name_en)
        self.assertNotContains(response, self.livelihood_zone_baseline2.name_en)

        response = self.client.get(
            self.url,
            {"q": self.livelihood_zone_baseline2.name_en},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.livelihood_zone_baseline2.name_en)
        self.assertNotContains(response, self.livelihood_zone_baseline1.name_en)

        response = self.client.get(
            self.url,
            {"q": self.livelihood_zone_baseline1.livelihood_zone.code},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.livelihood_zone_baseline1.livelihood_zone)
        self.assertNotContains(response, self.livelihood_zone_baseline2.livelihood_zone)

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

    def test_livelihood_zone_baseline_displays_poor_baseline_summary_fields(self):
        response = self.client.get(
            reverse("admin:baseline_livelihoodzonebaseline_change", args=[self.baseline_with_poor_main_staple.pk])
        )

        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, "html.parser")

        poor_main_staple = soup.select_one(".field-poor_main_staple .readonly")
        self.assertIsNotNone(poor_main_staple)
        self.assertEqual(
            poor_main_staple.get_text(strip=True),
            str(self.baseline_with_poor_main_staple.poor_main_staple),
        )

        poor_household_size = soup.select_one(".field-poor_household_size .readonly")
        self.assertIsNotNone(poor_household_size)
        self.assertEqual(
            float(poor_household_size.get_text(strip=True)),
            self.baseline_with_poor_main_staple.poor_household_size,
        )

        poor_survival_non_food_expenditure = soup.select_one(".field-poor_survival_non_food_expenditure .readonly")
        self.assertIsNotNone(poor_survival_non_food_expenditure)
        self.assertEqual(
            float(poor_survival_non_food_expenditure.get_text(strip=True)),
            self.baseline_with_poor_main_staple.poor_survival_non_food_expenditure,
        )

    def test_create_livelihood_zone_baseline(self):
        bss = SimpleUploadedFile("test_bss.xlsx", b"Baseline content placeholder, just to be used for testing ...")
        livelihood_zone = LivelihoodZoneFactory(name_en="New Test Zone")
        current_count = LivelihoodZoneBaseline.objects.all().count()
        currency = CurrencyFactory()
        data = {
            "name_en": f"{livelihood_zone.code} Baseline",
            "description": f"{livelihood_zone.code} Baseline description",
            "livelihood_zone": livelihood_zone.pk,
            "primary_livelihood_system": LivelihoodSystemFactory().pk,
            "source_organization": SourceOrganizationFactory().pk,
            "bss": bss,
            "currency": currency,
            "reference_year_start_date": "2023-01-01",
            "reference_year_end_date": "2023-12-31",
            "valid_from_date": "2023-01-01",
            "valid_to_date": "2033-12-31",
            "population_source": "New Test Source",
            "population_estimate": 15000,
            # Management form data for corrections formset
            "corrections-TOTAL_FORMS": "0",
            "corrections-INITIAL_FORMS": "0",
            "corrections-MIN_NUM_FORMS": "0",
            "corrections-MAX_NUM_FORMS": "1000",
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
            {"q": self.strategy1.livelihood_zone_baseline.name_en},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.strategy1.product.cpc)
        self.assertNotContains(response, self.strategy2.product.cpc)

    def test_livelihoodstrategy_search_by_natural_key(self):
        zone_code = self.strategy1.livelihood_zone_baseline.livelihood_zone.code
        ref_end_date = self.strategy1.livelihood_zone_baseline.reference_year_end_date.isoformat()
        response = self.client.get(self.url, {"q": f"{zone_code}: {ref_end_date}"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.strategy1.product.cpc)
        self.assertNotContains(response, self.strategy2.product.cpc)

    def test_livelihoodstrategy_search_by_code_and_year(self):
        zone_code = self.strategy1.livelihood_zone_baseline.livelihood_zone.code
        ref_end_date = self.strategy1.livelihood_zone_baseline.reference_year_end_date
        response = self.client.get(self.url, {"q": f"{zone_code} {ref_end_date.year}"})
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


class KeyParameterAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username="admin", password="admin", email="admin@hea.org")
        cls.key_parameter1 = KeyParameterFactory(
            livelihood_strategy=LivelihoodStrategyFactory(additional_identifier="alpha"),
            monitor_quantity=True,
            monitor_price=False,
        )
        cls.key_parameter2 = KeyParameterFactory(
            livelihood_strategy=LivelihoodStrategyFactory(additional_identifier="beta"),
            monitor_quantity=False,
            monitor_price=True,
        )
        activate("en")
        cls.url = reverse("admin:baseline_keyparameter_changelist")
        cls.site = AdminSite()

    def setUp(self):
        self.client.login(username="admin", password="admin")
        self.admin = KeyParameterAdmin(model=KeyParameter, admin_site=self.site)

    def test_keyparameter_changelists(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.key_parameter1.livelihood_strategy.product.cpc)

    def test_keyparameter_search_fields(self):
        response = self.client.get(self.url, {"q": self.key_parameter1.livelihood_strategy.additional_identifier})
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, "html.parser")
        result_list = soup.find(id="result_list")
        result_list_str = str(result_list)
        self.assertIn(self.key_parameter1.livelihood_strategy.product.cpc, result_list_str)
        self.assertNotIn(self.key_parameter2.livelihood_strategy.product.cpc, result_list_str)


class WealthGroupAdminTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username="admin", password="admin", email="admin@hea.org")
        cls.wealth_group1 = WealthGroupFactory()
        cls.population_baseline = LivelihoodZoneBaselineFactory(
            population_source="Government statistics agency",
            population_estimate=1000,
        )
        cls.baseline_wealth_group = BaselineWealthGroupFactory(
            livelihood_zone_baseline=cls.population_baseline,
            percentage_of_households=0.6,
            average_household_size=4,
        )
        BaselineWealthGroupFactory(
            livelihood_zone_baseline=cls.population_baseline,
            percentage_of_households=0.4,
            average_household_size=6,
        )
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
            float(soup.find("input", {"id": "id_percentage_of_households"})["value"]),
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
                "percentage_of_households": 0.30,
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

    def test_wealth_group_admin_displays_serializer_readonly_fields(self):
        response = self.client.get(reverse(self.url, args=[self.baseline_wealth_group.pk]))

        soup = BeautifulSoup(response.content, "html.parser")

        for field_name in (
            "household_annual_kcals_cost",
            "survival_threshold_as_percentage_kcals",
            "survival_threshold_as_cash",
            "livelihoods_protection_threshold_as_percentage_kcals",
            "livelihoods_protection_threshold_as_cash",
            "population_source",
            "percentage_of_population",
            "population_estimate",
        ):
            self.assertIsNotNone(soup.select_one(f".field-{field_name}"), field_name)

        population_source = soup.select_one(".field-population_source .readonly")
        self.assertIsNotNone(population_source)
        self.assertEqual(population_source.get_text(strip=True), self.population_baseline.population_source)

        percentage_of_population = soup.select_one(".field-percentage_of_population .readonly")
        self.assertIsNotNone(percentage_of_population)
        self.assertAlmostEqual(float(percentage_of_population.get_text(strip=True)), 0.5)

        population_estimate = soup.select_one(".field-population_estimate .readonly")
        self.assertIsNotNone(population_estimate)
        self.assertEqual(int(population_estimate.get_text(strip=True)), 500)

    def test_wealth_group_search_by_livelihood_zone_code(self):
        other_wealth_group = WealthGroupFactory()

        response = self.client.get(
            reverse("admin:baseline_wealthgroup_changelist"),
            {"q": self.wealth_group1.livelihood_zone_baseline.livelihood_zone.code},
        )

        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, "html.parser")
        result_list = soup.find(id="result_list")
        result_list_str = str(result_list)
        self.assertIn(f"/admin/baseline/wealthgroup/{self.wealth_group1.pk}/change/", result_list_str)
        self.assertNotIn(f"/admin/baseline/wealthgroup/{other_wealth_group.pk}/change/", result_list_str)

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
            "community__full_name",
            "community__livelihood_zone_baseline__livelihood_zone__code",
            "community__livelihood_zone_baseline__livelihood_zone__alternate_code",
            "community__livelihood_zone_baseline__name_en",
            "community__livelihood_zone_baseline__name_fr",
            "community__livelihood_zone_baseline__name_ar",
            "community__livelihood_zone_baseline__name_es",
            "community__livelihood_zone_baseline__name_pt",
            "community__livelihood_zone_baseline__reference_year_end_date",
            "crop__description_en",
            "crop__description_fr",
            "crop__description_ar",
            "crop__description_es",
            "crop__description_pt",
            "crop__common_name_en",
            "crop__common_name_fr",
            "crop__common_name_ar",
            "crop__common_name_es",
            "crop__common_name_pt",
            "crop__cpc__iexact",
            "crop__aliases",
            "crop_purpose",
            "season__name_en",
            "season__name_fr",
            "season__name_ar",
            "season__name_es",
            "season__name_pt",
            "season__aliases",
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

    def test_search_fields(self):
        search_fields = (
            "community__full_name",
            "community__livelihood_zone_baseline__livelihood_zone__code",
            "community__livelihood_zone_baseline__livelihood_zone__alternate_code",
            "community__livelihood_zone_baseline__name_en",
            "community__livelihood_zone_baseline__name_fr",
            "community__livelihood_zone_baseline__name_ar",
            "community__livelihood_zone_baseline__name_es",
            "community__livelihood_zone_baseline__name_pt",
            "community__livelihood_zone_baseline__reference_year_end_date",
            "livestock__common_name_en",
            "livestock__common_name_fr",
            "livestock__common_name_ar",
            "livestock__common_name_es",
            "livestock__common_name_pt",
            "livestock__description_en",
            "livestock__description_fr",
            "livestock__description_ar",
            "livestock__description_es",
            "livestock__description_pt",
            "livestock__cpc__iexact",
            "livestock__aliases",
        )
        self.assertCountEqual(self.admin.search_fields, search_fields)


class BaselineRelatedAdminSearchFieldsTestCase(SimpleTestCase):
    def test_search_fields_include_livelihood_zone_code_for_baseline_related_admins(self):
        admin_search_fields = {
            LivelihoodZoneBaselineAdmin: {"livelihood_zone__code"},
            LivelihoodStrategyAdmin: {"livelihood_zone_baseline__livelihood_zone__code"},
            KeyParameterAdmin: {"livelihood_strategy__livelihood_zone_baseline__livelihood_zone__code"},
            LivelihoodActivityAdmin: {"livelihood_zone_baseline__livelihood_zone__code"},
            WealthGroupCharacteristicValueAdmin: {"wealth_group__livelihood_zone_baseline__livelihood_zone__code"},
            WealthGroupAdmin: {"livelihood_zone_baseline__livelihood_zone__code"},
            SeasonalActivityAdmin: {"livelihood_zone_baseline__livelihood_zone__code"},
            SeasonalActivityOccurrenceAdmin: {"seasonal_activity__livelihood_zone_baseline__livelihood_zone__code"},
            CommunityCropProductionAdmin: {"community__livelihood_zone_baseline__livelihood_zone__code"},
            CommunityLivestockAdmin: {"community__livelihood_zone_baseline__livelihood_zone__code"},
            MarketPriceAdmin: {"community__livelihood_zone_baseline__livelihood_zone__code"},
            HazardAdmin: {"community__livelihood_zone_baseline__livelihood_zone__code"},
            SeasonalProductionPerformanceAdmin: {"community__livelihood_zone_baseline__livelihood_zone__code"},
            EventAdmin: {"community__livelihood_zone_baseline__livelihood_zone__code"},
            ExpandabilityFactorAdmin: {
                "wealth_group__livelihood_zone_baseline__livelihood_zone__code",
            },
            CopingStrategyAdmin: {
                "wealth_group__livelihood_zone_baseline__livelihood_zone__code",
            },
        }

        for admin_class, expected_fields in admin_search_fields.items():
            with self.subTest(admin_class=admin_class.__name__):
                self.assertTrue(expected_fields.issubset(set(admin_class.search_fields)))


class LivelihoodActivityAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username="admin", password="password", email="admin@hea.org")
        cls.livelihood_zone_baseline1 = LivelihoodZoneBaselineFactory()
        cls.livelihood_zone_baseline2 = LivelihoodZoneBaselineFactory()
        cls.livelihood_strategy1 = LivelihoodStrategyFactory(
            livelihood_zone_baseline=cls.livelihood_zone_baseline1,
            strategy_type=LivelihoodStrategyType.MILK_PRODUCTION,
            additional_identifier="mukera",
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

    def test_search_by_baseline_natural_key(self):
        zone_code = self.livelihood_zone_baseline1.livelihood_zone.code
        ref_end_date = self.livelihood_zone_baseline1.reference_year_end_date.isoformat()
        natural_key = f"{zone_code}: {ref_end_date}"
        url = reverse("admin:baseline_livelihoodactivity_changelist") + f"?q={natural_key}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, "html.parser")
        result_list = soup.find(id="result_list")
        result_list_str = str(result_list)
        self.assertIn(f'value="{self.activity1.pk}"', result_list_str)
        self.assertNotIn(f'value="{self.activity2.pk}"', result_list_str)

    def test_search_by_baseline_code_and_year(self):
        zone_code = self.livelihood_zone_baseline1.livelihood_zone.code
        ref_end_date = self.livelihood_zone_baseline1.reference_year_end_date
        search_term = f"{zone_code} {ref_end_date.year}"
        url = reverse("admin:baseline_livelihoodactivity_changelist") + f"?q={search_term}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, "html.parser")
        result_list = soup.find(id="result_list")
        result_list_str = str(result_list)
        self.assertIn(f'value="{self.activity1.pk}"', result_list_str)
        self.assertNotIn(f'value="{self.activity2.pk}"', result_list_str)

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
        country = self.livelihood_zone_baseline1.livelihood_zone.country
        filters = {
            "strategy_type": self.livelihood_strategy1.strategy_type,
            "scenario": self.activity3.scenario,
            "livelihood_zone_baseline__id__exact": self.livelihood_zone_baseline1.pk,
            "wealth_group__wealth_group_category": self.activity1.wealth_group.wealth_group_category.pk,
            "livelihood_strategy__product__cpc": self.livelihood_strategy1.product.cpc,
            "livelihood_strategy__season__id__exact": self.livelihood_strategy2.season.pk,
            "livelihood_zone_baseline__livelihood_zone__country": country.iso3166a2,
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


class WealthGroupCharacteristicValueAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username="admin", password="password", email="hea@test.com")
        cls.wealth_group1 = WealthGroupFactory()
        wealth_category = WealthGroupCategoryFactory(code="BO", name_en="Better Off")
        cls.wealth_group2 = WealthGroupFactory(wealth_group_category=wealth_category)
        cls.product1 = ClassifiedProductFactory()
        cls.wealth_characteristic1 = WealthCharacteristicFactory(has_product=True, has_unit_of_measure=True)
        cls.wealth_characteristic2 = WealthCharacteristicFactory(has_product=True, has_unit_of_measure=True)
        cls.wealth_group_characteristic_value1 = WealthGroupCharacteristicValueFactory(
            wealth_group=cls.wealth_group1,
            wealth_characteristic=cls.wealth_characteristic1,
            product=cls.product1,
            unit_of_measure=UnitOfMeasureFactory(),
        )
        cls.wealth_group_characteristic_value2 = WealthGroupCharacteristicValueFactory(
            wealth_group=cls.wealth_group2,
            wealth_characteristic=cls.wealth_characteristic2,
            product=ClassifiedProductFactory(),
            unit_of_measure=UnitOfMeasureFactory(),
        )
        cls.site = AdminSite()

    def setUp(self):
        self.client.login(username="admin", password="password")

    def test_search(self):
        url = (
            reverse("admin:baseline_wealthgroupcharacteristicvalue_changelist")
            + "?q="
            + self.wealth_characteristic1.name
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, "html.parser")
        result_list = soup.find(id="result_list")
        result_list_str = str(result_list)
        self.assertIn(self.wealth_characteristic1.name, result_list_str)
        self.assertNotIn(self.wealth_characteristic2.name, result_list_str)

    def test_filters(self):
        base_url = reverse("admin:baseline_wealthgroupcharacteristicvalue_changelist")
        country1 = self.wealth_group1.livelihood_zone_baseline.livelihood_zone.country
        country2 = self.wealth_group2.livelihood_zone_baseline.livelihood_zone.country
        filters = {
            "wealth_group": (
                self.wealth_group1.id,
                self.wealth_group2,
            ),
            "wealth_group__wealth_group_category__code": (
                self.wealth_group1.wealth_group_category.code,
                self.wealth_group2.wealth_group_category.name,
            ),
            "wealth_group__livelihood_zone_baseline__livelihood_zone__country__iso3166a2": (
                country1.iso3166a2,
                country2.iso3166a2,
            ),
            "product": (
                self.product1.cpc,
                self.wealth_group_characteristic_value2.product.cpc,
            ),
        }
        for filter_name, filter_value in filters.items():
            with self.subTest(filter=filter_name):
                query_string = f"?{filter_name}={filter_value[0]}"
                response = self.client.get(base_url + query_string)
                self.assertEqual(response.status_code, 200)
                soup = BeautifulSoup(response.content, "html.parser")
                result_list = soup.find(id="result_list")
                result_list_str = str(result_list)
                self.assertIn(str(filter_value[0]), result_list_str)
                self.assertNotIn(str(filter_value[1]), result_list_str)
