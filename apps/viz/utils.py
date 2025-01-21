import logging
from collections import OrderedDict
from itertools import cycle
from typing import Any, List, Type

import numpy as np
from dash import dcc, html
from django import forms
from django.conf import settings
from django.forms.utils import pretty_name
from django.http import HttpRequest
from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import gettext as _
from shapely.geometry import Polygon, box
from warehouse.models import DataSeries, DataSet

from common.utils import name_from_class

logger = logging.getLogger(__name__)


help_text = dcc.Markdown(
    """
#### Interaction with graphs
* Single click on a legend item to exclude it from the graph
* Double click on a legend item to display only its trace
* Select any part of the graph to zoom it in
* Double click on the graph background to return it into the initial state
#### Save graph images
1. Select the desired ratio (once chosen, the ratio is applied to all graphs in the dashboard)
2. Click on the camera icon from the toolbar at the top right of the graph
"""
)

information_modal = html.Div(
    [
        html.Div(
            [help_text, html.Hr(), html.Button("Close", id="modal_close_button", n_clicks=0)],
            className="modal-content",
        ),
    ],
    id="dashboard_information_modal",
    className="modal",
    style={"display": "none"},
)

information_sign = html.Div(
    html.Div("\u003F", id="information_sign", className="information-icon", n_clicks=0),
    className="information-wrapper div-wrapper",
)


def change_graph_ratio(ratio, header):
    """Changes config of the graph with ratio to download the file"""
    conf = {"toImageButtonOptions": {"format": "png", "filename": header, "height": 400, "width": 800, "scale": 2}}
    if ratio == "  1x2":
        conf["toImageButtonOptions"]["height"] = 400
        conf["toImageButtonOptions"]["width"] = 800
    elif ratio == "  1x1":
        conf["toImageButtonOptions"]["height"] = 600
        conf["toImageButtonOptions"]["width"] = 600
    elif ratio == "  2x3":
        conf["toImageButtonOptions"]["height"] = 400
        conf["toImageButtonOptions"]["width"] = 600
    return conf


def get_empty_plot(text_phrase):
    """Layout for empty plotly graph"""
    return {
        "layout": {
            "paper_bgcolor": "#FFF",
            "plot_bgcolor": "#FFF",
            "xaxis": {"visible": False},
            "yaxis": {"visible": False},
            "annotations": [
                {
                    "text": str(text_phrase),
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": get_visualization_styles()["nested_parameters"]["font_title_plotly"],
                }
            ],
        }
    }


def get_visualization_styles():
    """
    Styling options for indiviudal traces or other figure elements for Plotly and Highcharts.
    Used for Plotly dashboards and standard visualizations via css and js views.
    """
    font_family = "Segoe UI, Open Sans, Arial, sans-serif"
    font_family_title = font_family
    open_sans_bold = "Open Sans Bold"
    open_sans_semibold = "Open Sans SemiBold"
    open_sans = "Open Sans Regular"

    bold = 700
    semibold_weight = 600
    normal_weight = 400
    italic = "italic"

    font_weight_title = semibold_weight
    font_size_title = 20
    font_size_title_react = 16
    font_weight_subtitle = normal_weight
    font_size_subtitle = 16
    font_size_subtitle_small = 16
    market_font_size = 9
    market_font_size_zoomed = 13

    header_padding_top = 12
    header_padding_right = 16
    header_padding_bottom = 14
    header_padding_left = 12
    header_padding_dropdown_top = 8
    header_padding_dropdown_right = 8

    title_line_height = 120
    subtitle_line_height = 120

    font_size_small = 12
    font_size_regular = 14
    font_size_large = 16
    font_size_other_titles = 16

    legend_padding = 16

    popup_line_height = 140

    usaid_black = "#212721"
    usaid_black_dark = "#090B09"
    globe_green = "#096640"
    globe_green_dark = "#074B2F"
    globe_green_light = "#0B8351"
    sky_blue = "#88BFB6"
    sky_blue_light = "#BDDBD6"
    sky_blue_lightest = "#E4F1EF"
    rust = "#A95B24"
    orange = "#E8792A"
    supporting_gray1 = "#F4F5F5"
    supporting_gray2 = "#E6E7E8"
    supporting_gray3 = "#D1D3D4"
    white = "#FFFFFF"

    data_stone_400 = "#ADADAD"
    data_stone_500 = "#808080"
    data_stone_600 = "#585858"
    data_stone_700 = "#424242"

    font_color = usaid_black
    font_color_title = usaid_black_dark
    title_react_background = supporting_gray1
    font_color_subtitle = usaid_black_dark

    water_blue = "#BCDAE9"

    # UI colors
    success_color = "#52B788"
    success_light_color = "#D8F3DC"
    info_color = "#2B6CB0"
    info_light_color = "#EBF8FF"
    warning_color = "#FDB833"
    warning_light_color = "#FFF6CC"
    error_color = "#AC1C1E"
    error_light_color = "#FEF0EF"
    background_color = "#FAFAFA"
    clickable_color = "#FAFCFC"

    fic_minimal = "#CDFACD"
    fic_stressed = "#FAE61E"
    fic_crisis = "#E67800"
    fic_emergency = "#C80000"
    fic_famine = "#640000"
    fic_minimal_faded = "#f4faf4"
    fic_stressed_faded = "#fef8b9"
    fic_crisis_faded = "#ffc180"
    fic_emergency_faded = "#ff9494"
    fic_famine_faded = "#ff5757"
    fic_cronic_minimal = "#CDFACD"
    fic_cronic_mild = "#CBC9E2"
    fic_cronic_moderate = "#9E9AC8"
    fic_cronic_severe = "#6A51A3"
    not_mapped = "#BDBDBD"
    wheat_bag_light = "#D6D9D9"
    wheat_bag_dark = "#808282"

    major_decrease = "#0C5D40"
    moderate_decrease = "#689F38"
    minor_decrease = "#AED581"
    stability = "#FFF59D"
    minor_increase = "#D6A79A"
    moderate_increase = "#B95A38"
    major_increase = "#6D4140"

    data_red_400 = "#A88A8A"
    data_red_500 = "#7A5A5A"
    data_red_600 = "#6D4140"
    data_red_700 = "#541E18"
    data_red_800 = "#451914"

    data_orange_400 = "#D6A79A"
    data_orange_500 = "#BA6B55"
    data_orange_600 = "#B95A38"
    data_orange_700 = "#AB4B1E"

    data_olive_green_400 = "#9B9D80"
    data_olive_green_500 = "#707257"
    data_olive_green_600 = "#60613A"
    data_olive_green_700 = "#484817"

    data_green_400 = "#319B86"
    data_green_500 = "#2C8C79"
    data_green_600 = "#107157"
    data_green_700 = "#0C5D40"

    data_blue_400 = "#A6BFE2"
    data_blue_500 = "#688CCA"
    data_blue_600 = "#426FBC"
    data_blue_700 = "#305088"

    data_purple_400 = "#DBBEE0"
    data_purple_500 = "#A173B3"
    data_purple_600 = "#784595"
    data_purple_700 = "#492674"

    data_steel_400 = "#98A9AE"
    data_steel_500 = "#6A8188"
    data_steel_600 = "#55747E"
    data_steel_700 = "#416371"

    data_charcoal_400 = "#7C888D"
    data_charcoal_500 = "#555E62"
    data_charcoal_700 = "#0C1D28"
    data_charcoal_600 = "#3A454C"

    base_gold_600 = "#FDB833"
    base_gold_700 = "#E39602"

    base_yellow_600 = "#FDD835"

    base_brick_200 = "#FEF0EF"
    base_brick_300 = "#F0CDCC"
    base_brick_400 = "#D58687"
    base_brick_500 = "#C15153"
    base_brick_600 = "#AC1C1E"
    base_brick_700 = "#7E201F"

    data_colors = [
        data_blue_600,
        data_green_400,
        data_charcoal_600,
        data_orange_500,
        data_red_500,
        data_steel_600,
        data_olive_green_500,
        data_purple_500,
        data_blue_700,
        data_green_600,
        data_charcoal_500,
        data_orange_600,
        data_red_600,
        data_steel_500,
        data_olive_green_600,
        data_purple_600,
    ]
    # Bars on combo charts should be gray
    combo_chart_data_colors = [data_stone_400] + data_colors

    ticklen = 10
    smaller_device_width = 1196
    # The most popular screen width is 1280, with borders and padding the actual viz container width is 1230 on the web site
    popular_device_width = 1280 - 50

    line_width1 = 1
    line_width2 = 2
    line_width4 = 4

    xdate_format_hc = "%B %Y"

    return dict(
        # General_variables
        line_width1=line_width1,
        line_width2=line_width2,
        font_family=font_family,
        font_color=font_color,
        font_size_small=font_size_small,
        font_size_regular=font_size_regular,
        font_size_large=font_size_large,
        font_size_other_titles=font_size_other_titles,
        container_radius=16,
        tooltip_radius=8,
        title_alignment="left",
        smaller_device_width=smaller_device_width,
        popular_device_width=popular_device_width,
        # Map variables
        outside_country_fill=supporting_gray2,
        country_of_focus_fill=white,
        open_sans_bold=open_sans_bold,
        water_blue=water_blue,
        # Map boundaries
        admin0_width=line_width2,
        admin0_width_zoomedout=line_width1,
        admin0_color=usaid_black,
        admin0_color_zoomedout=data_charcoal_600,
        admin1_width=line_width1,
        admin1_color=data_charcoal_600,
        admin2_width=line_width1,
        admin2_color=data_charcoal_400,
        # Roads
        road_major_width=line_width2,
        road_major_color=data_charcoal_600,
        road_minor_width=line_width1,
        road_minor_color=data_charcoal_500,
        # Map labels
        label_halo_color=white,
        label_halo_width=line_width1,
        admin0_label_size=font_size_regular,
        admin0_label_font=open_sans_bold,
        admin1_label_size=font_size_small,
        admin1_label_font=open_sans_semibold,
        admin2_label_size=font_size_small,
        admin2_label_font=open_sans_semibold,
        capital_size=font_size_regular,
        capital_font=open_sans,
        # Markets
        market_font_size=market_font_size,
        market_font_size_zoomed=market_font_size_zoomed,
        market_font=open_sans,
        market_font_color=usaid_black,
        # Titles/subtitles
        font_family_title=font_family_title,
        font_size_title=font_size_title,
        font_color_title=font_color_title,
        font_size_title_react=font_size_title_react,
        font_size_subtitle=font_size_subtitle,
        font_size_subtitle_small=font_size_subtitle_small,
        font_color_subtitle=font_color_subtitle,
        header_padding_top=header_padding_top,
        header_padding_right=header_padding_right,
        header_padding_bottom=header_padding_bottom,
        header_padding_left=header_padding_left,
        header_padding_dropdown_top=header_padding_dropdown_top,
        header_padding_dropdown_right=header_padding_dropdown_right,
        title_react_background=title_react_background,
        # Attributiom/disclaimer
        attribution_font_size=font_size_regular,
        attribution_color=usaid_black,
        disclaimer_font_size=font_size_small,
        disclaimer_color=usaid_black,
        disclaimer_font_style=italic,
        # Legend
        legend_padding=legend_padding,
        legend_font_size=font_size_regular,
        legend_title_font_size=font_size_regular,
        legend_title_case="uppercase",
        legend_subtitle_font_size=font_size_regular,
        legend_subtitle_color=data_charcoal_600,
        legend_content_color=data_charcoal_700,
        legend_instructional_text_color=info_color,
        legend_instructional_text_style=italic,
        legend_alignment_stacked="left",
        legend_border_color=data_charcoal_400,
        legend_border_width=2,
        legend_item_border_width=0.5,
        legend_item_border_color=usaid_black,
        # Colors
        usaid_black=usaid_black,
        usaid_black_dark=usaid_black_dark,
        globe_green=globe_green,
        globe_green_dark=globe_green_dark,
        globe_green_light=globe_green_light,
        sky_blue=sky_blue,
        sky_blue_light=sky_blue_light,
        sky_blue_lightest=sky_blue_lightest,
        orange=orange,
        rust=rust,
        supporting_gray1=supporting_gray1,
        supporting_gray2=supporting_gray2,
        supporting_gray3=supporting_gray3,
        success_color=success_color,
        success_light_color=success_light_color,
        info_color=info_color,
        info_light_color=info_light_color,
        warning_color=warning_color,
        warning_light_color=warning_light_color,
        error_color=error_color,
        error_light_color=error_light_color,
        background_color=background_color,
        clickable_color=clickable_color,
        data_red_400=data_red_400,
        data_red_500=data_red_500,
        data_red_600=data_red_600,
        data_red_700=data_red_700,
        data_red_800=data_red_800,
        data_orange_400=data_orange_400,
        data_orange_500=data_orange_500,
        data_orange_600=data_orange_600,
        data_orange_700=data_orange_700,
        data_olive_green_400=data_olive_green_400,
        data_olive_green_500=data_olive_green_500,
        data_olive_green_600=data_olive_green_600,
        data_olive_green_700=data_olive_green_700,
        data_green_400=data_green_400,
        data_green_500=data_green_500,
        data_green_600=data_green_600,
        data_green_700=data_green_700,
        data_blue_400=data_blue_400,
        data_blue_500=data_blue_500,
        data_blue_600=data_blue_600,
        data_blue_700=data_blue_700,
        data_purple_400=data_purple_400,
        data_purple_500=data_purple_500,
        data_purple_600=data_purple_600,
        data_purple_700=data_purple_700,
        data_steel_400=data_steel_400,
        data_steel_500=data_steel_500,
        data_steel_600=data_steel_600,
        data_steel_700=data_steel_700,
        data_charcoal_400=data_charcoal_400,
        data_charcoal_500=data_charcoal_500,
        data_charcoal_600=data_charcoal_600,
        data_charcoal_700=data_charcoal_700,
        data_stone_400=data_stone_400,
        data_stone_500=data_stone_500,
        data_stone_600=data_stone_600,
        data_stone_700=data_stone_700,
        base_brick_200=base_brick_200,
        base_brick_300=base_brick_300,
        base_brick_400=base_brick_400,
        base_brick_500=base_brick_500,
        base_brick_600=base_brick_600,
        base_brick_700=base_brick_700,
        base_yellow_600=base_yellow_600,
        base_gold_600=base_gold_600,
        base_gold_700=base_gold_700,
        colors_list=data_colors,
        combo_chart_data_colors_list=combo_chart_data_colors,
        major_decrease=major_decrease,
        moderate_decrease=moderate_decrease,
        minor_decrease=minor_decrease,
        stability=stability,
        minor_increase=minor_increase,
        moderate_increase=moderate_increase,
        major_increase=major_increase,
        # FIC colors
        fic_minimal=fic_minimal,
        fic_stressed=fic_stressed,
        fic_crisis=fic_crisis,
        fic_emergency=fic_emergency,
        fic_famine=fic_famine,
        fic_cronic_minimal=fic_cronic_minimal,
        fic_cronic_mild=fic_cronic_mild,
        fic_cronic_moderate=fic_cronic_moderate,
        fic_cronic_severe=fic_cronic_severe,
        not_mapped=not_mapped,
        fic_minimal_faded=fic_minimal_faded,
        fic_stressed_faded=fic_stressed_faded,
        fic_crisis_faded=fic_crisis_faded,
        fic_emergency_faded=fic_emergency_faded,
        fic_famine_faded=fic_famine_faded,
        wheat_bag_light=wheat_bag_light,
        wheat_bag_dark=wheat_bag_dark,
        # Links
        link_color=globe_green,
        link_hover_color=globe_green_light,
        # Chart settings
        axis_line_color=data_stone_400,
        axis_line_width=line_width1,
        left_yaxis_tick_color=data_stone_400,
        right_yaxis_tick_color=supporting_gray3,
        grid_color=supporting_gray1,
        line_width=line_width4,
        # line styles to distinguish when more than 6 traces selected
        dash_list=["solid"] * 10 + ["dash"] * 10 + ["dot"] * 10 + ["dashdot"] * 10,
        xdate_format_hc=xdate_format_hc,
        # Parameters that contain combined settings for Highcharts and Plotly figures
        # These parameters are not used in css or js views
        nested_parameters=dict(
            font_title_hc=dict(
                fontFamily=font_family_title,
                fontSize=font_size_title,
                color=font_color_title,
                fontWeight=font_weight_title,
                lineHeight="23px",
            ),
            font_subtitle_hc=dict(
                fontFamily=font_family,
                fontSize=font_size_subtitle,
                color=font_color_subtitle,
                fontWeight=font_weight_subtitle,
                lineHeight="23px",
            ),
            font_title_hc_small=dict(
                fontFamily=font_family_title,
                fontSize=font_size_title,
                color=font_color_title,
                fontWeight=font_weight_title,
            ),
            font_subtitle_hc_small=dict(
                fontFamily=font_family,
                fontSize=font_size_subtitle_small,
                color=font_color_subtitle,
                fontWeight=font_weight_subtitle,
            ),
            font_other_titles_hc=dict(
                fontFamily=font_family,
                fontSize=font_size_other_titles,
                color=usaid_black_dark,
                fontWeight=normal_weight,
            ),
            font_other_titles_bold_hc=dict(
                fontFamily=font_family,
                fontSize=font_size_other_titles,
                color=usaid_black_dark,
                fontWeight=semibold_weight,
            ),
            font_normal=dict(
                fontFamily=font_family, fontSize=font_size_regular, color=usaid_black_dark, fontWeight=normal_weight
            ),
            font_small=dict(
                fontFamily=font_family, fontSize=font_size_small, color=font_color, fontWeight=normal_weight
            ),
            font_tooltip_section=dict(
                fontFamily=font_family,
                fontSize=font_size_regular,
                color=usaid_black_dark,
                fontWeight=bold,
                lineHeight=23,
            ),
            font_tooltip_section_title=dict(
                fontFamily=font_family, fontSize=font_size_regular, color=usaid_black_dark, fontWeight=normal_weight
            ),
            font_labels_hc=dict(
                fontFamily=font_family,
                fontSize=font_size_regular,
                color=usaid_black_dark,
                fontWeight=bold,
            ),
            font_title_plotly=dict(family=font_family_title, size=font_size_title, color=font_color_title),
            font_other_titles_plotly=dict(family=font_family, size=font_size_other_titles, color=font_color),
            font_normal_plotly=dict(family=font_family, size=font_size_regular, color=font_color),
            font_ticks_plotly=dict(family=font_family, size=font_size_regular, color=font_color),
        ),
        # Parameters that only used with Plotly figures
        grid_line_width=1,
        tick_angle_vertical=-90,
        tick_angle_horizontal=0,
        ticklen=ticklen,
        # tick in format: Feb-18, should be vertical
        tickformat_month_year="%b-%y",
        # tick in format: 2019, should be horizontal
        tickformat_year="%Y",
        percentage_variables=dict(
            subtitle_line_height=subtitle_line_height,
            title_line_height=title_line_height,
            disclaimer_line_height=140,
            popup_line_height=popup_line_height,
        ),
        weight_variables=dict(
            font_weight_normal=normal_weight,
            font_weight_bold=bold,
            font_weight_semibold=semibold_weight,
            # Tooltip/popup
            tooltip_header_font_weight=bold,
            legend_subtitle_font_weight=bold,
            font_weight_subtitle=font_weight_subtitle,
            font_weight_title=font_weight_title,
        ),
    )


def get_plotly_layout():
    """
    Plotly Layout and Styling options for the chart.
    Used for Plotly dashboards and standard visualizations.
    """
    styles = get_visualization_styles()

    layout = dict(
        showlegend=True,
        font=styles["nested_parameters"]["font_normal_plotly"],
        paper_bgcolor="#FFF",
        plot_bgcolor="#FFF",
        margin=dict(r=15, t=20, b=15, l=20),
        hovermode="closest",
        hoverlabel=dict(
            align=styles["title_alignment"], font=dict(size=styles["font_size_small"], family=styles["font_family"])
        ),
        legend=dict(
            # orientation="v", # will break png_plotly charts, because there is no responsive layout
            orientation="h",
            xanchor="left",  # remove for vertical legend
            x=0,  # remove for vertical legend
            font=styles["nested_parameters"]["font_ticks_plotly"],
            bgcolor="#FFF",
            borderwidth=styles["legend_border_width"],
            bordercolor=styles["legend_border_color"],
            title=dict(font=styles["nested_parameters"]["font_other_titles_plotly"], text=_("LEGEND"), side="top"),
        ),
        title=dict(
            font=styles["nested_parameters"]["font_title_plotly"],
            xref="paper",
            x=0,
            yref="container",
            y=0.96,
            yanchor="top",
        ),
        xaxis=dict(
            zeroline=True,
            showgrid=False,
            zerolinecolor=styles["axis_line_color"],
            showline=True,
            ticks="",
            ticklen=styles["ticklen"],
            tickfont=styles["nested_parameters"]["font_ticks_plotly"],
            linewidth=styles["axis_line_width"],
            linecolor=styles["axis_line_color"],
            title=dict(font=styles["nested_parameters"]["font_other_titles_plotly"]),
        ),
        yaxis=dict(
            title=dict(font=styles["nested_parameters"]["font_other_titles_plotly"]),
            autorange=True,
            tickmode="auto",
            ticks="outside",
            ticklen=styles["ticklen"],
            tickwidth=styles["axis_line_width"],
            tickcolor=styles["left_yaxis_tick_color"],
            tickfont=styles["nested_parameters"]["font_ticks_plotly"],
            showgrid=True,
            gridcolor=styles["grid_color"],
            gridwidth=styles["grid_line_width"],
            zeroline=False,
            zerolinecolor=styles["axis_line_color"],
            showline=True,
            linewidth=styles["axis_line_width"],
            linecolor=styles["axis_line_color"],
            showspikes=False,
            spikethickness=0.5,
            spikecolor=styles["supporting_gray2"],
            spikedash="solid",
        ),
        yaxis2=dict(
            title=dict(font=styles["nested_parameters"]["font_other_titles_plotly"]),
            showgrid=False,
            showline=False,
            zeroline=False,
            showspikes=True,
            spikethickness=0.5,
            spikecolor=styles["grid_color"],
            spikedash="solid",
            side="right",
            overlaying="y",
            ticks="",
            ticklen=styles["ticklen"],
            tickcolor=styles["right_yaxis_tick_color"],
            tickfont=styles["nested_parameters"]["font_ticks_plotly"],
            linecolor=styles["axis_line_color"],
            linewidth=styles["axis_line_width"],
        ),
    )
    return layout


# Some dashboard charts have horizontal legend so they can use a whole page width
PLOTLY_DASHBOARD_LEGEND = dict(
    orientation="h",
    font=get_visualization_styles()["nested_parameters"]["font_ticks_plotly"],
    bgcolor="#FFF",
    borderwidth=get_visualization_styles()["legend_border_width"],
    bordercolor=get_visualization_styles()["legend_border_color"],
    title=dict(text=""),
    xanchor="left",
    x=0,
)


def make_plotly_axes_labels_bold(fig, bold_title=True):
    fig.update_yaxes(tickprefix="<b>", ticksuffix="</b>")
    fig.update_xaxes(tickprefix="<b>", ticksuffix="</b>")
    if bold_title:
        if fig["layout"]["title"]["text"]:
            title_text = fig["layout"]["title"]["text"]
            fig["layout"]["title"]["text"] = "<b>" + title_text + "</b>"

    return fig


def get_root_url(request: HttpRequest) -> str:
    """
    Return the correct base url for a visualisation, so that it can use absolute URLs for JS and CSS, etc.

    This is required because the HTML is being returned to be embedded in a remote site, so relative URLs won't work.

    We allow the request to include an explicit base_url as a query parameter, and fall back to the URI used to
    request the visualization.
    """
    parameter_url = request.GET.get("base_url", None)
    if parameter_url:
        # Use a base_url specified as a query param
        return parameter_url

    # No query param, so use the request uri instead.
    full_url = request.build_absolute_uri()
    relative_url = request.get_full_path()
    return full_url.replace(relative_url, "")


def absolute_static(path, base_url=None):
    """
    Return an absolute URL for a static file, suitable for returning to an external client
    """
    url = static(path) if path else settings.STATIC_URL
    if not url.startswith("http"):
        # Static Host isn't set, and Django is serving static files, so include the base url.
        url = (base_url or settings.DATA_EXPLORER_API_URL_ROOT.rstrip("/")) + url
    return url


COLORS_CYCLE = cycle(get_visualization_styles()["colors_list"])
FEWSNET_GROUP_COLORS = OrderedDict(
    [
        ("FEWS NET Presence", next(COLORS_CYCLE)),
        ("Remote Monitoring", next(COLORS_CYCLE)),
        ("Other Destination Countries", next(COLORS_CYCLE)),
    ]
)

COMTRADE_PRODUCT_GROUPS = {
    "P3415": "Amine-function compounds",
    "P3461": "Nitrogenous fertilizers",
    "P3462": "Phosphatic fertilizers",
    "P3463": "Potassic fertilizers",
    "P3464": "Mineral & chemical fertilizers",
    "P21533": "Crude Sunflower-seed oil",
    "P21543": "Ref. Sunflower-seed oil",
    "R01152": "Barley Grain",
    "R01122AA": "Maize (Corn)",
    "R01112": "Wheat Grain",
    "R01111AA": "Wheat planting seed",
    "R01445AA": "Sunflower Seed",
}


def join_iterables(iterable):
    """
    Join iterables into string with commas and 'and' between the last members.
    e.g. 'Kenya, Somalia and Mali'
    """
    local_and = _("and")
    if len(iterable) > 2:
        return ", ".join([str(i) for i in iterable[:-1]]) + f", {local_and} " + str(iterable[-1])
    if len(iterable) == 2:
        return f" {local_and} ".join([str(i) for i in iterable])
    if len(iterable) == 1:
        return str(iterable[0])


def get_select_options(df, value_column, label_column):
    """
    Return the list of options for a select box from a dataframe.
    """
    df = df[[value_column, label_column]].drop_duplicates()
    df.columns = ["value", "label"]
    df.dropna(inplace=True)
    df = df.sort_values(by="label")
    return df.to_dict("records")


def get_zoom_center(bbox: list) -> [float, dict]:
    """
    Returns zoom (float) and center ({longitude: float, latitude: float}) for Plotly layout.mapbox parameters.
    Parameters:
        bbox (list/np array): List or numpy array of 4 coordinates that represent bounding box.
    """
    b = box(bbox[0], bbox[1], bbox[2], bbox[3])
    coords = list(b.exterior.coords)
    p = Polygon(coords)
    area = p.area
    xp = [10, 20, 40, 60, 90, 130, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    width = 500
    fp = [val * width / 550 for val in [6.8, 6.7, 5.5, 5.3, 4.8, 4.6, 4.15, 4.1, 3.9, 3.7, 3.5, 3.3, 3.1, 2.9, 2.7]]
    zoom = np.interp(x=area, xp=xp, fp=fp)
    return zoom, {"lon": p.centroid.x, "lat": p.centroid.y}


def get_joined_names(items_list: List[Any]) -> str:
    """
    Join a list of items into string with commas and 'and' between the last members.
    E.g. 'Kenya, Somalia and Mali'
    """
    translated_and = _("and")
    items_list = [item for item in items_list if item]
    if len(items_list) > 2:
        return ", ".join([str(i) for i in items_list[:-1]]) + f", {translated_and} " + str(items_list[-1])
    if len(items_list) == 2:
        return f" {translated_and} ".join([str(i) for i in items_list])
    if len(items_list) == 1:
        return str(items_list[0])


# Map of autocomplete views that can be used to select specific models.
# If a ModelChoice field has either a large number of options, or the available
# options are dependent on user permissions, we need to use an autocomplete rather
# than a static list of choice when preparing the available visualizations dict.
MODEL_AUTOCOMPLETE_MAP = {
    "balance.models.CommodityBalance": "balance-dataseries-autocomplete",
    "balance.models.CommodityBalanceDataSet": "balance-dataset-autocomplete",
    "common.models.ClassifiedProduct": "classifiedproduct-autocomplete",
    "ipc.models.IPCClassificationDataSet": "ipcclassification-dataset-autocomplete",
    "price.models.ExchangeRate": "exchange-rate-autocomplete",
    "price.models.MarketProduct": "market-product-autocomplete",
    "price.models.PriceIndex": "price-index-autocomplete",
    "price.models.PriceRatio": "price-ratio-autocomplete",
    "price.models.PriceDataSet": "price-dataset-autocomplete",
    "spatial.models.GeographicUnit": "geographicunit-autocomplete",
    "warehouse.models.DataSet": "dataset-dataseries-autocomplete",
    "warehouse.models.DataSeries": "dataseries-autocomplete",
    "warehouse.models.DataSourceOrganization": "datasourcedocument-organization-autocomplete",
    # Temporary solution, need a way to separate different semistructured document types
    "semistructured.models.SemiStructuredDataSeries": "semistructured-mapketpriceprojection-dataseries-autocomplete",
}


def convert_widget(widget_name: str) -> str:
    if widget_name.startswith("django.forms.widgets."):
        widget_name = widget_name[21:]
    # We don't want to pass dal_select2.widgets.ModelSelect2Multiple or dal_select2.widgets.ModelSelect2 backend widgets to CMS,
    # because "SelectMultiple" and "Select" already have required functionality and implemented
    if widget_name == "dal_select2.widgets.ModelSelect2Multiple":
        widget_name = "SelectMultiple"
    if widget_name == "dal_select2.widgets.ModelSelect2":
        widget_name = "Select"
    return widget_name


def create_visualization_parameter_dict(parameter_name: str, parameter_field: Type[forms.Field]) -> dict:
    """Convert Django form field into a dictionary, so it can be rendered in a view."""
    parameter_dict = {
        "name": parameter_name,
        "default_value": parameter_field.initial,
    }
    # We aren't going to render the forms using Django, so no need to use the widget class name
    parameter_dict["widget"] = convert_widget(name_from_class(parameter_field.widget))

    # Other standard attributes
    for attr in ["required", "help_text", "label", "validators"]:
        parameter_dict[attr] = getattr(parameter_field, attr)

    if hasattr(parameter_field, "choices"):
        if isinstance(parameter_field, forms.ModelChoiceField):
            model = parameter_field.choices.queryset.model
            model_path = name_from_class(model)

            # Data Sets and Data Series choices depend on user permissions, so we must use
            # an autocomplete so that the user permissions can be applied at runtime as the
            # visualization is configured.
            # Other Models with a large number of items, e.g. ClassifiedProduct, may
            # benefit from autocomplete even if the list of options is static.
            try:
                parameter_dict["autocomplete_url"] = parameter_field.widget.url
            except AttributeError:
                # No specific widget on the field, so look up the model in MODEL_AUTOCOMPLETE_MAP
                # We force the use of MODEL_AUTOCOMPLETE_MAP for DataSeries and DataSet so that
                # can raise an error if the map is missing an entry for one of those classes.
                if issubclass(model, (DataSeries, DataSet)) or model_path in MODEL_AUTOCOMPLETE_MAP:
                    try:
                        parameter_dict["autocomplete_url"] = reverse(MODEL_AUTOCOMPLETE_MAP[name_from_class(model)])
                    except KeyError as e:
                        raise RuntimeError(
                            "Cannot find autocomplete_url for model %s from %s"
                            % (name_from_class(model), parameter_name)
                        ) from e
                else:
                    # We didn't find an autocomplete, so create static choices from the queryset,
                    # remembering to convert ModelChoiceIteratorValue to str
                    parameter_dict["choices"] = [(str(value), label) for value, label in parameter_field.choices]
        else:
            # Not a ModelChoiceField, so use static choices
            parameter_dict["choices"] = parameter_field.choices

    # Default the label if necessary
    if parameter_dict["label"] is None:
        parameter_dict["label"] = " ".join(pretty_name(parameter_name).split())
    return parameter_dict
