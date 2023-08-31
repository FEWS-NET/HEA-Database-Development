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


class SourceOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceOrganization
        fields = ["id", "name", "full_name", "description", "created", "modified"]


class LivelihoodZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = LivelihoodZone
        fields = ["code", "name", "description", "country", "created", "modified"]


class LivelihoodZoneBaselineSerializer(serializers.ModelSerializer):
    class Meta:
        model = LivelihoodZoneBaseline
        fields = [
            "id",
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
            "created",
            "modified",
        ]


class LivelihoodProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LivelihoodProductCategory
        fields = ["id", "livelihood_zone_baseline", "product", "basket", "created", "modified"]


class CommunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Community
        fields = [
            "id",
            "code",
            "name",
            "full_name",
            "livelihood_zone_baseline",
            "geography",
            "interview_number",
            "interviewers",
            "created",
            "modified",
        ]


class WealthGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = WealthGroup
        fields = [
            "id",
            "livelihood_zone_baseline",
            "community",
            "wealth_category",
            "percentage_of_households",
            "average_household_size",
            "created",
            "modified",
        ]


class BaselineWealthGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaselineWealthGroup
        fields = [
            "id",
            "livelihood_zone_baseline",
            "community",
            "wealth_category",
            "percentage_of_households",
            "average_household_size",
            "created",
            "modified",
        ]


class CommunityWealthGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityWealthGroup
        fields = [
            "id",
            "livelihood_zone_baseline",
            "community",
            "wealth_category",
            "percentage_of_households",
            "average_household_size",
            "created",
            "modified",
        ]


class WealthGroupCharacteristicValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = WealthGroupCharacteristicValue
        fields = [
            "id",
            "wealth_group",
            "wealth_characteristic",
            "value",
            "min_value",
            "max_value",
            "created",
            "modified",
        ]


class LivelihoodStrategySerializer(serializers.ModelSerializer):
    class Meta:
        model = LivelihoodStrategy
        fields = [
            "id",
            "livelihood_zone_baseline",
            "strategy_type",
            "season",
            "product",
            "unit_of_measure",
            "currency",
            "additional_identifier",
            "household_labor_provider",
            "created",
            "modified",
        ]


class LivelihoodActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = LivelihoodActivity
        fields = [
            "id",
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
            "created",
            "modified",
        ]


class BaselineLivelihoodActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = BaselineLivelihoodActivity
        fields = [
            "id",
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
            "created",
            "modified",
        ]


class ResponseLivelihoodActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ResponseLivelihoodActivity
        fields = [
            "id",
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
            "created",
            "modified",
        ]


class MilkProductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MilkProduction
        fields = [
            "id",
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
            "milking_animals",
            "lactation_days",
            "daily_production",
            "type_of_milk_sold_or_other_uses",
            "created",
            "modified",
        ]


class ButterProductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ButterProduction
        fields = [
            "id",
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
            "created",
            "modified",
        ]


class MeatProductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeatProduction
        fields = [
            "id",
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
            "animals_slaughtered",
            "carcass_weight",
            "created",
            "modified",
        ]


class LivestockSalesSerializer(serializers.ModelSerializer):
    class Meta:
        model = LivestockSales
        fields = [
            "id",
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
            "created",
            "modified",
        ]


class CropProductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CropProduction
        fields = [
            "id",
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
            "created",
            "modified",
        ]


class FoodPurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodPurchase
        fields = [
            "id",
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
            "unit_multiple",
            "purchases_per_month",
            "months_per_year",
            "created",
            "modified",
        ]


class PaymentInKindSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentInKind
        fields = [
            "id",
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
            "payment_per_time",
            "people_per_hh",
            "labor_per_month",
            "months_per_year",
            "created",
            "modified",
        ]


class ReliefGiftsOtherSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReliefGiftsOther
        fields = [
            "id",
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
            "unit_multiple",
            "received_per_year",
            "created",
            "modified",
        ]


class FishingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fishing
        fields = [
            "id",
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
            "created",
            "modified",
        ]


class WildFoodGatheringSerializer(serializers.ModelSerializer):
    class Meta:
        model = WildFoodGathering
        fields = [
            "id",
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
            "created",
            "modified",
        ]


class OtherCashIncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtherCashIncome
        fields = [
            "id",
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
            "payment_per_time",
            "people_per_hh",
            "labor_per_month",
            "months_per_year",
            "times_per_year",
            "created",
            "modified",
        ]


class OtherPurchasesSerializer(serializers.ModelSerializer):
    class Meta:
        model = OtherPurchases
        fields = [
            "id",
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
            "unit_multiple",
            "purchases_per_month",
            "months_per_year",
            "created",
            "modified",
        ]


class SeasonalActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = SeasonalActivity
        fields = ["id", "livelihood_zone_baseline", "activity_type", "season", "product", "created", "modified"]


class SeasonalActivityOccurrenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeasonalActivityOccurrence
        fields = [
            "id",
            "seasonal_activity",
            "livelihood_zone_baseline",
            "community",
            "start",
            "end",
            "created",
            "modified",
        ]


class CommunityCropProductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityCropProduction
        fields = [
            "id",
            "community",
            "crop",
            "crop_purpose",
            "season",
            "yield_with_inputs",
            "yield_without_inputs",
            "seed_requirement",
            "unit_of_measure",
            "created",
            "modified",
        ]


class CommunityLivestockSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityLivestock
        fields = [
            "id",
            "community",
            "livestock",
            "birth_interval",
            "wet_season_lactation_period",
            "wet_season_milk_production",
            "dry_season_lactation_period",
            "dry_season_milk_production",
            "age_at_sale",
            "additional_attributes",
            "created",
            "modified",
        ]


class MarketPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketPrice
        fields = [
            "id",
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
            "created",
            "modified",
        ]


class AnnualProductionPerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnualProductionPerformance
        fields = [
            "id",
            "community",
            "performance_year_start_date",
            "performance_year_end_date",
            "annual_performance",
            "description",
            "created",
            "modified",
        ]


class HazardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hazard
        fields = [
            "id",
            "community",
            "chronic_or_periodic",
            "ranking",
            "hazard_category",
            "description",
            "created",
            "modified",
        ]


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "id",
            "community",
            "event_year_start_date",
            "event_year_end_date",
            "description",
            "created",
            "modified",
        ]


class ExpandabilityFactorSerializer(serializers.ModelSerializer):
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


class CopingStrategySerializer(serializers.ModelSerializer):
    class Meta:
        model = CopingStrategy
        fields = ["id", "community", "leaders", "wealth_group", "livelihood_strategy", "strategy", "by_value"]
