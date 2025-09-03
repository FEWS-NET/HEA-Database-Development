from copy import deepcopy

from binary_database_files.models import File
from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from django.utils.translation import gettext_lazy as _

from common.fields import translation_fields
from metadata.models import LivelihoodStrategyType

from .forms import (
    FoodPurchaseForm,
    LivelihoodActivityForm,
    MilkProductionForm,
    OtherPurchaseForm,
    ReliefGiftOtherForm,
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
    LivelihoodActivity,
    LivelihoodStrategy,
    LivelihoodZone,
    LivelihoodZoneBaseline,
    LivelihoodZoneBaselineCorrection,
    LivestockSale,
    MarketPrice,
    MeatProduction,
    MilkProduction,
    OtherCashIncome,
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

admin.site.site_header = "HEA Baseline Database Administration"
admin.site.index_title = "HEA Baseline"
admin.site.site_title = "Administration"


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
        "country__iso_en_ro_name",
    ]
    list_filter = (("country", admin.RelatedOnlyFieldListFilter),)


class LivelihoodZoneBaselineCorrectionAdmin(admin.ModelAdmin):
    list_display = ("worksheet_name", "cell_range", "previous_value", "value", "correction_date", "author")
    list_filter = ("livelihood_zone_baseline", "worksheet_name", "correction_date", "author")
    search_fields = (
        "livelihood_zone_baseline__livelihood_zone__code",
        "livelihood_zone_baseline__livelihood_zone__alternate_code",
        *translation_fields("livelihood_zone_baseline__livelihood_zone__name"),
        *translation_fields("livelihood_zone_baseline__main_livelihood_category__name"),
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
                    "main_livelihood_category",
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
                ],
            },
        ),
    ]
    list_display = (
        "livelihood_zone",
        "livelihood_zone_alternate_code",
        "main_livelihood_category",
        "source_organization",
        "reference_year_start_date",
        "reference_year_end_date",
    )
    readonly_fields = ("livelihood_zone_alternate_code", "country", "bss_uploaded_date_time")
    search_fields = (
        "livelihood_zone__code",
        "livelihood_zone__alternate_code",
        *translation_fields("livelihood_zone__name"),
        *translation_fields("main_livelihood_category__name"),
        "source_organization__name",
    )
    list_filter = ["source_organization", ("livelihood_zone__country", admin.RelatedOnlyFieldListFilter)]
    date_hierarchy = "reference_year_start_date"
    inlines = [
        LivelihoodZoneBaselineCorrectionInlineAdmin,
    ]

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
    )
    readonly_fields = ("livelihood_zone_alternate_code", "country")
    search_fields = (
        "name",
        "full_name",
        *translation_fields("livelihood_zone_baseline__livelihood_zone__name__icontains"),
        "livelihood_zone_baseline__livelihood_zone__code",
        "livelihood_zone_baseline__livelihood_zone__alternate_code",
        "aliases__icontains",
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
        "strategy_type__icontains",
        "livelihood_zone_baseline__livelihood_zone__code",
        "livelihood_zone_baseline__livelihood_zone__alternate_code",
        "additional_identifier__icontains",
        "product__cpc__iexact",
        "product__aliases__icontains",
        "season__aliases__icontains",
        *translation_fields("livelihood_zone_baseline__livelihood_zone__name__icontains"),
        *translation_fields("product__common_name__icontains"),
        *translation_fields("season__name__icontains"),
    )

    list_filter = (
        "strategy_type",
        "livelihood_zone_baseline__livelihood_zone",
        ("livelihood_zone_baseline__livelihood_zone__country", admin.RelatedOnlyFieldListFilter),
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


class LivelihoodActivityAdmin(admin.ModelAdmin):
    form = LivelihoodActivityForm
    list_display = (
        "wealth_group",
        "strategy_type",
        "get_product_common_name",
        "get_season_name",
        "get_country_name",
    )
    list_filter = (
        "strategy_type",
        "scenario",
        ("livelihood_strategy__product", admin.RelatedOnlyFieldListFilter),
        ("livelihood_strategy__season", admin.RelatedOnlyFieldListFilter),
        ("livelihood_zone_baseline__livelihood_zone__country", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = (
        "wealth_group__wealth_group_category__code__iexact",
        *translation_fields("wealth_group__wealth_group_category__name"),
        "wealth_group__community__name",
        "wealth_group__community__full_name",
        "strategy_type__icontains",
        "livelihood_strategy__additional_identifier__icontains",
        "livelihood_zone_baseline__livelihood_zone__code",
        "livelihood_zone_baseline__livelihood_zone__alternate_code",
        "livelihood_strategy__product__cpc__iexact",
        "livelihood_strategy__product__aliases__icontains",
        "livelihood_strategy__season__aliases__icontains",
        "livelihood_strategy__additional_identifier",
        *translation_fields("livelihood_strategy__product__common_name__icontains"),
        *translation_fields("livelihood_strategy__product__description__icontains"),
        *translation_fields("livelihood_strategy__season__name__icontains"),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
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
        "wealth_group__wealth_group_category",
        ("wealth_group__livelihood_zone_baseline__livelihood_zone__country", admin.RelatedOnlyFieldListFilter),
        "wealth_characteristic__has_product",
        ("product", admin.RelatedOnlyFieldListFilter),
        "wealth_characteristic__has_unit_of_measure",
        ("unit_of_measure", admin.RelatedOnlyFieldListFilter),
    )

    search_fields = (
        "wealth_group__wealth_group_category__code__iexact",
        "wealth_group__wealth_group_category__aliases",
        "wealth_group__community__name",
        "wealth_group__community__full_name",
        *translation_fields("wealth_characteristic__name"),
        "wealth_characteristic__aliases",
        *translation_fields("wealth_group__wealth_group_category__name"),
        "wealth_group__livelihood_zone_baseline__livelihood_zone__code",
        "wealth_group__livelihood_zone_baseline__livelihood_zone__alternate_code",
        "wealth_group__livelihood_zone_baseline__livelihood_zone__country__name",
        *translation_fields("product__description__icontains"),
        *translation_fields("product__common_name__icontains"),
        "product__cpc",
        "product__aliases",
    )

    def get_wealth_group_category(self, obj):
        return obj.wealth_group.wealth_group_category.name

    get_wealth_group_category.admin_order_field = "wealth_group__category__name"
    get_wealth_group_category.short_description = "Wealth group category"

    def get_country_name(self, obj):
        return obj.wealth_group.livelihood_zone_baseline.livelihood_zone.country.name

    get_country_name.admin_order_field = "wealth_group__livelihood_zone_baseline__livelihood_zone__country__name"
    get_country_name.short_description = "Country Name"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "wealth_group__livelihood_zone_baseline__livelihood_zone__country", "product", "unit_of_measure"
        )

    def get_wealth_characteristic_common_name(self, obj):
        return obj.wealth_characteristic.name

    get_wealth_characteristic_common_name.admin_order_field = "wealth_characteristic.name"
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

    def get_fieldsets(self, request, obj=None):
        fieldsets = deepcopy(super().get_fieldsets(request, obj))
        fieldsets.insert(
            1,
            (
                "Payment",
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


class WealthGroupAdmin(admin.ModelAdmin):
    list_display = (
        "community",
        "wealth_group_category",
        "percentage_of_households",
    )
    search_fields = (
        "community__name",
        "wealth_group_category__code__iexact",
        *translation_fields("wealth_group_category__name"),
    )
    list_filter = (
        "livelihood_zone_baseline__source_organization",
        ("livelihood_zone_baseline__livelihood_zone__country", admin.RelatedOnlyFieldListFilter),
        *translation_fields("livelihood_zone_baseline__livelihood_zone__name"),
        ("community", admin.RelatedOnlyFieldListFilter),
        "wealth_group_category",
    )
    inlines = [
        WealthGroupCharacteristicValueInlineAdmin,
    ] + [child for child in LivelihoodActivityInlineAdmin.__subclasses__()]

    def get_queryset(self, request):
        queryset = super().get_queryset(request).prefetch_related("livelihoodactivity_set")
        return queryset


class SeasonalActivityAdmin(admin.ModelAdmin):
    fields = (
        "livelihood_zone_baseline",
        "seasonal_activity_type",
        "season",
        "product",
        "additional_identifier",
    )
    list_display = (
        "livelihood_zone_baseline",
        "seasonal_activity_type",
        "product",
    )
    search_fields = (
        "seasonal_activity_type",
        "season",
        "product",
        "additional_identifier",
    )
    list_filter = (
        "livelihood_zone_baseline__livelihood_zone",
        "seasonal_activity_type",
        "season",
        "product",
    )


class SeasonalActivityOccurrenceAdmin(admin.ModelAdmin):
    list_display = (
        "seasonal_activity",
        "community",
        "start_month",
        "end_month",
    )
    search_fields = (
        "seasonal_activity__seasonal_activity_type",
        "seasonal_activity__season",
        "seasonal_activity__product",
        "seasonal_activity__additional_identifier",
    )
    list_filter = (
        "community",
        "seasonal_activity__seasonal_activity_type",
        "seasonal_activity__season",
        "seasonal_activity__product",
    )
    ordering = ["start"]


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
        *translation_fields("crop__description"),
        "crop_purpose",
        *translation_fields("season__name"),
    )

    list_filter = (
        "community__livelihood_zone_baseline__livelihood_zone",
        "community__full_name",
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
    search_fields = (*translation_fields("livestock__common_name"),)
    list_filter = (
        "community__livelihood_zone_baseline__livelihood_zone",
        "community__full_name",
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
        "community",
        "chronic_or_periodic",
        "hazard_category",
    )
    list_filter = (
        "community",
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
        "community",
        "performance_year_start_date",
        "performance_year_end_date",
        "seasonal_performance",
        "description",
    )
    list_filter = (
        "community",
        "community__livelihood_zone_baseline__livelihood_zone",
    )


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
        "community",
        "description",
    )
    list_filter = (
        "community",
        "community__livelihood_zone_baseline__livelihood_zone",
    )


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
        "livelihood_strategy",
        "wealth_group",
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
        "community",
        "livelihood_strategy",
        "wealth_group",
    )
    list_filter = (
        "community",
        "livelihood_strategy",
        "wealth_group",
    )


admin.site.register(SourceOrganization, SourceOrganizationAdmin)
admin.site.register(LivelihoodZone, LivelihoodZoneAdmin)
admin.site.register(LivelihoodZoneBaseline, LivelihoodZoneBaselineAdmin)
admin.site.register(LivelihoodZoneBaselineCorrection, LivelihoodZoneBaselineCorrectionAdmin)
admin.site.register(Community, CommunityAdmin)
admin.site.register(LivelihoodStrategy, LivelihoodStrategyAdmin)
admin.site.register(WealthGroup, WealthGroupAdmin)

admin.site.register(CommunityCropProduction, CommunityCropProductionAdmin)
admin.site.register(CommunityLivestock, CommunityLivestockAdmin)

admin.site.register(MarketPrice, MarketPriceAdmin)
admin.site.register(Hazard, HazardAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(ExpandabilityFactor, ExpandabilityFactorAdmin)
admin.site.register(CopingStrategy, CopingStrategyAdmin)

admin.site.register(SeasonalActivity, SeasonalActivityAdmin)
admin.site.register(SeasonalActivityOccurrence, SeasonalActivityOccurrenceAdmin)
admin.site.register(SeasonalProductionPerformance, SeasonalProductionPerformanceAdmin)

admin.site.register(LivelihoodActivity, LivelihoodActivityAdmin)
admin.site.register(WealthGroupCharacteristicValue, WealthGroupCharacteristicValueAdmin)
