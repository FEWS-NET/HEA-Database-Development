import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from ...dash_wrapper import SecureDjangoDash
from .functions import (
    get_bss_corrections,
    get_livelihood_activity_dataframe,
    get_livelihood_zone_baseline,
    get_wealthcharactestics,
)

app = SecureDjangoDash("bss_inventory", suppress_callback_exceptions=True)
app.title = "BSS Inventory"


app.layout = html.Div(
    [
        html.Div([html.H1("BSS Inventories", style={"textAlign": "center", "color": "#2c3e50"})]),
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Select Country:", style={"fontWeight": "bold"}),
                        dcc.Dropdown(
                            id="country-dropdown",
                            # Options will be loaded dynamically in callback
                            options=[],
                            value=None,
                            clearable=True,
                            placeholder="Select a country (or leave blank for all)",
                        ),
                    ],
                    style={"width": "30%", "display": "inline-block", "marginRight": "20px"},
                ),
                html.Div(
                    [
                        html.Label("Select Livelihood Zone(s):", style={"fontWeight": "bold"}),
                        dcc.Dropdown(id="zone-dropdown", multi=True),
                    ],
                    style={"width": "65%", "display": "inline-block"},
                ),
            ],
            style={"margin": "20px", "padding": "20px", "backgroundColor": "#f8f9fa", "borderRadius": "10px"},
        ),
        html.Div(
            [dcc.Loading(id="loading-overview", type="circle", children=html.Div(id="overview-content"))],
            style={"padding": "20px"},
        ),
        # Hidden div to trigger initial loading
        html.Div(id="initial-load-trigger", style={"display": "none"}),
    ],
    style={"fontFamily": "Arial, sans-serif"},
)


@app.callback(
    Output("country-dropdown", "options"),
    Output("country-dropdown", "value"),
    Input("initial-load-trigger", "children"),
)
def initialize_country_dropdown(_):
    """Initialize country dropdown options on first load."""
    try:
        baseline_df = get_livelihood_zone_baseline()
        countries = sorted(baseline_df["country"].unique().tolist()) if not baseline_df.empty else []
        options = [{"label": country, "value": country} for country in countries]
        default_value = countries[0] if countries else None
        return options, default_value
    except Exception as e:
        # Handle gracefully in case of connection issues
        print(f"Error loading baseline data: {e}")
        return [], None


@app.callback(Output("zone-dropdown", "options"), Output("zone-dropdown", "value"), Input("country-dropdown", "value"))
def update_livelihood_zone_dropdown(selected_country):
    """Update zone dropdown based on selected country."""
    if not selected_country:
        return [], []

    try:
        baseline_df = get_livelihood_zone_baseline()
        zones = sorted(baseline_df[baseline_df["country"] == selected_country]["zone_code"].unique())
        options = [{"label": zone, "value": zone} for zone in zones]
        return options, zones
    except Exception as e:
        print(f"Error loading zone data: {e}")
        return [], []


@app.callback(
    Output("overview-content", "children"), Input("country-dropdown", "value"), Input("zone-dropdown", "value")
)
def update_kpi_content(selected_country, selected_zone):
    """Update main content based on selected filters."""
    try:
        # Load all required data fresh each time
        baseline_df = get_livelihood_zone_baseline()
        livelihood_activity_df = get_livelihood_activity_dataframe()
        corrections_df = get_bss_corrections()
        wealthcharactestics_df = get_wealthcharactestics()

        title_segment = selected_country if selected_country else "All Countries"

        if selected_country:
            filtered_baseline_df = baseline_df[baseline_df["country"] == selected_country].copy()
            if not livelihood_activity_df.empty:
                filtered_activity_df = livelihood_activity_df[
                    livelihood_activity_df["country"] == selected_country
                ].copy()
            else:
                filtered_activity_df = pd.DataFrame()
            filtered_corrections_df = pd.DataFrame()
            if not corrections_df.empty:
                filtered_corrections_df = corrections_df[corrections_df["country"] == selected_country].copy()

            most_frequent_wc = ""
            if not wealthcharactestics_df.empty:
                filtered_wc = wealthcharactestics_df[wealthcharactestics_df["country"] == selected_country].copy()
                counts = filtered_wc["wealth_characteristic"].value_counts()
                # Drop "household size" as it is in almost all bsses
                counts = counts.drop("household size", errors="ignore")
                if not counts.empty:
                    most_frequent_wc = counts.idxmax()

        else:
            filtered_baseline_df = baseline_df.copy()
            filtered_activity_df = livelihood_activity_df.copy()
            filtered_corrections_df = corrections_df.copy()
            most_frequent_wc = ""
            if not wealthcharactestics_df.empty:
                counts = wealthcharactestics_df["wealth_characteristic"].value_counts()
                # Drop "household size" as it is in almost all bsses
                counts = counts.drop("household size", errors="ignore")
                if not counts.empty:
                    most_frequent_wc = counts.idxmax()

        if filtered_baseline_df.empty:
            return html.Div(f"No data available for {title_segment}.", style={"padding": "20px"})

        return create_kpi_layout(filtered_baseline_df, filtered_activity_df, filtered_corrections_df, most_frequent_wc)

    except Exception as e:
        print(f"Error updating content: {e}")
        return html.Div(
            "Error loading data. Please try again later.",
            style={"padding": "20px", "color": "red", "textAlign": "center"},
        )


def create_livelihood_pie_chart(df):
    if df.empty:
        return go.Figure().update_layout(title_text="No Livelihood Category Data")
    livelihood_counts = df["main_livelihood_category"].value_counts()
    color_map = {
        "Agricultural": "#096640",  # brand green
        "Agropastoral": "#0B7A4A",  # slightly brighter
        "Fishing": "#0E8E54",  # lighter green
        "Irrigation": "#12A35F",  # medium green
        "Pastoral": "#27B96B",  # fresh green
        "Peri-Urban": "#52CC85",  # soft green
        "Urban": "#7FE09F",  # lightest green
    }
    fig = px.pie(
        values=livelihood_counts.values,
        names=livelihood_counts.index,
        title="Distribution of Main Livelihood Categories",
        hole=0.4,
        color=livelihood_counts.index,
        color_discrete_map=color_map,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(legend_title_text="Category", uniformtext_minsize=12, uniformtext_mode="hide")
    return fig


def create_organization_treemap(df):
    if df.empty:
        return go.Figure().update_layout(title_text="No Source Organization Data")
    org_counts = df["source_organization"].value_counts().reset_index()
    org_counts.columns = ["source_organization", "count"]
    fig = px.treemap(
        org_counts,
        path=[px.Constant("All Organizations"), "source_organization"],
        values="count",
        title="Data Contribution by Source Organization",
        color="count",
        color_continuous_scale="Blues",
    )
    fig.update_traces(textinfo="label+value")
    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    return fig


def create_strategy_barchart(activity_df):
    """
    Creates a bar chart showing the count of livelihood activities by strategy type.
    """
    if activity_df.empty or "strategy_type" not in activity_df.columns:
        return go.Figure().update_layout(title_text="No Livelihood Strategy Data")

    strategy_counts = activity_df["strategy_type"].value_counts().reset_index()
    strategy_counts.columns = ["strategy_type", "count"]

    fig = px.bar(
        strategy_counts,
        x="strategy_type",
        y="count",
        title="Livelihood Activities by Strategy Type",
        labels={"strategy_type": "Strategy Type", "count": "Number of Activities"},
        color="strategy_type",
        text_auto=True,
    )
    fig.update_layout(xaxis_title=None, yaxis_title="Number of Activities", showlegend=False)
    fig.update_traces(textposition="outside")
    return fig


def get_livelihood_activity_kpis(activity_df):
    if activity_df.empty:
        return 0, 0
    counts = activity_df["data_level"].value_counts().to_dict()
    return counts.get("community", 0), counts.get("baseline", 0)


def create_strategy_sunburst_chart(activity_df):
    """
    Creates a sunburst chart for livelihood strategy types.
    """
    if activity_df.empty or "strategy_type" not in activity_df.columns:
        return go.Figure().update_layout(title_text="No Livelihood Activity Data Available")

    strategy_counts = activity_df.groupby(["data_level", "strategy_type"]).size().reset_index(name="count")
    fig = px.sunburst(
        strategy_counts,
        path=["data_level", "strategy_type"],
        values="count",
        title="Livelihood Activities by Strategy Type",
        color="data_level",
        color_discrete_map={"community": "#2980b9", "baseline": "#8e44ad", "(?)": "#7f8c8d"},
    )
    fig.update_traces(textinfo="label+percent parent", insidetextorientation="radial")
    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    return fig


def create_kpi_layout(filtered_baseline_df, filtered_activity_df, filtered_corrections_df, most_frequent_wc):
    """
    All KPI cards and charts into a single layout component.
    """

    total_bsses = len(filtered_baseline_df)
    community_count, baseline_count = get_livelihood_activity_kpis(filtered_activity_df)
    total_corrections = len(filtered_corrections_df)
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [html.H3(f"{total_bsses}", style={"color": "#2ECC71"}), html.P("Total BSSes loaded")],
                        className="summary-card",
                    ),
                    html.Div(
                        [
                            html.H3("Livelihood Activity Data", style={"color": "#3498db"}),
                            html.Div(
                                [
                                    html.Div([html.H4(community_count), html.P("Community")], className="sub-kpi"),
                                    html.Div([html.H4(baseline_count), html.P("Baseline")], className="sub-kpi"),
                                ],
                                style={"display": "flex", "justifyContent": "space-around", "marginTop": "10px"},
                            ),
                        ],
                        className="summary-card",
                    ),
                    html.Div(
                        [html.H3(f"{total_corrections}", style={"color": "#9b59b6"}), html.P("Corrections")],
                        className="summary-card",
                    ),
                    html.Div(
                        [
                            html.H3("Most Frequent Wealth Characterstics", style={"color": "#f39c12"}),
                            html.P(f"{most_frequent_wc}"),
                        ],
                        className="summary-card",
                    ),
                ],
                className="kpi-card-container",
            ),
            html.Div(
                [
                    html.Div(
                        [dcc.Graph(figure=create_livelihood_pie_chart(filtered_baseline_df))],
                        style={"width": "49%", "display": "inline-block", "verticalAlign": "top"},
                    ),
                    html.Div(
                        [dcc.Graph(figure=create_organization_treemap(filtered_baseline_df))],
                        style={"width": "49%", "display": "inline-block", "verticalAlign": "top"},
                    ),
                ],
                style={"marginTop": "30px"},
            ),
            html.Div(
                [
                    html.Div(
                        [dcc.Graph(figure=create_strategy_sunburst_chart(filtered_activity_df))],
                    ),
                    html.Div(
                        [dcc.Graph(figure=create_strategy_barchart(filtered_activity_df))],
                    ),
                ],
                style={"marginTop": "30px"},
            ),
        ]
    )
