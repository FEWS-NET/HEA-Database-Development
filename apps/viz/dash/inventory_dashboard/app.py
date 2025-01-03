import logging

import dash_bootstrap_components as dbc
import plotly.express as px
from dash import dash_table, dcc, html
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash

from .functions import clean_livelihood_data, clean_wealth_group_data

# Unique countries and livelihood zones for dropdowns
unique_countries = sorted(clean_livelihood_data["country_code"].dropna().unique())
unique_zones = sorted(clean_livelihood_data["livelihood_zone_baseline_label"].dropna().unique())

logger = logging.getLogger(__name__)

# Dash app
app = DjangoDash("Inventory_dashboard", suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "HEA Dashboard"

# Layout
app.layout = html.Div(
    [
        html.H1("HEA Data Inventory Dashboard", style={"textAlign": "center"}),
        html.Div(
            [
                html.Div(
                    [
                        dcc.Dropdown(
                            id="country-dropdown",
                            options=[{"label": country, "value": country} for country in unique_countries],
                            placeholder="Select Country(s)",
                            multi=True,
                        ),
                    ],
                    style={"flex": "1", "marginRight": "10px"},  # Set flex and spacing
                ),
                html.Div(
                    [
                        dcc.Dropdown(
                            id="livelihood-zone-dropdown",
                            options=[{"label": zone, "value": zone} for zone in unique_zones],
                            placeholder="Select Livelihood Zone(s)",
                            multi=True,
                        ),
                    ],
                    style={"flex": "1"},
                ),
            ],
            style={
                "display": "flex",
                "width": "100%",
                "justifyContent": "space-between",
                "marginBottom": "20px",
            },
        ),
        html.Div(
            [
                html.Div(
                    dcc.Graph(id="wealth-chart"),
                    style={"width": "30%", "display": "inline-block"},
                ),
                html.Div(
                    dcc.Graph(id="livelihood-chart"),
                    style={"width": "30%", "display": "inline-block"},
                ),
                html.Div(
                    dcc.Graph(id="wealth-monthly-chart"),
                    style={"width": "30%", "display": "inline-block"},
                ),
            ],
        ),
        html.Div(
            [
                html.H3("Data Table", style={"textAlign": "center"}),
                dash_table.DataTable(
                    id="data-table",
                    columns=[
                        {"name": "Livelihood Zone", "id": "livelihood_zone_baseline_label"},
                        {"name": "Strategy Type Count", "id": "Count"},
                        {"name": "Wealth Characteristics Count", "id": "Wealth Characteristics Count"},
                    ],
                    style_table={"overflowX": "auto"},
                    style_cell={"textAlign": "left"},
                    page_size=12,
                ),
            ],
            className="inventory-filter inventory-filter-last",
        ),
    ],
    className="div-wrapper control-panel-wrapper",
)


# Callbacks
@app.callback(
    [
        Output("livelihood-zone-dropdown", "options"),
        Output("wealth-chart", "figure"),
        Output("livelihood-chart", "figure"),
        Output("wealth-monthly-chart", "figure"),
        Output("data-table", "data"),
    ],
    [Input("country-dropdown", "value"), Input("livelihood-zone-dropdown", "value")],
)
def update_charts(selected_countries, selected_zones):
    # Handle multi-country selection
    if selected_countries:
        filtered_livelihood = clean_livelihood_data[clean_livelihood_data["country_code"].isin(selected_countries)]
        filtered_wealth = clean_wealth_group_data[clean_wealth_group_data["country_code"].isin(selected_countries)]
        filtered_zones = sorted(filtered_livelihood["livelihood_zone_baseline_label"].unique())
    else:
        filtered_livelihood = clean_livelihood_data
        filtered_wealth = clean_wealth_group_data
        filtered_zones = unique_zones

    # Update options for livelihood zone dropdown
    zone_options = [{"label": zone, "value": zone} for zone in filtered_zones]

    # Filter data based on selected livelihood zones
    if selected_zones:
        filtered_livelihood = filtered_livelihood[
            filtered_livelihood["livelihood_zone_baseline_label"].isin(selected_zones)
        ]
        filtered_wealth = filtered_wealth[filtered_wealth["livelihood_zone_baseline_label"].isin(selected_zones)]

    # Group data for charts
    livelihood_grouped = (
        filtered_livelihood.groupby(["livelihood_zone_baseline_label", "strategy_type_label"])
        .size()
        .reset_index(name="Count")
    )
    wealth_grouped = (
        filtered_wealth.groupby("livelihood_zone_baseline_label")
        .size()
        .reset_index(name="Wealth Characteristics Count")
    )
    wealth_monthly_grouped = (
        filtered_wealth.groupby(["created_month", "livelihood_zone_baseline_label"])
        .size()
        .reset_index(name="Wealth Characteristics Count")
    )

    wealth_fig = px.bar(
        wealth_grouped,
        x="livelihood_zone_baseline_label",
        y="Wealth Characteristics Count",
        title="Wealth Characteristics per Baseline",
        labels={
            "livelihood_zone_baseline_label": "Baseline",
            "Wealth Characteristics Count": "No. of Wealth Characteristics",
        },
    )

    livelihood_fig = px.bar(
        livelihood_grouped,
        x="strategy_type_label",
        y="Count",
        color="livelihood_zone_baseline_label",
        title="Livelihood Strategies per Baseline",
        labels={
            "strategy_type_label": "Strategy Type",
            "Count": "No. of Livelihood Strategies",
            "livelihood_zone_baseline_label": "Baseline",
        },
    )

    # Stacked/multiple column chart for wealth characteristics by month
    wealth_monthly_fig = px.bar(
        wealth_monthly_grouped,
        x="created_month",
        y="Wealth Characteristics Count",
        color="livelihood_zone_baseline_label",
        barmode="stack",  # Use 'group' for multiple column chart
        title="Wealth Characteristics by Month and Baseline",
        labels={
            "created_month": "Month",
            "Wealth Characteristics Count": "No. of Wealth Characteristics",
            "livelihood_zone_baseline_label": "Baseline",
        },
    )

    return zone_options, wealth_fig, livelihood_fig, wealth_monthly_fig, livelihood_grouped.to_dict("records")


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
