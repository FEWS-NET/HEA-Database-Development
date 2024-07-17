import logging

from django import template
from django.conf import settings

logger = logging.getLogger(__name__)
register = template.Library()

ALLOWABLE_VALUES = {
    "ORG_NAME",
    "THEME",
    "GOOGLE_ANALYTICS_TRACKING_ID",
    "PINGDOM_TRACKING_ID",
    "SUPPORT_EMAIL_ADDRESS",
    "HELPDESK_ADDRESS",
    "SUPPORT_EMAIL_PARAMS",
    "ACCOUNT_APPROVAL_ORG",
    "MANIFEST_PATH",
    "FAVICON_PATH",
    "HEA_FAVICON_PATH",
    "PRIVACY_URL",
    "DISCLAIMER_URL",
}


# settings value
@register.simple_tag
def settings_value(key, default=None):
    if key in ALLOWABLE_VALUES:
        return getattr(settings, key, default)
    logger.warning(f"Non-allowed setting {key} requested by template.")
    return ""
