from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.utils import translation
from rest_framework.test import APIClient

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

    def test_api(self):
        url = reverse("classifiedproduct-detail", args=(self.product.pk,))
        for code, name in settings.LANGUAGES:
            different_code = "es" if code == "pt" else "pt"
            with self.subTest(language=code, url=url, wrong_code=different_code):

                # From HTTP header in APIClient constructor (DRF doesn't detect header from vanilla Django test client)
                drf_client = APIClient(HTTP_ACCEPT_LANGUAGE=code)
                response = drf_client.get(url)
                self.assertEqual(response.status_code, 200)
                description_from_api = response.json()["description"]
                self.assertEqual(description_from_api, getattr(self.product, f"description_{code}"))
                self.assertNotEqual(description_from_api, getattr(self.product, f"description_{different_code}"))

                # From dynamic HTTP header (DRF doesn't detect header from vanilla Django test client)
                drf_client = APIClient()
                response = drf_client.get(url, headers={"accept-language": code})
                self.assertEqual(response.status_code, 200)
                description_from_api = response.json()["description"]
                self.assertEqual(description_from_api, getattr(self.product, f"description_{code}"))
                self.assertNotEqual(description_from_api, getattr(self.product, f"description_{different_code}"))

                # From Django language cookie (using vanilla Django test client)
                self.client.cookies.load({settings.LANGUAGE_COOKIE_NAME: code})
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                description_from_api = response.json()["description"]
                self.assertEqual(description_from_api, getattr(self.product, f"description_{code}"))
                self.assertNotEqual(description_from_api, getattr(self.product, f"description_{different_code}"))

                # From custom LanguageMiddleware language parameter. Takes precedence over cookie
                response = self.client.get(url, {"language": different_code})
                self.assertEqual(response.status_code, 200)
                description_from_api = response.json()["description"]
                self.assertEqual(description_from_api, getattr(self.product, f"description_{different_code}"))
                self.assertNotEqual(description_from_api, getattr(self.product, f"description_{code}"))

                # Custom LanguageMiddleware language parameter. Takes precedence over HTTP header
                drf_client = APIClient(HTTP_ACCEPT_LANGUAGE=code)
                response = drf_client.get(url, {"language": different_code}, headers={"accept-language": code})
                self.assertEqual(response.status_code, 200)
                description_from_api = response.json()["description"]
                self.assertEqual(description_from_api, getattr(self.product, f"description_{different_code}"))
                self.assertNotEqual(description_from_api, getattr(self.product, f"description_{code}"))

    def test_jsi18n(self):
        # Used to translate Javascript clients. Provided by Django, so sufficient to test just that the view is served
        response = self.client.get(reverse("javascript-catalog"))
        self.assertEqual(response.status_code, 200)
        translation.activate("pt")
        response = self.client.get(reverse("javascript-catalog"))
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        # Ref: https://docs.djangoproject.com/en/4.2/topics/testing/tools/#setting-the-language
        translation.activate(settings.LANGUAGE_CODE)
