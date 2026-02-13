import base64

import graphviz
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html
from pipelines import defs

from ...dash_wrapper import SecureDjangoDash
from .functions import get_partion_status_dataframe

app = SecureDjangoDash("pipeline_status_dashboard", suppress_callback_exceptions=True)
app.title = "Pipeline Run Status"


def get_pipeline_data():
    df = get_partion_status_dataframe()
    countries = sorted(df["country"].unique().tolist())
    return df, countries


# Layout with data stores and main content
app.layout = html.Div(
    [
        dcc.Store(id="pipeline-data-store"),
        dcc.Store(id="countries-store"),
        dcc.Interval(id="init-interval", interval=100, n_intervals=0, max_intervals=1),
        dcc.Loading(
            id="loading-initial",
            type="circle",
            children=[html.Div(id="initialization-status")],
        ),
        html.Div(id="main-dashboard-content", style={"display": "none"}),
    ],
    style={"fontFamily": "Arial, sans-serif"},
)


# Separate callback for initial data loading
@app.callback(
    [
        Output("pipeline-data-store", "data"),
        Output("countries-store", "data"),
        Output("initialization-status", "children"),
        Output("main-dashboard-content", "style"),
    ],
    [Input("init-interval", "n_intervals")],
    prevent_initial_call=False,
)
def load_initial_data(n_intervals):
    # Load data only once when dashboard initializes
    if n_intervals == 0:
        return {}, [], html.Div("Initializing..."), {"display": "none"}

    try:
        df, countries = get_pipeline_data()

        df_dict = df.to_dict("records")

        return df_dict, countries, [], {"display": "block"}

    except Exception as e:
        error_msg = html.Div(
            [
                html.H4("Error Loading Dashboard", style={"color": "red", "textAlign": "center"}),
                html.P(f"Failed to load pipeline data: {str(e)}", style={"textAlign": "center", "color": "red"}),
            ]
        )
        return {}, [], error_msg, {"display": "none"}


# Callback to populate main dashboard layout after data is loaded
@app.callback(
    Output("main-dashboard-content", "children"), [Input("countries-store", "data")], prevent_initial_call=True
)
def create_dashboard_layout(countries):
    if not countries:
        return html.Div("No countries data available")

    return create_main_layout(countries)


def create_main_layout(countries):
    return html.Div(
        [
            # Header
            html.Div(
                [
                    html.H1(
                        "Pipeline Monitoring Dashboard",
                        style={"textAlign": "center", "color": "#2c3e50", "marginBottom": "10px"},
                    ),
                ]
            ),
            # Controls
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Select Country:", style={"fontWeight": "bold"}),
                            dcc.Dropdown(
                                id="country-dropdown",
                                options=[{"label": country, "value": country} for country in countries],
                                value=countries[0] if countries else None,
                                clearable=False,
                                style={"marginTop": "5px"},
                            ),
                        ],
                        style={"width": "30%", "display": "inline-block", "marginRight": "20px"},
                    ),
                    html.Div(
                        [
                            html.Label("Select Partition(s):", style={"fontWeight": "bold"}),
                            dcc.Dropdown(id="partition-dropdown", multi=True, style={"marginTop": "5px"}),
                        ],
                        style={"width": "65%", "display": "inline-block"},
                    ),
                ],
                style={"margin": "20px", "padding": "20px", "backgroundColor": "#ecf0f1", "borderRadius": "10px"},
            ),
            html.Div(
                [
                    dcc.Loading(id="loading-overview", type="circle", children=html.Div(id="overview-content")),
                    dcc.Loading(id="loading-matrix", type="circle", children=html.Div(id="matrix-content")),
                    dcc.Loading(id="loading-graph", type="circle", children=html.Div(id="graph-content")),
                ],
                style={"padding": "20px"},
            ),
        ]
    )


def get_df_from_store(stored_data):
    if not stored_data:
        return pd.DataFrame()
    return pd.DataFrame(stored_data)


# Updated callbacks to use stored data instead of global variables
@app.callback(
    [Output("partition-dropdown", "options"), Output("partition-dropdown", "value")],
    [Input("country-dropdown", "value"), Input("pipeline-data-store", "data")],
)
def update_partition_dropdown(selected_country, stored_data):
    if not selected_country or not stored_data:
        return [], []

    df = get_df_from_store(stored_data)
    partitions = sorted(df[df["country"] == selected_country]["partition_key"].unique())
    options = [{"label": partition, "value": partition} for partition in partitions]
    return options, partitions


@app.callback(
    Output("overview-content", "children"), [Input("country-dropdown", "value"), Input("pipeline-data-store", "data")]
)
def update_kpi_content(selected_country, stored_data):
    if not stored_data:
        return html.Div("Loading data...", style={"padding": "20px"})

    df = get_df_from_store(stored_data)
    title_segment = selected_country if selected_country else "All Countries"

    if selected_country:
        data_df = df[df["country"] == selected_country].copy()
    else:
        data_df = df.copy()

    if data_df.empty:
        return html.Div(f"No data available for {title_segment}.", style={"padding": "20px"})

    return create_kpi_layout(data_df, title_segment)


@app.callback(
    Output("matrix-content", "children"),
    [Input("country-dropdown", "value"), Input("partition-dropdown", "value"), Input("pipeline-data-store", "data")],
)
def update_heat_map_content(selected_country, selected_partitions, stored_data):
    if not stored_data:
        return html.Div("Loading data...", style={"padding": "20px"})

    if not selected_country:
        return html.Div("Please select a country to see the matrix.", style={"padding": "20px"})

    df = get_df_from_store(stored_data)
    country_df = df[df["country"] == selected_country]

    if selected_partitions:
        country_df = country_df[country_df["partition_key"].isin(selected_partitions)]

    print(country_df)
    return create_heatmap(country_df, selected_country)


@app.callback(
    Output("graph-content", "children"),
    [
        Input("country-dropdown", "value"),
        Input("partition-dropdown", "value"),
        Input("pipeline-data-store", "data"),
    ],
)
def update_graph_content(selected_country, selected_partitions, stored_data):
    if not stored_data:
        return html.Div("Loading data...", style={"padding": "20px"})

    if not selected_country or not selected_partitions:
        return html.Div("Please select a country and partition(s).", style={"padding": "20px", "textAlign": "center"})

    df = get_df_from_store(stored_data)

    if len(selected_partitions) == 1:
        country_df = df[df["country"] == selected_country]
        return create_or_update_graph_viz(country_df, selected_partitions[0])
    else:
        return html.Div(
            "Please select a single partition to view its dependency graph.",
            style={"padding": "20px", "textAlign": "center", "fontWeight": "bold", "color": "#7f8c8d"},
        )


def create_kpi_layout(country_df, title_segment):
    # Create the KPI cards
    total_statuses = len(country_df)
    materialized_count = len(country_df[country_df["status"] == "Materialized"])
    sucess_rate = (materialized_count / total_statuses * 100) if total_statuses > 0 else 0

    country_df["last_run_date"] = pd.to_datetime(country_df["last_run_date"])
    last_run = country_df["last_run_date"].max()
    freshness = last_run.strftime("%Y-%m-%d %H:%M") if pd.notna(last_run) else "N/A"

    total_runs = country_df["run_count"].sum()

    failed_partitions = country_df[country_df["status"] == "Failed"]["partition_key"].value_counts()
    most_failed_partition = failed_partitions.index[0] if not failed_partitions.empty else "None"

    return html.Div(
        [
            # KPI Summary Cards
            html.Div(
                [
                    html.Div(
                        [
                            html.H3(f"{sucess_rate:.1f}%", style={"color": "#2ECC71"}),
                            html.P("Success Rate per Country"),
                        ],
                        className="summary-card",
                    ),
                    html.Div(
                        [
                            html.H3(freshness, style={"color": "#3498db"}),
                            html.P("Latest Data  per Country"),
                        ],
                        className="summary-card",
                    ),
                    html.Div(
                        [
                            html.H3(f"{total_runs}", style={"color": "#9b59b6"}),
                            html.P("Total Runs  for Country"),
                        ],
                        className="summary-card",
                    ),
                    html.Div(
                        [
                            html.H3(most_failed_partition, style={"color": "#f39c12", "fontSize": "1.2em"}),
                            html.P("Top Failing Partition of a Country"),
                        ],
                        className="summary-card",
                    ),
                ],
                className="kpi-card-container",
            ),
        ],
        style={"padding": "20px"},
    )


def create_heatmap(country_df, country):
    # create the matrix heatmap
    fig_df = country_df.pivot(index="partition_key", columns="asset_key", values="status")
    status_map = {"Materialized": 2, "Failed": -1, "Missing": 0, None: 0}
    fig_df_numeric = fig_df.replace(status_map)
    text_labels = fig_df_numeric.replace({-1: "Failed", 0: "Missing", 2: "Materialized"})

    asset_order = []
    asset_dependencies = {
        asset.key.to_user_string(): [dep.to_user_string() for dep in asset.asset_deps.get(asset.key, [])]
        for asset in defs.assets
    }
    while asset_dependencies:
        no_deps = [key for key, deps in asset_dependencies.items() if not deps]
        if not no_deps:
            break
        asset_order.extend(sorted(no_deps))
        asset_dependencies = {
            key: [dep for dep in deps if dep not in no_deps]
            for key, deps in asset_dependencies.items()
            if key not in no_deps
        }

    available_assets = [asset for asset in asset_order if asset in fig_df.columns]
    fig_df_numeric = fig_df_numeric[available_assets]

    heatmap_fig = go.Figure(
        data=go.Heatmap(
            z=fig_df_numeric.values,
            x=fig_df_numeric.columns,
            y=fig_df_numeric.index,
            text=text_labels.values,
            texttemplate="",
            colorscale=[[0.0, "#FF6B6B"], [0.5, "#95A5A6"], [1.0, "#2ECC71"]],
            zmid=0,
            textfont={"size": 8},
            hovertemplate="<b>%{y}</b><br>Asset: %{x}<br>Status: %{text}<extra></extra>",
            showscale=True,
            colorbar=dict(title="Status", tickvals=[-1, 0, 2], ticktext=["Failed", "Missing", "Materialized"]),
            xgap=2,
            ygap=2,
        )
    )

    heatmap_fig.update_layout(
        title=f"Asset Status Matrix - {country}",
        xaxis_title="Assets (Dependency Order)",
        yaxis_title="Partitions",
        height=800,
        xaxis=dict(tickangle=45),
        yaxis=dict(autorange="reversed"),
    )

    return html.Div([dcc.Graph(figure=heatmap_fig)])


def create_or_update_graph_viz(country_df, selected_partition):
    # Dependency graph tab for a single partition
    partition_df = country_df[country_df["partition_key"] == selected_partition]

    if partition_df.empty:
        return html.Div(f"No data available for the partition: {selected_partition}")

    dot = graphviz.Digraph(comment=selected_partition, engine="dot")
    dot.attr(rankdir="LR")
    for _, row in partition_df.iterrows():
        # ... (node creation)
        asset_key = row["asset_key"]
        status = row["status"]
        if status == "Materialized":
            node_color = "#2ecc71"
        elif status == "Failed":
            node_color = "#e74c3c"
        else:
            node_color = "#bdc3c7"
        dot.node(asset_key, asset_key, color="black", style="filled", fillcolor=node_color)

    # Add edges
    for asset_def in defs.assets:
        for asset_key, asset_deps in asset_def.asset_deps.items():
            if asset_key.to_user_string() in partition_df["asset_key"].values:
                for asset_dep in asset_deps:
                    if asset_dep.to_user_string() in partition_df["asset_key"].values:
                        dot.edge(asset_dep.to_user_string(), asset_key.to_user_string())

    # Generate SVG and encode it
    svg_content = dot.pipe(format="svg", encoding="utf-8")
    svg_bytes = svg_content.encode("utf-8")
    b64_svg = base64.b64encode(svg_bytes).decode()
    svg_data_uri = f"data:image/svg+xml;base64,{b64_svg}"

    return html.Div(
        [
            html.H4(f"Displaying Dependencies for Partition: {selected_partition}", style={"textAlign": "center"}),
            html.Img(
                src=svg_data_uri,
                style={"width": "100%", "height": "auto", "border": "1px solid #ddd", "borderRadius": "5px"},
            ),
        ]
    )
