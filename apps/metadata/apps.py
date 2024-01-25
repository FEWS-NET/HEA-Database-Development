from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MetadataConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "metadata"
    verbose_name = _("metadata")
