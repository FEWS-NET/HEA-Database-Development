from django.conf import settings
from django.test import TestCase
from django.utils import translation

from common.tests.factories import ClassifiedProductFactory


class TranslatedFieldsTestCase(TestCase):
    def test_translated_fields(self):
        product = ClassifiedProductFactory()
        self.assertEqual(product.common_name_en[-2:], "en")
        self.assertEqual(product.description_en[-2:], "en")
        # Check properties return default language
        self.assertEqual(product.common_name[-2:], "en")
        self.assertEqual(product.description[-2:], "en")
        self.assertEqual(product.common_name, product.common_name_en)
        self.assertEqual(product.description, product.description_en)
        # Check properties return non-default language when selected
        translation.activate("pt")
        self.assertEqual(product.common_name_pt[-2:], "pt")
        self.assertEqual(product.description_pt[-2:], "pt")
        self.assertEqual(product.common_name[-2:], "pt")
        self.assertEqual(product.description[-2:], "pt")
        self.assertEqual(product.common_name, product.common_name_pt)
        self.assertEqual(product.description, product.description_pt)
        for code, name in settings.LANGUAGES:
            translation.activate(code)
            wrong_code = "es" if code == "pt" else "pt"
            self.assertEqual(product.common_name, getattr(product, f"common_name_{code}"))
            self.assertEqual(product.description, getattr(product, f"description_{code}"))
            self.assertNotEqual(product.common_name, getattr(product, f"common_name_{wrong_code}"))
            self.assertNotEqual(product.description, getattr(product, f"description_{wrong_code}"))

    def tearDown(self):
        # Ref: https://docs.djangoproject.com/en/4.2/topics/testing/tools/#setting-the-language
        translation.activate(settings.LANGUAGE_CODE)
