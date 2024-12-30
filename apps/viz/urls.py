
from django.urls import path

from .views import InventoryDashboardView

app_name = "viz"

urlpatterns = [
    path("", InventoryDashboardView.as_view(), name="Inventory_dashboard"),
]
