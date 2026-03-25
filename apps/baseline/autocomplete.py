from dal import autocomplete
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Community, LivelihoodStrategy, LivelihoodZoneBaseline, WealthGroup


class WealthGroupAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    #  autocomplete endpoint for WealthGroup FK fields.

    def get_queryset(self):
        qs = WealthGroup.objects.select_related(
            "community",
            "livelihood_zone_baseline__livelihood_zone",
            "wealth_group_category",
        )
        if self.q:
            qs = (
                WealthGroup.objects.filter(community__name__icontains=self.q)
                | WealthGroup.objects.filter(livelihood_zone_baseline__livelihood_zone__code__icontains=self.q)
                | WealthGroup.objects.filter(wealth_group_category__code__icontains=self.q)
            )
        return qs


class CommunityAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    # autocomplete endpoint for Community FK fields.

    def get_queryset(self):
        qs = Community.objects.select_related(
            "livelihood_zone_baseline__livelihood_zone",
        )
        if self.q:
            qs = (
                Community.objects.filter(name__icontains=self.q)
                | Community.objects.filter(full_name__icontains=self.q)
                | Community.objects.filter(livelihood_zone_baseline__livelihood_zone__code__icontains=self.q)
            )
        return qs


class LivelihoodZoneBaselineAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    # autocomplete endpoint for LivelihoodZoneBaseline FK fields

    def get_queryset(self):
        qs = LivelihoodZoneBaseline.objects.select_related(
            "livelihood_zone",
            "source_organization",
        )
        if self.q:
            qs = (
                LivelihoodZoneBaseline.objects.filter(livelihood_zone__code__icontains=self.q)
                | LivelihoodZoneBaseline.objects.filter(livelihood_zone__name_en__icontains=self.q)
                | LivelihoodZoneBaseline.objects.filter(livelihood_zone__alternate_code__icontains=self.q)
            )
        return qs


class LivelihoodStrategyAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    # autocomplete endpoint for LivelihoodStrategy FK fields

    def get_queryset(self):
        qs = LivelihoodStrategy.objects.select_related(
            "livelihood_zone_baseline__livelihood_zone",
            "product",
        )
        if self.q:
            qs = (
                LivelihoodStrategy.objects.filter(strategy_type__icontains=self.q)
                | LivelihoodStrategy.objects.filter(additional_identifier__icontains=self.q)
                | LivelihoodStrategy.objects.filter(livelihood_zone_baseline__livelihood_zone__code__icontains=self.q)
            )
        return qs
