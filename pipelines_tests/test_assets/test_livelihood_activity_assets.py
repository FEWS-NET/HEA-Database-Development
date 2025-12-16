import json
from pathlib import Path

import pandas as pd
from django.test import TestCase
from pipelines.assets.livelihood_activity import (
    get_label_attributes,
    get_livelihood_activity_label_map,
)

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

    def test_activity_label_override(self):
        label = "riz - kg produits"
        expected_regex_attributes = {
            "activity_label": label,
            "is_start": True,
            "product_id": "riz",
            "unit_of_measure_id": "kg",
            "attribute": "quantity_produced",
        }
        # Test that the regular expression matches the label and returns the expected attributes
        regex_attributes = {k: v for k, v in get_label_attributes(label, LIVELIHOOD_ACTIVITY).items()}
        self.assertDictEqual(
            expected_regex_attributes,
            {k: v for k, v in regex_attributes.items() if k in expected_regex_attributes},
        )
        # Now create an ActivityLabel instance with status=OVERRIDE for the same label but different attributes
        expected_override_attributes = {
            "activity_label": label,
            "is_start": False,
            "product_id": "R01132",
            "season": "season 1",
        }
        ActivityLabel.objects.create(
            status=ActivityLabel.LabelStatus.OVERRIDE,
            activity_type=LIVELIHOOD_ACTIVITY,
            **expected_override_attributes,
        )
        # Clear the cache of label attributes
        get_label_attributes.cache_clear()
        get_livelihood_activity_label_map.cache_clear()
        # Test that the override attributes are returned instead of the regex attributes
        override_attributes = {k: v for k, v in get_label_attributes(label, LIVELIHOOD_ACTIVITY).items()}
        self.assertDictEqual(
            expected_override_attributes,
            {k: v for k, v in override_attributes.items() if k in expected_override_attributes},
        )
        # Test that additional attributes set in the regex instance are ignored when using the override
        self.assertEqual(None, override_attributes["unit_of_measure_id"])
        # Update the ActivityLabel instance to make it use the regex again
        ActivityLabel.objects.filter(activity_label=label, activity_type=LIVELIHOOD_ACTIVITY).update(
            status=ActivityLabel.LabelStatus.REGULAR_EXPRESSION
        )
        # Clear the cache of label attributes
        get_label_attributes.cache_clear()
        get_livelihood_activity_label_map.cache_clear()
        # Test that the regex attributes are returned again
        regex_attributes = {k: v for k, v in get_label_attributes(label, LIVELIHOOD_ACTIVITY).items()}
        self.assertDictEqual(
            expected_regex_attributes,
            {k: v for k, v in regex_attributes.items() if k in expected_regex_attributes},
        )
        # Test that additional attributes set in the ActivityLabel instance are ignored when using the regex
        self.assertEqual("", regex_attributes["season"])
