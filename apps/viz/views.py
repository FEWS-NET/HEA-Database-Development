"""
Views for visualizing the status and quality of the HEA data and pipelines.
"""

import datetime
import json
import logging
from typing import TYPE_CHECKING
from urllib.parse import quote

import graphviz
import pandas as pd
import plotly.graph_objects as go
from dagster import DagsterInstance
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.cache import cache
from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView
from plotly.utils import PlotlyJSONEncoder

if TYPE_CHECKING:
    from pipelines.status import MonitoredPipeline

logger = logging.getLogger(__name__)


def get_monitored_pipelines() -> list["MonitoredPipeline"]:
    """
    Return the monitored pipelines from the Dagster definitions.

    The pipelines module is imported here rather than at module level, because loading the Dagster definitions is
    slow and is only required by the pipeline status views.
    """
    from pipelines import defs
    from pipelines.status import get_monitored_pipelines as get_pipelines

    return get_pipelines(defs.resolve_asset_graph())


def get_monitored_pipeline(slug: str) -> "MonitoredPipeline":
    """
    Return the monitored pipeline identified by `slug`, or raise Http404 if there isn't one.
    """
    for pipeline in get_monitored_pipelines():
        if pipeline.slug == slug:
            return pipeline
    raise Http404(f"Pipeline '{slug}' is not monitored")


def get_pipeline_status(pipeline: "MonitoredPipeline", cache_seconds: int = 60) -> dict:
    """
    Return the status of every asset in the pipeline for every partition, cached for `cache_seconds`.
    """
    from pipelines.status import (
        get_asset_status_dataframe,
        get_partition_summary_dataframe,
    )

    def load() -> dict:
        """
        Fetch the status of the pipeline from the Dagster instance.
        """
        with DagsterInstance.get() as instance:
            status_df = get_asset_status_dataframe(instance, pipeline)
        return {
            "status_df": status_df,
            "summary_df": get_partition_summary_dataframe(status_df, pipeline),
            "updated": datetime.datetime.now(datetime.timezone.utc),
        }

    return cache.get_or_set(f"pipeline_status:{pipeline.slug}", load, cache_seconds)


def get_status_heatmap_figure(status_df: pd.DataFrame, asset_keys: list[str], partition_keys: list[str]) -> dict:
    """
    Return the JSON data for a Plotly heatmap of asset status, with a row for each partition and a column for each asset.
    """
    from pipelines.status import STATUS_COLORS, AssetStatus

    statuses = list(AssetStatus)
    status_codes = {status: code for code, status in enumerate(statuses)}
    # Stepped colorscale so that each integer status code gets a single, discrete color
    colorscale = []
    for code, status in enumerate(statuses):
        colorscale.append([code / len(statuses), STATUS_COLORS[status]])
        colorscale.append([(code + 1) / len(statuses), STATUS_COLORS[status]])

    pivot_df = status_df.pivot(index="partition_key", columns="asset_key", values="status").reindex(
        index=partition_keys, columns=asset_keys
    )
    figure = go.Figure(
        go.Heatmap(
            z=pivot_df.map(status_codes.get).values,
            x=asset_keys,
            y=partition_keys,
            customdata=pivot_df.map(str).values,
            colorscale=colorscale,
            zmin=-0.5,
            zmax=len(statuses) - 0.5,
            showscale=False,
            xgap=1,
            ygap=1,
            hovertemplate="<b>%{y}</b><br>%{x}: %{customdata}<extra></extra>",
        )
    )
    figure.update_layout(
        height=160 + 22 * len(partition_keys),
        margin={"l": 10, "r": 10, "t": 150, "b": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"side": "top", "tickangle": -45, "fixedrange": True},
        yaxis={
            "autorange": "reversed",
            "automargin": True,
            "fixedrange": True,
            "tickmode": "array",
            "tickvals": partition_keys,
        },
    )
    return json.loads(json.dumps(figure.to_plotly_json(), cls=PlotlyJSONEncoder))


def get_asset_graph_svg(
    partition_key: str, statuses: dict[str, str], dependencies: dict[str, list[str]], root_failures: list[str]
) -> str | None:
    """
    Return an SVG diagram of the assets in the pipeline for a partition, colored by status.

    Root failures are drawn with a heavy border, and each asset links to its partition in the Dagster UI.
    Returns None if the Graphviz `dot` executable is not installed.
    """
    from pipelines.status import (
        STATUS_COLORS,
        AssetStatus,
        get_dagster_asset_partition_url,
    )

    dot = graphviz.Digraph(
        graph_attr={"rankdir": "LR", "bgcolor": "transparent"},
        node_attr={"shape": "box", "style": "rounded,filled", "fontname": "sans-serif", "fontsize": "10"},
    )
    for asset_key, status in statuses.items():
        dot.node(
            asset_key,
            asset_key,
            fillcolor=STATUS_COLORS[status],
            fontcolor="white" if status in (AssetStatus.FAILED, AssetStatus.IN_PROGRESS) else "black",
            penwidth="3" if asset_key in root_failures else "1",
            URL=get_dagster_asset_partition_url(asset_key, partition_key),
            target="_top",
            tooltip=f"{asset_key}: {status}",
        )
    for asset_key, parents in dependencies.items():
        for parent in parents:
            dot.edge(parent, asset_key)
    try:
        svg = dot.pipe(format="svg", encoding="utf-8")
    except graphviz.ExecutableNotFound:
        logger.warning("Graphviz dot executable not found, so the pipeline asset graph cannot be drawn")
        return None
    # Strip the XML declaration and doctype so that the SVG can be embedded in the page
    return svg[svg.index("<svg") :]


class PipelineStatusMixin(LoginRequiredMixin, PermissionRequiredMixin):
    """
    Restrict the pipeline status views to users with access to the Dagster UI.
    """

    permission_required = "common.access_dagster_ui"
    login_url = "/admin/login/"
    raise_exception = False


class PipelineStatusIndexView(PipelineStatusMixin, TemplateView):
    """
    List the monitored pipelines, with the number of partitions in each status.
    """

    template_name = "viz/pipeline_status_index.html"

    def get_context_data(self, **kwargs) -> dict:
        """
        Summarize the status of each monitored pipeline.
        """
        from pipelines.status import PartitionStatus

        context = super().get_context_data(**kwargs)
        pipelines = []
        for pipeline in get_monitored_pipelines():
            summary_df = get_pipeline_status(pipeline)["summary_df"]
            pipelines.append(
                {
                    "label": pipeline.label,
                    "terminal_asset": pipeline.terminal_asset,
                    "asset_count": len(pipeline.asset_keys),
                    "partition_count": len(summary_df),
                    "status_counts": [(summary_df["status"] == status).sum() for status in PartitionStatus],
                    "url": reverse("viz:pipeline_status", args=[pipeline.slug]),
                }
            )
        context.update(
            {
                "title": "Pipeline Status",
                "partition_statuses": [str(status) for status in PartitionStatus],
                "pipelines": pipelines,
            }
        )
        return context


class PipelineStatusView(PipelineStatusMixin, TemplateView):
    """
    Show the status of a pipeline for every partition, highlighting where each failing partition failed.
    """

    template_name = "viz/pipeline_status.html"

    def get_context_data(self, **kwargs) -> dict:
        """
        Filter the cached pipeline status by group and status and build the heatmap.
        """
        from pipelines.status import (
            STATUS_COLORS,
            PartitionStatus,
            get_dagster_asset_partition_url,
        )

        context = super().get_context_data(**kwargs)
        pipeline = get_monitored_pipeline(kwargs["pipeline"])
        pipeline_status = get_pipeline_status(pipeline)
        summary_df = pipeline_status["summary_df"]

        group = self.request.GET.get("group", "")
        partition_status = self.request.GET.get("status", "")
        filtered_df = summary_df
        if group:
            filtered_df = filtered_df[filtered_df["group"] == group]
        if partition_status:
            filtered_df = filtered_df[filtered_df["status"] == partition_status]

        partition_url = reverse("viz:pipeline_status_partition", args=[pipeline.slug, "PARTITION_KEY"])
        failures = [
            {
                "partition_key": row.partition_key,
                "url": partition_url.replace("PARTITION_KEY", quote(row.partition_key)),
                "root_failures": [
                    {"asset_key": asset_key, "url": get_dagster_asset_partition_url(asset_key, row.partition_key)}
                    for asset_key in row.root_failures
                ],
            }
            for row in filtered_df[filtered_df["status"] == PartitionStatus.FAILED].itertuples()
        ]

        context.update(
            {
                "title": pipeline.label,
                "pipeline": pipeline,
                "updated": pipeline_status["updated"],
                "groups": sorted(group for group in summary_df["group"].unique() if group),
                "partition_statuses": [str(status) for status in PartitionStatus],
                "selected_group": group,
                "selected_status": partition_status,
                "status_counts": [
                    {"status": str(status), "count": (filtered_df["status"] == status).sum()}
                    for status in PartitionStatus
                ],
                "partition_count": len(filtered_df),
                "failures": failures,
                "legend": [{"status": str(status), "color": color} for status, color in STATUS_COLORS.items()],
                "partition_url": partition_url,
                "heatmap": (
                    get_status_heatmap_figure(
                        pipeline_status["status_df"],
                        list(pipeline.dependencies),
                        filtered_df["partition_key"].tolist(),
                    )
                    if not filtered_df.empty
                    else None
                ),
            }
        )
        return context


class PipelineStatusPartitionView(PipelineStatusMixin, TemplateView):
    """
    Show the status of each asset in a pipeline for a single partition, as a graph and a table.
    """

    template_name = "viz/pipeline_status_partition.html"

    def get_context_data(self, **kwargs) -> dict:
        """
        Fetch the current status and latest runs for each asset in the pipeline for the requested partition.
        """
        from pipelines.status import (
            get_asset_partition_details,
            get_asset_status_dataframe,
            get_dagster_asset_partition_url,
            get_dagster_run_url,
            get_partition_status,
            get_root_failures,
        )

        context = super().get_context_data(**kwargs)
        pipeline = get_monitored_pipeline(kwargs["pipeline"])
        partition_key = kwargs["partition_key"]
        with DagsterInstance.get() as instance:
            if partition_key not in pipeline.get_partition_keys(instance):
                raise Http404(f"Partition '{partition_key}' does not exist")
            status_df = get_asset_status_dataframe(instance, pipeline, partition_keys=[partition_key])
            details = get_asset_partition_details(instance, pipeline, partition_key)

        statuses = dict(zip(status_df["asset_key"], status_df["status"]))
        root_failures = get_root_failures(statuses, pipeline.dependencies)
        assets = []
        for asset_key, status in statuses.items():
            asset_details = details[asset_key]
            assets.append(
                {
                    "asset_key": asset_key,
                    "status": str(status),
                    "is_root_failure": asset_key in root_failures,
                    "url": get_dagster_asset_partition_url(asset_key, partition_key),
                    "last_materialized": asset_details["last_materialized"],
                    "last_materialized_run_url": (
                        get_dagster_run_url(asset_details["last_materialized_run_id"])
                        if asset_details["last_materialized_run_id"]
                        else None
                    ),
                    "latest_run_url": (
                        get_dagster_run_url(asset_details["latest_run_id"]) if asset_details["latest_run_id"] else None
                    ),
                }
            )

        context.update(
            {
                "title": partition_key,
                "pipeline": pipeline,
                "partition_key": partition_key,
                "partition_status": str(get_partition_status(statuses, pipeline.terminal_asset)),
                "root_failures": root_failures,
                "assets": assets,
                "graph_svg": get_asset_graph_svg(partition_key, statuses, pipeline.dependencies, root_failures),
            }
        )
        return context
