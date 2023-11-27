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
        self.currency1 = CurrencyFactory(iso4217a3="ZZZ", iso4217n3="888")
        self.currency2 = CurrencyFactory(iso4217a3="ZZA", iso4217n3="777")

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
        self.assertFalse(Currency.objects.filter(iso4217a3="XXX").exists())
        data = {
            "iso4217a3": "XXX",
            "iso4217n3": "900",
            "iso_en_name": "Test",
        }
        self.client.post(reverse("admin:common_currency_add"), data)
        self.assertTrue(Currency.objects.filter(iso4217a3="XXX").exists())


class CountryAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username="admin", password="admin", email="admin@hea.org")
        activate("en")

    def setUp(self):
        self.client.login(username="admin", password="admin")
        self.country1 = CountryFactory(iso3166a2="AA")
        self.country2 = CountryFactory(iso3166a2="AB")

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
        self.assertFalse(Country.objects.filter(iso3166a2="ZZ").exists())
        data = {
            "iso3166a2": "ZZ",
            "name": "Test new country",
            "iso3166a3": "ZZZ",
            "iso3166n3": "999",
            "iso_en_name": "Test new country",
        }
        respone = self.client.post(reverse("admin:common_country_add"), data)
        # Missing required fields, validation error
        self.assertIn("Please correct the errors below", str(respone.content))
        data.update(
            {
                "iso_en_proper": "Test new country",
                "iso_en_ro_name": "Test new country",
                "iso_en_ro_proper": "Test new country",
                "iso_fr_name": "Tester un nouveau pays",
                "iso_fr_proper": "Tester un nouveau pays",
                "iso_es_name": "Probar nuevo país",
            }
        )
        self.client.post(reverse("admin:common_country_add"), data)
        self.assertTrue(Country.objects.filter(iso3166a2="ZZ").exists())


class ClassifiedProductAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username="admin", password="admin", email="admin@hea.org")
        activate("en")

    def setUp(self):
        self.client.login(username="admin", password="admin")
        self.product1 = ClassifiedProductFactory(cpcv2="A00001AA")
        self.product2 = ClassifiedProductFactory(cpcv2="A00002AA")

    def test_list_classified_product(self):
        response = self.client.get(reverse("admin:common_classifiedproduct_changelist"))
        for attr in ClassifiedProductAdmin.list_display:
            self.assertContains(response, getattr(self.product1, attr))
            self.assertContains(response, getattr(self.product2, attr))

    def test_search_classified_product(self):
        response = self.client.get(
            reverse("admin:common_classifiedproduct_changelist"), {"q": self.product1.common_name_en}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product1.cpcv2)

    def test_creation_classified_product(self):
        unit = UnitOfMeasureFactory()
        data = {
            "cpcv2": "020202",
            "description_en": "New Test Product",
            "description_pt": "New Test Product",
            "description_ar": "New Test Product",
            "description_fr": "New Test Product",
            "description_es": "New Test Product",
            "common_name_en": "New Test Common Name",
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
