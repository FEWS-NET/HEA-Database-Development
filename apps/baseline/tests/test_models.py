import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase

from baseline.models import (
    BaselineLivelihoodActivity,
    FoodPurchase,
    LivelihoodActivity,
    LivelihoodProductCategory,
    OtherCashIncome,
    OtherPurchase,
    PaymentInKind,
    ReliefGiftOther,
    WealthGroupCharacteristicValue,
)
from common.tests.factories import ClassifiedProductFactory
from common.utils import conditional_logging
from metadata.models import WealthGroupCategory

from .factories import (
    BaselineWealthGroupFactory,
    CommunityFactory,
    FoodPurchaseFactory,
    LivelihoodProductCategoryFactory,
    LivelihoodZoneBaselineFactory,
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
            extra={"product__kcals_per_unit": 100},
        )
        cls.other_food_activity = FoodPurchaseFactory(
            livelihood_zone_baseline=cls.baseline,
            wealth_group=cls.poor_wealth_group,
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
