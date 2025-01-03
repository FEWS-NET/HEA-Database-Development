from django.urls import path

import viz.dash.inventory_dashboard.app

from .views import InventoryDashboardView

app_name = "viz"

urlpatterns = [
    path("", InventoryDashboardView.as_view(), name="inventory_dashboard"),
]
