from django.conf import settings
from django.test import TestCase
from django.utils import translation

from common.tests.factories import ClassifiedProductFactory


class TranslatedFieldsTestCase(TestCase):
    def test_translated_fields(self):
        product = ClassifiedProductFactory()
        self.assertEqual(product.common_name_en, "Product R09999AA en")
        self.assertEqual(product.description_en, "Product Description R09999AA en")
        # Check properties return default language
        self.assertEqual(product.common_name, "Product R09999AA en")
        self.assertEqual(product.description, "Product Description R09999AA en")
        # Check properties return non-default language when selected
        translation.activate("pt")
        self.assertEqual(product.common_name_pt, "Product R09999AA pt")
        self.assertEqual(product.description_pt, "Product Description R09999AA pt")
        self.assertEqual(product.common_name, "Product R09999AA pt")
        self.assertEqual(product.description, "Product Description R09999AA pt")
        for code, name in settings.LANGUAGES:
            translation.activate(code)
            wrong_code = "es" if code == "pt" else "pt"
            self.assertEqual(product.common_name, getattr(product, f"common_name_{code}"))
            self.assertEqual(product.description, getattr(product, f"description_{code}"))
            self.assertNotEqual(product.common_name, getattr(product, f"common_name_{wrong_code}"))
            self.assertNotEqual(product.description, getattr(product, f"description_{wrong_code}"))

        # TODO: Add test for product.display_name

    def tearDown(self):
        # https://docs.djangoproject.com/en/4.2/topics/testing/tools/#setting-the-language
        translation.activate(settings.LANGUAGE_CODE)
