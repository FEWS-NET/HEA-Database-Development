"""
Admin sidebar menu configuration.

Defines the structure as zones > sections > items.
The context processor in context_processors.py uses this to build a
permission-filtered menu for each user, passed to templates as
``admin_menu_zones``.
"""

from django.utils.translation import gettext_lazy as _

# App-index ordering & icons
# Models not listed here fall back to Django's alphabetical app_list.

APP_INDEX_CONFIG = {
    "baseline": [
        # Group 1 – Core baseline hierarchy
        [
            {
                "label": _("Source Organizations"),
                "url_name": "admin:baseline_sourceorganization_changelist",
                "perm": "baseline.view_sourceorganization",
                "icon": "bi-building",
            },
            {
                "label": _("Livelihood Zones"),
                "url_name": "admin:baseline_livelihoodzone_changelist",
                "perm": "baseline.view_livelihoodzone",
                "icon": "bi-map",
            },
            {
                "label": _("Communities"),
                "url_name": "admin:baseline_community_changelist",
                "perm": "baseline.view_community",
                "icon": "bi-people-fill",
            },
            {
                "label": _("Livelihood Zone Baselines"),
                "url_name": "admin:baseline_livelihoodzonebaseline_changelist",
                "perm": "baseline.view_livelihoodzonebaseline",
                "icon": "bi-clipboard-data",
            },
            {
                "label": _("Wealth Groups"),
                "url_name": "admin:baseline_wealthgroup_changelist",
                "perm": "baseline.view_wealthgroup",
                "icon": "bi-diagram-3",
            },
            {
                "label": _("Wealth Group Characteristic Values"),
                "url_name": "admin:baseline_wealthgroupcharacteristicvalue_changelist",
                "perm": "baseline.view_wealthgroupcharacteristicvalue",
                "icon": "bi-bar-chart",
            },
            {
                "label": _("Livelihood Activities"),
                "url_name": "admin:baseline_livelihoodactivity_changelist",
                "perm": "baseline.view_livelihoodactivity",
                "icon": "bi-activity",
            },
            {
                "label": _("Livelihood Strategies"),
                "url_name": "admin:baseline_livelihoodstrategy_changelist",
                "perm": "baseline.view_livelihoodstrategy",
                "icon": "bi-lightbulb",
            },
        ],
        # Group 2 – Baseline Correction
        [
            {
                "label": _("Livelihood Zone Baseline Corrections"),
                "url_name": "admin:baseline_livelihoodzonebaselinecorrection_changelist",
                "perm": "baseline.view_livelihoodzonebaselinecorrection",
                "icon": "bi-pencil-square",
            },
        ],
        # Group 3 – Supporting / supplementary
        [
            {
                "label": _("Community Crop Productions"),
                "url_name": "admin:baseline_communitycropproduction_changelist",
                "perm": "baseline.view_communitycropproduction",
                "icon": "bi-flower2",
            },
            {
                "label": _("Community Livestock"),
                "url_name": "admin:baseline_communitylivestock_changelist",
                "perm": "baseline.view_communitylivestock",
                "icon": "bi-collection",
            },
            {
                "label": _("Coping Strategies"),
                "url_name": "admin:baseline_copingstrategy_changelist",
                "perm": "baseline.view_copingstrategy",
                "icon": "bi-shield-check",
            },
            {
                "label": _("Events"),
                "url_name": "admin:baseline_event_changelist",
                "perm": "baseline.view_event",
                "icon": "bi-calendar-event",
            },
            {
                "label": _("Expandability Factors"),
                "url_name": "admin:baseline_expandabilityfactor_changelist",
                "perm": "baseline.view_expandabilityfactor",
                "icon": "bi-arrows-expand",
            },
            {
                "label": _("Hazards"),
                "url_name": "admin:baseline_hazard_changelist",
                "perm": "baseline.view_hazard",
                "icon": "bi-exclamation-triangle",
            },
            {
                "label": _("Market Prices"),
                "url_name": "admin:baseline_marketprice_changelist",
                "perm": "baseline.view_marketprice",
                "icon": "bi-cart3",
            },
            {
                "label": _("Seasonal Activities"),
                "url_name": "admin:baseline_seasonalactivity_changelist",
                "perm": "baseline.view_seasonalactivity",
                "icon": "bi-calendar3",
            },
            {
                "label": _("Seasonal Activity Occurrences"),
                "url_name": "admin:baseline_seasonalactivityoccurrence_changelist",
                "perm": "baseline.view_seasonalactivityoccurrence",
                "icon": "bi-calendar-week",
            },
            {
                "label": _("Seasonal Production Performance"),
                "url_name": "admin:baseline_seasonalproductionperformance_changelist",
                "perm": "baseline.view_seasonalproductionperformance",
                "icon": "bi-graph-up",
            },
        ],
    ],
    "common": [
        [
            {
                "label": _("Countries"),
                "url_name": "admin:common_country_changelist",
                "perm": "common.view_country",
                "icon": "bi-globe",
            },
            {
                "label": _("Currencies"),
                "url_name": "admin:common_currency_changelist",
                "perm": "common.view_currency",
                "icon": "bi-currency-exchange",
            },
            {
                "label": _("Products"),
                "url_name": "admin:common_classifiedproduct_changelist",
                "perm": "common.view_classifiedproduct",
                "icon": "bi-box-seam",
            },
            {
                "label": _("Units of Measure"),
                "url_name": "admin:common_unitofmeasure_changelist",
                "perm": "common.view_unitofmeasure",
                "icon": "bi-rulers",
            },
        ],
    ],
    "metadata": [
        # Group 1 – Reference lookup types
        [
            {
                "label": _("Livelihood Categories"),
                "url_name": "admin:metadata_livelihoodcategory_changelist",
                "perm": "metadata.view_livelihoodcategory",
                "icon": "bi-layers",
            },
            {
                "label": _("Wealth Group Categories"),
                "url_name": "admin:metadata_wealthgroupcategory_changelist",
                "perm": "metadata.view_wealthgroupcategory",
                "icon": "bi-people",
            },
            {
                "label": _("Characteristic Groups"),
                "url_name": "admin:metadata_characteristicgroup_changelist",
                "perm": "metadata.view_characteristicgroup",
                "icon": "bi-collection",
            },
            {
                "label": _("Wealth Characteristics"),
                "url_name": "admin:metadata_wealthcharacteristic_changelist",
                "perm": "metadata.view_wealthcharacteristic",
                "icon": "bi-list-check",
            },
            {
                "label": _("Hazard Categories"),
                "url_name": "admin:metadata_hazardcategory_changelist",
                "perm": "metadata.view_hazardcategory",
                "icon": "bi-exclamation-triangle",
            },
            {
                "label": _("Seasons"),
                "url_name": "admin:metadata_season_changelist",
                "perm": "metadata.view_season",
                "icon": "bi-sun",
            },
            {
                "label": _("Seasonal Activity Types"),
                "url_name": "admin:metadata_seasonalactivitytype_changelist",
                "perm": "metadata.view_seasonalactivitytype",
                "icon": "bi-calendar-check",
            },
            {
                "label": _("Markets"),
                "url_name": "admin:metadata_market_changelist",
                "perm": "metadata.view_market",
                "icon": "bi-shop",
            },
        ],
        # Group 2 – Labels
        [
            {
                "label": _("Activity Labels"),
                "url_name": "admin:metadata_activitylabel_changelist",
                "perm": "metadata.view_activitylabel",
                "icon": "bi-tag",
            },
            {
                "label": _("Wealth Characteristic Labels"),
                "url_name": "admin:metadata_wealthcharacteristiclabel_changelist",
                "perm": "metadata.view_wealthcharacteristiclabel",
                "icon": "bi-tags",
            },
        ],
    ],
    "auth": [
        [
            {
                "label": _("Users"),
                "url_name": "admin:auth_user_changelist",
                "perm": "auth.view_user",
                "icon": "bi-person-fill",
            },
            {
                "label": _("Groups"),
                "url_name": "admin:auth_group_changelist",
                "perm": "auth.view_group",
                "icon": "bi-people-fill",
            },
        ],
    ],
}

ADMIN_MENU_CONFIG = [
    {
        "id": "core",
        "label": _("Core Data"),
        "sections": [
            {
                "id": "bss-setup",
                "label": _("BSS Setup"),
                "icon": "bi-gear",
                "perms_any": [
                    "baseline.view_sourceorganization",
                    "baseline.view_livelihoodzone",
                    "baseline.view_livelihoodzonebaseline",
                    "baseline.view_community",
                    "baseline.view_livelihoodzonebaselinecorrection",
                ],
                "items": [
                    {
                        "label": _("Source Organizations"),
                        "url_name": "admin:baseline_sourceorganization_changelist",
                        "perm": "baseline.view_sourceorganization",
                    },
                    {
                        "label": _("Livelihood Zones"),
                        "url_name": "admin:baseline_livelihoodzone_changelist",
                        "perm": "baseline.view_livelihoodzone",
                    },
                    {
                        "label": _("Livelihood Zone Baselines"),
                        "url_name": "admin:baseline_livelihoodzonebaseline_changelist",
                        "perm": "baseline.view_livelihoodzonebaseline",
                    },
                    {
                        "label": _("Baseline Corrections"),
                        "url_name": "admin:baseline_livelihoodzonebaselinecorrection_changelist",
                        "perm": "baseline.view_livelihoodzonebaselinecorrection",
                    },
                    {
                        "label": _("Communities"),
                        "url_name": "admin:baseline_community_changelist",
                        "perm": "baseline.view_community",
                    },
                ],
            },
            {
                "id": "wg-data",
                "label": _("BSS WB, Data Sheets"),
                "icon": "bi-table",
                "perms_any": ["baseline.view_wealthgroup"],
                "items": [
                    {
                        "label": _("Wealth Group Data"),
                        "url_name": "admin:baseline_wealthgroup_changelist",
                        "perm": "baseline.view_wealthgroup",
                    },
                ],
            },
            {
                "id": "wg-activity",
                "label": _("Wealth, Activity and Strategy"),
                "icon": "bi-graph-up",
                "perms_any": [
                    "baseline.view_livelihoodactivity",
                    "baseline.view_wealthgroupcharacteristicvalue",
                    "baseline.view_livelihoodstrategy",
                ],
                "items": [
                    {
                        "label": _("Wealth Group Characteristic Value"),
                        "url_name": "admin:baseline_wealthgroupcharacteristicvalue_changelist",
                        "perm": "baseline.view_wealthgroupcharacteristicvalue",
                    },
                    {
                        "label": _("Livelihood Strategy"),
                        "url_name": "admin:baseline_livelihoodstrategy_changelist",
                        "perm": "baseline.view_livelihoodstrategy",
                    },
                    {
                        "label": _("Livelihood Activity"),
                        "url_name": "admin:baseline_livelihoodactivity_changelist",
                        "perm": "baseline.view_livelihoodactivity",
                    },
                ],
            },
            {
                "id": "labels",
                "label": _("Labels"),
                "icon": "bi-tags",
                "perms_any": [
                    "metadata.view_wealthcharacteristiclabel",
                    "metadata.view_activitylabel",
                ],
                "items": [
                    {
                        "label": _("Wealth Characteristic Label"),
                        "url_name": "admin:metadata_wealthcharacteristiclabel_changelist",
                        "perm": "metadata.view_wealthcharacteristiclabel",
                    },
                    {
                        "label": _("Activity Label"),
                        "url_name": "admin:metadata_activitylabel_changelist",
                        "perm": "metadata.view_activitylabel",
                    },
                ],
            },
            {
                "id": "production",
                "label": _("BSS Production Data"),
                "icon": "bi-tree",
                "perms_any": [
                    "baseline.view_communitycropproduction",
                    "baseline.view_communitylivestock",
                ],
                "items": [
                    {
                        "label": _("Crop Production"),
                        "url_name": "admin:baseline_communitycropproduction_changelist",
                        "perm": "baseline.view_communitycropproduction",
                    },
                    {
                        "label": _("Livestock Production"),
                        "url_name": "admin:baseline_communitylivestock_changelist",
                        "perm": "baseline.view_communitylivestock",
                    },
                ],
            },
            {
                "id": "markets",
                "label": _("Market Prices"),
                "icon": "bi-cart",
                "perms_any": [
                    "metadata.view_market",
                    "baseline.view_marketprice",
                ],
                "items": [
                    {
                        "label": _("Markets"),
                        "url_name": "admin:metadata_market_changelist",
                        "perm": "metadata.view_market",
                    },
                    {
                        "label": _("Market Prices"),
                        "url_name": "admin:baseline_marketprice_changelist",
                        "perm": "baseline.view_marketprice",
                    },
                ],
            },
            {
                "id": "seasonal",
                "label": _("Seasonal Calendars"),
                "icon": "bi-calendar3",
                "perms_any": [
                    "metadata.view_seasonalactivitytype",
                    "baseline.view_seasonalactivity",
                    "baseline.view_seasonalactivityoccurrence",
                ],
                "items": [
                    {
                        "label": _("Seasonal Activity Type"),
                        "url_name": "admin:metadata_seasonalactivitytype_changelist",
                        "perm": "metadata.view_seasonalactivitytype",
                    },
                    {
                        "label": _("Seasonal Activities"),
                        "url_name": "admin:baseline_seasonalactivity_changelist",
                        "perm": "baseline.view_seasonalactivity",
                    },
                    {
                        "label": _("Activity Occurrences"),
                        "url_name": "admin:baseline_seasonalactivityoccurrence_changelist",
                        "perm": "baseline.view_seasonalactivityoccurrence",
                    },
                ],
            },
            {
                "id": "hazards",
                "label": _("Hazards and Events"),
                "icon": "bi-exclamation-triangle",
                "perms_any": [
                    "baseline.view_seasonalproductionperformance",
                    "baseline.view_hazard",
                    "baseline.view_event",
                ],
                "items": [
                    {
                        "label": _("Annual Production Performances"),
                        "url_name": "admin:baseline_seasonalproductionperformance_changelist",
                        "perm": "baseline.view_seasonalproductionperformance",
                    },
                    {
                        "label": _("Hazards"),
                        "url_name": "admin:baseline_hazard_changelist",
                        "perm": "baseline.view_hazard",
                    },
                    {
                        "label": _("Events"),
                        "url_name": "admin:baseline_event_changelist",
                        "perm": "baseline.view_event",
                    },
                ],
            },
            {
                "id": "coping",
                "label": _("Expandability and Coping"),
                "icon": "bi-tools",
                "perms_any": [
                    "baseline.view_expandabilityfactor",
                    "baseline.view_copingstrategy",
                ],
                "items": [
                    {
                        "label": _("Expandability Factors"),
                        "url_name": "admin:baseline_expandabilityfactor_changelist",
                        "perm": "baseline.view_expandabilityfactor",
                    },
                    {
                        "label": _("Coping Strategies"),
                        "url_name": "admin:baseline_copingstrategy_changelist",
                        "perm": "baseline.view_copingstrategy",
                    },
                ],
            },
        ],
    },
    {
        "id": "reference",
        "label": _("Reference Data"),
        "sections": [
            {
                "id": "common",
                "label": _("Common"),
                "icon": "bi-globe",
                "perms_any": [
                    "common.view_country",
                    "common.view_currency",
                    "common.view_classifiedproduct",
                    "common.view_unitofmeasure",
                ],
                "items": [
                    {
                        "label": _("Countries"),
                        "url_name": "admin:common_country_changelist",
                        "perm": "common.view_country",
                    },
                    {
                        "label": _("Currencies"),
                        "url_name": "admin:common_currency_changelist",
                        "perm": "common.view_currency",
                    },
                    {
                        "label": _("Products"),
                        "url_name": "admin:common_classifiedproduct_changelist",
                        "perm": "common.view_classifiedproduct",
                    },
                    {
                        "label": _("Units of Measure"),
                        "url_name": "admin:common_unitofmeasure_changelist",
                        "perm": "common.view_unitofmeasure",
                    },
                ],
            },
            {
                "id": "metadata",
                "label": _("Metadata"),
                "icon": "bi-list-ul",
                "perms_any": [
                    "metadata.view_hazardcategory",
                    "metadata.view_livelihoodcategory",
                    "metadata.view_season",
                    "metadata.view_wealthgroupcategory",
                    "metadata.view_characteristicgroup",
                    "metadata.view_wealthcharacteristic",
                ],
                "items": [
                    {
                        "label": _("Hazard Categories"),
                        "url_name": "admin:metadata_hazardcategory_changelist",
                        "perm": "metadata.view_hazardcategory",
                    },
                    {
                        "label": _("Livelihood Categories"),
                        "url_name": "admin:metadata_livelihoodcategory_changelist",
                        "perm": "metadata.view_livelihoodcategory",
                    },
                    {
                        "label": _("Seasons"),
                        "url_name": "admin:metadata_season_changelist",
                        "perm": "metadata.view_season",
                    },
                    {
                        "label": _("Wealth Categories"),
                        "url_name": "admin:metadata_wealthgroupcategory_changelist",
                        "perm": "metadata.view_wealthgroupcategory",
                    },
                    {
                        "label": _("Characteristics Groups"),
                        "url_name": "admin:metadata_characteristicgroup_changelist",
                        "perm": "metadata.view_characteristicgroup",
                    },
                    {
                        "label": _("Wealth Group Characteristics"),
                        "url_name": "admin:metadata_wealthcharacteristic_changelist",
                        "perm": "metadata.view_wealthcharacteristic",
                    },
                ],
            },
        ],
    },
    {
        "id": "system",
        "label": _("System"),
        "sections": [
            {
                "id": "users",
                "label": _("User Management"),
                "icon": "bi-people",
                "perms_any": ["auth.view_user", "auth.view_group"],
                "items": [
                    {
                        "label": _("Users"),
                        "url_name": "admin:auth_user_changelist",
                        "perm": "auth.view_user",
                    },
                    {
                        "label": _("Groups"),
                        "url_name": "admin:auth_group_changelist",
                        "perm": "auth.view_group",
                    },
                ],
            },
        ],
    },
]
