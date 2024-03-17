from html import escape

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from common.admin import ClassifiedProductAdmin, CountryAdmin, CurrencyAdmin
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
        translation.activate("en")

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
        translation.activate("en")

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
        translation.activate("en")

    def tearDown(self):
        # Ref: https://docs.djangoproject.com/en/4.2/topics/testing/tools/#setting-the-language
        translation.activate(settings.LANGUAGE_CODE)

    def setUp(self):
        self.client.login(username="admin", password="admin")
        self.product1 = ClassifiedProductFactory(cpc="A00001AA")
        self.product2 = ClassifiedProductFactory(cpc="A00002AA")

    def test_translations(self):
        # These strings are an interpolation of two translations each. "Description" and the langauge names are
        # translated separately in the po files and so must be interpolated lazily at render time. So this covers
        # a more complex case than average.
        # Note that this test may fail if `./manage.py compilemessages` has not been run.
        translations = {
            "en": (
                "Description (English):",
                "Description (Spanish):",
                "Description (French):",
                "Description (Arabic):",
                "Description (Portuguese):",
            ),
            "es": (
                "Descripción (Inglés):",
                "Descripción (Portugués):",
                "Descripción (Arábica):",
                "Descripción (Español):",
                "Descripción (Francés):",
            ),
            "fr": (
                "Description (Anglais):",
                "Description (Portugais):",
                "Description (Arabe):",
                "Description (Espagnol):",
                "Description (Français):",
            ),
            "ar": (
                "وصف (إنجليزي):",
                "وصف (البرتغالية):",
                "وصف (عربي):",
                "وصف (الأسبانية):",
                "وصف (فرنسي):",
            ),
            "pt": (
                "Descrição (Inglês):",
                "Descrição (Português):",
                "Descrição (Árabe):",
                "Descrição (Espanhol):",
                "Descrição (Francês):",
            ),
        }
        for code in translations:
            translation.activate(code)
            url = reverse("admin:common_classifiedproduct_add")
            response = self.client.get(url)
            for trans in translations[code]:
                with self.subTest(language=code, trans=trans, url=url):
                    self.assertContains(response, escape(trans), html=True, msg_prefix=response.content.decode())

    def test_list_classified_product(self):
        # There are many products, so filter by the prefix, to guarantee that the product appears on the first page
        response = self.client.get(reverse("admin:common_classifiedproduct_changelist"), {"q": "A0"})
        for attr in ClassifiedProductAdmin.list_display:
            for product in [self.product1, self.product2]:
                expected = getattr(product, attr)
                if isinstance(expected, list) and expected:
                    # When testing the aliases, just check for the first entry in the list, because the representation
                    # of the aliases in the admin may be different.
                    expected = expected[0]
                with self.subTest(attr=attr, product=product):
                    self.assertContains(response, expected, msg_prefix=f"attr={attr}, product={product}")

    def test_search_classified_product(self):
        response = self.client.get(
            reverse("admin:common_classifiedproduct_changelist"), {"q": self.product1.common_name_en}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.product1.cpc)

    def test_creation_classified_product(self):
        unit = UnitOfMeasureFactory()
        data = {
            "cpc": "020202",
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
        self.assertTrue(ClassifiedProduct.objects.filter(cpc="020202").exists())


class UnitOfMeasureAdminTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username="admin", password="admin", email="admin@hea.org")
        translation.activate("en")

    def setUp(self):
        self.uom1 = UnitOfMeasureFactory(aliases=["alias1"])
        self.uom2 = UnitOfMeasureFactory(aliases=["alias2"])
        self.client.login(username="admin", password="admin")

    def test_list_returns_all_records(self):
        response = self.client.get(reverse("admin:common_unitofmeasure_changelist"))
        self.assertContains(response, self.uom1.abbreviation)
        self.assertContains(response, self.uom2.abbreviation)
        self.assertContains(response, self.uom1.description)
        self.assertContains(response, self.uom2.description)
        self.assertContains(response, "alias1")
        self.assertContains(response, "alias2")

    def test_unit_of_measure_search(self):
        response = self.client.get(reverse("admin:common_unitofmeasure_changelist"), {"q": self.uom1.abbreviation})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.uom1.abbreviation)
        self.assertContains(response, self.uom1.description)
        self.assertContains(response, "alias1")
        self.assertNotContains(response, self.uom2.abbreviation)

    def test_unit_of_measure_creation(self):
        data = {
            "abbreviation": "cm",
            "unit_type": UnitOfMeasure.LENGTH,
            "description_en": "Centimeter",
            "from_conversions-TOTAL_FORMS": "0",
            "from_conversions-INITIAL_FORMS": "0",
            "from_conversions-MIN_NUM_FORMS": "0",
            "from_conversions-MAX_NUM_FORMS": "0",
        }
        self.client.post(reverse("admin:common_unitofmeasure_add"), data)
        self.assertTrue(UnitOfMeasure.objects.filter(abbreviation="cm").exists())
