from django.urls import path

import viz.dash.inventory_dashboard.app  # NOQA: F401
import viz.dash.pipeline_status_dashboard.app  # NOQA: F401
from viz.views import InventoryDashboardView, PipelineStatusDashboardView

app_name = "viz"


urlpatterns = [
    path("inventory-dashboard/", InventoryDashboardView.as_view(), name="inventory_dashboard"),
    path("pipeline-status-dashboard/", PipelineStatusDashboardView.as_view(), name="pipeline_status_dashboard"),
]
