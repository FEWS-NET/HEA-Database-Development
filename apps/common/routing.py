from django.urls import re_path

from common.consumers import DagsterWebSocketProxyConsumer

websocket_urlpatterns = [
    # Route WebSocket connections for Dagster proxy
    re_path(r"^pipelines/(?P<path>.*)$", DagsterWebSocketProxyConsumer.as_asgi()),
]
