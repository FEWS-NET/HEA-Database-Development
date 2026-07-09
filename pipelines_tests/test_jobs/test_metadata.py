from unittest.mock import Mock

import pandas as pd
from django.test import TestCase

from metadata.models import ActivityLabel
from pipelines.jobs.metadata import load_metadata_for_model


class LoadMetadataForModelTestCase(TestCase):
    """
    Regression tests for metadata loading edge cases.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Create shared ActivityLabel test data.
        """
        cls.existing_label = ActivityLabel.objects.create(
            activity_label="Rice Sales",
            activity_type=ActivityLabel.LivelihoodActivityType.LIVELIHOOD_ACTIVITY,
            status="",
            is_start=False,
            notes="Original notes",
        )

    def test_activity_label_matches_existing_case_insensitively(self):
        """
        Preserve the stored label casing while updating other fields from the sheet.
        """
        dataframe = pd.DataFrame(
            [
                {
                    "activity_label": "rice sales",
                    "activity_type": ActivityLabel.LivelihoodActivityType.LIVELIHOOD_ACTIVITY,
                    "status": ActivityLabel.LabelStatus.OVERRIDE,
                    "is_start": True,
                    "notes": "Updated notes",
                }
            ]
        )

        load_metadata_for_model(Mock(), "ActivityLabel", ActivityLabel, dataframe)

        self.assertEqual(ActivityLabel.objects.count(), 1)
        updated_label = ActivityLabel.objects.get(pk=self.existing_label.pk)
        self.assertEqual(updated_label.activity_label, "Rice Sales")
        self.assertEqual(updated_label.status, ActivityLabel.LabelStatus.OVERRIDE)
        self.assertTrue(updated_label.is_start)
        self.assertEqual(updated_label.notes, "Updated notes")

    def test_activity_label_rejects_case_only_duplicates_in_sheet(self):
        """
        Reject ambiguous rows that collapse to the same case-insensitive key.
        """
        dataframe = pd.DataFrame(
            [
                {
                    "activity_label": "rice sales",
                    "activity_type": ActivityLabel.LivelihoodActivityType.LIVELIHOOD_ACTIVITY,
                },
                {
                    "activity_label": "Rice Sales",
                    "activity_type": ActivityLabel.LivelihoodActivityType.LIVELIHOOD_ACTIVITY,
                },
            ]
        )

        with self.assertRaisesMessage(ValueError, "case-insensitively"):
            load_metadata_for_model(Mock(), "ActivityLabel", ActivityLabel, dataframe)
