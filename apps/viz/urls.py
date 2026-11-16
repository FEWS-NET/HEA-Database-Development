"""
URL routes for visualizations of the HEA data and pipelines.
"""

from django.urls import path

from .views import (
    PipelineStatusIndexView,
    PipelineStatusPartitionView,
    PipelineStatusView,
)

app_name = "viz"

urlpatterns = [
    path("pipeline-status/", PipelineStatusIndexView.as_view(), name="pipeline_status_index"),
    path("pipeline-status/<str:pipeline>/", PipelineStatusView.as_view(), name="pipeline_status"),
    path(
        "pipeline-status/<str:pipeline>/<path:partition_key>/",
        PipelineStatusPartitionView.as_view(),
        name="pipeline_status_partition",
    ),
]
