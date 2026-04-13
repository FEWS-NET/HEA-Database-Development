import json
import logging

from django.views.generic.base import TemplateView

logger = logging.getLogger(__name__)


class DeconstructingJSONEncoder(json.JSONEncoder):
    """JSON encoder that can deconstruct objects that have a deconstruct method.

    This JSONEncoder subclass will call `deconstruct` on objects that have that method, such as
    Django Validators, falling back to `str` for other objects.
    """

    def default(self, obj):
        if hasattr(obj, "deconstruct"):
            return obj.deconstruct()
        return str(obj)


class InventoryDashboardView(TemplateView):

    dash_app = "bss_inventory"

    template_name = "dashboard/pipeline_dashboard.html"

    app_title = "Inventory Dashboard"

    def get_context_data(self, **kwargs) -> dict[str, any]:
        context = super().get_context_data(**kwargs)
        context["dash_app"] = self.dash_app
        return context


class PipelineStatusDashboardView(TemplateView):

    dash_app = "pipeline_status_dashboard"

    template_name = "dashboard/pipeline_dashboard.html"

    app_title = "Pipeline Status Dashboard"

    def get_context_data(self, **kwargs) -> dict[str, any]:
        context = super().get_context_data(**kwargs)
        context["dash_app"] = self.dash_app
        return context
