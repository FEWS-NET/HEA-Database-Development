from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver

from metadata.models import (
    LivelihoodActivityScenario,
    LivelihoodStrategyType,
)

from .models import (
    BaselineLivelihoodActivity,
    BaselineWealthGroup,
    FoodPurchase,
    LivelihoodActivity,
    LivelihoodProductCategory,
    LivelihoodZoneBaseline,
    OtherPurchase,
    WealthGroup,
)


def _schedule_baseline_refresh(livelihood_zone_baseline_id):
    """
    Schedule a refresh of the LivelihoodZoneBaseline by saving it after the current transaction commits.
    """
    if not livelihood_zone_baseline_id:
        return

    connection = transaction.get_connection()
    current_savepoint_ids = set(connection.savepoint_ids)

    # Don't schedule another refresh if one is already scheduled for the current savepoint and LivelihoodZoneBaseline
    for savepoint_ids, callback, *_rest in connection.run_on_commit:
        if (
            savepoint_ids == current_savepoint_ids
            and getattr(callback, "_baseline_refresh_id", None) == livelihood_zone_baseline_id
        ):
            return

    # Inline function to refresh the baseline after the transaction commits
    def refresh():
        try:
            baseline = LivelihoodZoneBaseline.objects.get(pk=livelihood_zone_baseline_id)
        except LivelihoodZoneBaseline.DoesNotExist:
            return
        baseline.save()

    # Attach the livelihood_zone_baseline_id to the refresh function so we can check for duplicates before scheduling
    refresh._baseline_refresh_id = livelihood_zone_baseline_id
    transaction.on_commit(refresh)


@receiver(post_save, sender=LivelihoodProductCategory)
@receiver(pre_delete, sender=LivelihoodProductCategory)
def refresh_baseline_after_livelihood_product_category_change(sender, instance, **kwargs):
    """
    Refresh the LivelihoodZoneBaseline when a LivelihoodProductCategory is changed.

    This forces the recalculation of the annual_kcals_cost for the Baseline, which depends on Basket 1 and Basket 2,
    and clears the cached Thresholds for the Wealth Groups, which depend on all the Baskets.
    """
    _schedule_baseline_refresh(instance.baseline_livelihood_activity.livelihood_zone_baseline_id)


@receiver(post_save, sender=LivelihoodActivity)
@receiver(pre_delete, sender=LivelihoodActivity)
@receiver(post_save, sender=BaselineLivelihoodActivity)
@receiver(pre_delete, sender=BaselineLivelihoodActivity)
@receiver(post_save, sender=FoodPurchase)
@receiver(pre_delete, sender=FoodPurchase)
@receiver(post_save, sender=OtherPurchase)
@receiver(pre_delete, sender=OtherPurchase)
def refresh_baseline_after_livelihood_activity_change(sender, instance, **kwargs):
    """
    Refresh the LivelihoodZoneBaseline when a FoodPurchase or OtherPurchase BaselineLivelihoodActivity is changed.

    This forces the recalculation of the annual_kcals_cost for the Baseline, and clears the cached Thresholds for the
    Wealth Groups. The calculations depend on the Baseline FoodPurchase and OtherPurchase activities that have
    Livelihood Product Categories, so we only need to trigger the refresh for Activities that meet those criteria.

    Django doesn't fire signals for subclasses of a model, so we need to listen to LivelihoodActivity and
    BaselineLivelihoodActivity as well as FoodPurchase, because we can't be sure exactly which model class is
    instantiated.
    """
    if (
        instance.scenario == LivelihoodActivityScenario.BASELINE
        and instance.strategy_type in [LivelihoodStrategyType.FOOD_PURCHASE, LivelihoodStrategyType.OTHER_PURCHASE]
        and instance.wealth_group_id
        and instance.wealth_group.community_id is None
    ):
        _schedule_baseline_refresh(instance.livelihood_zone_baseline_id)


@receiver(post_save, sender=WealthGroup)
@receiver(post_delete, sender=WealthGroup)
@receiver(post_save, sender=BaselineWealthGroup)
@receiver(post_delete, sender=BaselineWealthGroup)
def refresh_baseline_after_baseline_wealth_group_change(sender, instance, **kwargs):
    """
    Refresh the LivelihoodZoneBaseline when a baseline Wealth Group changes.

    This forces the recalculation of the annual_kcals_cost for the Baseline, which depends on the Poor
    Wealth Group, and clears the cached Thresholds for the Wealth Groups, which depend on the average
    household size of the Wealth Group that each Livelihood Product Category is defined for.
    """
    if instance.community_id is None:
        _schedule_baseline_refresh(instance.livelihood_zone_baseline_id)
