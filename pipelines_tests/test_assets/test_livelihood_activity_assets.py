import json
from pathlib import Path

import pandas as pd
from django.test import TestCase
from pipelines.assets.livelihood_activity import get_label_attributes

from metadata.models import ActivityLabel

LIVELIHOOD_ACTIVITY = ActivityLabel.LivelihoodActivityType.LIVELIHOOD_ACTIVITY


class GetActivityLabelAttributesTestCase(TestCase):

    def test_livelihood_activity_regexes(self):

        # Fetch the list of labels to test and the expected attributes
        with open(Path(__file__).parent / "test_livelihood_activity_regexes.json") as f:
            expected = json.load(f)

        for label, expected_attributes in expected.items():
            with self.subTest(label=label):
                attributes = {
                    k: v for k, v in get_label_attributes(label, LIVELIHOOD_ACTIVITY).items() if not pd.isna(v)
                }
                self.assertGreaterEqual(
                    len(attributes.keys()),
                    1,
                    f"No pattern matched '{label}'",
                )
                found_attributes = {k: v for k, v in attributes.items() if k in expected_attributes}
                self.assertEqual(
                    found_attributes,
                    expected_attributes,
                    f"Attributes from {attributes['notes']} did not match the expected attributes for '{label}'",
                )
                unwanted_attributes = {
                    k: v
                    for k, v in attributes.items()
                    if k not in expected_attributes and k not in ["activity_label", "notes"]
                }

                self.assertFalse(
                    any([bool(v) for k, v in unwanted_attributes.items()]),
                    msg=f"Extra attributes {({k: v for k, v in unwanted_attributes.items() if v})} found for '{label}'",
                )
