import plotly.express as px
from dash import dash_table, dcc, html
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash

from .functions import fetch_data, prepare_livelihood_data, prepare_wealth_group_data

# API Endpoints
LIVELIHOOD_STRATEGY_URL = "https://headev.fews.net/api/livelihoodstrategy/"
WEALTH_GROUP_URL = "https://headev.fews.net/api/wealthgroupcharacteristicvalue/"

# Fetch and prepare data
livelihood_data = fetch_data(LIVELIHOOD_STRATEGY_URL)
wealth_group_data = fetch_data(WEALTH_GROUP_URL)

livelihood_data = prepare_livelihood_data(livelihood_data)
wealth_group_data = prepare_wealth_group_data(wealth_group_data)

# Unique countries and livelihood zones for dropdowns
unique_countries = sorted(livelihood_data["country_code"].unique())
unique_zones = sorted(livelihood_data["livelihood_zone"].unique())

# Dash app
app = DjangoDash("Inventory_dashboard")
app.title = "HEA Dashboard"

# Layout
app.layout = html.Div(
    [
        html.H1("HEA Data Inventory Dashboard", style={"textAlign": "center"}),
        dcc.Dropdown(
            id="country-dropdown",
            options=[{"label": country, "value": country} for country in unique_countries],
            placeholder="Select Country",
            multi=False,
        ),
        dcc.Dropdown(
            id="livelihood-zone-dropdown",
            options=[{"label": zone, "value": zone} for zone in unique_zones],
            placeholder="Select Livelihood Zone(s)",
            multi=True,
        ),
        html.Div(
            [
                html.Div(dcc.Graph(id="wealth-chart"), style={"width": "48%", "display": "inline-block"}),
                html.Div(dcc.Graph(id="livelihood-chart"), style={"width": "48%", "display": "inline-block"}),
            ]
        ),
        html.Div(
            [
                html.H3("Data Table", style={"textAlign": "center"}),
                dash_table.DataTable(
                    id="data-table",
                    columns=[
                        {"name": "Livelihood Zone", "id": "livelihood_zone"},
                        {"name": "Strategy Type Count", "id": "Count"},
                        {"name": "Wealth Characteristics Count", "id": "Wealth Characteristics Count"},
                    ],
                    style_table={"overflowX": "auto"},
                    style_cell={"textAlign": "left"},
                    page_size=10,
                ),
            ]
        ),
    ]
)


# Callbacks
@app.callback(
    [
        Output("livelihood-zone-dropdown", "options"),
        Output("wealth-chart", "figure"),
        Output("livelihood-chart", "figure"),
        Output("data-table", "data"),
    ],
    [Input("country-dropdown", "value"), Input("livelihood-zone-dropdown", "value")],
)
def update_charts(selected_country, selected_zones):
    # Filter data based on selected country
    if selected_country:
        filtered_livelihood = livelihood_data[livelihood_data["country_code"] == selected_country]
        filtered_wealth = wealth_group_data[wealth_group_data["country_code"] == selected_country]
        filtered_zones = sorted(filtered_livelihood["livelihood_zone"].unique())
    else:
        filtered_livelihood = livelihood_data
        filtered_wealth = wealth_group_data
        filtered_zones = unique_zones

    # Update options for livelihood zone dropdown
    zone_options = [{"label": zone, "value": zone} for zone in filtered_zones]

    # Filter data based on selected livelihood zones
    if selected_zones:
        filtered_livelihood = filtered_livelihood[filtered_livelihood["livelihood_zone"].isin(selected_zones)]
        filtered_wealth = filtered_wealth[filtered_wealth["livelihood_zone"].isin(selected_zones)]

    # Group data for charts
    livelihood_grouped = (
        filtered_livelihood.groupby(["livelihood_zone", "strategy_type_label"]).size().reset_index(name="Count")
    )
    wealth_grouped = filtered_wealth.groupby("livelihood_zone").size().reset_index(name="Wealth Characteristics Count")

    wealth_fig = px.bar(
        wealth_grouped,
        x="livelihood_zone",
        y="Wealth Characteristics Count",
        title="Wealth Characteristics per Baseline",
        labels={"livelihood_zone": "Baseline", "Wealth Characteristics Count": "Count"},
    )

    livelihood_fig = px.bar(
        livelihood_grouped,
        x="strategy_type_label",
        y="Count",
        color="livelihood_zone",
        title="Livelihood Strategies per Baseline",
        labels={"strategy_type_label": "Strategy Type", "Count": "Count", "livelihood_zone": "Baseline"},
    )

    return zone_options, wealth_fig, livelihood_fig, livelihood_grouped.to_dict("records")


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
