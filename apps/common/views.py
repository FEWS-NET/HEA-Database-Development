import os

from django.contrib.auth.mixins import PermissionRequiredMixin
from revproxy.views import ProxyView


class DagsterProxyView(PermissionRequiredMixin, ProxyView):
    upstream = f"{os.environ.get('DAGSTER_WEBSERVER_URL')}/{os.environ.get('DAGSTER_WEBSERVER_PREFIX')}/"
    permission_required = "common.access_dagster_ui"
    raise_exception = True
