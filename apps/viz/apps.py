from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class VizConfig(AppConfig):
    """
    Visualizations of the status and quality of the HEA data and pipelines.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "viz"
    verbose_name = _("visualizations")
