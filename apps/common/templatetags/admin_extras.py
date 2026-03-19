from django import template
from django.apps import apps

register = template.Library()


@register.simple_tag
def get_dashboard_stats():
    # Return key record counts for the admin dashboard stats bar
    try:
        LivelihoodZoneBaseline = apps.get_model("baseline", "LivelihoodZoneBaseline")
        LivelihoodZone = apps.get_model("baseline", "LivelihoodZone")
        Community = apps.get_model("baseline", "Community")
        Country = apps.get_model("common", "Country")
        return {
            "baselines": LivelihoodZoneBaseline.objects.count(),
            "livelihood_zones": LivelihoodZone.objects.count(),
            "communities": Community.objects.count(),
            "countries": Country.objects.count(),
        }
    except Exception:
        return {}
