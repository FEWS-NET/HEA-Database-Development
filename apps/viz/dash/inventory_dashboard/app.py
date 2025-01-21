import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
from dash import dash_table, dcc, html
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash

from .functions import clean_livelihood_data, clean_wealth_group_data

# Unique countries and livelihood zones for dropdowns
unique_countries = sorted(clean_livelihood_data["country_code"].dropna().unique())
unique_zones = sorted(clean_livelihood_data["livelihood_zone_baseline_label"].dropna().unique())

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
                            placeholder=f"Select Country(s) (e.g., {unique_countries[0]})",
                            multi=True,
                        ),
                    ],
                    style={"flex": "1", "marginRight": "10px"},
                ),
                html.Div(
                    [
                        dcc.Dropdown(
                            id="livelihood-zone-dropdown",
                            options=[{"label": zone, "value": zone} for zone in unique_zones],
                            placeholder=f"Select Livelihood Zone(s) (e.g., {unique_zones[0]})",
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
                        {"name": "Total Strategy Type Count", "id": "Strategy Type Count"},
                        {"name": "Summary Wealth Characteristics", "id": "Summary Data"},
                        {"name": "Community Wealth Characteristics", "id": "Community Data"},
                    ],
                    style_table={"overflowX": "auto"},
                    style_cell={
                        "textAlign": "left",
                        "fontSize": "15px",  # Increase font size
                        "padding": "10px",  # Add padding
                    },
                    style_header={
                        "fontSize": "18px",  # Increase font size for header
                        "fontWeight": "bold",  # Make header bold
                        "textAlign": "center",
                    },
                    page_size=10,
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

    # Group and aggregate Strategy Type Count
    livelihood_grouped = (
        filtered_livelihood.groupby(["livelihood_zone_baseline_label", "strategy_type_label"])
        .size()
        .reset_index(name="Strategy Type Count")
    )
    livelihood_summary = (
        livelihood_grouped.groupby("livelihood_zone_baseline_label")["Strategy Type Count"].sum().reset_index()
    )

    # Group and pivot Wealth Characteristics Count
    wealth_grouped = (
        filtered_wealth.groupby(["livelihood_zone_baseline_label", "Record Type"])
        .size()
        .reset_index(name="Wealth Characteristics Count")
    )
    wealth_grouped_pivot = wealth_grouped.pivot_table(
        index="livelihood_zone_baseline_label",
        columns="Record Type",
        values="Wealth Characteristics Count",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    # Merge livelihood and wealth data
    merged_data = pd.merge(livelihood_summary, wealth_grouped_pivot, on="livelihood_zone_baseline_label", how="left")

    # Create charts
    wealth_fig = px.bar(
        wealth_grouped,
        x="livelihood_zone_baseline_label",
        y="Wealth Characteristics Count",
        color="Record Type",
        barmode="stack",
        title="Wealth Characteristics by Type",
        labels={
            "livelihood_zone_baseline_label": "Livelihood Zone",
        },
    )

    livelihood_fig = px.bar(
        livelihood_grouped,
        x="strategy_type_label",
        y="Strategy Type Count",
        color="livelihood_zone_baseline_label",
        barmode="stack",
        title="Strategy Types by Baseline",
        labels={
            "strategy_type_label": "Strategy Type",
            "livelihood_zone_baseline_label": "Baseline Zone",
        },
    )

    wealth_monthly_fig = px.bar(
        filtered_wealth.groupby(["created_month", "Record Type"])
        .size()
        .reset_index(name="Wealth Characteristics Count"),
        x="created_month",
        y="Wealth Characteristics Count",
        color="Record Type",
        barmode="stack",
        title="Wealth Characteristics by Month",
        labels={
            "created_month": "Month",
        },
    )

    return zone_options, wealth_fig, livelihood_fig, wealth_monthly_fig, merged_data.to_dict("records")


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
