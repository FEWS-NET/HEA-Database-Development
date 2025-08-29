from django.urls import path

import viz.dash.inventory_dashboard.app  # noqa

from .views import InventoryDashboardView  # noqa

app_name = "viz"

urlpatterns = [
    path("", InventoryDashboardView.as_view(), name="inventory_dashboard"),
]
