from django.conf import settings
from django.test import TestCase
from django.utils import translation

from common.fields import translation_fields
from common.tests.factories import ClassifiedProductFactory


class TranslatedFieldsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = ClassifiedProductFactory(
            common_name_en="common_name en",
            common_name_fr="common_name fr",
            common_name_ar="common_name ar",
            common_name_es="common_name es",
            common_name_pt="common_name pt",
            description_en="description en",
            description_fr="description fr",
            description_ar="description ar",
            description_es="description es",
            description_pt="description pt",
        )

    def test_blank_permission(self):
        # ClassifiedProduct common_name is blank=True, so all variants can be blank.
        # ClassifiedProduct description is blank=False. This validation should be applied to default language only.
        # So this tests that description_en blank=False, other languages, and all common_name variants blank=True.
        for translated_field in ("common_name", "description"):
            for field_name in translation_fields(translated_field):
                blankable = field_name != "description_en"
                with self.subTest(field=field_name):
                    self.assertEqual(
                        self.product._meta.get_field(field_name).blank,
                        blankable,
                        f"Field {field_name} blank is {self.product._meta.get_field(field_name).blank}",
                    )

    def test_translation(self):
        self.assertEqual(self.product.common_name_en, "common_name en")
        self.assertEqual(self.product.description_en, "description en")
        # Check properties return default language
        self.assertEqual(self.product.common_name, "common_name en")
        self.assertEqual(self.product.description, "description en")
        self.assertEqual(self.product.common_name, self.product.common_name_en)
        self.assertEqual(self.product.description, self.product.description_en)
        # Check properties return non-default language when selected
        translation.activate("pt")
        self.assertEqual(self.product.common_name_pt, "common_name pt")
        self.assertEqual(self.product.description_pt, "description pt")
        self.assertEqual(self.product.common_name, "common_name pt")
        self.assertEqual(self.product.description, "description pt")
        self.assertEqual(self.product.common_name, self.product.common_name_pt)
        self.assertEqual(self.product.description, self.product.description_pt)
        for code, name in settings.LANGUAGES:
            with self.subTest(language=code):
                translation.activate(code)
                wrong_code = "es" if code == "pt" else "pt"
                # Check model returns translated value
                self.assertEqual(self.product.common_name, getattr(self.product, f"common_name_{code}"))
                self.assertEqual(self.product.description, getattr(self.product, f"description_{code}"))
                self.assertNotEqual(self.product.common_name, getattr(self.product, f"common_name_{wrong_code}"))
                self.assertNotEqual(self.product.description, getattr(self.product, f"description_{wrong_code}"))

    def tearDown(self):
        # Ref: https://docs.djangoproject.com/en/4.2/topics/testing/tools/#setting-the-language
        translation.activate(settings.LANGUAGE_CODE)
