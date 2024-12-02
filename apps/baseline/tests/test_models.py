from django.core.exceptions import ValidationError
from django.test import TestCase

from baseline.models import (
    FoodPurchase,
    OtherCashIncome,
    OtherPurchase,
    PaymentInKind,
    ReliefGiftOther,
    WealthGroupCharacteristicValue,
)
from common.tests.factories import ClassifiedProductFactory
from common.utils import conditional_logging

from .factories import CommunityFactory, WealthGroupCharacteristicValueFactory


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
            quantity_produced=None,
        )
        cls.foodpurchase2 = FoodPurchase(
            unit_multiple=2,
            times_per_month=5,
            months_per_year=12,
            quantity_produced=120,
        )
        # Incorrect: 2 * 5 * 12 = 120
        cls.foodpurchase3 = FoodPurchase(
            unit_multiple=2,
            times_per_month=5,
            months_per_year=12,
            quantity_produced=100,
        )

    def test_validate_quantity_produced(self):
        """
        Test validate_quantity_produced method
        """
        # Missing data should not raise ValidationError
        self.foodpurchase1.validate_quantity_produced()
        # Expected consistant values, should not raise
        self.foodpurchase2.validate_quantity_produced()
        # Incorrect: 2 * 5 * 12 = 120
        with conditional_logging():
            self.assertRaises(ValidationError, self.foodpurchase3.validate_quantity_produced)


class PaymentInKindTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create different instances without saving
        cls.paymentinkind1 = PaymentInKind(
            payment_per_time=None,
            people_per_household=None,
            times_per_month=None,
            months_per_year=None,
            quantity_produced=None,
        )
        cls.paymentinkind2 = PaymentInKind(
            payment_per_time=10,
            people_per_household=2,
            times_per_month=5,
            months_per_year=12,
            quantity_produced=1200,  # 10 * 2 * 5 * 12 = 1200
        )
        cls.paymentinkind3 = PaymentInKind(
            payment_per_time=10,
            people_per_household=2,
            times_per_month=5,
            months_per_year=12,
            quantity_produced=1000,  # Incorrect: should be 1200
        )

    def test_validate_quantity_produced(self):
        """
        Test validate_quantity_produced method
        """
        # Missing data should not raise ValidationError
        self.paymentinkind1.validate_quantity_produced()

        # Expected consistent values, should not raise ValidationError
        self.paymentinkind2.validate_quantity_produced()

        # Incorrect: 10 * 2 * 5 * 12 = 1200
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
            times_per_year=None,
            quantity_produced=None,
        )
        cls.reliefgift2 = ReliefGiftOther(
            unit_multiple=10,
            times_per_year=12,
            quantity_produced=120,  # 10 * 12 = 120
        )
        cls.reliefgift3 = ReliefGiftOther(
            unit_multiple=10,
            times_per_year=12,
            quantity_produced=100,  # Incorrect: should be 10 * 12 = 120
        )

    def test_validate_quantity_produced(self):
        """
        Test validate_quantity_produced method
        """
        # Missing data should not raise ValidationError
        self.reliefgift1.validate_quantity_produced()

        # Expected consistent values, should not raise ValidationError
        self.reliefgift2.validate_quantity_produced()

        # Incorrect: 10 * 12 = 120
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
            income=None,
        )
        cls.othercashincome2 = OtherCashIncome(
            payment_per_time=100,
            people_per_household=2,
            times_per_month=5,
            months_per_year=12,
            income=12000,  # 100 * 2 * 5 * 12 = 12000
        )
        cls.othercashincome3 = OtherCashIncome(
            payment_per_time=100,
            people_per_household=2,
            times_per_month=5,
            months_per_year=12,
            income=10000,  # Incorrect: should be 12000
        )
        cls.othercashincome4 = OtherCashIncome(
            payment_per_time=100,
            times_per_year=24,
            income=2400,  # 100 * 24 = 2400
        )
        cls.othercashincome5 = OtherCashIncome(
            payment_per_time=100,
            times_per_year=24,
            income=2000,  # Incorrect: should be 2400
        )

    def test_validate_income(self):
        # Missing data should not raise ValidationError
        self.othercashincome1.validate_income()
        # Correct data should not raise ValidationError
        self.othercashincome2.validate_income()
        self.othercashincome4.validate_income()
        # Incorrect data should raise ValidationError.
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
