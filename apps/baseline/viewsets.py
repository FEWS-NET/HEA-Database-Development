from django.db import models
from django_filters import rest_framework as filters
from rest_framework import viewsets

from .models import (
    AnnualProductionPerformance,
    BaselineWealthGroup,
    ButterProduction,
    Community,
    CommunityCropProduction,
    CommunityLivestock,
    CommunityWealthGroup,
    CopingStrategy,
    CropProduction,
    Event,
    ExpandabilityFactor,
    Fishing,
    FoodPurchase,
    Hazard,
    LivelihoodActivity,
    LivelihoodProductCategory,
    LivelihoodStrategy,
    LivelihoodZone,
    LivelihoodZoneBaseline,
    LivestockSales,
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
from .serializers import (
    AnnualProductionPerformanceSerializer,
    BaselineWealthGroupSerializer,
    ButterProductionSerializer,
    CommunityCropProductionSerializer,
    CommunityLivestockSerializer,
    CommunitySerializer,
    CommunityWealthGroupSerializer,
    CopingStrategySerializer,
    CropProductionSerializer,
    EventSerializer,
    ExpandabilityFactorSerializer,
    FishingSerializer,
    FoodPurchaseSerializer,
    HazardSerializer,
    LivelihoodActivitySerializer,
    LivelihoodProductCategorySerializer,
    LivelihoodStrategySerializer,
    LivelihoodZoneBaselineSerializer,
    LivelihoodZoneSerializer,
    LivestockSalesSerializer,
    MarketPriceSerializer,
    MeatProductionSerializer,
    MilkProductionSerializer,
    OtherCashIncomeSerializer,
    OtherPurchasesSerializer,
    PaymentInKindSerializer,
    ReliefGiftsOtherSerializer,
    SeasonalActivityOccurrenceSerializer,
    SeasonalActivitySerializer,
    SourceOrganizationSerializer,
    WealthGroupCharacteristicValueSerializer,
    WealthGroupSerializer,
    WildFoodGatheringSerializer,
)


class SourceOrganizationFilterSet(filters.FilterSet):
    class Meta:
        model = SourceOrganization
        fields = ["id", "created", "modified", "name", "full_name", "description"]


class SourceOrganizationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows source organizations to be viewed or edited.
    """

    queryset = SourceOrganization.objects.all()
    serializer_class = SourceOrganizationSerializer
    filterset_class = SourceOrganizationFilterSet
    search_fields = ["name", "full_name", "description"]


class LivelihoodZoneFilterSet(filters.FilterSet):
    class Meta:
        model = LivelihoodZone
        fields = ["created", "modified", "code", "name", "description", "country"]


class LivelihoodZoneViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows livelihood zones to be viewed or edited.
    """

    queryset = LivelihoodZone.objects.all()
    serializer_class = LivelihoodZoneSerializer
    filterset_class = LivelihoodZoneFilterSet
    search_fields = ["code", "name", "description"]


class LivelihoodZoneBaselineFilterSet(filters.FilterSet):
    class Meta:
        model = LivelihoodZoneBaseline
        fields = [
            "id",
            "created",
            "modified",
            "livelihood_zone",
            "geography",
            "main_livelihood_category",
            "source_organization",
            "bss",
            "reference_year_start_date",
            "reference_year_end_date",
            "valid_from_date",
            "valid_to_date",
            "population_source",
            "population_estimate",
        ]
        exclude = ["geography"]
        filter_overrides = {
            models.FileField: {
                "filter_class": filters.CharFilter,
                "bss": lambda f: lambda f: {"lookup_expr": "exact"},
            },
        }


class LivelihoodZoneBaselineViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows livelihood zone baselines to be viewed or edited.
    """

    queryset = LivelihoodZoneBaseline.objects.all()
    serializer_class = LivelihoodZoneBaselineSerializer
    filterset_class = LivelihoodZoneBaselineFilterSet
    search_fields = ["population_source"]


class LivelihoodProductCategoryFilterSet(filters.FilterSet):
    class Meta:
        model = LivelihoodProductCategory
        fields = ["id", "created", "modified", "livelihood_zone_baseline", "product", "basket"]


class LivelihoodProductCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows livelihood product categories to be viewed or edited.
    """

    queryset = LivelihoodProductCategory.objects.all()
    serializer_class = LivelihoodProductCategorySerializer
    filterset_class = LivelihoodProductCategoryFilterSet


class CommunityFilterSet(filters.FilterSet):
    class Meta:
        model = Community
        fields = [
            "id",
            "created",
            "modified",
            "name",
            "livelihood_zone_baseline",
            "geography",
            "interview_number",
            "interviewers",
        ]
        exclude = ["geography"]


class CommunityViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows communities to be viewed or edited.
    """

    queryset = Community.objects.all()
    serializer_class = CommunitySerializer
    filterset_class = CommunityFilterSet
    search_fields = ["name", "interview_number", "interviewers"]


class WealthGroupFilterSet(filters.FilterSet):
    class Meta:
        model = WealthGroup
        fields = [
            "id",
            "created",
            "modified",
            "name",
            "livelihood_zone_baseline",
            "community",
            "wealth_category",
            "percentage_of_households",
            "average_household_size",
        ]


class WealthGroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows wealth groups to be viewed or edited.
    """

    queryset = WealthGroup.objects.all()
    serializer_class = WealthGroupSerializer
    filterset_class = WealthGroupFilterSet
    search_fields = ["name"]


class BaselineWealthGroupFilterSet(filters.FilterSet):
    class Meta:
        model = BaselineWealthGroup
        fields = [
            "id",
            "created",
            "modified",
            "name",
            "livelihood_zone_baseline",
            "community",
            "wealth_category",
            "percentage_of_households",
            "average_household_size",
        ]


class BaselineWealthGroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows baseline wealth groups to be viewed or edited.
    """

    queryset = BaselineWealthGroup.objects.all()
    serializer_class = BaselineWealthGroupSerializer
    filterset_class = BaselineWealthGroupFilterSet
    search_fields = ["name"]


class CommunityWealthGroupFilterSet(filters.FilterSet):
    class Meta:
        model = CommunityWealthGroup
        fields = [
            "id",
            "created",
            "modified",
            "name",
            "livelihood_zone_baseline",
            "community",
            "wealth_category",
            "percentage_of_households",
            "average_household_size",
        ]


class CommunityWealthGroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows community wealth groups to be viewed or edited.
    """

    queryset = CommunityWealthGroup.objects.all()
    serializer_class = CommunityWealthGroupSerializer
    filterset_class = CommunityWealthGroupFilterSet
    search_fields = ["name"]


class WealthGroupCharacteristicValueFilterSet(filters.FilterSet):
    class Meta:
        model = WealthGroupCharacteristicValue
        fields = [
            "id",
            "created",
            "modified",
            "wealth_group",
            "wealth_characteristic",
            "value",
            "min_value",
            "max_value",
        ]
        filter_overrides = {
            models.JSONField: {
                "filter_class": filters.CharFilter,
                "value": lambda f: {"lookup_expr": "icontains"},
                "min_value": lambda f: {"lookup_expr": "icontains"},
                "max_value": lambda f: {"lookup_expr": "icontains"},
            },
        }


class WealthGroupCharacteristicValueViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows wealth characteristic values to be viewed or edited.
    """

    queryset = WealthGroupCharacteristicValue.objects.all()
    serializer_class = WealthGroupCharacteristicValueSerializer
    filterset_class = WealthGroupCharacteristicValueFilterSet


class LivelihoodStrategyFilterSet(filters.FilterSet):
    class Meta:
        model = LivelihoodStrategy
        fields = [
            "id",
            "created",
            "modified",
            "livelihood_zone_baseline",
            "strategy_type",
            "season",
            "product",
            "unit_of_measure",
            "currency",
            "additional_identifier",
            "household_labor_provider",
        ]


class LivelihoodStrategyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows livelihood strategies to be viewed or edited.
    """

    queryset = LivelihoodStrategy.objects.all()
    serializer_class = LivelihoodStrategySerializer
    filterset_class = LivelihoodStrategyFilterSet
    search_fields = ["strategy_type", "additional_identifier", "household_labor_provider"]


class LivelihoodActivityFilterSet(filters.FilterSet):
    class Meta:
        model = LivelihoodActivity
        fields = [
            "id",
            "created",
            "modified",
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
        ]


class LivelihoodActivityViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows livelihood activities to be viewed or edited.
    """

    queryset = LivelihoodActivity.objects.all()
    serializer_class = LivelihoodActivitySerializer
    filterset_class = LivelihoodActivityFilterSet
    search_fields = ["strategy_type", "scenario"]


class MilkProductionFilterSet(filters.FilterSet):
    class Meta:
        model = MilkProduction
        fields = [
            "id",
            "created",
            "modified",
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "livelihoodactivity_ptr",
            "milking_animals",
            "lactation_days",
            "daily_production",
            "type_of_milk_sold_or_other_uses",
        ]


class MilkProductionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows milk production to be viewed or edited.
    """

    queryset = MilkProduction.objects.all()
    serializer_class = MilkProductionSerializer
    filterset_class = MilkProductionFilterSet
    search_fields = ["strategy_type", "scenario", "type_of_milk_sold_or_other_uses"]


class ButterProductionFilterSet(filters.FilterSet):
    class Meta:
        model = ButterProduction
        fields = [
            "id",
            "created",
            "modified",
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "livelihoodactivity_ptr",
        ]


class ButterProductionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows butter production to be viewed or edited.
    """

    queryset = ButterProduction.objects.all()
    serializer_class = ButterProductionSerializer
    filterset_class = ButterProductionFilterSet
    search_fields = ["strategy_type", "scenario"]


class MeatProductionFilterSet(filters.FilterSet):
    class Meta:
        model = MeatProduction
        fields = [
            "id",
            "created",
            "modified",
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "livelihoodactivity_ptr",
            "animals_slaughtered",
            "carcass_weight",
        ]


class MeatProductionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows meat production to be viewed or edited.
    """

    queryset = MeatProduction.objects.all()
    serializer_class = MeatProductionSerializer
    filterset_class = MeatProductionFilterSet
    search_fields = ["strategy_type", "scenario"]


class LivestockSalesFilterSet(filters.FilterSet):
    class Meta:
        model = LivestockSales
        fields = [
            "id",
            "created",
            "modified",
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
        ]


class LivestockSalesViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows livestock sales to be viewed or edited.
    """

    queryset = LivestockSales.objects.all()
    serializer_class = LivestockSalesSerializer
    filterset_class = LivestockSalesFilterSet
    search_fields = ["strategy_type", "scenario"]


class CropProductionFilterSet(filters.FilterSet):
    class Meta:
        model = CropProduction
        fields = [
            "id",
            "created",
            "modified",
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
        ]


class CropProductionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows crop production to be viewed or edited.
    """

    queryset = CropProduction.objects.all()
    serializer_class = CropProductionSerializer
    filterset_class = CropProductionFilterSet
    search_fields = ["strategy_type", "scenario"]


class FoodPurchaseFilterSet(filters.FilterSet):
    class Meta:
        model = FoodPurchase
        fields = [
            "id",
            "created",
            "modified",
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "livelihoodactivity_ptr",
            "unit_multiple",
            "purchases_per_month",
            "months_per_year",
        ]


class FoodPurchaseViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows food purchases to be viewed or edited.
    """

    queryset = FoodPurchase.objects.all()
    serializer_class = FoodPurchaseSerializer
    filterset_class = FoodPurchaseFilterSet
    search_fields = ["strategy_type", "scenario"]


class PaymentInKindFilterSet(filters.FilterSet):
    class Meta:
        model = PaymentInKind
        fields = [
            "id",
            "created",
            "modified",
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "livelihoodactivity_ptr",
            "payment_per_time",
            "people_per_hh",
            "labor_per_month",
            "months_per_year",
        ]


class PaymentInKindViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows payments in kind to be viewed or edited.
    """

    queryset = PaymentInKind.objects.all()
    serializer_class = PaymentInKindSerializer
    filterset_class = PaymentInKindFilterSet
    search_fields = ["strategy_type", "scenario"]


class ReliefGiftsOtherFilterSet(filters.FilterSet):
    class Meta:
        model = ReliefGiftsOther
        fields = [
            "id",
            "created",
            "modified",
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "livelihoodactivity_ptr",
            "unit_multiple",
            "received_per_year",
        ]


class ReliefGiftsOtherViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows relief, gifts and other food to be viewed or edited.
    """

    queryset = ReliefGiftsOther.objects.all()
    serializer_class = ReliefGiftsOtherSerializer
    filterset_class = ReliefGiftsOtherFilterSet
    search_fields = ["strategy_type", "scenario"]


class FishingFilterSet(filters.FilterSet):
    class Meta:
        model = Fishing
        fields = [
            "id",
            "created",
            "modified",
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
        ]


class FishingViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows fishing to be viewed or edited.
    """

    queryset = Fishing.objects.all()
    serializer_class = FishingSerializer
    filterset_class = FishingFilterSet
    search_fields = ["strategy_type", "scenario"]


class WildFoodGatheringFilterSet(filters.FilterSet):
    class Meta:
        model = WildFoodGathering
        fields = [
            "id",
            "created",
            "modified",
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
        ]


class WildFoodGatheringViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows wild food gathering to be viewed or edited.
    """

    queryset = WildFoodGathering.objects.all()
    serializer_class = WildFoodGatheringSerializer
    filterset_class = WildFoodGatheringFilterSet
    search_fields = ["strategy_type", "scenario"]


class OtherCashIncomeFilterSet(filters.FilterSet):
    class Meta:
        model = OtherCashIncome
        fields = [
            "id",
            "created",
            "modified",
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "livelihoodactivity_ptr",
            "payment_per_time",
            "people_per_hh",
            "labor_per_month",
            "months_per_year",
            "times_per_year",
        ]


class OtherCashIncomeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows other cash income to be viewed or edited.
    """

    queryset = OtherCashIncome.objects.all()
    serializer_class = OtherCashIncomeSerializer
    filterset_class = OtherCashIncomeFilterSet
    search_fields = ["strategy_type", "scenario"]


class OtherPurchasesFilterSet(filters.FilterSet):
    class Meta:
        model = OtherPurchases
        fields = [
            "id",
            "created",
            "modified",
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "livelihoodactivity_ptr",
            "unit_multiple",
            "purchases_per_month",
            "months_per_year",
        ]


class OtherPurchasesViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows other purchases to be viewed or edited.
    """

    queryset = OtherPurchases.objects.all()
    serializer_class = OtherPurchasesSerializer
    filterset_class = OtherPurchasesFilterSet
    search_fields = ["strategy_type", "scenario"]


class SeasonalActivityFilterSet(filters.FilterSet):
    class Meta:
        model = SeasonalActivity
        fields = ["id", "created", "modified", "livelihood_zone_baseline", "activity_type", "season", "product"]


class SeasonalActivityViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows seasonal activities to be viewed or edited.
    """

    queryset = SeasonalActivity.objects.all()
    serializer_class = SeasonalActivitySerializer
    filterset_class = SeasonalActivityFilterSet


class SeasonalActivityOccurrenceFilterSet(filters.FilterSet):
    class Meta:
        model = SeasonalActivityOccurrence
        fields = [
            "id",
            "created",
            "modified",
            "seasonal_activity",
            "livelihood_zone_baseline",
            "community",
            "start",
            "end",
        ]


class SeasonalActivityOccurrenceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows seasonal activity occurrences to be viewed or edited.
    """

    queryset = SeasonalActivityOccurrence.objects.all()
    serializer_class = SeasonalActivityOccurrenceSerializer
    filterset_class = SeasonalActivityOccurrenceFilterSet


class CommunityCropProductionFilterSet(filters.FilterSet):
    class Meta:
        model = CommunityCropProduction
        fields = [
            "id",
            "created",
            "modified",
            "community",
            "crop_type",
            "crop_purpose",
            "season",
            "yield_with_inputs",
            "yield_without_inputs",
            "seed_requirement",
            "unit_of_land",
        ]


class CommunityCropProductionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows community crop productions to be viewed or edited.
    """

    queryset = CommunityCropProduction.objects.all()
    serializer_class = CommunityCropProductionSerializer
    filterset_class = CommunityCropProductionFilterSet
    search_fields = ["crop_purpose"]


class CommunityLivestockFilterSet(filters.FilterSet):
    class Meta:
        model = CommunityLivestock
        fields = [
            "id",
            "created",
            "modified",
            "community",
            "livestock_type",
            "birth_interval",
            "wet_season_lactation_period",
            "wet_season_milk_production",
            "dry_season_lactation_period",
            "dry_season_milk_production",
            "age_at_sale",
            "additional_attributes",
        ]
        filter_overrides = {
            models.JSONField: {
                "filter_class": filters.CharFilter,
                "additional_attributes": lambda f: {"lookup_expr": "icontains"},
            },
        }


class CommunityLivestockViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows wealth group attributes to be viewed or edited.
    """

    queryset = CommunityLivestock.objects.all()
    serializer_class = CommunityLivestockSerializer
    filterset_class = CommunityLivestockFilterSet


class MarketPriceFilterSet(filters.FilterSet):
    class Meta:
        model = MarketPrice
        fields = [
            "id",
            "created",
            "modified",
            "community",
            "product",
            "market",
            "description",
            "currency",
            "unit_of_measure",
            "low_price_start",
            "low_price_end",
            "low_price",
            "high_price_start",
            "high_price_end",
            "high_price",
        ]


class MarketPriceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows market prices to be viewed or edited.
    """

    queryset = MarketPrice.objects.all()
    serializer_class = MarketPriceSerializer
    filterset_class = MarketPriceFilterSet
    search_fields = ["description"]


class AnnualProductionPerformanceFilterSet(filters.FilterSet):
    class Meta:
        model = AnnualProductionPerformance
        fields = [
            "id",
            "created",
            "modified",
            "community",
            "performance_year_start_date",
            "performance_year_end_date",
            "annual_performance",
            "description",
        ]


class AnnualProductionPerformanceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows annual production performance to be viewed or edited.
    """

    queryset = AnnualProductionPerformance.objects.all()
    serializer_class = AnnualProductionPerformanceSerializer
    filterset_class = AnnualProductionPerformanceFilterSet
    search_fields = ["description"]


class HazardFilterSet(filters.FilterSet):
    class Meta:
        model = Hazard
        fields = [
            "id",
            "created",
            "modified",
            "community",
            "chronic_or_periodic",
            "ranking",
            "hazard_category",
            "description",
        ]


class HazardViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows hazards to be viewed or edited.
    """

    queryset = Hazard.objects.all()
    serializer_class = HazardSerializer
    filterset_class = HazardFilterSet
    search_fields = ["chronic_or_periodic", "description"]


class EventFilterSet(filters.FilterSet):
    class Meta:
        model = Event
        fields = [
            "id",
            "created",
            "modified",
            "community",
            "event_year_start_date",
            "event_year_end_date",
            "description",
        ]


class EventViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows events to be viewed or edited.
    """

    queryset = Event.objects.all()
    serializer_class = EventSerializer
    filterset_class = EventFilterSet
    search_fields = ["description"]


class ExpandabilityFactorFilterSet(filters.FilterSet):
    class Meta:
        model = ExpandabilityFactor
        fields = [
            "id",
            "livelihood_strategy",
            "wealth_group",
            "percentage_produced",
            "percentage_sold",
            "percentage_other_uses",
            "percentge_consumed",
            "precentage_income",
            "percentage_expenditure",
            "remark",
        ]


class ExpandabilityFactorViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows expandability factor to be viewed or edited.
    """

    queryset = ExpandabilityFactor.objects.all()
    serializer_class = ExpandabilityFactorSerializer
    filterset_class = ExpandabilityFactorFilterSet
    search_fields = ["remark"]


class CopingStrategyFilterSet(filters.FilterSet):
    class Meta:
        model = CopingStrategy
        fields = ["id", "community", "leaders", "wealth_group", "livelihood_strategy", "strategy", "by_value"]


class CopingStrategyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows coping strategies to be viewed or edited.
    """

    queryset = CopingStrategy.objects.all()
    serializer_class = CopingStrategySerializer
    filterset_class = CopingStrategyFilterSet
    search_fields = ["leaders", "strategy"]
