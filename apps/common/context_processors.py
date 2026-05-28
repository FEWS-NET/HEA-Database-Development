"""
Context processors for the HEA admin.
"""

from django.conf import settings
from django.urls import NoReverseMatch, reverse

from common.menu_config import ADMIN_MENU_CONFIG, APP_INDEX_CONFIG


def theme_context(request):
    # Retrieve the theme from settings (environment variable) or default to 'hea_default'
    theme = getattr(settings, "THEME", "hea_default")
    # Return the theme as a dictionary to be included in the template context
    return {"theme": theme}


def selected_settings(request):
    return {"APP_VERSION": settings.APP_VERSION}


def _build_app_index_config(user):
    # Resolves APP_INDEX_CONFIG into a dict of {app_label: [groups]}
    result = {}
    for app_label, groups in APP_INDEX_CONFIG.items():
        resolved_groups = []
        for group_items in groups:
            resolved_items = []
            for item in group_items:
                if not user.has_perm(item["perm"]):
                    continue
                try:
                    url = reverse(item["url_name"])
                except NoReverseMatch:
                    continue
                add_perm = item["perm"].replace("view_", "add_")
                add_url = None
                if user.has_perm(add_perm):
                    try:
                        add_url = reverse(item["url_name"].replace("_changelist", "_add"))
                    except NoReverseMatch:
                        pass
                resolved_items.append(
                    {
                        "label": item["label"],
                        "icon": item.get("icon", "bi-circle"),
                        "url": url,
                        "add_url": add_url,
                    }
                )
            if resolved_items:
                resolved_groups.append(resolved_items)
        if resolved_groups:
            result[app_label] = resolved_groups
    return result


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

    return {
        "admin_menu_zones": filtered_zones,
        "app_index_config": _build_app_index_config(user),
    }
