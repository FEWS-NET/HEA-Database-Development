from django import forms

from baseline.models import LivelihoodActivity


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
        self.fields["quantity_produced"].label = "Produced"
        self.fields["quantity_sold"].label = "Sold"
        self.fields["quantity_consumed"].label = "Consumed"
        self.fields["quantity_other_uses"].label = "Other uses"
        self.fields["total_kcals_consumed"].label = "Total Consumed"
        self.fields["percentage_kcals"].label = "Percentage"
