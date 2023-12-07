from django.core.exceptions import ValidationError
from django.test import TestCase

from baseline.models import WealthGroupCharacteristicValue
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
