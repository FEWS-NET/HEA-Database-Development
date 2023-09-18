from django.core.exceptions import ValidationError
from django.test import TestCase

from common.tests.factories import ClassifiedProductFactory
from common.utils import conditional_logging

from ..models import WealthGroupCharacteristicValue
from .factories import CommunityFactory, WealthGroupCharacteristicValueFactory


class WealthGroupCharacteristicValueTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.wealth_group_characteristic_value = WealthGroupCharacteristicValueFactory()

    def test_source(self):

        # Source = SUMMARY for a Baseline Wealth Group is OK
        self.wealth_group_characteristic_value.source = WealthGroupCharacteristicValue.CharacteristicSource.SUMMARY
        self.wealth_group_characteristic_value.wealth_group.community = None
        self.wealth_group_characteristic_value.save()

        # Source = COMMUNITY for a Community Wealth Group is OK
        self.wealth_group_characteristic_value.source = WealthGroupCharacteristicValue.CharacteristicSource.COMMUNITY
        self.wealth_group_characteristic_value.wealth_group.community = CommunityFactory(
            livelihood_zone_baseline=self.wealth_group_characteristic_value.wealth_group.livelihood_zone_baseline
        )
        self.wealth_group_characteristic_value.save()

        # Source = SUMMARY for a Community Wealth Group is not OK
        self.wealth_group_characteristic_value.source = WealthGroupCharacteristicValue.CharacteristicSource.SUMMARY
        with conditional_logging():
            self.assertRaises(ValidationError, self.wealth_group_characteristic_value.save)

        # Source = COMMUNITY for a Baseline Wealth Group is not OK
        self.wealth_group_characteristic_value.source = WealthGroupCharacteristicValue.CharacteristicSource.COMMUNITY
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
