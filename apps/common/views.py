import os

import fsspec
from dagster import AssetKey, DagsterEventType, DagsterInstance, EventRecordsFilter
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import Http404, HttpResponseRedirect
from django.views import View
from revproxy.views import ProxyView

EXPLORER_CLOUDFRONT_URL = settings.EXPLORER_CLOUDFRONT_URL


class DagsterProxyView(LoginRequiredMixin, PermissionRequiredMixin, ProxyView):
    login_url = "/admin/login/"
    # ignore type warning because parent class uses a property for "upstream"
    upstream = f"{os.environ.get('DAGSTER_WEBSERVER_URL')}/{os.environ.get('DAGSTER_WEBSERVER_PREFIX')}/"  # type: ignore
    permission_required = "common.access_dagster_ui"
    raise_exception = False


class AssetDownloadView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """
    A view that generates the s3 url for direct download of materialized assets
    """

    permission_required = "common.access_dagster_ui"
    login_url = "/admin/login/"
    raise_exception = False

    def get(self, request, asset_name, partition_name=None):
        try:
            with DagsterInstance.get() as instance:
                filter_kwargs = {
                    "event_type": DagsterEventType.ASSET_MATERIALIZATION,
                    "asset_key": AssetKey([asset_name]),
                }
                if partition_name:
                    filter_kwargs["asset_partitions"] = [partition_name]

                records = list(instance.get_event_records(EventRecordsFilter(**filter_kwargs), limit=1))
                if not records:
                    raise Http404(f"No materialization found for asset '{asset_name}'")

                metadata = records[0].asset_materialization.metadata or {}
                asset_uri = metadata.get("path")
                if not asset_uri:
                    raise Http404(f"Asset '{asset_name}' does not contain a 'path' in metadata")

                # Generate signed URL for S3
                protocol, path = asset_uri.value.split("://", 1)
                fs = fsspec.filesystem(protocol)

                if not hasattr(fs, "sign"):
                    raise NotImplementedError(f"Filesystem '{protocol}' does not support pre-signed URLs")

                signed_url = fs.sign(path)
                return HttpResponseRedirect(signed_url)

        except Exception as e:
            raise Http404(f"Failed to locate or sign asset '{asset_name}': {str(e)}")


class BaselineExplorerProxyView(ProxyView):
    """
    A revproxy view to serve the data explorer assets via a cloudfront distribution.
    """

    upstream = EXPLORER_CLOUDFRONT_URL  # type: ignore
