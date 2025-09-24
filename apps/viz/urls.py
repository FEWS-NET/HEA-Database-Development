from django.urls import path

from viz.dash.inventory_dashboard import app as inventory  # NOQA: F401
from viz.dash.pipeline_status_dashboard import app as pipeline_status  # NOQA: F401
from viz.views import (
    InventoryDashboardView,
    PipelineStatusDashboardView,
)

app_name = "viz"


urlpatterns = [
    path("inventory-dashboard/", InventoryDashboardView.as_view(), name="inventory_dashboard"),
    path("pipeline-status-dashboard/", PipelineStatusDashboardView.as_view(), name="pipeline_status_dashboard"),
]
