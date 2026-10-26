import json
from unittest.mock import patch

from dagster import build_asset_context
from django.apps import apps
from django.core import serializers
from django.db import models
from django.test import TestCase

from baseline.models import (
    Community,
    Hazard,
    KeyParameter,
    LivelihoodActivity,
    LivelihoodStrategy,
    LivelihoodZoneBaselineCorrection,
    MilkProduction,
    SeasonalActivity,
    SeasonalActivityOccurrence,
    WealthGroup,
    WealthGroupCharacteristicValue,
)
from baseline.tests.factories import (
    BaselineWealthGroupCharacteristicValueFactory,
    BaselineWealthGroupFactory,
    CommunityFactory,
    CommunityWealthGroupFactory,
    HazardFactory,
    KeyParameterFactory,
    LivelihoodStrategyFactory,
    LivelihoodZoneBaselineFactory,
    MilkProductionFactory,
    SeasonalActivityFactory,
    SeasonalActivityOccurrenceFactory,
)
from common.tests.factories import UserFactory
from metadata.tests.factories import SeasonFactory
from pipelines.assets.fixtures import (
    BASELINE_RECONCILIATION_EXCLUDED_MODELS,
    get_baseline_reconciliation_models,
    get_livelihood_zone_baseline_lookup,
    get_root_model,
    import_fixture,
    imported_baseline,
)
from pipelines.assets.seasonal_calendar import imported_seasonal_activities


def get_fixture(*instances: models.Model) -> list[dict]:
    """
    Create a fixture in the format produced by the pipeline from existing model instances.

    The records use natural keys rather than primary keys, and records for multi-table inheritance children, such as
    MilkProduction, contain the fields from their parent models as well as their own fields. Proxy models, such as
    BaselineWealthGroup, use the label of their concrete model, which provides the natural key lookup.
    """
    fixture = []
    for instance in instances:
        objects = [
            parent_model._base_manager.get(pk=instance.pk) for parent_model in instance._meta.get_parent_list()
        ] + [instance]
        records = json.loads(
            serializers.serialize("json", objects, use_natural_foreign_keys=True, use_natural_primary_keys=True)
        )
        fields = {}
        for record in records:
            fields.update(record["fields"])
        fixture.append({"model": instance._meta.concrete_model._meta.label_lower, "fields": fields})
    return fixture


class ImportFixtureReconciliationTestCase(TestCase):
    """
    Tests for reconciling existing Baseline data with an imported fixture.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Create a Baseline containing instances that are in the fixture and legacy instances that are not.
        """
        cls.livelihood_zone_baseline = LivelihoodZoneBaselineFactory()
        cls.partition_key = "~".join(
            [
                cls.livelihood_zone_baseline.livelihood_zone.country_id,
                *cls.livelihood_zone_baseline.natural_key(),
            ]
        )
        # Livelihood Strategy natural keys require a Season in the same Country as the Livelihood Zone
        cls.season = SeasonFactory(country=cls.livelihood_zone_baseline.livelihood_zone.country)
        cls.community = CommunityFactory(livelihood_zone_baseline=cls.livelihood_zone_baseline)
        cls.correction = LivelihoodZoneBaselineCorrection.objects.create(
            livelihood_zone_baseline=cls.livelihood_zone_baseline,
            worksheet_name="WB",
            cell_range="B2",
            previous_value="old",
            value="new",
            author=UserFactory(),
            comment="Test correction",
        )

        # Instances that are in the fixture
        cls.wealth_group = BaselineWealthGroupFactory(livelihood_zone_baseline=cls.livelihood_zone_baseline)
        cls.wealth_group_characteristic_value = BaselineWealthGroupCharacteristicValueFactory(
            wealth_group=cls.wealth_group
        )
        cls.livelihood_strategy = LivelihoodStrategyFactory(
            livelihood_zone_baseline=cls.livelihood_zone_baseline,
            strategy_type="MilkProduction",
            season=cls.season,
        )
        cls.livelihood_activity = MilkProductionFactory(
            livelihood_zone_baseline=cls.livelihood_zone_baseline,
            livelihood_strategy=cls.livelihood_strategy,
            wealth_group=cls.wealth_group,
            scenario="baseline",
        )
        cls.seasonal_activity = SeasonalActivityFactory(livelihood_zone_baseline=cls.livelihood_zone_baseline)
        cls.seasonal_activity_occurrence = SeasonalActivityOccurrenceFactory(
            seasonal_activity=cls.seasonal_activity,
            livelihood_zone_baseline=cls.livelihood_zone_baseline,
            community=cls.community,
        )
        cls.fixture = get_fixture(
            cls.wealth_group,
            cls.wealth_group_characteristic_value,
            cls.livelihood_strategy,
            cls.livelihood_activity,
            cls.seasonal_activity,
            cls.seasonal_activity_occurrence,
        )
        cls.seasonal_activity_fixture = get_fixture(cls.seasonal_activity, cls.seasonal_activity_occurrence)

        # Legacy instances that are not in the fixture
        cls.legacy_wealth_group = CommunityWealthGroupFactory(
            livelihood_zone_baseline=cls.livelihood_zone_baseline, community=cls.community
        )
        cls.legacy_wealth_group_characteristic_value = BaselineWealthGroupCharacteristicValueFactory(
            wealth_group=cls.wealth_group
        )
        cls.legacy_livelihood_strategy = LivelihoodStrategyFactory(
            livelihood_zone_baseline=cls.livelihood_zone_baseline,
            strategy_type="MilkProduction",
            season=cls.season,
        )
        cls.legacy_livelihood_activity = MilkProductionFactory(
            livelihood_zone_baseline=cls.livelihood_zone_baseline,
            livelihood_strategy=cls.legacy_livelihood_strategy,
            wealth_group=cls.wealth_group,
            scenario="baseline",
        )
        cls.legacy_key_parameter = KeyParameterFactory(livelihood_strategy=cls.livelihood_strategy)
        cls.legacy_seasonal_activity = SeasonalActivityFactory(livelihood_zone_baseline=cls.livelihood_zone_baseline)
        cls.legacy_seasonal_activity_occurrence = SeasonalActivityOccurrenceFactory(
            seasonal_activity=cls.seasonal_activity,
            livelihood_zone_baseline=cls.livelihood_zone_baseline,
            community=CommunityFactory(livelihood_zone_baseline=cls.livelihood_zone_baseline),
        )
        cls.legacy_hazard = HazardFactory(community=cls.community)

        # Instances for a different Baseline, which must not be affected
        cls.other_livelihood_activity = MilkProductionFactory(scenario="baseline")

    def assertExists(self, *instances: models.Model):
        """
        Assert that each instance still exists in the database.
        """
        for instance in instances:
            self.assertTrue(
                get_root_model(type(instance))._base_manager.filter(pk=instance.pk).exists(),
                f"{instance._meta.label} {instance.pk} was deleted",
            )

    def assertDeleted(self, *instances: models.Model):
        """
        Assert that each instance has been deleted from the database.
        """
        for instance in instances:
            self.assertFalse(
                get_root_model(type(instance))._base_manager.filter(pk=instance.pk).exists(),
                f"{instance._meta.label} {instance.pk} was not deleted",
            )

    def test_imported_baseline_deletes_instances_not_in_fixture(self):
        """
        Importing the consolidated fixture deletes legacy instances and retains Communities and Corrections.
        """
        output = imported_baseline(build_asset_context(partition_key=self.partition_key), self.fixture)

        self.assertExists(
            self.wealth_group,
            self.wealth_group_characteristic_value,
            self.livelihood_strategy,
            self.livelihood_activity,
            self.seasonal_activity,
            self.seasonal_activity_occurrence,
            self.community,
            self.correction,
            self.other_livelihood_activity,
        )
        self.assertDeleted(
            self.legacy_wealth_group,
            self.legacy_wealth_group_characteristic_value,
            self.legacy_livelihood_strategy,
            self.legacy_livelihood_activity,
            self.legacy_key_parameter,
            self.legacy_seasonal_activity,
            self.legacy_seasonal_activity_occurrence,
            self.legacy_hazard,
        )
        # The multi-table inheritance child row is deleted along with the root row
        self.assertFalse(MilkProduction.objects.filter(pk=self.legacy_livelihood_activity.pk).exists())
        self.assertEqual(Community.objects.filter(livelihood_zone_baseline=self.livelihood_zone_baseline).count(), 2)
        self.assertEqual(output.metadata["num_deleted_wealthgroup"].value, 1)
        self.assertEqual(output.metadata["num_deleted_livelihoodactivity"].value, 1)
        self.assertEqual(output.metadata["num_deleted_milkproduction"].value, 1)
        self.assertEqual(output.metadata["num_deleted_hazard"].value, 1)

    def test_import_updates_existing_instances_in_place(self):
        """
        Instances that are in the fixture are updated and keep their primary keys.
        """
        fixture = json.loads(json.dumps(self.fixture))
        fixture[0]["fields"]["percentage_of_households"] = "12.34"

        imported_baseline(build_asset_context(partition_key=self.partition_key), fixture)

        wealth_group = WealthGroup.objects.get(pk=self.wealth_group.pk)
        self.assertEqual(str(wealth_group.percentage_of_households), "12.34")
        self.assertEqual(
            WealthGroup.objects.filter(livelihood_zone_baseline=self.livelihood_zone_baseline).count(),
            1,
        )

    def test_import_without_reconcile_deletes_nothing(self):
        """
        Partial fixtures, such as those for a single worksheet, don't delete instances that they don't contain.
        """
        import_fixture(get_fixture(self.wealth_group, self.livelihood_strategy))

        self.assertExists(
            self.legacy_wealth_group,
            self.legacy_livelihood_activity,
            self.legacy_key_parameter,
            self.legacy_seasonal_activity,
        )

    def test_imported_seasonal_activities_only_reconciles_seasonal_calendar(self):
        """
        Importing the Seasonal Calendar fixture deletes legacy Seasonal Activities but not other models.
        """
        imported_seasonal_activities(
            build_asset_context(partition_key=self.partition_key), self.seasonal_activity_fixture
        )

        self.assertExists(self.seasonal_activity, self.seasonal_activity_occurrence, self.legacy_wealth_group)
        self.assertDeleted(self.legacy_seasonal_activity, self.legacy_seasonal_activity_occurrence)
        self.assertEqual(
            SeasonalActivity.objects.filter(livelihood_zone_baseline=self.livelihood_zone_baseline).count(), 1
        )
        self.assertEqual(
            SeasonalActivityOccurrence.objects.filter(livelihood_zone_baseline=self.livelihood_zone_baseline).count(),
            1,
        )

    def test_failed_reconciliation_rolls_back_import(self):
        """
        If the reconciliation fails then the import is rolled back too.
        """
        fixture = json.loads(json.dumps(self.fixture))
        fixture[0]["fields"]["percentage_of_households"] = "12.34"

        with patch("pipelines.assets.fixtures.reconcile_fixture", side_effect=RuntimeError("Reconciliation failed")):
            with self.assertRaises(RuntimeError):
                imported_baseline(build_asset_context(partition_key=self.partition_key), fixture)

        wealth_group = WealthGroup.objects.get(pk=self.wealth_group.pk)
        self.assertEqual(wealth_group.percentage_of_households, self.wealth_group.percentage_of_households)
        self.assertExists(self.legacy_wealth_group)

    def test_import_fixture_reconciles_every_baseline_in_fixture(self):
        """
        A fixture containing several Baselines is authoritative for each of them, but not for other Baselines.
        """
        second_livelihood_zone_baseline = LivelihoodZoneBaselineFactory()
        second_wealth_group = BaselineWealthGroupFactory(livelihood_zone_baseline=second_livelihood_zone_baseline)
        second_legacy_wealth_group = CommunityWealthGroupFactory(
            livelihood_zone_baseline=second_livelihood_zone_baseline,
            community=CommunityFactory(livelihood_zone_baseline=second_livelihood_zone_baseline),
        )

        output = import_fixture(
            self.fixture + get_fixture(second_wealth_group), reconcile=get_baseline_reconciliation_models()
        )

        self.assertExists(self.wealth_group, second_wealth_group, self.other_livelihood_activity)
        self.assertDeleted(self.legacy_wealth_group, second_legacy_wealth_group)
        self.assertEqual(output.metadata["num_deleted_wealthgroup"].value, 2)


class BaselineReconciliationModelsTestCase(TestCase):
    """
    Tests for the models that are reconciled when importing a Baseline.
    """

    def test_every_baseline_model_is_reconciled_or_excluded(self):
        """
        Every model in the `baseline` app can be filtered by Baseline, or is explicitly excluded.
        """
        reconciled_models = get_baseline_reconciliation_models()
        for model in apps.get_app_config("baseline").get_models():
            root_model = get_root_model(model)
            with self.subTest(model=model._meta.label):
                if root_model in BASELINE_RECONCILIATION_EXCLUDED_MODELS:
                    self.assertNotIn(root_model, reconciled_models)
                else:
                    self.assertIn(root_model, reconciled_models)
                    self.assertIsNotNone(get_livelihood_zone_baseline_lookup(root_model))

    def test_reconciled_models(self):
        """
        The reconciled models include the data loaded from the BSS, but not Communities or Corrections.
        """
        reconciled_models = get_baseline_reconciliation_models()
        for model in [
            WealthGroup,
            WealthGroupCharacteristicValue,
            LivelihoodStrategy,
            LivelihoodActivity,
            KeyParameter,
            SeasonalActivity,
            SeasonalActivityOccurrence,
            Hazard,
        ]:
            self.assertIn(model, reconciled_models)
        for model in [Community, LivelihoodZoneBaselineCorrection]:
            self.assertNotIn(model, reconciled_models)
