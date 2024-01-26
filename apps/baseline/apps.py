from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BaselineConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "baseline"
    verbose_name = _("baseline")
