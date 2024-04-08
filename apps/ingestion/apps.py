from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class IngestionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ingestion"
    verbose_name = _("ingestion")
