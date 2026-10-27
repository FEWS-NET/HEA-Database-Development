import datetime

from binary_database_files.models import File
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext

from baseline.models import (
    BaselineLivelihoodActivity,
    FoodPurchase,
    LivelihoodActivity,
    LivelihoodProductCategory,
    LivelihoodZoneBaseline,
    OtherCashIncome,
    OtherPurchase,
    PaymentInKind,
    ReliefGiftOther,
    WealthGroup,
    WealthGroupCharacteristicValue,
)
from common.tests.factories import ClassifiedProductFactory
from common.utils import conditional_logging
from metadata.models import LivelihoodActivityScenario, WealthGroupCategory

from .factories import (
    BaselineWealthGroupFactory,
    CommunityFactory,
    CommunityWealthGroupFactory,
    FoodPurchaseFactory,
    LivelihoodProductCategoryFactory,
    LivelihoodZoneBaselineFactory,
    OtherPurchaseFactory,
    SeasonalActivityFactory,
    WealthGroupCharacteristicValueFactory,
)


class LivelihoodZoneBaselineTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.baseline = LivelihoodZoneBaselineFactory(reference_year_end_date=datetime.date(2024, 12, 31))
        cls.poor_wealth_group = BaselineWealthGroupFactory(
            livelihood_zone_baseline=cls.baseline,
            wealth_group_category__code=WealthGroupCategory.POOR,
            average_household_size=5,
        )
        cls.main_staple_activity = FoodPurchaseFactory(
            livelihood_zone_baseline=cls.baseline,
            wealth_group=cls.poor_wealth_group,
            scenario=LivelihoodActivityScenario.BASELINE,
            extra={"product__kcals_per_unit": 100},
        )
        cls.other_food_activity = FoodPurchaseFactory(
            livelihood_zone_baseline=cls.baseline,
            wealth_group=cls.poor_wealth_group,
            scenario=LivelihoodActivityScenario.BASELINE,
        )
        cls.main_staple_category = LivelihoodProductCategoryFactory(
            baseline_livelihood_activity=cls.main_staple_activity,
            basket=LivelihoodProductCategory.ProductBasket.MAIN_STAPLE,
            percentage_allocation_to_basket=1,
        )
        cls.other_food_category = LivelihoodProductCategoryFactory(
            baseline_livelihood_activity=cls.other_food_activity,
            basket=LivelihoodProductCategory.ProductBasket.SURVIVAL_OTHER_FOOD,
            percentage_allocation_to_basket=0.25,
        )
        cls.non_food_activity = FoodPurchaseFactory(
            livelihood_zone_baseline=cls.baseline,
            wealth_group=cls.poor_wealth_group,
            scenario=LivelihoodActivityScenario.BASELINE,
        )
        cls.non_food_category = LivelihoodProductCategoryFactory(
            baseline_livelihood_activity=cls.non_food_activity,
            basket=LivelihoodProductCategory.ProductBasket.SURVIVAL_NON_FOOD,
            percentage_allocation_to_basket=0.2,
        )
        # Save the Baseline to force the calculation of annual_kcals_cost.
        cls.baseline.save()

    def get_expected_annual_kcals_cost(self):
        # Calculate the expected annual kcals cost.
        # It is defined as the cost of providing 100% of required kcals for the P
        # Wealth Group divided by the average_household_size. The cost is
        # calculated as the cost of Basket 2 (Other food survival) plus the cost
        # of providing the remainder of kcals by purchasing the main staple. All
        # costs are in the currency for the BSS.
        return (
            self.other_food_activity.expenditure * self.other_food_category.percentage_allocation_to_basket
            + (
                (
                    1
                    - (
                        self.other_food_activity.percentage_kcals
                        * self.other_food_category.percentage_allocation_to_basket
                    )
                )
                * 2100
                * 365
                * self.poor_wealth_group.average_household_size
                / self.main_staple_activity.extra["product__kcals_per_unit"]
                * self.main_staple_activity.price
            )
        ) / self.poor_wealth_group.average_household_size

    def test_calculate_fields_stores_annual_kcals_cost(self):
        expected_annual_kcals_cost = self.get_expected_annual_kcals_cost()
        self.assertAlmostEqual(self.baseline.annual_kcals_cost, expected_annual_kcals_cost)
        self.assertAlmostEqual(self.baseline._annual_kcals_cost, expected_annual_kcals_cost)
        self.assertAlmostEqual(self.baseline._get_annual_kcals_cost(), expected_annual_kcals_cost)
        self.assertAlmostEqual(self.baseline._get_annual_kcals_cost_sql(), expected_annual_kcals_cost)

    def _precompute_bss_content_hash(self):
        """
        Factory-created test files are empty (no content to hash from), so tests
        that care about the already-hashed steady state must set the column directly.
        """
        File.objects.filter(name=self.baseline.bss.name).update(_content_hash="a" * 128)
        return File.objects.get(name=self.baseline.bss.name)

    def test_bss_metadata_uses_cached_database_file(self):
        database_file = self._precompute_bss_content_hash()
        expected_uploaded_datetime = (
            database_file.created_datetime + datetime.timedelta(microseconds=500_000)
        ).replace(microsecond=0)

        with self.assertNumQueries(1):
            self.assertEqual(self.baseline.bss_content_hash, database_file.content_hash)
            self.assertEqual(self.baseline.bss_uploaded_datetime, expected_uploaded_datetime)
            self.assertEqual(self.baseline.bss_size, database_file.size)

        with self.assertNumQueries(0):
            self.baseline.bss_content_hash
            self.baseline.bss_uploaded_datetime
            self.baseline.bss_size

    def test_bss_metadata_does_not_load_file_content(self):
        """
        The BSS file content can be multiple MB. Reading the hash/size/upload-time metadata
        must not pull that content into memory, since these are read for every baseline row
        whenever the API list/detail views serialize them.
        """
        self._precompute_bss_content_hash()

        with CaptureQueriesContext(connection) as queries:
            self.baseline.bss_content_hash
            self.baseline.bss_uploaded_datetime
            self.baseline.bss_size

        self.assertEqual(len(queries.captured_queries), 1)
        self.assertNotIn('"content"', queries.captured_queries[0]["sql"])

    def test_poor_survival_non_food_expenditure(self):
        expected_expenditure = (
            self.non_food_activity.expenditure * self.non_food_category.percentage_allocation_to_basket
        )
        self.assertAlmostEqual(self.baseline.poor_survival_non_food_expenditure, expected_expenditure)

    def test_poor_average_household_size(self):
        baseline = LivelihoodZoneBaseline.objects.get(pk=self.baseline.pk)
        self.assertEqual(baseline.poor_average_household_size, 5)

    def test_poor_average_household_size_without_main_staple(self):
        baseline = LivelihoodZoneBaselineFactory()
        BaselineWealthGroupFactory(
            livelihood_zone_baseline=baseline,
            wealth_group_category__code=WealthGroupCategory.POOR,
            average_household_size=7,
        )
        self.assertIsNone(baseline.poor_main_staple)
        self.assertEqual(baseline.poor_average_household_size, 7)

    def test_poor_average_household_size_without_poor_wealth_group(self):
        baseline = LivelihoodZoneBaselineFactory()
        self.assertIsNone(baseline.poor_average_household_size)
        annotated_baseline = LivelihoodZoneBaseline.objects.with_poor_average_household_size().get(pk=baseline.pk)
        self.assertIsNone(annotated_baseline.poor_average_household_size)

    def test_poor_average_household_size_uses_annotation(self):
        baseline = LivelihoodZoneBaseline.objects.with_poor_average_household_size().get(pk=self.baseline.pk)
        with self.assertNumQueries(0):
            self.assertEqual(baseline.poor_average_household_size, 5)

    def test_product_category_change_resaves_baseline_on_commit(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.other_food_category.percentage_allocation_to_basket = 0.5
            self.other_food_category.save()

        self.baseline.refresh_from_db()
        self.assertAlmostEqual(self.baseline.annual_kcals_cost, self.get_expected_annual_kcals_cost())

    def test_baseline_livelihood_activity_change_resaves_baseline_on_commit(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.main_staple_activity.price = 3
            self.main_staple_activity.expenditure = self.main_staple_activity.quantity_purchased * 3
            self.main_staple_activity.save()

        self.baseline.refresh_from_db()
        self.assertAlmostEqual(self.baseline.annual_kcals_cost, self.get_expected_annual_kcals_cost())

    def test_baseline_livelihood_activity_superclass_resaves_baseline_on_commit(self):
        with self.captureOnCommitCallbacks(execute=True):
            activity = BaselineLivelihoodActivity.objects.get(pk=self.main_staple_activity.pk)
            activity.price = 4
            activity.expenditure = activity.quantity_purchased * 4
            activity.save()

        self.baseline.refresh_from_db()
        self.main_staple_activity.refresh_from_db()
        self.assertAlmostEqual(self.baseline.annual_kcals_cost, self.get_expected_annual_kcals_cost())

    def test_livelihood_activity_superclass_resaves_baseline_on_commit(self):
        with self.captureOnCommitCallbacks(execute=True):
            activity = LivelihoodActivity.objects.get(pk=self.main_staple_activity.pk)
            activity.price = 5
            activity.expenditure = activity.quantity_purchased * 5
            activity.save()

        self.baseline.refresh_from_db()
        self.main_staple_activity.refresh_from_db()
        self.assertAlmostEqual(self.baseline.annual_kcals_cost, self.get_expected_annual_kcals_cost())

    def test_product_category_changes_for_same_baseline_queue_one_on_commit_callback(self):
        with self.captureOnCommitCallbacks(execute=False) as callbacks:
            self.main_staple_category.percentage_allocation_to_basket = 0.9
            self.main_staple_category.save()
            self.other_food_category.percentage_allocation_to_basket = 0.5
            self.other_food_category.save()

        self.assertEqual(len(callbacks), 1)

    def test_poor_baseline_wealth_group_change_resaves_baseline_on_commit(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.poor_wealth_group.average_household_size = 10
            self.poor_wealth_group.save()

        self.baseline.refresh_from_db()
        self.poor_wealth_group.refresh_from_db()
        self.assertAlmostEqual(self.baseline.annual_kcals_cost, self.get_expected_annual_kcals_cost())


class LivelihoodProductCategoryBasketTestCase(TestCase):
    """
    Tests for the Basket contributions and the Thresholds calculated from them.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Create a Baseline with a Poor and a Middle Wealth Group and Livelihood Product Categories for each Basket.

        The Poor Wealth Group has a Livelihoods Protection item that the Middle Wealth Group inherits, and a
        Livelihoods Protection food item that the Middle Wealth Group overrides with its own allocation.
        """
        cls.baseline = LivelihoodZoneBaselineFactory()
        cls.poor_wealth_group = BaselineWealthGroupFactory(
            livelihood_zone_baseline=cls.baseline,
            wealth_group_category__code=WealthGroupCategory.POOR,
            average_household_size=5,
        )
        cls.middle_wealth_group = BaselineWealthGroupFactory(
            livelihood_zone_baseline=cls.baseline,
            wealth_group_category__code="M",
            average_household_size=8,
        )
        cls.main_staple = LivelihoodProductCategoryFactory(
            baseline_livelihood_activity=FoodPurchaseFactory(
                livelihood_zone_baseline=cls.baseline,
                wealth_group=cls.poor_wealth_group,
                scenario=LivelihoodActivityScenario.BASELINE,
                extra={"product__kcals_per_unit": 3500},
            ),
            basket=LivelihoodProductCategory.ProductBasket.MAIN_STAPLE,
            percentage_allocation_to_basket=1,
        )
        cls.other_food = LivelihoodProductCategoryFactory(
            baseline_livelihood_activity=FoodPurchaseFactory(
                livelihood_zone_baseline=cls.baseline,
                wealth_group=cls.poor_wealth_group,
                scenario=LivelihoodActivityScenario.BASELINE,
            ),
            basket=LivelihoodProductCategory.ProductBasket.SURVIVAL_OTHER_FOOD,
            percentage_allocation_to_basket=0.5,
        )
        cls.non_food = LivelihoodProductCategoryFactory(
            baseline_livelihood_activity=OtherPurchaseFactory(
                livelihood_zone_baseline=cls.baseline,
                wealth_group=cls.poor_wealth_group,
                scenario=LivelihoodActivityScenario.BASELINE,
            ),
            basket=LivelihoodProductCategory.ProductBasket.SURVIVAL_NON_FOOD,
            percentage_allocation_to_basket=0.25,
        )
        cls.inherited_livelihoods_protection = LivelihoodProductCategoryFactory(
            baseline_livelihood_activity=OtherPurchaseFactory(
                livelihood_zone_baseline=cls.baseline,
                wealth_group=cls.poor_wealth_group,
                scenario=LivelihoodActivityScenario.BASELINE,
            ),
            basket=LivelihoodProductCategory.ProductBasket.LIVELIHOODS_PROTECTION,
            percentage_allocation_to_basket=0.5,
        )
        cls.poor_livelihoods_protection_food = LivelihoodProductCategoryFactory(
            baseline_livelihood_activity=FoodPurchaseFactory(
                livelihood_zone_baseline=cls.baseline,
                wealth_group=cls.poor_wealth_group,
                scenario=LivelihoodActivityScenario.BASELINE,
            ),
            basket=LivelihoodProductCategory.ProductBasket.LIVELIHOODS_PROTECTION,
            percentage_allocation_to_basket=0.2,
        )
        cls.middle_livelihoods_protection_food = LivelihoodProductCategoryFactory(
            baseline_livelihood_activity=FoodPurchaseFactory(
                livelihood_zone_baseline=cls.baseline,
                livelihood_strategy=cls.poor_livelihoods_protection_food.baseline_livelihood_activity.livelihood_strategy,
                wealth_group=cls.middle_wealth_group,
                scenario=LivelihoodActivityScenario.BASELINE,
            ),
            basket=LivelihoodProductCategory.ProductBasket.LIVELIHOODS_PROTECTION,
            percentage_allocation_to_basket=0.6,
        )
        # Save the Baseline to force the calculation of annual_kcals_cost.
        cls.baseline.save()

    def get_expected_contribution(self, category):
        """
        Return the expected contribution to the Threshold for a Livelihood Product Category.
        """
        activity = category.baseline_livelihood_activity
        allocation = category.percentage_allocation_to_basket
        percentage_kcals = (activity.percentage_kcals or 0) * allocation
        expenditure_as_percentage_kcals = (activity.expenditure * allocation) / (
            activity.wealth_group.average_household_size * self.baseline.annual_kcals_cost
        )
        if category.basket == LivelihoodProductCategory.ProductBasket.MAIN_STAPLE:
            return 1 - self.get_expected_contribution(self.other_food)
        if category.basket == LivelihoodProductCategory.ProductBasket.SURVIVAL_OTHER_FOOD:
            return percentage_kcals
        if category.basket == LivelihoodProductCategory.ProductBasket.SURVIVAL_NON_FOOD:
            return expenditure_as_percentage_kcals
        return expenditure_as_percentage_kcals - percentage_kcals

    def get_expected_survival_threshold(self):
        """
        Return the expected Survival Threshold, using the original definition of 100% kcals plus non-food items.
        """
        return 1 + (
            self.non_food.baseline_livelihood_activity.expenditure * self.non_food.percentage_allocation_to_basket
        ) / (self.poor_wealth_group.average_household_size * self.baseline.annual_kcals_cost)

    def test_with_allocation(self):
        category = LivelihoodProductCategory.objects.with_allocation().get(pk=self.other_food.pk)
        activity = self.other_food.baseline_livelihood_activity
        self.assertAlmostEqual(category.activity_percentage_kcals, activity.percentage_kcals)
        self.assertAlmostEqual(category.activity_expenditure, activity.expenditure)
        self.assertAlmostEqual(category.allocated_percentage_kcals, activity.percentage_kcals * 0.5)
        self.assertAlmostEqual(category.allocated_expenditure, activity.expenditure * 0.5)

    def test_with_allocation_treats_missing_percentage_kcals_as_zero(self):
        category = LivelihoodProductCategory.objects.with_allocation().get(pk=self.non_food.pk)
        self.assertIsNone(category.activity_percentage_kcals)
        self.assertEqual(category.allocated_percentage_kcals, 0)

    def test_with_basket_contribution(self):
        categories = LivelihoodProductCategory.objects.filter(
            baseline_livelihood_activity__livelihood_zone_baseline=self.baseline
        ).with_basket_contribution()
        self.assertEqual(len(categories), 6)
        for category in categories:
            with self.subTest(basket=category.basket, pk=category.pk):
                self.assertAlmostEqual(category.basket_percentage_kcals, self.get_expected_contribution(category))

    def test_for_wealth_group(self):
        self.assertCountEqual(
            LivelihoodProductCategory.objects.for_wealth_group(self.poor_wealth_group),
            [
                self.main_staple,
                self.other_food,
                self.non_food,
                self.inherited_livelihoods_protection,
                self.poor_livelihoods_protection_food,
            ],
        )
        self.assertCountEqual(
            LivelihoodProductCategory.objects.for_wealth_group(self.middle_wealth_group),
            [
                self.main_staple,
                self.other_food,
                self.non_food,
                self.inherited_livelihoods_protection,
                self.middle_livelihoods_protection_food,
            ],
        )

    def test_for_wealth_group_with_community_wealth_group(self):
        community_wealth_group = CommunityWealthGroupFactory(
            livelihood_zone_baseline=self.baseline,
            community__livelihood_zone_baseline=self.baseline,
            wealth_group_category=self.middle_wealth_group.wealth_group_category,
        )
        self.assertCountEqual(
            LivelihoodProductCategory.objects.for_wealth_group(community_wealth_group),
            LivelihoodProductCategory.objects.for_wealth_group(self.middle_wealth_group),
        )

    def test_for_threshold_wealth_groups(self):
        components = LivelihoodProductCategory.objects.filter(
            baseline_livelihood_activity__livelihood_zone_baseline=self.baseline
        ).for_threshold_wealth_groups()
        poor = self.poor_wealth_group
        middle = self.middle_wealth_group
        self.assertCountEqual(
            [
                (component.pk, component.threshold_wealth_group, component.threshold_wealth_group_category)
                + (component.is_inherited,)
                for component in components
            ],
            [
                (self.main_staple.pk, poor.pk, poor.wealth_group_category_id, False),
                (self.other_food.pk, poor.pk, poor.wealth_group_category_id, False),
                (self.non_food.pk, poor.pk, poor.wealth_group_category_id, False),
                (self.inherited_livelihoods_protection.pk, poor.pk, poor.wealth_group_category_id, False),
                (self.poor_livelihoods_protection_food.pk, poor.pk, poor.wealth_group_category_id, False),
                (self.main_staple.pk, middle.pk, middle.wealth_group_category_id, True),
                (self.other_food.pk, middle.pk, middle.wealth_group_category_id, True),
                (self.non_food.pk, middle.pk, middle.wealth_group_category_id, True),
                (self.inherited_livelihoods_protection.pk, middle.pk, middle.wealth_group_category_id, True),
                (self.middle_livelihoods_protection_food.pk, middle.pk, middle.wealth_group_category_id, False),
            ],
        )

    def test_for_threshold_wealth_groups_excludes_community_wealth_groups(self):
        CommunityWealthGroupFactory(
            livelihood_zone_baseline=self.baseline,
            community__livelihood_zone_baseline=self.baseline,
            wealth_group_category=self.middle_wealth_group.wealth_group_category,
        )
        components = LivelihoodProductCategory.objects.filter(
            baseline_livelihood_activity__livelihood_zone_baseline=self.baseline
        ).for_threshold_wealth_groups()
        self.assertCountEqual(
            {component.threshold_wealth_group for component in components},
            [self.poor_wealth_group.pk, self.middle_wealth_group.pk],
        )

    def test_survival_threshold(self):
        expected = self.get_expected_survival_threshold()
        for wealth_group in [self.poor_wealth_group, self.middle_wealth_group]:
            with self.subTest(wealth_group=wealth_group.wealth_group_category_id):
                self.assertAlmostEqual(wealth_group._get_survival_threshold_as_percentage_kcals(), expected)

    def test_survival_threshold_requires_non_food_basket(self):
        self.non_food.delete()
        self.assertIsNone(self.poor_wealth_group._get_survival_threshold_as_percentage_kcals())

    def test_livelihoods_protection_threshold(self):
        for wealth_group, livelihoods_protection_food in [
            (self.poor_wealth_group, self.poor_livelihoods_protection_food),
            (self.middle_wealth_group, self.middle_livelihoods_protection_food),
        ]:
            with self.subTest(wealth_group=wealth_group.wealth_group_category_id):
                # The Poor expenditure inherited by the Middle Wealth Group is scaled by household size,
                # so it is the same percentage of kcals.
                expected = (
                    self.get_expected_survival_threshold()
                    + self.get_expected_contribution(self.inherited_livelihoods_protection)
                    + self.get_expected_contribution(livelihoods_protection_food)
                )
                self.assertAlmostEqual(
                    wealth_group._get_livelihoods_protection_threshold_as_percentage_kcals(), expected
                )

    def test_livelihoods_protection_threshold_with_community_wealth_group(self):
        community_wealth_group = CommunityWealthGroupFactory(
            livelihood_zone_baseline=self.baseline,
            community__livelihood_zone_baseline=self.baseline,
            wealth_group_category=self.middle_wealth_group.wealth_group_category,
            average_household_size=3,
        )
        self.assertAlmostEqual(
            community_wealth_group._get_livelihoods_protection_threshold_as_percentage_kcals(),
            self.middle_wealth_group._get_livelihoods_protection_threshold_as_percentage_kcals(),
        )

    def test_threshold_components_sum_to_livelihoods_protection_threshold(self):
        components = (
            LivelihoodProductCategory.objects.filter(
                baseline_livelihood_activity__livelihood_zone_baseline=self.baseline
            )
            .with_basket_contribution()
            .for_threshold_wealth_groups()
        )
        for wealth_group in [self.poor_wealth_group, self.middle_wealth_group]:
            with self.subTest(wealth_group=wealth_group.wealth_group_category_id):
                self.assertAlmostEqual(
                    sum(
                        component.basket_percentage_kcals
                        for component in components
                        if component.threshold_wealth_group == wealth_group.pk
                    ),
                    wealth_group._get_livelihoods_protection_threshold_as_percentage_kcals(),
                )

    @override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
    def test_baseline_save_clears_threshold_cache(self):
        keys = [
            key
            for wealth_group in [self.poor_wealth_group, self.middle_wealth_group]
            for key in WealthGroup.get_threshold_cache_keys(wealth_group.pk)
        ]
        cache.set_many({key: 99 for key in keys})
        self.baseline.save()
        self.assertEqual(cache.get_many(keys), {})

    def assert_change_clears_threshold_cache_on_commit(self, change):
        """
        Assert that the change clears the cached Thresholds for the Middle Wealth Group when the transaction commits.
        """
        keys = WealthGroup.get_threshold_cache_keys(self.middle_wealth_group.pk)
        cache.set_many({key: 99 for key in keys})
        with self.captureOnCommitCallbacks(execute=True):
            change()
        self.assertEqual(cache.get_many(keys), {})

    @override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
    def test_livelihoods_protection_category_change_clears_threshold_cache_on_commit(self):
        self.assert_change_clears_threshold_cache_on_commit(self.inherited_livelihoods_protection.save)

    @override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
    def test_other_purchase_change_clears_threshold_cache_on_commit(self):
        self.assert_change_clears_threshold_cache_on_commit(self.non_food.baseline_livelihood_activity.save)

    @override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
    def test_baseline_wealth_group_change_clears_threshold_cache_on_commit(self):
        self.assert_change_clears_threshold_cache_on_commit(self.middle_wealth_group.save)


class SeasonalActivityTestCase(TestCase):
    def test_is_key_defaults_from_seasonal_activity_type(self):
        seasonal_activity = SeasonalActivityFactory(
            seasonal_activity_type__code="KEYSA", seasonal_activity_type__is_key=True
        )

        self.assertTrue(seasonal_activity.is_key)

    def test_is_key_can_override_seasonal_activity_type_default(self):
        seasonal_activity = SeasonalActivityFactory(
            seasonal_activity_type__code="KEYSB",
            seasonal_activity_type__is_key=True,
            is_key=False,
        )

        self.assertFalse(seasonal_activity.is_key)


class WealthGroupCharacteristicValueTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.wealth_group_characteristic_value = WealthGroupCharacteristicValueFactory()

    def test_reference_type(self):

        # Reference Type = SUMMARY for a Baseline Wealth Group is OK
        self.wealth_group_characteristic_value.reference_type = (
            WealthGroupCharacteristicValue.CharacteristicReference.SUMMARY
        )
        self.wealth_group_characteristic_value.wealth_group.community = None
        self.wealth_group_characteristic_value.save()

        # Reference Type = COMMUNITY for a Community Wealth Group is OK
        self.wealth_group_characteristic_value.reference_type = (
            WealthGroupCharacteristicValue.CharacteristicReference.COMMUNITY
        )
        self.wealth_group_characteristic_value.wealth_group.community = CommunityFactory(
            livelihood_zone_baseline=self.wealth_group_characteristic_value.wealth_group.livelihood_zone_baseline
        )
        self.wealth_group_characteristic_value.save()

        # Reference Type = SUMMARY for a Community Wealth Group is not OK
        self.wealth_group_characteristic_value.reference_type = (
            WealthGroupCharacteristicValue.CharacteristicReference.SUMMARY
        )
        with conditional_logging():
            self.assertRaises(ValidationError, self.wealth_group_characteristic_value.save)

        # Reference Type = COMMUNITY for a Baseline Wealth Group is not OK
        self.wealth_group_characteristic_value.reference_type = (
            WealthGroupCharacteristicValue.CharacteristicReference.COMMUNITY
        )
        self.wealth_group_characteristic_value.wealth_group.community = None
        with conditional_logging():
            self.assertRaises(ValidationError, self.wealth_group_characteristic_value.save)

    def test_product(self):

        # Product for Characteristic that has a Product is OK
        self.wealth_group_characteristic_value.wealth_characteristic.has_product = True
        self.wealth_group_characteristic_value.product = ClassifiedProductFactory()
        self.wealth_group_characteristic_value.save()

        # No product for Characteristic that doesn't have a Product is OK
        self.wealth_group_characteristic_value.wealth_characteristic.has_product = False
        self.wealth_group_characteristic_value.product = None
        self.wealth_group_characteristic_value.save()

        # Product for Characteristic that doesn't have a Product is not OK
        self.wealth_group_characteristic_value.product = ClassifiedProductFactory()
        with conditional_logging():
            self.assertRaises(ValidationError, self.wealth_group_characteristic_value.save)

        # No product for Characteristic that has a Product is not OK
        self.wealth_group_characteristic_value.wealth_characteristic.has_product = True
        self.wealth_group_characteristic_value.product = None
        with conditional_logging():
            self.assertRaises(ValidationError, self.wealth_group_characteristic_value.save)

    def test_get_by_natural_key(self):

        instance = WealthGroupCharacteristicValue.objects.get_by_natural_key(
            code=self.wealth_group_characteristic_value.wealth_group.livelihood_zone_baseline.livelihood_zone.code,
            reference_year_end_date=self.wealth_group_characteristic_value.wealth_group.livelihood_zone_baseline.reference_year_end_date,
            wealth_group_category=self.wealth_group_characteristic_value.wealth_group.wealth_group_category.code,
            wealth_characteristic=self.wealth_group_characteristic_value.wealth_characteristic.code,
            reference_type=self.wealth_group_characteristic_value.reference_type,
            product=(
                self.wealth_group_characteristic_value.product.cpc
                if self.wealth_group_characteristic_value.product
                else ""
            ),
            full_name=self.wealth_group_characteristic_value.wealth_group.community.full_name,
        )
        self.assertEqual(instance, self.wealth_group_characteristic_value)

    def test_get_by_natural_key_with_only_community_name(self):

        instance = WealthGroupCharacteristicValue.objects.get_by_natural_key(
            code=self.wealth_group_characteristic_value.wealth_group.livelihood_zone_baseline.livelihood_zone.code,
            reference_year_end_date=self.wealth_group_characteristic_value.wealth_group.livelihood_zone_baseline.reference_year_end_date,
            wealth_group_category=self.wealth_group_characteristic_value.wealth_group.wealth_group_category.code,
            wealth_characteristic=self.wealth_group_characteristic_value.wealth_characteristic.code,
            reference_type=self.wealth_group_characteristic_value.reference_type,
            product=(
                self.wealth_group_characteristic_value.product.cpc
                if self.wealth_group_characteristic_value.product
                else ""
            ),
            full_name=self.wealth_group_characteristic_value.wealth_group.community.name,
        )
        self.assertEqual(instance, self.wealth_group_characteristic_value)

    def test_get_by_natural_key_for_a_baseline_wealth_group(self):

        wealth_group_characteristic_value = WealthGroupCharacteristicValueFactory(wealth_group__community=None)
        instance = WealthGroupCharacteristicValue.objects.get_by_natural_key(
            code=wealth_group_characteristic_value.wealth_group.livelihood_zone_baseline.livelihood_zone.code,
            reference_year_end_date=wealth_group_characteristic_value.wealth_group.livelihood_zone_baseline.reference_year_end_date,
            wealth_group_category=wealth_group_characteristic_value.wealth_group.wealth_group_category.code,
            wealth_characteristic=wealth_group_characteristic_value.wealth_characteristic.code,
            reference_type=wealth_group_characteristic_value.reference_type,
            product=(
                wealth_group_characteristic_value.product.cpc if wealth_group_characteristic_value.product else ""
            ),
            full_name="",
        )
        self.assertEqual(instance, wealth_group_characteristic_value)


class FoodPurchaseTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create different instances without saving
        cls.foodpurchase1 = FoodPurchase(
            unit_multiple=None,
            times_per_month=None,
            months_per_year=None,
            times_per_year=None,
            quantity_purchased=None,
        )
        # Correct via times_per_month/months_per_year path (times_per_year matches)
        cls.foodpurchase2 = FoodPurchase(
            unit_multiple=2,
            times_per_month=5,
            months_per_year=12,
            times_per_year=60,  # 5 * 12 = 60
            quantity_purchased=120,  # 2 * 60 = 120
        )
        # Incorrect quantity_purchased: 2 * 60 = 120, not 100
        cls.foodpurchase3 = FoodPurchase(
            unit_multiple=2,
            times_per_month=5,
            months_per_year=12,
            times_per_year=60,
            quantity_purchased=100,
        )
        # Correct via times_per_year only (no times_per_month/months_per_year)
        cls.foodpurchase4 = FoodPurchase(
            unit_multiple=3,
            times_per_year=10,
            quantity_purchased=30,  # 3 * 10 = 30
        )
        # Inconsistent times_per_year vs times_per_month * months_per_year
        cls.foodpurchase5 = FoodPurchase(
            unit_multiple=2,
            times_per_month=5,
            months_per_year=12,
            times_per_year=50,  # Incorrect: should be 60
            quantity_purchased=100,
        )

    def test_validate_quantity_purchased(self):
        """
        Test validate_quantity_purchased method
        """
        # Missing data should not raise ValidationError
        self.foodpurchase1.validate_quantity_purchased()
        # Correct via times_per_month/months_per_year (times_per_year set consistently)
        self.foodpurchase2.validate_quantity_purchased()
        # Incorrect quantity_purchased
        with conditional_logging():
            self.assertRaises(ValidationError, self.foodpurchase3.validate_quantity_purchased)
        # Correct via times_per_year only
        self.foodpurchase4.validate_quantity_purchased()
        # Inconsistent times_per_year
        with self.assertRaises(ValidationError):
            self.foodpurchase5.validate_quantity_purchased()


class PaymentInKindTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create different instances without saving
        cls.paymentinkind1 = PaymentInKind(
            payment_per_time=None,
            people_per_household=None,
            times_per_month=None,
            months_per_year=None,
            times_per_year=None,
            quantity_produced=None,
        )
        # Correct: times_per_year = 5 * 12 = 60; quantity_produced = 10 * 2 * 60 = 1200
        cls.paymentinkind2 = PaymentInKind(
            payment_per_time=10,
            people_per_household=2,
            times_per_month=5,
            months_per_year=12,
            times_per_year=60,
            quantity_produced=1200,
        )
        # Incorrect quantity_produced: 10 * 2 * 60 = 1200, not 1000
        cls.paymentinkind3 = PaymentInKind(
            payment_per_time=10,
            people_per_household=2,
            times_per_month=5,
            months_per_year=12,
            times_per_year=60,
            quantity_produced=1000,
        )

    def test_validate_quantity_produced(self):
        """
        Test validate_quantity_produced method
        """
        # Missing data should not raise ValidationError
        self.paymentinkind1.validate_quantity_produced()

        # Correct (times_per_year consistent with times_per_month * months_per_year)
        self.paymentinkind2.validate_quantity_produced()

        # Incorrect quantity_produced
        with self.assertRaises(ValidationError):
            self.paymentinkind3.validate_quantity_produced()

    def test_payment_per_time_required(self):
        """
        Test that clean enforces payment_per_time when required.
        """
        instance = PaymentInKind(
            payment_per_time=None,
            people_per_household=2,
            times_per_month=5,
            months_per_year=12,
        )
        with self.assertRaises(ValidationError):
            instance.clean()


class ReliefGiftOtherTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create different instances without saving
        cls.reliefgift1 = ReliefGiftOther(
            unit_multiple=None,
            times_per_month=None,
            months_per_year=None,
            times_per_year=None,
            quantity_produced=None,
        )
        # Correct via times_per_year only
        cls.reliefgift2 = ReliefGiftOther(
            unit_multiple=10,
            times_per_year=12,
            quantity_produced=120,  # 10 * 12 = 120
        )
        # Incorrect quantity_produced
        cls.reliefgift3 = ReliefGiftOther(
            unit_multiple=10,
            times_per_year=12,
            quantity_produced=100,  # Incorrect: should be 120
        )

    def test_validate_quantity_produced(self):
        """
        Test validate_quantity_produced method
        """
        # Missing data should not raise ValidationError
        self.reliefgift1.validate_quantity_produced()

        # Correct via times_per_year only
        self.reliefgift2.validate_quantity_produced()

        # Incorrect quantity_produced
        with self.assertRaises(ValidationError):
            self.reliefgift3.validate_quantity_produced()


class OtherCashIncomeTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create instances for testing
        cls.othercashincome1 = OtherCashIncome(
            payment_per_time=None,
            people_per_household=None,
            times_per_month=None,
            months_per_year=None,
            times_per_year=None,
            income=None,
        )
        # Correct: times_per_year = 5 * 12 = 60; income = 100 * 2 * 60 = 12000
        cls.othercashincome2 = OtherCashIncome(
            payment_per_time=100,
            people_per_household=2,
            times_per_month=5,
            months_per_year=12,
            times_per_year=60,
            income=12000,
        )
        # Incorrect income: 100 * 2 * 60 = 12000, not 10000
        cls.othercashincome3 = OtherCashIncome(
            payment_per_time=100,
            people_per_household=2,
            times_per_month=5,
            months_per_year=12,
            times_per_year=60,
            income=10000,
        )
        # Correct via times_per_year only (no people_per_household — income cannot be validated)
        cls.othercashincome4 = OtherCashIncome(
            payment_per_time=100,
            times_per_year=24,
            income=2400,
        )
        # Incorrect income with all fields present: 100 * 2 * 24 = 4800, not 2000
        cls.othercashincome5 = OtherCashIncome(
            payment_per_time=100,
            people_per_household=2,
            times_per_year=24,
            income=2000,
        )

    def test_validate_income(self):
        # Missing data should not raise ValidationError
        self.othercashincome1.validate_income()
        # Correct data should not raise ValidationError
        self.othercashincome2.validate_income()
        # No people_per_household: income cannot be validated, so no error even with mismatched income
        self.othercashincome4.validate_income()
        # Incorrect income should raise ValidationError
        with self.assertRaises(ValidationError):
            self.othercashincome3.validate_income()
        with self.assertRaises(ValidationError):
            self.othercashincome5.validate_income()


class OtherPurchaseTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create instances for testing
        cls.otherpurchase1 = OtherPurchase(
            unit_multiple=None,
            times_per_month=None,
            months_per_year=None,
            times_per_year=None,
            price=None,
            expenditure=None,
        )
        cls.otherpurchase2 = OtherPurchase(
            unit_multiple=2,
            times_per_month=5,
            months_per_year=12,
            times_per_year=60,  # 5 * 12 = 60
            price=10,
            expenditure=1200,  # 10 * 2 * 60 = 1200
        )
        cls.otherpurchase3 = OtherPurchase(
            unit_multiple=2,
            times_per_month=5,
            months_per_year=12,
            times_per_year=50,  # Incorrect: should be 5 * 12 = 60
            price=10,
            expenditure=1200,
        )
        cls.otherpurchase4 = OtherPurchase(
            unit_multiple=2,
            times_per_month=5,
            months_per_year=12,
            times_per_year=60,
            price=10,
            expenditure=1000,  # Incorrect: should be 10 * 2 * 60 = 1200
        )

    def test_validate_expenditure(self):
        # Missing data should not raise ValidationError
        self.otherpurchase1.validate_expenditure()
        # Correct data should not raise ValidationError
        self.otherpurchase2.validate_expenditure()
        # Incorrect data should raise ValidationError
        with self.assertRaises(ValidationError):
            self.otherpurchase3.validate_expenditure()
        with self.assertRaises(ValidationError):
            self.otherpurchase4.validate_expenditure()
