import re
from copy import deepcopy

from binary_database_files.models import File
from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django.utils.translation import gettext_lazy as _

from common.fields import translation_fields
from metadata.models import LivelihoodStrategyType

from .forms import (
    CommunityForm,
    FoodPurchaseForm,
    LivelihoodActivityForm,
    LivelihoodStrategyForm,
    MeatProductionForm,
    MilkProductionForm,
    OtherCashIncomeForm,
    OtherPurchaseForm,
    PaymentInKindForm,
    ReliefGiftOtherForm,
    WealthGroupCharacteristicValueForm,
    WealthGroupForm,
)
from .models import (
    ButterProduction,
    Community,
    CommunityCropProduction,
    CommunityLivestock,
    CopingStrategy,
    CropProduction,
    Event,
    ExpandabilityFactor,
    Fishing,
    FoodPurchase,
    Hazard,
    Hunting,
    KeyParameter,
    LivelihoodActivity,
    LivelihoodProductCategory,
    LivelihoodStrategy,
    LivelihoodZone,
    LivelihoodZoneBaseline,
    LivelihoodZoneBaselineCorrection,
    LivestockSale,
    MarketPrice,
    MeatProduction,
    MilkProduction,
    OtherCashIncome,
    OtherLivestockProduction,
    OtherPurchase,
    PaymentInKind,
    ReliefGiftOther,
    SeasonalActivity,
    SeasonalActivityOccurrence,
    SeasonalProductionPerformance,
    SourceOrganization,
    WealthGroup,
    WealthGroupCharacteristicValue,
    WildFoodGathering,
)

admin.site.site_header = "Livelihoods Database Administration"
admin.site.index_title = "Livelihoods Database"
admin.site.site_title = "Livelihoods Database Administration"


class SummaryValueListFilter(admin.SimpleListFilter):
    """
    Filter that toggles between summary (community is null) and community-level records.
    """

    title = _("record type")
    parameter_name = "record_type"
    community_field = "community"

    def lookups(self, request, model_admin):
        return [
            ("summary", _("Summary only")),
            ("community", _("Community only")),
        ]

    def queryset(self, request, queryset):
        if self.value() == "summary":
            return queryset.filter(**{f"{self.community_field}__isnull": True})
        if self.value() == "community":
            return queryset.filter(**{f"{self.community_field}__isnull": False})
        return queryset


class WealthGroupSummaryValueListFilter(SummaryValueListFilter):
    """
    Summary/community filter for models that reach community via wealth_group FK.
    """

    community_field = "wealth_group__community"


class SourceOrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "full_name",
    )
    search_fields = [
        "name",
        "full_name",
        "description",
    ]


class LivelihoodZoneAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "alternate_code",
        "name",
        "country",
    )
    search_fields = [
        "code",
        "alternate_code",
        *translation_fields("name"),
        *translation_fields("description"),
        "country__name",
    ]
    list_filter = (("country", admin.RelatedOnlyFieldListFilter),)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("country")


class LivelihoodZoneBaselineCorrectionAdmin(admin.ModelAdmin):
    list_display = ("worksheet_name", "cell_range", "previous_value", "value", "correction_date", "author")
    list_filter = ("worksheet_name", "correction_date", "author")
    search_fields = (
        "livelihood_zone_baseline__livelihood_zone__code",
        "livelihood_zone_baseline__livelihood_zone__alternate_code",
        *translation_fields("livelihood_zone_baseline__name"),
        "livelihood_zone_baseline__reference_year_end_date",
        *translation_fields("livelihood_zone_baseline__primary_livelihood_system__name"),
        "livelihood_zone_baseline__source_organization__name",
        "cell_range",
        "previous_value",
        "value",
        "comment",
    )
    date_hierarchy = "correction_date"


class LivelihoodZoneBaselineCorrectionInlineAdmin(admin.StackedInline):
    model = LivelihoodZoneBaselineCorrection
    list_display = ("worksheet_name", "cell_range", "previous_value", "value", "correction_date", "author")
    readonly_fields = ("correction_date",)
    extra = 1


class GISModelAdminReadOnly(GISModelAdmin):
    """
    A GISModelAdmin where the geometry field is read-only
    """

    # disabled set to True removes the "Delete all Features"
    gis_widget_kwargs = {"attrs": {"map_width": 1000, "modifiable": False, "disabled": True}}


class LivelihoodZoneBaselineAdmin(GISModelAdminReadOnly):
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "livelihood_zone",
                    "livelihood_zone_alternate_code",
                    "country",
                    *translation_fields("name"),
                    "primary_livelihood_system",
                    "source_organization",
                    "bss",
                    "bss_uploaded_date_time",
                    "bss_language",
                    *translation_fields("profile_report"),
                    "reference_year_start_date",
                    "reference_year_end_date",
                    "valid_from_date",
                    "valid_to_date",
                    "data_collection_start_date",
                    "data_collection_end_date",
                    "publication_date",
                    "currency",
                    *translation_fields("description"),
                ]
            },
        ),
        (
            "Additional",
            {
                "classes": ["collapse", "extrapretty"],
                "fields": [
                    "geography",
                    "population_source",
                    "population_estimate",
                    "poor_main_staple",
                    "poor_household_size",
                    "poor_survival_non_food_expenditure",
                    "annual_kcals_cost",
                ],
            },
        ),
    ]
    list_display = (
        "livelihood_zone",
        "livelihood_zone_alternate_code",
        "primary_livelihood_system",
        "source_organization",
        "reference_year_start_date",
        "reference_year_end_date",
    )
    readonly_fields = (
        "livelihood_zone_alternate_code",
        "country",
        "bss_uploaded_date_time",
        "poor_main_staple",
        "poor_household_size",
        "poor_survival_non_food_expenditure",
        "annual_kcals_cost",
    )
    search_fields = (
        "livelihood_zone__code",
        "livelihood_zone__alternate_code",
        *translation_fields("name"),
        "reference_year_end_date",
        *translation_fields("primary_livelihood_system__name"),
        "source_organization__name",
    )
    list_filter = ["source_organization", ("livelihood_zone__country", admin.RelatedOnlyFieldListFilter)]
    date_hierarchy = "reference_year_start_date"
    inlines = [
        LivelihoodZoneBaselineCorrectionInlineAdmin,
    ]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "livelihood_zone__country",
                "primary_livelihood_system",
                "source_organization",
            )
        )

    @admin.display(description=_("Livelihood Zone Alternate Code"))
    def livelihood_zone_alternate_code(self, instance):
        """
        Display the alternate code for the livelihood zone as a readonly field.
        """
        return instance.livelihood_zone.alternate_code

    @admin.display(description=_("Country"))
    def country(self, instance):
        """
        Display the country for the livelihood zone as a readonly field.
        """
        return instance.livelihood_zone.country

    @admin.display(description=_("BSS Uploaded At"))
    def bss_uploaded_date_time(self, instance):
        """
        Display the date and time that the BSS was uploaded.
        """
        try:
            return File.objects.get(name=instance.bss).created_datetime.strftime("%Y-%m-%d %H:%M:%S")
        except File.DoesNotExist:
            return ""

    @admin.display(description=_("Poor Main Staple"))
    def poor_main_staple(self, instance):
        return instance.poor_main_staple

    @admin.display(description=_("Poor Household Size"))
    def poor_household_size(self, instance):
        return instance.poor_household_size

    @admin.display(description=_("Poor Survival Non-Food Expenditure"))
    def poor_survival_non_food_expenditure(self, instance):
        return instance.poor_survival_non_food_expenditure

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj=obj)
        if obj and obj.geography:
            # Check if 'geography' field has a value
            return fieldsets
        else:
            # Find the "Additional" fieldset and remove the "geography" field
            for fieldset in fieldsets:
                if fieldset[0] == "Additional":
                    fieldset[1]["fields"] = [field for field in fieldset[1]["fields"] if field != "geography"]
                    break
            return fieldsets


class CommunityAdmin(GISModelAdminReadOnly):
    form = CommunityForm
    fields = (
        "name",
        "full_name",
        "livelihood_zone_baseline",
        "livelihood_zone_alternate_code",
        "country",
        "aliases",
        "interview_number",
        "community_interview_date",
        "wealth_group_interview_date",
        "geography",
    )
    list_display = (
        "livelihood_zone_baseline",
        "livelihood_zone_alternate_code",
        "country",
        "full_name",
        "aliases",
    )
    readonly_fields = ("livelihood_zone_alternate_code", "country")
    search_fields = (
        "name",
        "full_name",
        "livelihood_zone_baseline__livelihood_zone__code",
        "livelihood_zone_baseline__livelihood_zone__alternate_code",
        *translation_fields("livelihood_zone_baseline__name"),
        "livelihood_zone_baseline__reference_year_end_date",
        "aliases",
    )
    list_filter = (("livelihood_zone_baseline__livelihood_zone__country", admin.RelatedOnlyFieldListFilter),)

    @admin.display(description=_("Livelihood Zone Alternate Code"))
    def livelihood_zone_alternate_code(self, instance):
        """
        Display the alternate code for the livelihood zone as a readonly field.
        """
        return instance.livelihood_zone_baseline.livelihood_zone.alternate_code

    def country(self, instance):
        """
        Display the country for the livelihood zone as a readonly field.
        """
        return instance.livelihood_zone_baseline.livelihood_zone.country

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("livelihood_zone_baseline__livelihood_zone__country")

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj=obj)
        if obj and obj.geography:
            # Check if 'geography' is already in the fields list
            if "geography" not in fields:
                # Add 'geography' to the fields
                fields += ("geography",)
        else:
            # Remove 'geography' from the fields if it's empty or null
            fields = [field for field in fields if field != "geography"]
        return fields


class LivelihoodStrategyAdmin(admin.ModelAdmin):
    form = LivelihoodStrategyForm
    fields = (
        "livelihood_zone_baseline",
        "strategy_type",
        "season",
        "product",
        "unit_of_measure",
        "currency",
        "additional_identifier",
    )
    list_display = (
        "livelihood_zone_baseline",
        "strategy_type",
        "season",
        "product",
        "unit_of_measure",
    )

    search_fields = (
        "strategy_type",
        "livelihood_zone_baseline__livelihood_zone__code",
        "livelihood_zone_baseline__livelihood_zone__alternate_code",
        *translation_fields("livelihood_zone_baseline__name"),
        "livelihood_zone_baseline__reference_year_end_date",
        "additional_identifier",
        "product__cpc__iexact",
        *translation_fields("product__description"),
        *translation_fields("product__common_name"),
        "product__aliases",
        *translation_fields("season__name"),
        "season__aliases",
        "livelihood_zone_baseline__livelihood_zone__country__name",
    )

    list_filter = (
        "strategy_type",
        ("livelihood_zone_baseline__livelihood_zone__country", admin.RelatedOnlyFieldListFilter),
    )

    def get_search_results(self, request, queryset, search_term):
        # Allow natural key format "BF01: 2011-10-31" by stripping the colon separator.
        normalized = search_term.replace(":", "")
        date_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", normalized)
        year_match = re.search(r"\b(\d{4})\b", normalized)
        # Remove date/year from the term so text fields are searched without them.
        text_term = re.sub(r"\b\d{4}(?:-\d{2}-\d{2})?\b", "", normalized).strip()
        queryset, use_distinct = super().get_search_results(request, queryset, text_term)
        if date_match:
            queryset = queryset.filter(livelihood_zone_baseline__reference_year_end_date=date_match.group(1))
        elif year_match:
            queryset = queryset.filter(
                livelihood_zone_baseline__reference_year_end_date__year=int(year_match.group(1))
            )
        return queryset, use_distinct

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "livelihood_zone_baseline__livelihood_zone",
                "season",
                "product",
                "unit_of_measure",
            )
        )


class KeyParameterAdmin(admin.ModelAdmin):
    autocomplete_fields = ("livelihood_strategy",)
    fields = (
        "livelihood_strategy",
        "monitor_quantity",
        "monitor_price",
    )
    list_display = (
        "livelihood_strategy",
        "monitor_quantity",
        "monitor_price",
    )
    search_fields = (
        "livelihood_strategy__livelihood_zone_baseline__livelihood_zone__code",
        "livelihood_strategy__livelihood_zone_baseline__livelihood_zone__alternate_code",
        *translation_fields("livelihood_strategy__product__common_name"),
        *translation_fields("livelihood_strategy__product__description"),
        "livelihood_strategy__product__cpc",
        "livelihood_strategy__additional_identifier",
    )
    list_filter = (
        "monitor_quantity",
        "monitor_price",
        "livelihood_strategy__strategy_type",
        ("livelihood_strategy__livelihood_zone_baseline__livelihood_zone__country", admin.RelatedOnlyFieldListFilter),
        ("livelihood_strategy__product", admin.RelatedOnlyFieldListFilter),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "livelihood_strategy__livelihood_zone_baseline__livelihood_zone__country",
                "livelihood_strategy__season",
                "livelihood_strategy__product",
                "livelihood_strategy__unit_of_measure",
            )
        )


class WealthGroupCharacteristicValueInlineAdmin(admin.TabularInline):
    fields = ["wealth_characteristic", "value", "min_value", "max_value"]
    model = WealthGroupCharacteristicValue
    extra = 1
    classes = ["collapse"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "wealth_characteristic",
                "wealth_group__livelihood_zone_baseline",
                "wealth_group__community",
            )
        )

    def get_extra(self, request, obj=None, **kwargs):
        extra = super().get_extra(request, obj, **kwargs)
        if extra:
            self.verbose_name_plural = "Wealth characteristics"
        return extra


class LivelihoodActivityAdmin(admin.ModelAdmin):
    form = LivelihoodActivityForm

    # Maps strategy_type to the subclass accessor name, its form, extra fieldsets,
    # and any extra fields to append to the base "Quantity" fieldset.
    _SUBCLASS_CONFIG = {
        LivelihoodStrategyType.MILK_PRODUCTION: {
            "accessor": "milkproduction",
            "form": MilkProductionForm,
            "quantity_extra": ["quantity_butter_production"],
            "extra_fieldsets": [
                (
                    "Milk source",
                    {
                        "fields": [
                            "milking_animals",
                            "lactation_days",
                            "daily_production",
                            "type_of_milk_consumed",
                            "type_of_milk_sold_or_other_uses",
                        ]
                    },
                ),
            ],
        },
        LivelihoodStrategyType.MEAT_PRODUCTION: {
            "accessor": "meatproduction",
            "form": MeatProductionForm,
            "extra_fieldsets": [
                (
                    "Meat source",
                    {
                        "fields": [
                            "animals_slaughtered",
                            "carcass_weight",
                        ]
                    },
                ),
            ],
        },
        LivelihoodStrategyType.FOOD_PURCHASE: {
            "accessor": "foodpurchase",
            "form": FoodPurchaseForm,
            "extra_fieldsets": [
                (
                    "Purchases",
                    {
                        "fields": [
                            "unit_multiple",
                            "times_per_month",
                            "months_per_year",
                            "times_per_year",
                        ]
                    },
                ),
            ],
        },
        LivelihoodStrategyType.PAYMENT_IN_KIND: {
            "accessor": "paymentinkind",
            "form": PaymentInKindForm,
            "extra_fieldsets": [
                (
                    "Payment",
                    {
                        "fields": [
                            "payment_product",
                            "payment_per_time",
                            "people_per_household",
                            "times_per_month",
                            "months_per_year",
                            "times_per_year",
                        ]
                    },
                ),
            ],
        },
        LivelihoodStrategyType.RELIEF_GIFT_OTHER: {
            "accessor": "reliefgiftother",
            "form": ReliefGiftOtherForm,
            "extra_fieldsets": [
                (
                    "Relief",
                    {
                        "fields": [
                            "unit_multiple",
                            "times_per_month",
                            "months_per_year",
                            "times_per_year",
                        ]
                    },
                ),
            ],
        },
        LivelihoodStrategyType.OTHER_CASH_INCOME: {
            "accessor": "othercashincome",
            "form": OtherCashIncomeForm,
            "extra_fieldsets": [
                (
                    "Income",
                    {
                        "fields": [
                            "payment_per_time",
                            "people_per_household",
                            "times_per_month",
                            "months_per_year",
                            "times_per_year",
                        ]
                    },
                ),
            ],
        },
        LivelihoodStrategyType.OTHER_PURCHASE: {
            "accessor": "otherpurchase",
            "form": OtherPurchaseForm,
            "extra_fieldsets": [
                (
                    "Purchases",
                    {
                        "fields": [
                            "unit_multiple",
                            "times_per_month",
                            "months_per_year",
                            "times_per_year",
                        ]
                    },
                ),
            ],
        },
    }

    list_display = (
        "wealth_group",
        "strategy_type",
        "get_product_common_name",
        "get_season_name",
        "get_country_name",
    )
    list_filter = (
        WealthGroupSummaryValueListFilter,
        "strategy_type",
        "scenario",
        ("wealth_group__wealth_group_category", admin.RelatedOnlyFieldListFilter),
        ("livelihood_strategy__product", admin.RelatedOnlyFieldListFilter),
        ("livelihood_strategy__season", admin.RelatedOnlyFieldListFilter),
        ("livelihood_zone_baseline__livelihood_zone__country", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = (
        "wealth_group__wealth_group_category__code__iexact",
        *translation_fields("wealth_group__wealth_group_category__name"),
        "wealth_group__community__name",
        "wealth_group__community__full_name",
        "strategy_type",
        "livelihood_zone_baseline__livelihood_zone__code",
        "livelihood_zone_baseline__livelihood_zone__alternate_code",
        *translation_fields("livelihood_zone_baseline__name"),
        "livelihood_zone_baseline__reference_year_end_date",
        "livelihood_strategy__product__cpc__iexact",
        *translation_fields("livelihood_strategy__product__description"),
        *translation_fields("livelihood_strategy__product__common_name"),
        "livelihood_strategy__product__aliases",
        *translation_fields("livelihood_strategy__season__name"),
        "livelihood_strategy__season__aliases",
        "livelihood_strategy__additional_identifier",
        "livelihood_zone_baseline__livelihood_zone__country__name",
    )

    def get_search_results(self, request, queryset, search_term):
        # Allow natural key format "BF01: 2011-10-31" by stripping the colon separator.
        normalized = search_term.replace(":", "")
        date_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", normalized)
        year_match = re.search(r"\b(\d{4})\b", normalized)
        text_term = re.sub(r"\b\d{4}(?:-\d{2}-\d{2})?\b", "", normalized).strip()
        queryset, use_distinct = super().get_search_results(request, queryset, text_term)
        if date_match:
            queryset = queryset.filter(livelihood_zone_baseline__reference_year_end_date=date_match.group(1))
        elif year_match:
            queryset = queryset.filter(
                livelihood_zone_baseline__reference_year_end_date__year=int(year_match.group(1))
            )
        return queryset, use_distinct

    def get_object(self, request, object_id, from_field=None):
        obj = super().get_object(request, object_id, from_field)
        if obj is None:
            return None
        config = self._SUBCLASS_CONFIG.get(obj.strategy_type)
        if config:
            try:
                return getattr(obj, config["accessor"])
            except AttributeError:
                pass
        return obj

    def get_form(self, request, obj=None, change=False, **kwargs):
        if obj is not None:
            config = self._SUBCLASS_CONFIG.get(obj.strategy_type)
            if config and config.get("form"):
                return config["form"]
        return super().get_form(request, obj, change, **kwargs)

    def get_fieldsets(self, request, obj=None):
        fieldsets = deepcopy(self.fieldsets)
        if obj is None:
            return fieldsets
        config = self._SUBCLASS_CONFIG.get(obj.strategy_type)
        if not config:
            return fieldsets
        for extra_field in config.get("quantity_extra", []):
            for fs in fieldsets:
                if fs[0] == "Quantity":
                    fs[1]["fields"].append(extra_field)
                    break
        for i, extra_fs in enumerate(config.get("extra_fieldsets", []), start=1):
            fieldsets.insert(i, extra_fs)
        return fieldsets

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "wealth_group__community__livelihood_zone_baseline__livelihood_zone",
            "wealth_group__wealth_group_category",
            "wealth_group__livelihood_zone_baseline",
            "livelihood_strategy__livelihood_zone_baseline__livelihood_zone",
            "livelihood_strategy__product",
            "livelihood_strategy__season",
            "livelihood_zone_baseline__livelihood_zone__country",
        )

    def get_product_common_name(self, obj):
        if obj.livelihood_strategy.product:
            return obj.livelihood_strategy.product.common_name
        return None

    get_product_common_name.admin_order_field = "livelihood_strategy__product__common_name"
    get_product_common_name.short_description = "Product Common Name"

    def get_season_name(self, obj):
        if obj.livelihood_strategy.season:
            return obj.livelihood_strategy.season.name
        return None

    get_season_name.admin_order_field = "livelihood_strategy__season__name"
    get_season_name.short_description = "Season Name"

    def get_country_name(self, obj):
        return obj.livelihood_zone_baseline.livelihood_zone.country.name

    get_country_name.admin_order_field = "livelihood_zone_baseline__livelihood_zone__country__name"
    get_country_name.short_description = "Country Name"

    model = LivelihoodActivity
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "wealth_group",
                    "livelihood_strategy",
                    "scenario",
                    "extra",
                ]
            },
        ),
        (
            "Quantity",
            {
                "fields": [
                    "quantity_produced",
                    "quantity_purchased",
                    "quantity_consumed",
                    "quantity_sold",
                    "quantity_other_uses",
                ]
            },
        ),
        (
            "KCals",
            {
                "fields": [
                    "kcals_consumed",
                    "percentage_kcals",
                ],
            },
        ),
        (
            "Economy",
            {"fields": ["price", "income", "expenditure", "household_labor_provider"]},
        ),
    ]


class WealthGroupCharacteristicValueAdmin(admin.ModelAdmin):
    form = WealthGroupCharacteristicValueForm
    list_display = [
        "wealth_group",
        "get_wealth_characteristic_common_name",
        "get_wealth_group_category",
        "get_country_name",
        "product",
        "value",
    ]
    model = WealthGroupCharacteristicValue

    list_filter = (
        ("wealth_group__livelihood_zone_baseline", admin.RelatedOnlyFieldListFilter),
        "wealth_group__wealth_group_category",
        ("wealth_group__livelihood_zone_baseline__livelihood_zone__country", admin.RelatedOnlyFieldListFilter),
        WealthGroupSummaryValueListFilter,
        "wealth_characteristic__has_product",
        ("product", admin.RelatedOnlyFieldListFilter),
        "wealth_characteristic__has_unit_of_measure",
        ("unit_of_measure", admin.RelatedOnlyFieldListFilter),
    )

    search_fields = (
        "wealth_group__wealth_group_category__code__iexact",
        "wealth_group__wealth_group_category__aliases",
        "wealth_group__community__full_name",
        *translation_fields("wealth_characteristic__name"),
        "wealth_characteristic__aliases",
        *translation_fields("wealth_group__wealth_group_category__name"),
        "wealth_group__livelihood_zone_baseline__livelihood_zone__code",
        "wealth_group__livelihood_zone_baseline__livelihood_zone__alternate_code",
        *translation_fields("wealth_group__livelihood_zone_baseline__name"),
        "wealth_group__livelihood_zone_baseline__reference_year_end_date",
        "wealth_group__livelihood_zone_baseline__livelihood_zone__country__name",
        "product__cpc",
        *translation_fields("product__description"),
        *translation_fields("product__common_name"),
        "product__aliases",
    )

    def get_wealth_group_category(self, obj):
        return obj.wealth_group.wealth_group_category.name

    get_wealth_group_category.admin_order_field = "wealth_group__wealth_group_category__name_en"
    get_wealth_group_category.short_description = "Wealth group category"

    def get_country_name(self, obj):
        return obj.wealth_group.livelihood_zone_baseline.livelihood_zone.country.name

    get_country_name.admin_order_field = "wealth_group__livelihood_zone_baseline__livelihood_zone__country__name"
    get_country_name.short_description = "Country Name"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "wealth_group__livelihood_zone_baseline__livelihood_zone__country",
            "wealth_group__community__livelihood_zone_baseline__livelihood_zone",
            "wealth_group__wealth_group_category",
            "wealth_characteristic",
            "product",
            "unit_of_measure",
        )

    def get_wealth_characteristic_common_name(self, obj):
        return obj.wealth_characteristic.name

    get_wealth_characteristic_common_name.admin_order_field = "wealth_characteristic__name_en"
    get_wealth_characteristic_common_name.short_description = "Wealth characteristic name"


class LivelihoodActivityInlineAdmin(admin.StackedInline):
    model = LivelihoodActivity
    classes = ["collapse"]
    form = LivelihoodActivityForm
    extra = 0
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "livelihood_strategy",
                    "scenario",
                    "extra",
                ]
            },
        ),
        (
            "Quantity",
            {
                "fields": [
                    "quantity_produced",
                    "quantity_purchased",
                    "quantity_consumed",
                    "quantity_sold",
                    "quantity_other_uses",
                ]
            },
        ),
        (
            "KCals",
            {
                "fields": [
                    "kcals_consumed",
                    "percentage_kcals",
                ],
            },
        ),
        (
            "Economy",
            {"fields": ["price", "income", "expenditure", "household_labor_provider"]},
        ),
    ]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj=obj, **kwargs)
        base_form = formset.form

        class ExistingLivelihoodActivityForm(base_form):
            def __init__(self, *args, **inner_kwargs):
                super().__init__(*args, **inner_kwargs)
                if self.instance and self.instance.pk:
                    if "livelihood_strategy" in self.fields:
                        self.fields["livelihood_strategy"].disabled = True
                    if "scenario" in self.fields:
                        self.fields["scenario"].disabled = True

        formset.form = ExistingLivelihoodActivityForm
        return formset

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "livelihood_strategy__livelihood_zone_baseline",
                "livelihood_strategy__season",
                "wealth_group__livelihood_zone_baseline",
                "wealth_group__wealth_group_category",
            )
        )


class MilkProductionInlineAdmin(LivelihoodActivityInlineAdmin):
    model = MilkProduction
    form = MilkProductionForm

    def get_fieldsets(self, request, obj=None):
        fieldsets = deepcopy(super().get_fieldsets(request, obj))
        fieldsets[1][1]["fields"].append("quantity_butter_production")
        fieldsets.insert(
            1,
            (
                "Milk source",
                {
                    "fields": [
                        "milking_animals",
                        "lactation_days",
                        "daily_production",
                        "type_of_milk_consumed",
                        "type_of_milk_sold_or_other_uses",
                    ]
                },
            ),
        )
        return fieldsets

    def get_queryset(self, request):
        return super().get_queryset(request).filter(strategy_type=LivelihoodStrategyType.MILK_PRODUCTION)


class ButterProductionInlineAdmin(LivelihoodActivityInlineAdmin):
    model = ButterProduction

    def get_queryset(self, request):
        return super().get_queryset(request).filter(strategy_type=LivelihoodStrategyType.BUTTER_PRODUCTION)


class MeatProductionInlineAdmin(LivelihoodActivityInlineAdmin):
    model = MeatProduction

    def get_fieldsets(self, request, obj=None):
        fieldsets = deepcopy(super().get_fieldsets(request, obj))
        fieldsets.insert(
            1,
            (
                "Meat source",
                {
                    "fields": [
                        "animals_slaughtered",
                        "carcass_weight",
                    ]
                },
            ),
        )
        return fieldsets

    def get_queryset(self, request):
        return super().get_queryset(request).filter(strategy_type=LivelihoodStrategyType.MEAT_PRODUCTION)


class LivestockSaleInlineAdmin(LivelihoodActivityInlineAdmin):
    model = LivestockSale

    def get_queryset(self, request):
        return super().get_queryset(request).filter(strategy_type=LivelihoodStrategyType.LIVESTOCK_SALE)


class OtherLivestockProductionInlineAdmin(LivelihoodActivityInlineAdmin):
    model = OtherLivestockProduction

    def get_queryset(self, request):
        return super().get_queryset(request).filter(strategy_type=LivelihoodStrategyType.OTHER_LIVESTOCK_PRODUCTION)


class CropProductionInlineAdmin(LivelihoodActivityInlineAdmin):
    model = CropProduction

    def get_queryset(self, request):
        return super().get_queryset(request).filter(strategy_type=LivelihoodStrategyType.CROP_PRODUCTION)


class FoodPurchaseProductionInlineAdmin(LivelihoodActivityInlineAdmin):
    model = FoodPurchase
    form = FoodPurchaseForm

    def get_fieldsets(self, request, obj=None):
        fieldsets = deepcopy(super().get_fieldsets(request, obj))
        fieldsets.insert(
            1,
            (
                "Purchases",
                {
                    "fields": [
                        "unit_multiple",
                        "times_per_month",
                        "months_per_year",
                        "times_per_year",
                    ]
                },
            ),
        )
        return fieldsets

    def get_queryset(self, request):
        return super().get_queryset(request).filter(strategy_type=LivelihoodStrategyType.FOOD_PURCHASE)


class PaymentInKindInlineAdmin(LivelihoodActivityInlineAdmin):
    model = PaymentInKind
    autocomplete_fields = ("payment_product",)

    def get_fieldsets(self, request, obj=None):
        fieldsets = deepcopy(super().get_fieldsets(request, obj))
        fieldsets.insert(
            1,
            (
                "Payment",
                {
                    "fields": [
                        "payment_product",
                        "people_per_household",
                        "times_per_month",
                        "months_per_year",
                        "times_per_year",
                    ]
                },
            ),
        )
        return fieldsets

    def get_queryset(self, request):
        return super().get_queryset(request).filter(strategy_type=LivelihoodStrategyType.PAYMENT_IN_KIND)


class ReliefGiftOtherInlineAdmin(LivelihoodActivityInlineAdmin):
    model = ReliefGiftOther
    form = ReliefGiftOtherForm

    def get_fieldsets(self, request, obj=None):
        fieldsets = deepcopy(super().get_fieldsets(request, obj))
        fieldsets.insert(
            1,
            (
                "Relief",
                {
                    "fields": [
                        "unit_multiple",
                        "times_per_month",
                        "months_per_year",
                        "times_per_year",
                    ]
                },
            ),
        )
        return fieldsets

    def get_queryset(self, request):
        return super().get_queryset(request).filter(strategy_type=LivelihoodStrategyType.RELIEF_GIFT_OTHER)


class OtherCashIncomeInlineAdmin(LivelihoodActivityInlineAdmin):
    model = OtherCashIncome

    def get_fieldsets(self, request, obj=None):
        fieldsets = deepcopy(super().get_fieldsets(request, obj))
        fieldsets.insert(
            1,
            (
                None,
                {
                    "fields": [
                        "people_per_household",
                        "times_per_month",
                        "months_per_year",
                        "times_per_year",
                    ]
                },
            ),
        )
        return fieldsets

    def get_queryset(self, request):
        return super().get_queryset(request).filter(strategy_type=LivelihoodStrategyType.OTHER_CASH_INCOME)


class HuntingInlineAdmin(LivelihoodActivityInlineAdmin):
    model = Hunting

    def get_queryset(self, request):
        return super().get_queryset(request).filter(strategy_type=LivelihoodStrategyType.HUNTING)


class FishingInlineAdmin(LivelihoodActivityInlineAdmin):
    model = Fishing

    def get_queryset(self, request):
        return super().get_queryset(request).filter(strategy_type=LivelihoodStrategyType.FISHING)


class WildFoodGatheringInlineAdmin(LivelihoodActivityInlineAdmin):
    model = WildFoodGathering

    def get_queryset(self, request):
        return super().get_queryset(request).filter(strategy_type=LivelihoodStrategyType.WILD_FOOD_GATHERING)


class OtherPurchaseInlineAdmin(LivelihoodActivityInlineAdmin):
    model = OtherPurchase
    form = OtherPurchaseForm

    def get_fieldsets(self, request, obj=None):
        fieldsets = deepcopy(super().get_fieldsets(request, obj))
        fieldsets.insert(
            1,
            (
                None,
                {
                    "fields": [
                        "unit_multiple",
                        "times_per_month",
                        "months_per_year",
                        "times_per_year",
                    ]
                },
            ),
        )
        return fieldsets

    def get_queryset(self, request):
        return super().get_queryset(request).filter(strategy_type=LivelihoodStrategyType.OTHER_PURCHASE)


class CommunityRelatedOnlyFieldListFilter(admin.RelatedOnlyFieldListFilter):
    """
    RelatedOnlyFieldListFilter for Community that prefetches livelihood_zone_baseline__livelihood_zone.
    To avoid the current excess repeated queries executed due to str(community)
    """

    def field_choices(self, field, request, model_admin):
        pk_qs = model_admin.get_queryset(request).distinct().values_list("%s__pk" % self.field_path, flat=True)
        ordering = self.field_admin_ordering(field, request, model_admin)
        return [
            (community.pk, str(community))
            for community in Community.objects.filter(pk__in=pk_qs)
            .select_related("livelihood_zone_baseline__livelihood_zone")
            .order_by(*ordering)
        ]


class WealthGroupAdmin(admin.ModelAdmin):
    form = WealthGroupForm
    fields = (
        "livelihood_zone_baseline",
        "community",
        "wealth_group_category",
        "average_household_size",
        "percentage_of_households",
        "percentage_of_population",
        "population_source",
        "population_estimate",
        "household_annual_kcals_cost",
        "survival_threshold_as_percentage_kcals",
        "survival_threshold_as_cash",
        "livelihoods_protection_threshold_as_percentage_kcals",
        "livelihoods_protection_threshold_as_cash",
    )
    list_display = (
        "livelihood_zone_baseline",
        "community",
        "wealth_group_category",
        "percentage_of_households",
    )
    readonly_fields = (
        "household_annual_kcals_cost",
        "survival_threshold_as_percentage_kcals",
        "survival_threshold_as_cash",
        "livelihoods_protection_threshold_as_percentage_kcals",
        "livelihoods_protection_threshold_as_cash",
        "population_source",
        "percentage_of_population",
        "population_estimate",
    )
    search_fields = (
        "community__full_name",
        "livelihood_zone_baseline__livelihood_zone__code",
        "livelihood_zone_baseline__livelihood_zone__alternate_code",
        *translation_fields("livelihood_zone_baseline__name"),
        "livelihood_zone_baseline__reference_year_end_date",
        "wealth_group_category__code__iexact",
        *translation_fields("wealth_group_category__name"),
    )
    list_filter = (
        "wealth_group_category",
        SummaryValueListFilter,
        "livelihood_zone_baseline__source_organization",
        ("livelihood_zone_baseline__livelihood_zone__country", admin.RelatedOnlyFieldListFilter),
    )
    inlines = [
        WealthGroupCharacteristicValueInlineAdmin,
    ] + [child for child in LivelihoodActivityInlineAdmin.__subclasses__()]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "community__livelihood_zone_baseline__livelihood_zone",
                "wealth_group_category",
                "livelihood_zone_baseline",
            )
            .prefetch_related("livelihoodactivity_set")
        )

    @admin.display(description=_("Population source"))
    def population_source(self, instance):
        return instance.livelihood_zone_baseline.population_source

    def _get_percentage_of_population(self, instance):
        if instance.percentage_of_households is None or instance.average_household_size is None:
            return None

        baseline_wealth_groups = WealthGroup.objects.filter(
            livelihood_zone_baseline=instance.livelihood_zone_baseline,
            community__isnull=True,
            percentage_of_households__isnull=False,
            percentage_of_households__gt=0,
            average_household_size__isnull=False,
        )

        total_percentage_of_households = 0
        weighted_total_household_size = 0
        for wealth_group in baseline_wealth_groups:
            total_percentage_of_households += wealth_group.percentage_of_households
            weighted_total_household_size += (
                wealth_group.percentage_of_households * wealth_group.average_household_size
            )

        if not total_percentage_of_households or not weighted_total_household_size:
            return None

        baseline_weighted_average_household_size = weighted_total_household_size / total_percentage_of_households
        return (
            instance.percentage_of_households
            * instance.average_household_size
            / baseline_weighted_average_household_size
        )

    @admin.display(description=_("Percentage of population"))
    def percentage_of_population(self, instance):
        return self._get_percentage_of_population(instance)

    @admin.display(description=_("Population estimate"))
    def population_estimate(self, instance):
        percentage_of_population = self._get_percentage_of_population(instance)
        if instance.livelihood_zone_baseline.population_estimate is None or percentage_of_population is None:
            return None
        return round(instance.livelihood_zone_baseline.population_estimate * percentage_of_population)


class LivelihoodProductCategoryAdmin(admin.ModelAdmin):
    fields = (
        "baseline_livelihood_activity",
        "basket",
        "percentage_allocation_to_basket",
    )
    list_display = (
        "baseline_livelihood_activity",
        "basket",
        "percentage_allocation_to_basket",
    )
    search_fields = (
        "baseline_livelihood_activity__livelihood_zone_baseline__livelihood_zone__code",
        "baseline_livelihood_activity__livelihood_zone_baseline__livelihood_zone__alternate_code",
        "baseline_livelihood_activity__wealth_group__wealth_group_category__code",
        "baseline_livelihood_activity__livelihood_strategy__product__cpc",
    )
    list_filter = (
        "baseline_livelihood_activity__wealth_group__wealth_group_category__code",
        "basket",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "baseline_livelihood_activity__livelihood_zone_baseline__livelihood_zone",
            "baseline_livelihood_activity__wealth_group__wealth_group_category",
            "baseline_livelihood_activity__livelihood_strategy__season",
            "baseline_livelihood_activity__livelihood_strategy__livelihood_zone_baseline",
        )


class SeasonalActivityAdmin(admin.ModelAdmin):
    fields = (
        "livelihood_zone_baseline",
        "seasonal_activity_type",
        "season",
        "product",
        "additional_identifier",
        "is_key",
    )
    list_display = (
        "livelihood_zone_baseline",
        "seasonal_activity_type",
        "product",
        "is_key",
    )
    search_fields = (
        "livelihood_zone_baseline__livelihood_zone__code",
        "livelihood_zone_baseline__livelihood_zone__alternate_code",
        *translation_fields("livelihood_zone_baseline__name"),
        "livelihood_zone_baseline__reference_year_end_date",
        "seasonal_activity_type__code",
        *translation_fields("seasonal_activity_type__name"),
        *translation_fields("season__name"),
        "season__aliases",
        "product__cpc__iexact",
        *translation_fields("product__description"),
        *translation_fields("product__common_name"),
        "product__aliases",
        "additional_identifier",
    )
    list_filter = (
        "seasonal_activity_type",
        ("season", admin.RelatedOnlyFieldListFilter),
        ("product", admin.RelatedOnlyFieldListFilter),
        "is_key",
    )

    def get_search_results(self, request, queryset, search_term):
        # Allow natural key format "BF01: 2011-10-31" by stripping the colon separator.
        normalized = search_term.replace(":", "")
        date_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", normalized)
        year_match = re.search(r"\b(\d{4})\b", normalized)
        text_term = re.sub(r"\b\d{4}(?:-\d{2}-\d{2})?\b", "", normalized).strip()
        queryset, use_distinct = super().get_search_results(request, queryset, text_term)
        if date_match:
            queryset = queryset.filter(livelihood_zone_baseline__reference_year_end_date=date_match.group(1))
        elif year_match:
            queryset = queryset.filter(
                livelihood_zone_baseline__reference_year_end_date__year=int(year_match.group(1))
            )
        return queryset, use_distinct


class SeasonalActivityOccurrenceAdmin(admin.ModelAdmin):
    list_display = (
        "seasonal_activity",
        "community",
        "seasonal_activity_is_key",
        "start_month",
        "end_month",
    )
    search_fields = (
        "community__full_name",
        "seasonal_activity__livelihood_zone_baseline__livelihood_zone__code",
        "seasonal_activity__livelihood_zone_baseline__livelihood_zone__alternate_code",
        *translation_fields("seasonal_activity__livelihood_zone_baseline__name"),
        "seasonal_activity__livelihood_zone_baseline__reference_year_end_date",
        "seasonal_activity__seasonal_activity_type__code",
        *translation_fields("seasonal_activity__seasonal_activity_type__name"),
        *translation_fields("seasonal_activity__season__name"),
        "seasonal_activity__product__cpc__iexact",
        *translation_fields("seasonal_activity__product__description"),
        *translation_fields("seasonal_activity__product__common_name"),
        "seasonal_activity__season__aliases",
        "seasonal_activity__additional_identifier",
    )
    list_filter = (
        "seasonal_activity__seasonal_activity_type",
        ("seasonal_activity__season", admin.RelatedOnlyFieldListFilter),
        ("seasonal_activity__product", admin.RelatedOnlyFieldListFilter),
    )
    ordering = ["start"]

    def get_search_results(self, request, queryset, search_term):
        # Allow natural key format "BF01: 2011-10-31" by stripping the colon separator.
        normalized = search_term.replace(":", "")
        date_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", normalized)
        year_match = re.search(r"\b(\d{4})\b", normalized)
        text_term = re.sub(r"\b\d{4}(?:-\d{2}-\d{2})?\b", "", normalized).strip()
        queryset, use_distinct = super().get_search_results(request, queryset, text_term)
        if date_match:
            queryset = queryset.filter(
                seasonal_activity__livelihood_zone_baseline__reference_year_end_date=date_match.group(1)
            )
        elif year_match:
            queryset = queryset.filter(
                seasonal_activity__livelihood_zone_baseline__reference_year_end_date__year=int(year_match.group(1))
            )
        return queryset, use_distinct

    @admin.display(boolean=True, description="Key seasonal activity")
    def seasonal_activity_is_key(self, obj):
        return obj.seasonal_activity.is_key


class CommunityCropProductionAdmin(admin.ModelAdmin):
    fields = (
        "community",
        "crop",
        "crop_purpose",
        "season",
        "yield_with_inputs",
        "yield_without_inputs",
        "seed_requirement",
        "crop_unit_of_measure",
        "land_unit_of_measure",
    )
    list_display = (
        "community",
        "crop",
        "season",
        "yield_with_inputs",
        "yield_without_inputs",
        "crop_unit_of_measure",
        "land_unit_of_measure",
    )
    search_fields = (
        "community__full_name",
        "community__livelihood_zone_baseline__livelihood_zone__code",
        "community__livelihood_zone_baseline__livelihood_zone__alternate_code",
        *translation_fields("community__livelihood_zone_baseline__name"),
        "community__livelihood_zone_baseline__reference_year_end_date",
        "crop__cpc__iexact",
        *translation_fields("crop__description"),
        *translation_fields("crop__common_name"),
        "crop__aliases",
        "crop_purpose",
        *translation_fields("season__name"),
        "season__aliases",
    )

    list_filter = (
        "community__livelihood_zone_baseline__livelihood_zone",
        "crop",
        "season",
    )


class CommunityLivestockAdmin(admin.ModelAdmin):
    fields = (
        "community",
        "livestock",
        "birth_interval",
        "wet_season_lactation_period",
        "wet_season_milk_production",
        "dry_season_lactation_period",
        "dry_season_milk_production",
        "age_at_sale",
        "additional_attributes",
    )
    list_display = (
        "community",
        "livestock",
        "wet_season_milk_production",
        "dry_season_milk_production",
    )
    search_fields = (
        "community__full_name",
        "community__livelihood_zone_baseline__livelihood_zone__code",
        "community__livelihood_zone_baseline__livelihood_zone__alternate_code",
        *translation_fields("community__livelihood_zone_baseline__name"),
        "community__livelihood_zone_baseline__reference_year_end_date",
        "livestock__cpc__iexact",
        *translation_fields("livestock__description"),
        *translation_fields("livestock__common_name"),
        "livestock__aliases",
    )
    list_filter = (
        "community__livelihood_zone_baseline__livelihood_zone",
        "livestock",
    )


class MarketPriceAdmin(admin.ModelAdmin):
    fields = (
        "community",
        "product",
        "currency",
        "market",
        "description",
        "low_price",
        "low_price_start",
        "low_price_end",
        "high_price",
        "high_price_start",
        "high_price_end",
        "unit_of_measure",
    )
    list_display = (
        "community",
        "product",
        "unit_of_measure",
        "market",
        "low_price",
        "low_price_start_month",
        "low_price_end_month",
        "high_price_start_month",
        "high_price_end_month",
        "high_price",
        "currency",
    )
    search_fields = (
        "community__full_name",
        "community__livelihood_zone_baseline__livelihood_zone__code",
        "community__livelihood_zone_baseline__livelihood_zone__alternate_code",
        *translation_fields("community__livelihood_zone_baseline__name"),
        "community__livelihood_zone_baseline__reference_year_end_date",
        "product__cpc__iexact",
        *translation_fields("product__description"),
        *translation_fields("product__common_name"),
        "product__aliases",
        "market__code__iexact",
        *translation_fields("market__full_name"),
        "market__aliases",
        "description",
    )
    list_filter = (
        "market",
        "community__livelihood_zone_baseline__livelihood_zone",
        "product",
    )


class HazardAdmin(admin.ModelAdmin):
    fields = (
        "community",
        "chronic_or_periodic",
        "ranking",
        "hazard_category",
        "description",
    )
    list_display = (
        "community",
        "chronic_or_periodic",
        "ranking",
        "hazard_category",
    )
    search_fields = (
        "community__full_name",
        "community__livelihood_zone_baseline__livelihood_zone__code",
        "community__livelihood_zone_baseline__livelihood_zone__alternate_code",
        *translation_fields("community__livelihood_zone_baseline__name"),
        "community__livelihood_zone_baseline__reference_year_end_date",
        "chronic_or_periodic",
        "hazard_category__code__iexact",
        *translation_fields("hazard_category__name"),
        "hazard_category__aliases",
        "description",
    )
    list_filter = (
        "hazard_category",
        "chronic_or_periodic",
        "community__livelihood_zone_baseline__livelihood_zone",
    )


class SeasonalProductionPerformanceAdmin(admin.ModelAdmin):
    fields = (
        "community",
        "performance_year_start_date",
        "performance_year_end_date",
        "seasonal_performance",
    )
    list_display = (
        "community",
        "performance_year_start_date",
        "performance_year_end_date",
        "seasonal_performance",
    )
    search_fields = (
        "community__full_name",
        "community__livelihood_zone_baseline__livelihood_zone__code",
        "community__livelihood_zone_baseline__livelihood_zone__alternate_code",
        *translation_fields("community__livelihood_zone_baseline__name"),
        "community__livelihood_zone_baseline__reference_year_end_date",
        "performance_year_start_date",
        "performance_year_end_date",
        "seasonal_performance",
        "description",
    )
    list_filter = ("community__livelihood_zone_baseline__livelihood_zone",)


class EventAdmin(admin.ModelAdmin):
    fields = (
        "community",
        "event_year_start_date",
        "event_year_end_date",
        "description",
    )
    list_display = (
        "community",
        "event_year_start_date",
        "event_year_end_date",
        "description",
    )
    search_fields = (
        "community__full_name",
        "community__livelihood_zone_baseline__livelihood_zone__code",
        "community__livelihood_zone_baseline__livelihood_zone__alternate_code",
        *translation_fields("community__livelihood_zone_baseline__name"),
        "community__livelihood_zone_baseline__reference_year_end_date",
        "description",
    )
    list_filter = ("community__livelihood_zone_baseline__livelihood_zone",)


class ExpandabilityFactorAdmin(admin.ModelAdmin):
    fields = (
        "livelihood_strategy",
        "wealth_group",
        "percentage_produced",
        "percentage_sold",
        "percentage_other_uses",
        "percentage_consumed",
        "percentage_income",
        "percentage_expenditure",
        "remark",
    )
    list_display = (
        "livelihood_strategy",
        "wealth_group",
        "percentage_produced",
        "percentage_sold",
        "percentage_other_uses",
        "percentage_consumed",
        "percentage_income",
        "percentage_expenditure",
    )
    search_fields = (
        "livelihood_strategy__strategy_type",
        "livelihood_strategy__additional_identifier",
        "livelihood_strategy__product__cpc__iexact",
        "livelihood_strategy__product__aliases",
        *translation_fields("livelihood_strategy__product__common_name"),
        *translation_fields("livelihood_strategy__product__description"),
        "livelihood_strategy__season__aliases",
        *translation_fields("livelihood_strategy__season__name"),
        "wealth_group__wealth_group_category__code__iexact",
        *translation_fields("wealth_group__wealth_group_category__name"),
        "wealth_group__livelihood_zone_baseline__livelihood_zone__code",
        "wealth_group__livelihood_zone_baseline__livelihood_zone__alternate_code",
        *translation_fields("wealth_group__livelihood_zone_baseline__name"),
        "wealth_group__livelihood_zone_baseline__reference_year_end_date",
        "remark",
    )
    list_filter = (
        "livelihood_strategy",
        "wealth_group",
    )


class CopingStrategyAdmin(admin.ModelAdmin):
    fields = (
        "community",
        "leaders",
        "wealth_group",
        "livelihood_strategy",
        "strategy",
        "by_value",
    )
    list_display = (
        "community",
        "leaders",
        "wealth_group",
        "livelihood_strategy",
        "strategy",
        "by_value",
    )
    search_fields = (
        "community__full_name",
        "livelihood_strategy__strategy_type",
        "livelihood_strategy__additional_identifier",
        "livelihood_strategy__product__cpc__iexact",
        *translation_fields("livelihood_strategy__product__description"),
        *translation_fields("livelihood_strategy__product__common_name"),
        "livelihood_strategy__product__aliases",
        "livelihood_strategy__season__aliases",
        *translation_fields("livelihood_strategy__season__name"),
        "wealth_group__wealth_group_category__code__iexact",
        *translation_fields("wealth_group__wealth_group_category__name"),
        "wealth_group__livelihood_zone_baseline__livelihood_zone__code",
        "wealth_group__livelihood_zone_baseline__livelihood_zone__alternate_code",
        *translation_fields("wealth_group__livelihood_zone_baseline__name"),
        "wealth_group__livelihood_zone_baseline__reference_year_end_date",
    )
    list_filter = (
        "livelihood_strategy",
        "wealth_group",
    )


admin.site.register(SourceOrganization, SourceOrganizationAdmin)
admin.site.register(LivelihoodZone, LivelihoodZoneAdmin)
admin.site.register(LivelihoodZoneBaseline, LivelihoodZoneBaselineAdmin)
admin.site.register(LivelihoodZoneBaselineCorrection, LivelihoodZoneBaselineCorrectionAdmin)
admin.site.register(Community, CommunityAdmin)
admin.site.register(LivelihoodStrategy, LivelihoodStrategyAdmin)
admin.site.register(KeyParameter, KeyParameterAdmin)
admin.site.register(WealthGroup, WealthGroupAdmin)

admin.site.register(CommunityCropProduction, CommunityCropProductionAdmin)
admin.site.register(CommunityLivestock, CommunityLivestockAdmin)

admin.site.register(MarketPrice, MarketPriceAdmin)
admin.site.register(Hazard, HazardAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(ExpandabilityFactor, ExpandabilityFactorAdmin)
admin.site.register(CopingStrategy, CopingStrategyAdmin)

admin.site.register(LivelihoodProductCategory, LivelihoodProductCategoryAdmin)
admin.site.register(SeasonalActivity, SeasonalActivityAdmin)
admin.site.register(SeasonalActivityOccurrence, SeasonalActivityOccurrenceAdmin)
admin.site.register(SeasonalProductionPerformance, SeasonalProductionPerformanceAdmin)

admin.site.register(LivelihoodActivity, LivelihoodActivityAdmin)
admin.site.register(WealthGroupCharacteristicValue, WealthGroupCharacteristicValueAdmin)
