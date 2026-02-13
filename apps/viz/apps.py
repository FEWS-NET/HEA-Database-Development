# viz/apps.py
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class VizConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "viz"
    verbose_name = _("viz")
