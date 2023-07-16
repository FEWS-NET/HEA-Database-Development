from django.contrib import admin

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
    LivelihoodStrategy,
    LivelihoodZone,
    LivelihoodZoneBaseline,
    LivestockSales,
    Market,
    MarketPrice,
    MeatProduction,
    MilkProduction,
    OtherCashIncome,
    PaymentInKind,
    Season,
    SeasonalActivity,
    SeasonalActivityType,
    SourceOrganization,
    WealthGroup,
    WealthGroupCharacteristicValue,
    WildFoodGathering,
    ReliefGiftsOther,
    OtherPurchases,
    LivelihoodActivity,
)
from common.admin import GeoModelAdmin

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
    list_filter = (
        "source_organization",
        "livelihood_zone__country",
    )
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

    fields = ("livelihood_zone_baseline", "strategy_type", "season", "product", "additional_identifier")
    list_display = ("livelihood_zone_baseline", "strategy_type", "season", "product")
    search_fields = ("strategy_type", "livelihood_zone_baseline", "product")
    list_filter = (
        "strategy_type",
        "livelihood_zone_baseline__livelihood_zone__name",
        "livelihood_zone_baseline__livelihood_zone__country",
    )


class WealthGroupCharacteristicValueInlineAdmin(admin.TabularInline):
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
    extra = 1
    fieldsets = [
        (
            None,
            {
                "fields": [
                    "livelihood_strategy",
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
                    "unit_of_measure",
                ]
            },
        ),
        (
            "KCals",
            {
                # "classes": ["collapse", "extrapretty"],
                "fields": [
                    "total_kcals_consumed",
                    "percentage_kcals",
                ],
            },
        ),
        ("Economy", {"fields": ["price", "currency", "income", "expenditure"]}),
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
        fieldsets.insert(1, ("Meat source", {"fields": ["animals_slaughtered", "item_yield"]}))
        return fieldsets


class LivestockSalesInlineAdmin(LivelihoodActivityInlineAdmin):
    model = LivestockSales

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj).copy()
        fieldsets.insert(1, ("Livestock", {"fields": ["product_destination", "animals_sold"]}))
        return fieldsets


class CropProductionInlineAdmin(LivelihoodActivityInlineAdmin):
    model = CropProduction

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj).copy()
        fieldsets.insert(1, ("Crop", {"fields": ["production_system"]}))
        return fieldsets


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
        "livelihood_zone_baseline__livelihood_zone",
        "wealth_category",
    )
    inlines = [
        WealthGroupCharacteristicValueInlineAdmin,
    ] + [child for child in LivelihoodActivityInlineAdmin.__subclasses__()]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


@admin.register(SeasonalActivityType)
class SeasonalActivityTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    pass


@admin.register(SeasonalActivity)
class SeasonalActivityAdmin(admin.ModelAdmin):
    pass


@admin.register(CommunityCropProduction)
class CommunityCropProductionAdmin(admin.ModelAdmin):
    pass


@admin.register(CommunityLivestock)
class CommunityLivestockAdmin(admin.ModelAdmin):
    pass


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    pass


@admin.register(MarketPrice)
class MarketPriceAdmin(admin.ModelAdmin):
    pass


@admin.register(Hazard)
class HazardAdmin(admin.ModelAdmin):
    pass


admin.site.register(SourceOrganization, SourceOrganizationAdmin)
admin.site.register(LivelihoodZone, LivelihoodZoneAdmin)
admin.site.register(LivelihoodZoneBaseline, LivelihoodZoneBaselineAdmin)
admin.site.register(Community, CommunityAdmin)
admin.site.register(LivelihoodStrategy, LivelihoodStrategyAdmin)
admin.site.register(WealthGroup, WealthGroupAdmin)
# admin.site.register(WealthGroupCharacteristicValue, WealthGroupCharacteristicValueAdmin)

# admin.site.register(MilkProduction, MilkProductionAdmin)
# admin.site.register(ButterProduction, ButterProductionAdmin)
# admin.site.register(MeatProduction, MeatProductionAdmin)
# admin.site.register(LivestockSales, LivestockSalesAdmin)
# admin.site.register(CropProduction, CropProductionAdmin)
# admin.site.register(FoodPurchase, FoodPurchaseProductionAdmin)
#
# admin.site.register(PaymentInKind, PaymentInKindAdmin)
# admin.site.register(ReliefGiftsOther, ReliefGiftsAdmin)
# admin.site.register(Fishing, FishingAdmin)
# admin.site.register(WildFoodGathering, WildFoodGatheringAdmin)
# admin.site.register(OtherCashIncome, OtherCashIncomeAdmin)
# admin.site.register(OtherPurchases, OtherPurchasesAdmin)
