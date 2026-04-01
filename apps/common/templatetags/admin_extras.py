from django import template
from django.apps import apps

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.simple_tag
def get_dashboard_stats():
    # Return key record counts for the admin dashboard stats
    try:
        LivelihoodZoneBaseline = apps.get_model("baseline", "LivelihoodZoneBaseline")
        WealthGroupCharacteristicValue = apps.get_model("baseline", "WealthGroupCharacteristicValue")
        LivelihoodActivity = apps.get_model("baseline", "LivelihoodActivity")
        return {
            "baselines": f"{LivelihoodZoneBaseline.objects.count():,}",
            "wealth_characteristic_values": f"{WealthGroupCharacteristicValue.objects.count():,}",
            "community_activities": f"{LivelihoodActivity.objects.filter(wealth_group__community__isnull=False).count():,}",
            "baseline_activities": f"{LivelihoodActivity.objects.filter(wealth_group__community__isnull=True).count():,}",
        }
    except Exception:
        return {}
