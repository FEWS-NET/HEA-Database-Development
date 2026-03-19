"""
Context processors for the HEA admin.
"""

from django.conf import settings

from common.menu_config import ADMIN_MENU_CONFIG


def theme_context(request):
    # Retrieve the theme from settings (environment variable) or default to 'hea_default'
    theme = getattr(settings, "THEME", "hea_default")
    # Return the theme as a dictionary to be included in the template context
    return {"theme": theme}


def selected_settings(request):
    return {"APP_VERSION": settings.APP_VERSION}


def admin_menu_context(request):
    """
    Injects a permission-filtered menu structure into the template context.
    """
    user = getattr(request, "user", None)
    if user is None or not user.is_active or not user.is_staff:
        return {}

    def has_perm(perm):
        return user.has_perm(perm)

    filtered_zones = []
    for zone in ADMIN_MENU_CONFIG:
        filtered_sections = []
        for section in zone["sections"]:
            perms_any = section.get("perms_any", [])
            if perms_any and not any(has_perm(p) for p in perms_any):
                continue

            filtered_items = [item for item in section["items"] if has_perm(item["perm"])]
            if filtered_items:
                filtered_sections.append({**section, "items": filtered_items})

        if filtered_sections:
            filtered_zones.append({**zone, "sections": filtered_sections})

    return {"admin_menu_zones": filtered_zones}
