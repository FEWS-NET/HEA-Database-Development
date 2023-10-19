from django import forms
from django.utils.translation import gettext_lazy as _

from baseline.models import (
    FoodPurchase,
    LivelihoodActivity,
    MilkProduction,
    OtherPurchase,
    ReliefGiftOther,
)


class LivelihoodActivityForm(forms.ModelForm):
    class Meta:
        model = LivelihoodActivity
        exclude = [
            # "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["quantity_produced"].label = _("Produced")
        self.fields["quantity_purchased"].label = _("Purchased")
        self.fields["quantity_sold"].label = _("Sold")
        self.fields["quantity_consumed"].label = _("Consumed")
        self.fields["quantity_other_uses"].label = _("Other uses")
        self.fields["percentage_kcals"].label = _("Percentage")


class MilkProductionForm(LivelihoodActivityForm):
    class Meta:
        model = MilkProduction
        exclude = [
            # "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["quantity_butter_production"].label = _("Butter Production")


class FoodPurchaseForm(LivelihoodActivityForm):
    class Meta:
        model = FoodPurchase
        exclude = [
            # "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["unit_multiple"].label = _("Purchase size")


class ReliefGiftOtherForm(LivelihoodActivityForm):
    class Meta:
        model = ReliefGiftOther
        exclude = [
            # "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["unit_multiple"].label = _("Relief size")


class OtherPurchaseForm(LivelihoodActivityForm):
    class Meta:
        model = OtherPurchase
        exclude = [
            # "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["unit_multiple"].label = _("Purchase size")
