from rest_framework import serializers

from .models import (
    AnnualProductionPerformance,
    BaselineLivelihoodActivity,
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
    ResponseLivelihoodActivity,
    SeasonalActivity,
    SeasonalActivityOccurrence,
    SourceOrganization,
    WealthGroup,
    WealthGroupCharacteristicValue,
    WildFoodGathering,
)


class SourceOrganizationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SourceOrganization
        fields = ["id", "created", "modified", "name", "full_name", "description"]


class LivelihoodZoneSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LivelihoodZone
        fields = ["created", "modified", "code", "name", "description", "country"]


class LivelihoodZoneBaselineSerializer(serializers.HyperlinkedModelSerializer):
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


class LivelihoodProductCategorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LivelihoodProductCategory
        fields = ["id", "created", "modified", "livelihood_zone_baseline", "product", "basket"]


class CommunitySerializer(serializers.HyperlinkedModelSerializer):
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


class WealthGroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = WealthGroup
        fields = [
            "id",
            "created",
            "modified",
            "livelihood_zone_baseline",
            "community",
            "wealth_category",
            "percentage_of_households",
            "average_household_size",
        ]


class BaselineWealthGroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = BaselineWealthGroup
        fields = [
            "id",
            "created",
            "modified",
            "livelihood_zone_baseline",
            "community",
            "wealth_category",
            "percentage_of_households",
            "average_household_size",
        ]


class CommunityWealthGroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CommunityWealthGroup
        fields = [
            "id",
            "created",
            "modified",
            "livelihood_zone_baseline",
            "community",
            "wealth_category",
            "percentage_of_households",
            "average_household_size",
        ]


class WealthGroupCharacteristicValueSerializer(serializers.HyperlinkedModelSerializer):
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


class LivelihoodStrategySerializer(serializers.HyperlinkedModelSerializer):
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


class LivelihoodActivitySerializer(serializers.HyperlinkedModelSerializer):
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


class BaselineLivelihoodActivitySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = BaselineLivelihoodActivity
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


class ResponseLivelihoodActivitySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ResponseLivelihoodActivity
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


class MilkProductionSerializer(serializers.HyperlinkedModelSerializer):
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


class ButterProductionSerializer(serializers.HyperlinkedModelSerializer):
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


class MeatProductionSerializer(serializers.HyperlinkedModelSerializer):
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


class LivestockSalesSerializer(serializers.HyperlinkedModelSerializer):
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


class CropProductionSerializer(serializers.HyperlinkedModelSerializer):
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


class FoodPurchaseSerializer(serializers.HyperlinkedModelSerializer):
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


class PaymentInKindSerializer(serializers.HyperlinkedModelSerializer):
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


class ReliefGiftsOtherSerializer(serializers.HyperlinkedModelSerializer):
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


class FishingSerializer(serializers.HyperlinkedModelSerializer):
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


class WildFoodGatheringSerializer(serializers.HyperlinkedModelSerializer):
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


class OtherCashIncomeSerializer(serializers.HyperlinkedModelSerializer):
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


class OtherPurchasesSerializer(serializers.HyperlinkedModelSerializer):
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


class SeasonalActivitySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SeasonalActivity
        fields = ["id", "created", "modified", "livelihood_zone_baseline", "activity_type", "season", "product"]


class SeasonalActivityOccurrenceSerializer(serializers.HyperlinkedModelSerializer):
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


class CommunityCropProductionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CommunityCropProduction
        fields = [
            "id",
            "created",
            "modified",
            "community",
            "crop",
            "crop_purpose",
            "season",
            "yield_with_inputs",
            "yield_without_inputs",
            "seed_requirement",
            "unit_of_measure",
        ]


class CommunityLivestockSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CommunityLivestock
        fields = [
            "id",
            "created",
            "modified",
            "community",
            "livestock",
            "birth_interval",
            "wet_season_lactation_period",
            "wet_season_milk_production",
            "dry_season_lactation_period",
            "dry_season_milk_production",
            "age_at_sale",
            "additional_attributes",
        ]


class MarketPriceSerializer(serializers.HyperlinkedModelSerializer):
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


class AnnualProductionPerformanceSerializer(serializers.HyperlinkedModelSerializer):
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


class HazardSerializer(serializers.HyperlinkedModelSerializer):
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


class EventSerializer(serializers.HyperlinkedModelSerializer):
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


class ExpandabilityFactorSerializer(serializers.HyperlinkedModelSerializer):
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


class CopingStrategySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CopingStrategy
        fields = ["id", "community", "leaders", "wealth_group", "livelihood_strategy", "strategy", "by_value"]
