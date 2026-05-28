from dal import autocomplete
from django import forms
from django.utils.translation import gettext_lazy as _

from baseline.models import (
    Community,
    FoodPurchase,
    LivelihoodActivity,
    LivelihoodStrategy,
    MeatProduction,
    MilkProduction,
    OtherCashIncome,
    OtherPurchase,
    PaymentInKind,
    ReliefGiftOther,
    WealthGroup,
    WealthGroupCharacteristicValue,
)


class LivelihoodActivityForm(forms.ModelForm):
    class Meta:
        model = LivelihoodActivity
        exclude = [
            # "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
        ]
        widgets = {
            "livelihood_strategy": autocomplete.ModelSelect2(url="livelihoodstrategy-autocomplete"),
            "wealth_group": autocomplete.ModelSelect2(url="wealthgroup-autocomplete"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "quantity_produced" in self.fields:
            self.fields["quantity_produced"].label = _("Produced")
        if "quantity_purchased" in self.fields:
            self.fields["quantity_purchased"].label = _("Purchased")
        if "quantity_sold" in self.fields:
            self.fields["quantity_sold"].label = _("Sold")
        if "quantity_consumed" in self.fields:
            self.fields["quantity_consumed"].label = _("Consumed")
        if "quantity_other_uses" in self.fields:
            self.fields["quantity_other_uses"].label = _("Other uses")
        if "percentage_kcals" in self.fields:
            self.fields["percentage_kcals"].label = _("Percentage")


class MilkProductionForm(LivelihoodActivityForm):
    class Meta:
        model = MilkProduction
        exclude = [
            # "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
        ]
        widgets = {
            "livelihood_strategy": autocomplete.ModelSelect2(url="livelihoodstrategy-autocomplete"),
            "wealth_group": autocomplete.ModelSelect2(url="wealthgroup-autocomplete"),
        }

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
        widgets = {
            "livelihood_strategy": autocomplete.ModelSelect2(url="livelihoodstrategy-autocomplete"),
            "wealth_group": autocomplete.ModelSelect2(url="wealthgroup-autocomplete"),
        }

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
        widgets = {
            "livelihood_strategy": autocomplete.ModelSelect2(url="livelihoodstrategy-autocomplete"),
            "wealth_group": autocomplete.ModelSelect2(url="wealthgroup-autocomplete"),
        }

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
        widgets = {
            "livelihood_strategy": autocomplete.ModelSelect2(url="livelihoodstrategy-autocomplete"),
            "wealth_group": autocomplete.ModelSelect2(url="wealthgroup-autocomplete"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["unit_multiple"].label = _("Purchase size")


class MeatProductionForm(LivelihoodActivityForm):
    class Meta:
        model = MeatProduction
        exclude = [
            "livelihood_zone_baseline",
            "strategy_type",
        ]
        widgets = {
            "livelihood_strategy": autocomplete.ModelSelect2(url="livelihoodstrategy-autocomplete"),
            "wealth_group": autocomplete.ModelSelect2(url="wealthgroup-autocomplete"),
        }


class PaymentInKindForm(LivelihoodActivityForm):
    class Meta:
        model = PaymentInKind
        exclude = [
            "livelihood_zone_baseline",
            "strategy_type",
        ]
        widgets = {
            "livelihood_strategy": autocomplete.ModelSelect2(url="livelihoodstrategy-autocomplete"),
            "wealth_group": autocomplete.ModelSelect2(url="wealthgroup-autocomplete"),
        }


class OtherCashIncomeForm(LivelihoodActivityForm):
    class Meta:
        model = OtherCashIncome
        exclude = [
            "livelihood_zone_baseline",
            "strategy_type",
        ]
        widgets = {
            "livelihood_strategy": autocomplete.ModelSelect2(url="livelihoodstrategy-autocomplete"),
            "wealth_group": autocomplete.ModelSelect2(url="wealthgroup-autocomplete"),
        }


class WealthGroupCharacteristicValueForm(forms.ModelForm):
    class Meta:
        model = WealthGroupCharacteristicValue
        fields = "__all__"
        widgets = {
            "wealth_group": autocomplete.ModelSelect2(url="wealthgroup-autocomplete"),
        }


class WealthGroupForm(forms.ModelForm):
    class Meta:
        model = WealthGroup
        fields = "__all__"
        widgets = {
            "livelihood_zone_baseline": autocomplete.ModelSelect2(url="livelihoodzonebaseline-autocomplete"),
            "community": autocomplete.ModelSelect2(url="community-autocomplete"),
        }


class LivelihoodStrategyForm(forms.ModelForm):
    class Meta:
        model = LivelihoodStrategy
        fields = "__all__"
        widgets = {
            "livelihood_zone_baseline": autocomplete.ModelSelect2(url="livelihoodzonebaseline-autocomplete"),
        }


class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = "__all__"
        widgets = {
            "livelihood_zone_baseline": autocomplete.ModelSelect2(url="livelihoodzonebaseline-autocomplete"),
        }
