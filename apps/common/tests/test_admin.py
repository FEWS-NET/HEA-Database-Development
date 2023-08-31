from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import activate

from common.admin import (
    ClassifiedProductAdmin,
    CountryAdmin,
    CurrencyAdmin,
    UnitOfMeasureAdmin,
)
from common.models import ClassifiedProduct, Country, Currency, UnitOfMeasure

from .factories import (
    ClassifiedProductFactory,
    CountryFactory,
    CurrencyFactory,
    UnitOfMeasureFactory,
)


class CurrencyAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username="admin", password="admin", email="admin@hea.org")
        activate("en")

    def setUp(self):
        self.client.login(username="admin", password="admin")
        self.currency1 = CurrencyFactory(iso4217a3="USD", iso4217n3="840", iso_en_name="US Dollar")
        self.currency2 = CurrencyFactory(iso4217a3="KES", iso4217n3="404", iso_en_name="Kenyan Shilling")

    def test_list_currency(self):
        response = self.client.get(reverse("admin:common_currency_changelist"))
        self.assertEqual(response.status_code, 200)
        for attr in CurrencyAdmin.list_display:
            self.assertContains(response, getattr(self.currency1, attr))
            self.assertContains(response, getattr(self.currency2, attr))

    def test_search_currency(self):
        response = self.client.get(reverse("admin:common_currency_changelist"), {"q": self.currency1.iso4217a3})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.currency1.iso4217a3)

    def test_create_currency(self):
        self.assertFalse(Currency.objects.filter(iso4217a3="MWK").exists())
        data = {
            "iso4217a3": "MWK",
            "iso4217n3": "454",
            "iso_en_name": "Kwacha",
        }
        self.client.post(reverse("admin:common_currency_add"), data)
        self.assertTrue(Currency.objects.filter(iso4217a3="MWK").exists())


class CountryAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username="admin", password="admin", email="admin@hea.org")
        activate("en")

    def setUp(self):
        self.client.login(username="admin", password="admin")
        self.country1 = CountryFactory()
        self.country2 = CountryFactory()

    def test_list_country(self):
        response = self.client.get(reverse("admin:common_country_changelist"))
        self.assertEqual(response.status_code, 200)
        for attr in CountryAdmin.list_display:
            self.assertContains(response, getattr(self.country1, attr))
            self.assertContains(response, getattr(self.country2, attr))

    def test_search_country(self):
        response = self.client.get(reverse("admin:common_country_changelist"), {"q": self.country1.name})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.country1.iso3166a2)

    def test_create_country(self):
        self.assertFalse(Country.objects.filter(iso3166a2="FR").exists())
        data = {
            "iso3166a2": "FR",
            "name": "France",
            "iso3166a3": "FRA",
            "iso3166n3": "250",
            "iso_en_name": "France",
        }
        respone = self.client.post(reverse("admin:common_country_add"), data)
        # Missing required fields, validation error
        self.assertIn("Please correct the errors below", str(respone.content))
        data.update(
            {
                "iso_en_proper": "France",
                "iso_en_ro_name": "France",
                "iso_en_ro_proper": "France",
                "iso_fr_name": "France",
                "iso_fr_proper": "France",
                "iso_es_name": "Francia",
            }
        )
        self.client.post(reverse("admin:common_country_add"), data)
        self.assertTrue(Country.objects.filter(iso3166a2="FR").exists())


class ClassifiedProductAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username="admin", password="admin", email="admin@hea.org")
        activate("en")

    def setUp(self):
        self.client.login(username="admin", password="admin")
        self.product1 = ClassifiedProductFactory()
        self.product2 = ClassifiedProductFactory()

    def test_list_classified_product(self):
        response = self.client.get(reverse("admin:common_classifiedproduct_changelist"))
        for attr in ClassifiedProductAdmin.list_display:
            self.assertContains(response, getattr(self.product1, attr))
            self.assertContains(response, getattr(self.product2, attr))

    def test_search_classified_product(self):
        response = self.client.get(
            reverse("admin:common_classifiedproduct_changelist"), {"q": self.product1.common_name}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product1.cpcv2)

    def test_creation_classified_product(self):
        unit = UnitOfMeasureFactory()
        data = {
            "cpcv2": "020202",
            "description": "New Test Product",
            "common_name": "New Test Common Name",
            "scientific_name": "New Test Scientific Name",
            "unit_of_measure": unit.abbreviation,
            "_position": "first-child",
        }
        self.client.post(reverse("admin:common_classifiedproduct_add"), data)
        self.assertTrue(ClassifiedProduct.objects.filter(cpcv2="020202").exists())


class UnitOfMeasureAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username="admin", password="admin", email="admin@hea.org")
        activate("en")

    def setUp(self):
        self.uom1 = UnitOfMeasureFactory()
        self.uom2 = UnitOfMeasureFactory()
        self.client.login(username="admin", password="admin")

    def test_unit_of_measure_filter(self):
        response = self.client.get(reverse("admin:common_unitofmeasure_changelist"))
        for attr in UnitOfMeasureAdmin.list_display:
            self.assertContains(response, getattr(self.uom1, attr))
            self.assertContains(response, getattr(self.uom2, attr))

        self.assertContains(response, self.uom1.abbreviation)

    def test_unit_of_measure_search(self):

        response = self.client.get(reverse("admin:common_unitofmeasure_changelist"), {"q": self.uom1.abbreviation})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.uom1.abbreviation)

    def test_unit_of_measure_creation(self):
        data = {
            "abbreviation": "cm",
            "unit_type": UnitOfMeasure.LENGTH,
            "description": "Centimeter",
            "from_conversions-TOTAL_FORMS": "0",
            "from_conversions-INITIAL_FORMS": "0",
            "from_conversions-MIN_NUM_FORMS": "0",
            "from_conversions-MAX_NUM_FORMS": "0",
        }
        self.client.post(reverse("admin:common_unitofmeasure_add"), data)
        self.assertTrue(UnitOfMeasure.objects.filter(abbreviation="cm").exists())
