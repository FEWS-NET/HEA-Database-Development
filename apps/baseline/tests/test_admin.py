from datetime import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from baseline.models import LivelihoodZoneBaseline

from .admin import LivelihoodZoneBaselineAdmin


class LivelihoodZoneBaselineAdminTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username="admin", password="admin", email="admin@example.com")
        self.client.login(username="admin", password="admin")

        # Create a sample instance for testing
        self.baseline = LivelihoodZoneBaseline.objects.create(
            livelihood_zone="Test Zone",
            main_livelihood_category="Test Category",
            source_organization="Test Org",
            bss="Test BSS",
            reference_year_start_date=datetime(2022, 1, 1),
            reference_year_end_date=datetime(2022, 12, 31),
            valid_from_date=datetime(2022, 1, 1),
            valid_to_date=datetime(2022, 12, 31),
            geography="Test Geography",
            population_source="Test Source",
            population_estimate=10000,
        )

    def test_list_display(self):
        response = self.client.get(reverse("admin:app_label_livelihoodzonebaseline_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Zone")
        self.assertContains(response, "Test Category")
        self.assertContains(response, "Test Org")
        self.assertContains(response, "2022-01-01")
        self.assertContains(response, "2022-12-31")

    def test_search_fields(self):
        response = self.client.get(reverse("admin:app_label_livelihoodzonebaseline_changelist"), {"q": "Test Zone"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Zone")

    def test_list_filter(self):
        response = self.client.get(
            reverse("admin:app_label_livelihoodzonebaseline_changelist"),
            {"source_organization__id__exact": self.baseline.source_organization.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Zone")

    def test_date_hierarchy(self):
        response = self.client.get(reverse("admin:app_label_livelihoodzonebaseline_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2022-01-01")

    def test_create_baseline(self):
        data = {
            "livelihood_zone": "New Test Zone",
            "main_livelihood_category": "New Test Category",
            "source_organization": "New Test Org",
            "bss": "New Test BSS",
            "reference_year_start_date": "2023-01-01",
            "reference_year_end_date": "2023-12-31",
            "valid_from_date": "2023-01-01",
            "valid_to_date": "2023-12-31",
            "geography": "New Test Geography",
            "population_source": "New Test Source",
            "population_estimate": 15000,
        }
        response = self.client.post(reverse("admin:app_label_livelihoodzonebaseline_add"), data)
        self.assertEqual(response.status_code, 302)  # Should redirect after successful creation
        self.assertTrue(LivelihoodZoneBaseline.objects.filter(livelihood_zone="New Test Zone").exists())
