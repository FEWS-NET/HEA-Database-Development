from django.contrib import admin

from common.admin import GeoModelAdmin

from .forms import LivelihoodActivityForm
from .models import (
    ButterProduction,
    Community,
    CommunityCropProduction,
    CommunityLivestock,
    CropProduction,
    Fishing,
    FoodPurchase,
    Hazard,
    LivelihoodActivity,
    LivelihoodStrategy,
    LivelihoodZone,
    LivelihoodZoneBaseline,
    LivestockSales,
    Market,
    MarketPrice,
    MeatProduction,
    MilkProduction,
    OtherCashIncome,
    OtherPurchases,
    PaymentInKind,
    ReliefGiftsOther,
    SeasonalActivity,
    SeasonalActivityOccurrence,
    SourceOrganization,
    WealthGroup,
    WealthGroupCharacteristicValue,
    WildFoodGathering,
)

admin.site.site_header = "HEA Baseline Database Administration"
admin.site.index_title = "HEA Baseline"


class SourceOrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "full_name")
    search_fields = ["name", "full_name", "description"]


class LivelihoodZoneAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "country")
    search_fields = ["code", "name", "description", "country"]
    list_filter = ("country",)


class LivelihoodZoneBaselineAdmin(GeoModelAdmin):
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "livelihood_zone",
                    "main_livelihood_category",
                    "source_organization",
                    "bss",
                    "reference_year_start_date",
                    "reference_year_end_date",
                    "valid_from_date",
                    "valid_to_date",
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
                ],
            },
        ),
    ]
    list_display = (
        "livelihood_zone",
        "main_livelihood_category",
        "source_organization",
        "reference_year_start_date",
        "reference_year_end_date",
    )
    search_fields = [
        "livelihood_zone",
        "main_livelihood_category",
        "source_organization",
    ]
    list_filter = [
        "source_organization",
        "livelihood_zone__country",
    ]
    date_hierarchy = "reference_year_start_date"


class CommunityAdmin(GeoModelAdmin):
    fields = ("name", "livelihood_zone_baseline", "interview_number", "interviewers", "geography")
    list_display = (
        "name",
        "livelihood_zone_baseline",
    )
    search_fields = ("name", "livelihood_zone_baseline")
    list_filter = (
        "livelihood_zone_baseline__livelihood_zone__name",
        "livelihood_zone_baseline__livelihood_zone__country",
    )


class LivelihoodStrategyAdmin(admin.ModelAdmin):
    fields = (
        "livelihood_zone_baseline",
        "strategy_type",
        "season",
        "product",
        "unit_of_measure",
        "household_labor_provider",
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
    search_fields = ("strategy_type", "livelihood_zone_baseline", "product")
    list_filter = (
        "strategy_type",
        "livelihood_zone_baseline__livelihood_zone__name",
        "livelihood_zone_baseline__livelihood_zone__country",
    )


class WealthGroupCharacteristicValueInlineAdmin(admin.TabularInline):
    fields = ["wealth_characteristic", "value", "min_value", "max_value"]
    model = WealthGroupCharacteristicValue
    extra = 1
    classes = ["collapse"]

    def get_extra(self, request, obj=None, **kwargs):
        extra = super().get_extra(request, obj, **kwargs)
        if extra:
            self.verbose_name_plural = "Wealth characteristics"
        return extra


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
                ]
            },
        ),
        (
            "Quantity",
            {
                "fields": [
                    "quantity_produced",
                    "quantity_consumed",
                    "quantity_sold",
                    "quantity_other_uses",
                ]
            },
        ),
        (
            "KCals",
            {
                "classes": ["collapse", "extrapretty"],
                "fields": [
                    "kcals_consumed",
                    "percentage_kcals",
                ],
            },
        ),
        ("Economy", {"fields": ["price", "income", "expenditure"]}),
    ]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


class MilkProductionInlineAdmin(LivelihoodActivityInlineAdmin):
    model = MilkProduction

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj).copy()
        fieldsets.insert(
            1,
            (
                "Milk source",
                {
                    "fields": [
                        "milking_animals",
                        "lactation_days",
                        "daily_production",
                        "type_of_milk_sold_or_other_uses",
                    ]
                },
            ),
        )
        return fieldsets


class ButterProductionInlineAdmin(LivelihoodActivityInlineAdmin):
    model = ButterProduction


class MeatProductionInlineAdmin(LivelihoodActivityInlineAdmin):
    model = MeatProduction

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj).copy()
        fieldsets.insert(1, ("Meat source", {"fields": ["animals_slaughtered", "carcass_weight"]}))
        return fieldsets


class LivestockSalesInlineAdmin(LivelihoodActivityInlineAdmin):
    model = LivestockSales


class CropProductionInlineAdmin(LivelihoodActivityInlineAdmin):
    model = CropProduction


class FoodPurchaseProductionInlineAdmin(LivelihoodActivityInlineAdmin):
    model = FoodPurchase

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj).copy()
        fieldsets.insert(1, ("Purchases", {"fields": ["unit_multiple", "purchases_per_month", "months_per_year"]}))
        return fieldsets


class PaymentInKindInlineAdmin(LivelihoodActivityInlineAdmin):
    model = PaymentInKind

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj).copy()
        fieldsets.insert(1, ("Payment", {"fields": ["people_per_hh", "labor_per_month", "months_per_year"]}))
        return fieldsets


class ReliefGiftsInlineAdmin(LivelihoodActivityInlineAdmin):
    model = ReliefGiftsOther

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj).copy()
        fieldsets.insert(1, ("Relief", {"fields": ["unit_multiple", "received_per_year"]}))
        return fieldsets


class OtherCashIncomeInlineAdmin(LivelihoodActivityInlineAdmin):
    model = OtherCashIncome

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj).copy()
        fieldsets.insert(
            1, (None, {"fields": ["people_per_hh", "labor_per_month", "months_per_year", "times_per_year"]})
        )
        return fieldsets


class FishingInlineAdmin(LivelihoodActivityInlineAdmin):
    model = Fishing


class WildFoodGatheringInlineAdmin(LivelihoodActivityInlineAdmin):
    model = WildFoodGathering


class OtherPurchasesAdmin(LivelihoodActivityInlineAdmin):
    model = OtherPurchases

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj).copy()
        fieldsets.insert(1, (None, {"fields": ["unit_multiple", "purchases_per_month", "months_per_year"]}))
        return fieldsets


class WealthGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "community", "wealth_category", "percentage_of_households")
    search_fields = ("name", "community__name", "wealth_category")
    list_filter = (
        "livelihood_zone_baseline__source_organization",
        "livelihood_zone_baseline__livelihood_zone__country",
        "livelihood_zone_baseline__livelihood_zone__name",
        "community",
        "wealth_category",
    )
    inlines = [
        WealthGroupCharacteristicValueInlineAdmin,
    ] + [child for child in LivelihoodActivityInlineAdmin.__subclasses__()]

    def get_queryset(self, request):
        queryset = super().get_queryset(request).prefetch_related("livelihoodactivity_set")
        return queryset


class SeasonalActivityTypeAdmin(admin.ModelAdmin):
    fields = ("name", "activity_category")
    list_display = ("name", "activity_category")
    search_fields = ("name", "activity_category")


class SeasonalActivityAdmin(admin.ModelAdmin):
    fields = ("livelihood_zone_baseline", "activity_type", "season", "product")
    list_display = ("livelihood_zone_baseline", "activity_type", "season", "product")
    search_fields = ("activity_type", "season", "product")
    list_filter = ("livelihood_zone_baseline__livelihood_zone", "activity_type", "season", "product")


class SeasonalActivityOccurrenceAdmin(admin.ModelAdmin):
    list_display = ("seasonal_activity", "community", "start_month", "end_month")
    search_fields = ("seasonal_activity__activity_type", "seasonal_activity__season", "seasonal_activity__product")
    list_filter = (
        "community",
        "seasonal_activity__activity_type",
        "seasonal_activity__season",
        "seasonal_activity__product",
    )
    ordering = ["start"]


class CommunityCropProductionAdmin(admin.ModelAdmin):
    fields = (
        "community",
        "crop_type",
        "crop_purpose",
        "season",
        "yield_with_inputs",
        "yield_without_inputs",
        "seed_requirement",
        "unit_of_land",
    )
    list_display = (
        "community",
        "crop_type",
        "season",
        "yield_with_inputs",
        "yield_without_inputs",
        "unit_of_land",
    )
    search_fields = (
        "crop_type",
        "crop_purpose",
        "season",
    )
    list_filter = (
        "community__livelihood_zone_baseline__livelihood_zone",
        "community",
        "crop_type",
        "season",
    )


class CommunityLivestockAdmin(admin.ModelAdmin):
    fields = (
        "community",
        "livestock_type",
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
        "livestock_type",
        "wet_season_milk_production",
        "dry_season_milk_production",
    )
    search_fields = ("livestock_type",)
    list_filter = (
        "community__livelihood_zone_baseline__livelihood_zone",
        "community",
        "livestock_type",
    )


class MarketAdmin(admin.ModelAdmin):
    fields = (
        "name",
        "community",
    )
    list_display = (
        "name",
        "community",
    )
    search_fields = (
        "name",
        "community",
    )
    list_filter = (
        "community",
        "community__livelihood_zone_baseline__livelihood_zone",
    )


class MarketPriceAdmin(admin.ModelAdmin):
    fields = (
        "community",
        "product",
        "market",
        "low_price",
        "low_price_month",
        "high_price",
        "high_price_month",
        "unit_of_measure",
    )
    list_display = (
        "community",
        "product",
        "market",
        "low_price",
        "low_price_month",
        "high_price",
        "high_price_month",
        "unit_of_measure",
    )
    search_fields = (
        "community",
        "product",
        "market",
    )
    list_filter = (
        "community",
        "market",
        "community__livelihood_zone_baseline__livelihood_zone",
        "product",
    )


class HazardAdmin(admin.ModelAdmin):
    fields = ("community", "hazard_category", "is_chronic", "year", "seasonal_performance", "event", "response")
    list_display = (
        "community",
        "hazard_category",
        "is_chronic",
        "year",
    )
    search_fields = (
        "community",
        "hazard_category",
    )
    list_filter = (
        "community",
        "hazard_category",
        "community__livelihood_zone_baseline__livelihood_zone",
    )


admin.site.register(SourceOrganization, SourceOrganizationAdmin)
admin.site.register(LivelihoodZone, LivelihoodZoneAdmin)
admin.site.register(LivelihoodZoneBaseline, LivelihoodZoneBaselineAdmin)
admin.site.register(Community, CommunityAdmin)
admin.site.register(LivelihoodStrategy, LivelihoodStrategyAdmin)
admin.site.register(WealthGroup, WealthGroupAdmin)

admin.site.register(CommunityCropProduction, CommunityCropProductionAdmin)
admin.site.register(CommunityLivestock, CommunityLivestockAdmin)

admin.site.register(Market, MarketAdmin)
admin.site.register(MarketPrice, MarketPriceAdmin)
admin.site.register(Hazard, HazardAdmin)

admin.site.register(SeasonalActivity, SeasonalActivityAdmin)
admin.site.register(SeasonalActivityOccurrence, SeasonalActivityOccurrenceAdmin)
