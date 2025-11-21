from django.db.models import Sum
from django.utils import translation
from rest_framework import fields as rest_framework_fields
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from common.fields import translation_fields
from metadata.models import LivelihoodStrategyType

from .models import (
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
    Hunting,
    LivelihoodActivity,
    LivelihoodProductCategory,
    LivelihoodStrategy,
    LivelihoodZone,
    LivelihoodZoneBaseline,
    LivestockSale,
    MarketPrice,
    MeatProduction,
    MilkProduction,
    OtherCashIncome,
    OtherPurchase,
    PaymentInKind,
    ReliefGiftOther,
    ResponseLivelihoodActivity,
    SeasonalActivity,
    SeasonalActivityOccurrence,
    SeasonalProductionPerformance,
    SourceOrganization,
    WealthGroup,
    WealthGroupCharacteristicValue,
    WildFoodGathering,
)


class SourceOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceOrganization
        fields = [
            "id",
            "name",
            "full_name",
            "description",
        ]


class LivelihoodZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = LivelihoodZone
        fields = (
            "code",
            "alternate_code",
            "name",
            "description",
            "country",
            "country_name",
        )

    country_name = serializers.CharField(source="country.iso_en_ro_name", read_only=True)


class LivelihoodZoneBaselineSerializer(serializers.ModelSerializer):
    class Meta:
        model = LivelihoodZoneBaseline
        fields = (
            "id",
            "name",
            "description",
            "source_organization",
            "source_organization_name",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "main_livelihood_category",
            "bss",
            "bss_language",
            "currency",
            *translation_fields("profile_report"),
            "reference_year_start_date",
            "reference_year_end_date",
            "valid_from_date",
            "valid_to_date",
            "population_source",
            "population_estimate",
        )

    livelihood_zone_name = serializers.CharField(source="livelihood_zone.name", read_only=True)
    source_organization_name = serializers.CharField(source="source_organization.pk", read_only=True)
    livelihood_zone_country = serializers.CharField(source="livelihood_zone.country.pk", read_only=True)
    livelihood_zone_country_name = serializers.CharField(source="livelihood_zone.country.name", read_only=True)
    bss_language = serializers.SerializerMethodField()

    def get_bss_language(self, obj):
        return obj.get_bss_language_display()


class LivelihoodZoneBaselineGeoSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = LivelihoodZoneBaseline
        fields = (
            "id",
            "name",
            "description",
            "source_organization",
            "source_organization_name",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "geography",
            "main_livelihood_category",
            "bss",
            "bss_language",
            "currency",
            *translation_fields("profile_report"),
            "reference_year_start_date",
            "reference_year_end_date",
            "valid_from_date",
            "valid_to_date",
            "population_source",
            "population_estimate",
        )
        geo_field = "geography"
        auto_bbox = True

    livelihood_zone_name = serializers.CharField(source="livelihood_zone.name", read_only=True)
    source_organization_name = serializers.CharField(source="source_organization.pk", read_only=True)
    livelihood_zone_country = serializers.CharField(source="livelihood_zone.country.pk", read_only=True)
    livelihood_zone_country_name = serializers.CharField(source="livelihood_zone.country.name", read_only=True)
    bss_language = serializers.SerializerMethodField()

    def get_bss_language(self, obj):
        return obj.get_bss_language_display()


class LivelihoodProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LivelihoodProductCategory
        fields = [
            "id",
            "source_organization",
            "source_organization_name",
            "baseline_livelihood_activity",
            "livelihood_zone",
            "livelihood_zone_baseline_label",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "product",
            "product_common_name",
            "product_description",
            "basket",
            "basket_name",
            "percentage_allocation_to_basket",
        ]

    source_organization = serializers.CharField(
        source="baseline_livelihood_activity.livelihood_zone_baseline.source_organization.pk", read_only=True
    )
    source_organization_name = serializers.CharField(
        source="baseline_livelihood_activity.livelihood_zone_baseline.source_organization.name", read_only=True
    )
    livelihood_zone_baseline_label = serializers.SerializerMethodField()

    def get_livelihood_zone_baseline_label(self, obj):
        return str(obj.baseline_livelihood_activity.livelihood_zone_baseline)

    product = serializers.SerializerMethodField()

    def get_product(self, obj):
        return str(obj.baseline_livelihood_activity.livelihood_strategy.product)

    product_description = serializers.CharField(
        source="baseline_livelihood_activity.livelihood_strategy.product.description", read_only=True
    )
    product_common_name = serializers.CharField(
        source="baseline_livelihood_activity.livelihood_strategy.product.common_name", read_only=True
    )
    livelihood_zone_name = serializers.CharField(
        source="baseline_livelihood_activity.livelihood_zone_baseline.livelihood_zone.name", read_only=True
    )
    livelihood_zone = serializers.CharField(
        source="baseline_livelihood_activity.livelihood_zone_baseline.livelihood_zone.pk", read_only=True
    )
    source_organization_name = serializers.CharField(
        source="baseline_livelihood_activity.livelihood_zone_baseline.source_organization.name", read_only=True
    )
    livelihood_zone_country = serializers.CharField(
        source="baseline_livelihood_activity.livelihood_zone_baseline.livelihood_zone.country.pk", read_only=True
    )
    livelihood_zone_country_name = serializers.CharField(
        source="baseline_livelihood_activity.livelihood_zone_baseline.livelihood_zone.country.name", read_only=True
    )
    basket_name = serializers.SerializerMethodField()

    def get_basket_name(self, obj):
        return obj.get_basket_display()


class CommunitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Community
        fields = [
            "id",
            "code",
            "name",
            "full_name",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country_code",
            "livelihood_zone_country_name",
            "geography",
            "aliases",
        ]

    livelihood_zone_baseline_label = serializers.SerializerMethodField()

    def get_livelihood_zone_baseline_label(self, obj):
        return str(obj.livelihood_zone_baseline)

    livelihood_zone_name = serializers.CharField(
        source="livelihood_zone_baseline.livelihood_zone.name", read_only=True
    )
    livelihood_zone = serializers.CharField(source="livelihood_zone_baseline.livelihood_zone.pk", read_only=True)
    livelihood_zone_country_code = serializers.CharField(
        source="livelihood_zone_baseline.livelihood_zone.country.pk", read_only=True
    )
    livelihood_zone_country_name = serializers.CharField(
        source="livelihood_zone_baseline.livelihood_zone.country.name", read_only=True
    )
    source_organization = serializers.IntegerField(
        source="livelihood_zone_baseline.source_organization.pk", read_only=True
    )
    source_organization_name = serializers.CharField(
        source="livelihood_zone_baseline.source_organization.name", read_only=True
    )


class WealthGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = WealthGroup
        fields = [
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country_code",
            "livelihood_zone_country_name",
            "community",
            "community_name",
            "wealth_group_category",
            "percentage_of_households",
            "average_household_size",
        ]

    livelihood_zone_baseline_label = serializers.SerializerMethodField()

    def get_livelihood_zone_baseline_label(self, obj):
        return str(obj.livelihood_zone_baseline)

    livelihood_zone_name = serializers.CharField(
        source="livelihood_zone_baseline.livelihood_zone.name", read_only=True
    )
    livelihood_zone = serializers.CharField(source="livelihood_zone_baseline.livelihood_zone.pk", read_only=True)
    livelihood_zone_country_code = serializers.CharField(
        source="livelihood_zone_baseline.livelihood_zone.country.pk", read_only=True
    )
    livelihood_zone_country_name = serializers.CharField(
        source="livelihood_zone_baseline.livelihood_zone.country.name", read_only=True
    )
    community_name = serializers.CharField(source="community.name", read_only=True)
    source_organization = serializers.IntegerField(
        source="livelihood_zone_baseline.source_organization.pk", read_only=True
    )
    source_organization_name = serializers.CharField(
        source="livelihood_zone_baseline.source_organization.name", read_only=True
    )


class BaselineWealthGroupSerializer(WealthGroupSerializer):
    class Meta:
        model = BaselineWealthGroup
        fields = [f for f in WealthGroupSerializer.Meta.fields if f not in {"community", "community_name"}]

    livelihood_zone_baseline_label = serializers.SerializerMethodField()

    def get_livelihood_zone_baseline_label(self, obj):
        return str(obj.livelihood_zone_baseline)

    livelihood_zone_name = serializers.CharField(
        source="livelihood_zone_baseline.livelihood_zone.name", read_only=True
    )
    livelihood_zone = serializers.CharField(source="livelihood_zone_baseline.livelihood_zone.pk", read_only=True)
    livelihood_zone_country_code = serializers.CharField(
        source="livelihood_zone_baseline.livelihood_zone.country.pk", read_only=True
    )
    livelihood_zone_country_name = serializers.CharField(
        source="livelihood_zone_baseline.livelihood_zone.country.name", read_only=True
    )
    source_organization = serializers.IntegerField(
        source="livelihood_zone_baseline.source_organization.pk", read_only=True
    )
    source_organization_name = serializers.CharField(
        source="livelihood_zone_baseline.source_organization.name", read_only=True
    )


class CommunityWealthGroupSerializer(WealthGroupSerializer):
    class Meta:
        model = CommunityWealthGroup
        fields = WealthGroupSerializer.Meta.fields


class WealthGroupCharacteristicValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = WealthGroupCharacteristicValue
        fields = [
            "id",
            "wealth_group",
            "wealth_group_label",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country_code",
            "livelihood_zone_country_name",
            "community",
            "community_name",
            "wealth_group_category",
            "wealth_group_category_name",
            "wealth_group_category_description",
            "wealth_characteristic",
            "wealth_characteristic_name",
            "wealth_characteristic_description",
            "value",
            "min_value",
            "max_value",
        ]

    livelihood_zone_baseline_label = serializers.SerializerMethodField()

    def get_livelihood_zone_baseline_label(self, obj):
        return (
            str(obj.wealth_group.community.livelihood_zone_baseline)
            if obj.wealth_group.community
            else str(obj.wealth_group.livelihood_zone_baseline)
        )

    wealth_group_label = serializers.SerializerMethodField()

    def get_wealth_group_label(self, obj):
        return str(obj.wealth_group)

    wealth_group_category = serializers.CharField(source="wealth_group.wealth_group_category.pk", read_only=True)
    wealth_group_category_name = serializers.CharField(
        source="wealth_group.wealth_group_category.name", read_only=True
    )
    wealth_group_category_description = serializers.CharField(
        source="wealth_group.wealth_group_category.description", read_only=True
    )
    wealth_characteristic_name = serializers.CharField(source="wealth_characteristic.name", read_only=True)
    wealth_characteristic_description = serializers.CharField(
        source="wealth_characteristic.description", read_only=True
    )
    livelihood_zone_baseline = serializers.IntegerField(
        source="wealth_group.community.livelihood_zone_baseline.pk", read_only=True
    )
    livelihood_zone_name = serializers.CharField(
        source="wealth_group.community.livelihood_zone_baseline.livelihood_zone.name", read_only=True
    )
    livelihood_zone = serializers.CharField(
        source="wealth_group.community.livelihood_zone_baseline.livelihood_zone.pk", read_only=True
    )
    livelihood_zone_country_code = serializers.CharField(
        source="wealth_group.community.livelihood_zone_baseline.livelihood_zone.country.pk", read_only=True
    )
    livelihood_zone_country_name = serializers.CharField(
        source="wealth_group.community.livelihood_zone_baseline.livelihood_zone.country.name", read_only=True
    )
    community = serializers.IntegerField(source="wealth_group.community.pk", read_only=True)
    community_name = serializers.CharField(source="wealth_group.community.name", read_only=True)
    source_organization = serializers.IntegerField(
        source="wealth_group.community.livelihood_zone_baseline.source_organization.pk", read_only=True
    )
    source_organization_name = serializers.CharField(
        source="wealth_group.community.livelihood_zone_baseline.source_organization.name", read_only=True
    )


class LivelihoodStrategySerializer(serializers.ModelSerializer):
    class Meta:
        model = LivelihoodStrategy
        fields = [
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "strategy_type",
            "strategy_type_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_name",
            "unit_of_measure_description",
            "currency",
            "additional_identifier",
        ]

    livelihood_zone_name = serializers.CharField(
        source="livelihood_zone_baseline.livelihood_zone.name", read_only=True
    )
    livelihood_zone = serializers.CharField(source="livelihood_zone_baseline.livelihood_zone.pk", read_only=True)
    livelihood_zone_country = serializers.CharField(
        source="livelihood_zone_baseline.livelihood_zone.country.pk", read_only=True
    )
    livelihood_zone_country_name = serializers.CharField(
        source="livelihood_zone_baseline.livelihood_zone.country.name", read_only=True
    )
    source_organization = serializers.IntegerField(
        source="livelihood_zone_baseline.source_organization.pk", read_only=True
    )
    source_organization_name = serializers.CharField(
        source="livelihood_zone_baseline.source_organization.name", read_only=True
    )
    unit_of_measure_name = serializers.CharField(source="unit_of_measure.name", read_only=True)
    unit_of_measure_description = serializers.CharField(source="unit_of_measure.description", read_only=True)
    product_common_name = serializers.CharField(source="product.common_name", read_only=True)
    product_description = serializers.CharField(source="product.description", read_only=True)
    season_name = serializers.CharField(source="season.name", read_only=True)
    season_description = serializers.CharField(source="season.description", read_only=True)
    season_type = serializers.CharField(source="season.season_type", read_only=True)
    season_type_label = serializers.SerializerMethodField()

    def get_season_type_label(self, obj):
        return obj.season.get_season_type_display() if obj.season else ""

    strategy_type_label = serializers.SerializerMethodField()

    def get_strategy_type_label(self, obj):
        return obj.get_strategy_type_display()

    livelihood_zone_baseline_label = serializers.SerializerMethodField()

    def get_livelihood_zone_baseline_label(self, obj):
        return str(obj.livelihood_zone_baseline)


class LivelihoodActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = LivelihoodActivity
        fields = [
            "id",
            # LivelihoodStrategy
            "livelihood_strategy",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "strategy_type",
            "strategy_type_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_name",
            "unit_of_measure_description",
            "currency",
            "additional_identifier",
            # End LivelihoodStrategy
            "household_labor_provider",
            "household_labor_provider_label",
            "scenario",
            "scenario_label",
            "extra",
            # WealthGroup
            "wealth_group",
            "wealth_group_label",
            "community",
            "community_name",
            "wealth_group_category",
            "wealth_group_category_name",
            "wealth_group_category_description",
            "wealth_group_percentage_of_households",
            "wealth_group_average_household_size",
            # End WealthGroup
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

    livelihood_zone_name = serializers.CharField(
        source="wealth_group.community.livelihood_zone_baseline.livelihood_zone.name", read_only=True
    )
    livelihood_zone = serializers.CharField(
        source="wealth_group.community.livelihood_zone_baseline.livelihood_zone.pk", read_only=True
    )
    livelihood_zone_country = serializers.CharField(
        source="wealth_group.community.livelihood_zone_baseline.livelihood_zone.country.pk", read_only=True
    )
    livelihood_zone_country_name = serializers.CharField(
        source="wealth_group.community.livelihood_zone_baseline.livelihood_zone.country.name", read_only=True
    )
    source_organization = serializers.IntegerField(
        source="wealth_group.community.livelihood_zone_baseline.source_organization.pk", read_only=True
    )
    source_organization_name = serializers.CharField(
        source="wealth_group.community.livelihood_zone_baseline.source_organization.name", read_only=True
    )
    livelihood_zone_baseline_label = serializers.SerializerMethodField()

    def get_livelihood_zone_baseline_label(self, obj):
        return str(obj.livelihood_strategy.livelihood_zone_baseline)

    additional_identifier = serializers.CharField(source="livelihood_strategy.additional_identifier", read_only=True)
    currency = serializers.CharField(source="livelihood_strategy.currency.pk", read_only=True)
    community = serializers.IntegerField(source="wealth_group.community.pk", read_only=True)
    community_name = serializers.CharField(source="wealth_group.community.name", read_only=True)
    unit_of_measure = serializers.CharField(source="livelihood_strategy.unit_of_measure.pk", read_only=True)
    unit_of_measure_name = serializers.CharField(source="livelihood_strategy.unit_of_measure.name", read_only=True)
    unit_of_measure_description = serializers.CharField(
        source="livelihood_strategy.unit_of_measure.description", read_only=True
    )
    product = serializers.CharField(source="livelihood_strategy.product.pk", read_only=True)
    product_common_name = serializers.CharField(source="livelihood_strategy.product.common_name", read_only=True)
    product_description = serializers.CharField(source="livelihood_strategy.product.description", read_only=True)
    season = serializers.IntegerField(source="livelihood_strategy.season.pk", read_only=True)
    season_name = serializers.CharField(source="livelihood_strategy.season.name", read_only=True)
    season_description = serializers.CharField(source="livelihood_strategy.season.description", read_only=True)
    season_type = serializers.CharField(source="livelihood_strategy.season.season_type", read_only=True)
    season_type_label = serializers.SerializerMethodField()
    wealth_group_percentage_of_households = serializers.IntegerField(
        source="wealth_group.percentage_of_households", read_only=True
    )
    wealth_group_average_household_size = serializers.IntegerField(
        source="wealth_group.average_household_size", read_only=True
    )
    wealth_group_category = serializers.CharField(source="wealth_group.wealth_group_category.pk", read_only=True)
    wealth_group_category_name = serializers.CharField(
        source="wealth_group.wealth_group_category.name", read_only=True
    )
    wealth_group_category_description = serializers.CharField(
        source="wealth_group.wealth_group_category.description", read_only=True
    )

    def get_season_type_label(self, obj):
        return obj.livelihood_strategy.season.get_season_type_display() if obj.livelihood_strategy.season else ""

    strategy_type_label = serializers.SerializerMethodField()

    def get_strategy_type_label(self, obj):
        return obj.livelihood_strategy.get_strategy_type_display()

    household_labor_provider_label = serializers.SerializerMethodField()

    def get_household_labor_provider_label(self, obj):
        return obj.get_household_labor_provider_display()

    scenario_label = serializers.SerializerMethodField()

    def get_scenario_label(self, obj):
        return obj.get_scenario_display()

    wealth_group_label = serializers.SerializerMethodField()

    def get_wealth_group_label(self, obj):
        return str(obj.wealth_group)


class BaselineLivelihoodActivitySerializer(LivelihoodActivitySerializer):
    class Meta:
        model = BaselineLivelihoodActivity
        fields = LivelihoodActivitySerializer.Meta.fields


class ResponseLivelihoodActivitySerializer(LivelihoodActivitySerializer):
    class Meta:
        model = ResponseLivelihoodActivity
        fields = LivelihoodActivitySerializer.Meta.fields


class MilkProductionSerializer(LivelihoodActivitySerializer):
    class Meta:
        model = MilkProduction
        fields = LivelihoodActivitySerializer.Meta.fields + [
            "milking_animals",
            "lactation_days",
            "daily_production",
            "type_of_milk_sold_or_other_uses",
        ]


class ButterProductionSerializer(LivelihoodActivitySerializer):
    class Meta:
        model = ButterProduction
        fields = LivelihoodActivitySerializer.Meta.fields


class MeatProductionSerializer(LivelihoodActivitySerializer):
    class Meta:
        model = MeatProduction
        fields = LivelihoodActivitySerializer.Meta.fields + [
            "animals_slaughtered",
            "carcass_weight",
        ]


class LivestockSaleSerializer(LivelihoodActivitySerializer):
    class Meta:
        model = LivestockSale
        fields = LivelihoodActivitySerializer.Meta.fields


class CropProductionSerializer(LivelihoodActivitySerializer):
    class Meta:
        model = CropProduction
        fields = LivelihoodActivitySerializer.Meta.fields


class FoodPurchaseSerializer(LivelihoodActivitySerializer):
    class Meta:
        model = FoodPurchase
        fields = LivelihoodActivitySerializer.Meta.fields + [
            "unit_multiple",
            "times_per_month",
            "months_per_year",
            "times_per_year",
        ]


class PaymentInKindSerializer(LivelihoodActivitySerializer):
    class Meta:
        model = PaymentInKind
        fields = LivelihoodActivitySerializer.Meta.fields + [
            "payment_per_time",
            "people_per_household",
            "times_per_month",
            "months_per_year",
        ]


class ReliefGiftOtherSerializer(LivelihoodActivitySerializer):
    class Meta:
        model = ReliefGiftOther
        fields = LivelihoodActivitySerializer.Meta.fields + [
            "unit_multiple",
            "months_per_year",
            "times_per_month",
            "times_per_year",
        ]


class HuntingSerializer(LivelihoodActivitySerializer):
    class Meta:
        model = Hunting
        fields = LivelihoodActivitySerializer.Meta.fields


class FishingSerializer(LivelihoodActivitySerializer):
    class Meta:
        model = Fishing
        fields = LivelihoodActivitySerializer.Meta.fields


class WildFoodGatheringSerializer(LivelihoodActivitySerializer):
    class Meta:
        model = WildFoodGathering
        fields = LivelihoodActivitySerializer.Meta.fields


class OtherCashIncomeSerializer(LivelihoodActivitySerializer):
    class Meta:
        model = OtherCashIncome
        fields = LivelihoodActivitySerializer.Meta.fields + [
            "payment_per_time",
            "people_per_household",
            "times_per_month",
            "months_per_year",
            "times_per_year",
        ]


class OtherPurchaseSerializer(LivelihoodActivitySerializer):
    class Meta:
        model = OtherPurchase
        fields = LivelihoodActivitySerializer.Meta.fields + [
            "unit_multiple",
            "times_per_month",
            "months_per_year",
        ]


class SeasonalActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = SeasonalActivity
        fields = [
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "seasonal_activity_type",
            "seasonal_activity_type_name",
            "seasonal_activity_type_description",
            "activity_category",
            "activity_category_label",
            "product",
            "product_common_name",
            "product_description",
            "additional_identifier",
        ]

    livelihood_zone_name = serializers.CharField(
        source="livelihood_zone_baseline.livelihood_zone.name", read_only=True
    )
    livelihood_zone = serializers.CharField(source="livelihood_zone_baseline.livelihood_zone.pk", read_only=True)
    livelihood_zone_country = serializers.CharField(
        source="livelihood_zone_baseline.livelihood_zone.country.pk", read_only=True
    )
    livelihood_zone_country_name = serializers.CharField(
        source="livelihood_zone_baseline.livelihood_zone.country.name", read_only=True
    )
    product_common_name = serializers.CharField(source="product.common_name", read_only=True)
    product_description = serializers.CharField(source="product.description", read_only=True)
    seasonal_activity_type_name = serializers.CharField(source="seasonal_activity_type.name", read_only=True)
    seasonal_activity_type_description = serializers.CharField(
        source="seasonal_activity_type.description", read_only=True
    )
    activity_category = serializers.CharField(source="seasonal_activity_type.activity_category", read_only=True)
    activity_category_label = serializers.SerializerMethodField()
    additional_identifier = serializers.CharField(read_only=True)

    def get_activity_category_label(self, obj):
        return obj.seasonal_activity_type.get_activity_category_display()

    source_organization = serializers.IntegerField(
        source="livelihood_zone_baseline.source_organization.pk", read_only=True
    )
    source_organization_name = serializers.CharField(
        source="livelihood_zone_baseline.source_organization.name", read_only=True
    )
    livelihood_zone_baseline_label = serializers.SerializerMethodField()

    def get_livelihood_zone_baseline_label(self, obj):
        return str(obj.livelihood_zone_baseline)


class SeasonalActivityOccurrenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeasonalActivityOccurrence
        fields = [
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            # SeasonalActivity
            "seasonal_activity",
            "seasonal_activity_type",
            "seasonal_activity_type_name",
            "seasonal_activity_type_description",
            "activity_category",
            "activity_category_label",
            "product",
            "product_common_name",
            "product_description",
            "additional_identifier",
            # End SeasonalActivity
            "community",
            "community_name",
            "start",
            "end",
        ]

    livelihood_zone_name = serializers.CharField(
        source="livelihood_zone_baseline.livelihood_zone.name", read_only=True
    )
    livelihood_zone = serializers.CharField(source="livelihood_zone_baseline.livelihood_zone.pk", read_only=True)
    livelihood_zone_country = serializers.CharField(
        source="livelihood_zone_baseline.livelihood_zone.country.pk", read_only=True
    )
    livelihood_zone_country_name = serializers.CharField(
        source="livelihood_zone_baseline.livelihood_zone.country.name", read_only=True
    )
    community_name = serializers.CharField(source="community.name", read_only=True)
    source_organization = serializers.IntegerField(
        source="livelihood_zone_baseline.source_organization.pk", read_only=True
    )
    source_organization_name = serializers.CharField(
        source="livelihood_zone_baseline.source_organization.name", read_only=True
    )
    livelihood_zone_baseline_label = serializers.SerializerMethodField()

    def get_livelihood_zone_baseline_label(self, obj):
        return str(obj.livelihood_zone_baseline)

    product = serializers.CharField(source="seasonal_activity.product.pk", read_only=True)
    product_common_name = serializers.CharField(source="seasonal_activity.product.common_name", read_only=True)
    product_description = serializers.CharField(source="seasonal_activity.product.description", read_only=True)
    additional_identifier = serializers.CharField(source="seasonal_activity.additional_identifier", read_only=True)
    seasonal_activity_type = serializers.CharField(
        source="seasonal_activity.seasonal_activity_type.pk", read_only=True
    )
    seasonal_activity_type_name = serializers.CharField(
        source="seasonal_activity.seasonal_activity_type.name", read_only=True
    )
    seasonal_activity_type_description = serializers.CharField(
        source="seasonal_activity.seasonal_activity_type.description", read_only=True
    )
    activity_category = serializers.CharField(
        source="seasonal_activity.seasonal_activity_type.activity_category", read_only=True
    )
    activity_category_label = serializers.SerializerMethodField()

    def get_activity_category_label(self, obj):
        return obj.seasonal_activity.seasonal_activity_type.get_activity_category_display()


class CommunityCropProductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityCropProduction
        fields = [
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "community",
            "community_name",
            "crop",
            "crop_common_name",
            "crop_description",
            "crop_purpose",
            "crop_purpose_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "yield_with_inputs",
            "yield_without_inputs",
            "seed_requirement",
            "crop_unit_of_measure",
            "crop_unit_of_measure_name",
            "crop_unit_of_measure_description",
            "land_unit_of_measure",
            "land_unit_of_measure_name",
            "land_unit_of_measure_description",
        ]

    crop_common_name = serializers.CharField(source="crop.common_name", read_only=True)
    crop_description = serializers.CharField(source="crop.description", read_only=True)
    community_name = serializers.CharField(source="community.name", read_only=True)
    crop_unit_of_measure_name = serializers.CharField(source="crop_unit_of_measure.name", read_only=True)
    crop_unit_of_measure_description = serializers.CharField(source="crop_unit_of_measure.description", read_only=True)
    land_unit_of_measure_name = serializers.CharField(source="land_unit_of_measure.name", read_only=True)
    land_unit_of_measure_description = serializers.CharField(source="land_unit_of_measure.description", read_only=True)
    season_name = serializers.CharField(source="season.name", read_only=True)
    season_description = serializers.CharField(source="season.description", read_only=True)
    season_type = serializers.CharField(source="season.season_type", read_only=True)
    season_type_label = serializers.SerializerMethodField()

    def get_season_type_label(self, obj):
        return obj.season.get_season_type_display() if obj.season else ""

    crop_purpose_label = serializers.SerializerMethodField()

    def get_crop_purpose_label(self, obj):
        return obj.get_crop_purpose_display()

    livelihood_zone_baseline = serializers.IntegerField(source="community.livelihood_zone_baseline.pk", read_only=True)
    livelihood_zone_name = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.name", read_only=True
    )
    livelihood_zone = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.pk", read_only=True
    )
    livelihood_zone_country = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.country.pk", read_only=True
    )
    livelihood_zone_country_name = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.country.name", read_only=True
    )
    source_organization = serializers.IntegerField(
        source="community.livelihood_zone_baseline.source_organization.pk", read_only=True
    )
    source_organization_name = serializers.CharField(
        source="community.livelihood_zone_baseline.source_organization.name", read_only=True
    )
    livelihood_zone_baseline_label = serializers.SerializerMethodField()

    def get_livelihood_zone_baseline_label(self, obj):
        return str(obj.community.livelihood_zone_baseline)


class CommunityLivestockSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityLivestock
        fields = [
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "community",
            "community_name",
            "livestock",
            "livestock_common_name",
            "livestock_description",
            "birth_interval",
            "wet_season_lactation_period",
            "wet_season_milk_production",
            "dry_season_lactation_period",
            "dry_season_milk_production",
            "age_at_sale",
            "additional_attributes",
        ]

    livelihood_zone_baseline = serializers.IntegerField(source="community.livelihood_zone_baseline.pk", read_only=True)
    livelihood_zone_name = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.name", read_only=True
    )
    livelihood_zone = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.pk", read_only=True
    )
    livelihood_zone_country = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.country.pk", read_only=True
    )
    livelihood_zone_country_name = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.country.name", read_only=True
    )
    community_name = serializers.CharField(source="community.name", read_only=True)
    source_organization = serializers.IntegerField(
        source="community.livelihood_zone_baseline.source_organization.pk", read_only=True
    )
    source_organization_name = serializers.CharField(
        source="community.livelihood_zone_baseline.source_organization.name", read_only=True
    )
    livelihood_zone_baseline_label = serializers.SerializerMethodField()

    def get_livelihood_zone_baseline_label(self, obj):
        return str(obj.community.livelihood_zone_baseline)

    livestock_common_name = serializers.CharField(source="livestock.common_name", read_only=True)
    livestock_description = serializers.CharField(source="livestock.description", read_only=True)


class MarketPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketPrice
        fields = [
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "community",
            "community_name",
            "market",
            "market_name",
            "market_description",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_name",
            "unit_of_measure_description",
            "currency",
            "description",
            "low_price_start",
            "low_price_end",
            "low_price",
            "high_price_start",
            "high_price_end",
            "high_price",
        ]

    market_name = serializers.CharField(source="market.name", read_only=True)
    market_description = serializers.CharField(source="market.description", read_only=True)
    product = serializers.CharField(source="product.pk", read_only=True)
    product_common_name = serializers.CharField(source="product.common_name", read_only=True)
    product_description = serializers.CharField(source="product.description", read_only=True)
    unit_of_measure_name = serializers.CharField(source="unit_of_measure.name", read_only=True)
    unit_of_measure_description = serializers.CharField(source="unit_of_measure.description", read_only=True)
    livelihood_zone_baseline = serializers.IntegerField(source="community.livelihood_zone_baseline.pk", read_only=True)
    livelihood_zone_name = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.name", read_only=True
    )
    livelihood_zone = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.pk", read_only=True
    )
    livelihood_zone_country = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.country.pk", read_only=True
    )
    livelihood_zone_country_name = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.country.name", read_only=True
    )
    community_name = serializers.CharField(source="community.name", read_only=True)
    source_organization = serializers.IntegerField(
        source="community.livelihood_zone_baseline.source_organization.pk", read_only=True
    )
    source_organization_name = serializers.CharField(
        source="community.livelihood_zone_baseline.source_organization.name", read_only=True
    )
    livelihood_zone_baseline_label = serializers.SerializerMethodField()

    def get_livelihood_zone_baseline_label(self, obj):
        return str(obj.community.livelihood_zone_baseline)


class SeasonalProductionPerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeasonalProductionPerformance
        fields = [
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "community",
            "community_name",
            "performance_year_start_date",
            "performance_year_end_date",
            "seasonal_performance",
            "seasonal_performance_label",
        ]

    livelihood_zone_baseline = serializers.IntegerField(source="community.livelihood_zone_baseline.pk", read_only=True)
    livelihood_zone_name = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.name", read_only=True
    )
    livelihood_zone = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.pk", read_only=True
    )
    livelihood_zone_country = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.country.pk", read_only=True
    )
    livelihood_zone_country_name = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.country.name", read_only=True
    )
    community_name = serializers.CharField(source="community.name", read_only=True)
    source_organization = serializers.IntegerField(
        source="community.livelihood_zone_baseline.source_organization.pk", read_only=True
    )
    source_organization_name = serializers.CharField(
        source="community.livelihood_zone_baseline.source_organization.name", read_only=True
    )
    livelihood_zone_baseline_label = serializers.SerializerMethodField()

    def get_livelihood_zone_baseline_label(self, obj):
        return str(obj.community.livelihood_zone_baseline)

    seasonal_performance_label = serializers.SerializerMethodField()

    def get_seasonal_performance_label(self, obj):
        return obj.get_seasonal_performance_display()


class HazardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hazard
        fields = [
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "community",
            "community_name",
            "chronic_or_periodic",
            "chronic_or_periodic_label",
            "ranking",
            "ranking_label",
            "hazard_category",
            "hazard_category_name",
            "hazard_category_description",
            "description",
        ]

    livelihood_zone_baseline = serializers.IntegerField(source="community.livelihood_zone_baseline.pk", read_only=True)
    hazard_category_name = serializers.CharField(source="hazard_category.name", read_only=True)
    hazard_category_description = serializers.CharField(source="hazard_category.description", read_only=True)
    livelihood_zone_name = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.name", read_only=True
    )
    livelihood_zone = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.pk", read_only=True
    )
    livelihood_zone_country = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.country.pk", read_only=True
    )
    livelihood_zone_country_name = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.country.name", read_only=True
    )
    community_name = serializers.CharField(source="community.name", read_only=True)
    source_organization = serializers.IntegerField(
        source="community.livelihood_zone_baseline.source_organization.pk", read_only=True
    )
    source_organization_name = serializers.CharField(
        source="community.livelihood_zone_baseline.source_organization.name", read_only=True
    )
    livelihood_zone_baseline_label = serializers.SerializerMethodField()

    def get_livelihood_zone_baseline_label(self, obj):
        return str(obj.community.livelihood_zone_baseline)

    chronic_or_periodic_label = serializers.SerializerMethodField()

    def get_chronic_or_periodic_label(self, obj):
        return obj.get_chronic_or_periodic_display()

    ranking_label = serializers.SerializerMethodField()

    def get_ranking_label(self, obj):
        return obj.get_ranking_display()


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "community",
            "community_name",
            "event_year_start_date",
            "event_year_end_date",
            "description",
        ]

    livelihood_zone_baseline = serializers.IntegerField(source="community.livelihood_zone_baseline.pk", read_only=True)
    livelihood_zone_name = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.name", read_only=True
    )
    livelihood_zone = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.pk", read_only=True
    )
    livelihood_zone_country = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.country.pk", read_only=True
    )
    livelihood_zone_country_name = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.country.name", read_only=True
    )
    community_name = serializers.CharField(source="community.name", read_only=True)
    source_organization = serializers.IntegerField(
        source="community.livelihood_zone_baseline.source_organization.pk", read_only=True
    )
    source_organization_name = serializers.CharField(
        source="community.livelihood_zone_baseline.source_organization.name", read_only=True
    )
    livelihood_zone_baseline_label = serializers.SerializerMethodField()

    def get_livelihood_zone_baseline_label(self, obj):
        return str(obj.community.livelihood_zone_baseline)


class ExpandabilityFactorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpandabilityFactor
        fields = [
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone_name",
            "livelihood_zone",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "community",
            "community_name",
            # LivelihoodStrategy
            "livelihood_strategy",
            "strategy_type",
            "strategy_type_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_name",
            "unit_of_measure_description",
            "currency",
            "additional_identifier",
            # End LivelihoodStrategy
            # WealthGroup
            "wealth_group",
            "wealth_group_label",
            "wealth_group_category",
            "wealth_group_category_name",
            "wealth_group_category_description",
            "wealth_group_percentage_of_households",
            "wealth_group_average_household_size",
            # End WealthGroup
            "percentage_produced",
            "percentage_sold",
            "percentage_other_uses",
            "percentage_consumed",
            "percentage_income",
            "percentage_expenditure",
            "remark",
        ]

    livelihood_zone_name = serializers.CharField(
        source="wealth_group.community.livelihood_zone_baseline.livelihood_zone.name", read_only=True
    )
    livelihood_zone = serializers.CharField(
        source="wealth_group.community.livelihood_zone_baseline.livelihood_zone.pk", read_only=True
    )
    livelihood_zone_country = serializers.CharField(
        source="wealth_group.community.livelihood_zone_baseline.livelihood_zone.country.pk", read_only=True
    )
    livelihood_zone_country_name = serializers.CharField(
        source="wealth_group.community.livelihood_zone_baseline.livelihood_zone.country.name", read_only=True
    )
    source_organization = serializers.IntegerField(
        source="wealth_group.community.livelihood_zone_baseline.source_organization.pk", read_only=True
    )
    source_organization_name = serializers.CharField(
        source="wealth_group.community.livelihood_zone_baseline.source_organization.name", read_only=True
    )

    livelihood_zone_baseline = serializers.IntegerField(
        source="wealth_group.community.livelihood_zone_baseline.pk", read_only=True
    )
    livelihood_zone_baseline_label = serializers.SerializerMethodField()

    def get_livelihood_zone_baseline_label(self, obj):
        return str(obj.wealth_group.community.livelihood_zone_baseline)

    additional_identifier = serializers.CharField(source="livelihood_strategy.additional_identifier", read_only=True)
    currency = serializers.CharField(source="livelihood_strategy.currency.pk", read_only=True)
    community = serializers.IntegerField(source="wealth_group.community.pk", read_only=True)
    community_name = serializers.CharField(source="wealth_group.community.name", read_only=True)
    unit_of_measure = serializers.CharField(source="livelihood_strategy.unit_of_measure.pk", read_only=True)
    unit_of_measure_name = serializers.CharField(source="livelihood_strategy.unit_of_measure.name", read_only=True)
    unit_of_measure_description = serializers.CharField(
        source="livelihood_strategy.unit_of_measure.description", read_only=True
    )
    product = serializers.CharField(source="livelihood_strategy.product.pk", read_only=True)
    product_common_name = serializers.CharField(source="livelihood_strategy.product.common_name", read_only=True)
    product_description = serializers.CharField(source="livelihood_strategy.product.description", read_only=True)
    season = serializers.IntegerField(source="livelihood_strategy.season.pk", read_only=True)
    season_name = serializers.CharField(source="livelihood_strategy.season.name", read_only=True)
    season_description = serializers.CharField(source="livelihood_strategy.season.description", read_only=True)
    season_type = serializers.CharField(source="livelihood_strategy.season.season_type", read_only=True)
    season_type_label = serializers.SerializerMethodField()
    wealth_group_percentage_of_households = serializers.IntegerField(
        source="wealth_group.percentage_of_households", read_only=True
    )
    wealth_group_average_household_size = serializers.IntegerField(
        source="wealth_group.average_household_size", read_only=True
    )
    wealth_group_category = serializers.CharField(source="wealth_group.wealth_group_category.pk", read_only=True)
    wealth_group_category_name = serializers.CharField(
        source="wealth_group.wealth_group_category.name", read_only=True
    )
    wealth_group_category_description = serializers.CharField(
        source="wealth_group.wealth_group_category.description", read_only=True
    )

    def get_season_type_label(self, obj):
        return obj.livelihood_strategy.season.get_season_type_display() if obj.livelihood_strategy.season else ""

    strategy_type = serializers.CharField(source="livelihood_strategy.strategy_type", read_only=True)
    strategy_type_label = serializers.SerializerMethodField()

    def get_strategy_type_label(self, obj):
        return obj.livelihood_strategy.get_strategy_type_display()

    wealth_group_label = serializers.SerializerMethodField()

    def get_wealth_group_label(self, obj):
        return str(obj.wealth_group)


class CopingStrategySerializer(serializers.ModelSerializer):
    class Meta:
        model = CopingStrategy
        fields = [
            "id",
            "community",
            "community_name",
            "leaders",
            # WealthGroup
            "wealth_group",
            "wealth_group_label",
            "wealth_group_category",
            "wealth_group_category_name",
            "wealth_group_category_description",
            "wealth_group_percentage_of_households",
            "wealth_group_average_household_size",
            # End WealthGroup
            # LivelihoodStrategy
            "livelihood_strategy",
            "source_organization",
            "source_organization_name",
            "livelihood_zone_baseline",
            "livelihood_zone_baseline_label",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "strategy_type",
            "strategy_type_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
            "unit_of_measure",
            "unit_of_measure_name",
            "unit_of_measure_description",
            "currency",
            "additional_identifier",
            # End LivelihoodStrategy
            "strategy",
            "strategy_label",
            "by_value",
        ]

    livelihood_zone_baseline = serializers.IntegerField(source="community.livelihood_zone_baseline.pk", read_only=True)
    livelihood_zone_name = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.name", read_only=True
    )
    livelihood_zone = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.pk", read_only=True
    )
    livelihood_zone_country = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.country.pk", read_only=True
    )
    livelihood_zone_country_name = serializers.CharField(
        source="community.livelihood_zone_baseline.livelihood_zone.country.name", read_only=True
    )
    source_organization = serializers.IntegerField(
        source="community.livelihood_zone_baseline.source_organization.pk", read_only=True
    )
    source_organization_name = serializers.CharField(
        source="community.livelihood_zone_baseline.source_organization.name", read_only=True
    )
    livelihood_zone_baseline_label = serializers.SerializerMethodField()

    def get_livelihood_zone_baseline_label(self, obj):
        return str(obj.community.livelihood_zone_baseline)

    additional_identifier = serializers.CharField(source="livelihood_strategy.additional_identifier", read_only=True)
    currency = serializers.CharField(source="livelihood_strategy.currency.pk", read_only=True)
    unit_of_measure = serializers.CharField(source="livelihood_strategy.unit_of_measure.pk", read_only=True)
    unit_of_measure_name = serializers.CharField(source="livelihood_strategy.unit_of_measure.name", read_only=True)
    unit_of_measure_description = serializers.CharField(
        source="livelihood_strategy.unit_of_measure.description", read_only=True
    )
    product = serializers.CharField(source="livelihood_strategy.product.pk", read_only=True)
    product_common_name = serializers.CharField(source="livelihood_strategy.product.common_name", read_only=True)
    product_description = serializers.CharField(source="livelihood_strategy.product.description", read_only=True)
    season = serializers.IntegerField(source="livelihood_strategy.season.pk", read_only=True)
    season_name = serializers.CharField(source="livelihood_strategy.season.name", read_only=True)
    season_description = serializers.CharField(source="livelihood_strategy.season.description", read_only=True)
    season_type = serializers.CharField(source="livelihood_strategy.season.season_type", read_only=True)
    season_type_label = serializers.SerializerMethodField()
    wealth_group_percentage_of_households = serializers.IntegerField(
        source="wealth_group.percentage_of_households", read_only=True
    )
    wealth_group_average_household_size = serializers.IntegerField(
        source="wealth_group.average_household_size", read_only=True
    )
    wealth_group_category = serializers.CharField(source="wealth_group.wealth_group_category.pk", read_only=True)
    wealth_group_category_name = serializers.CharField(
        source="wealth_group.wealth_group_category.name", read_only=True
    )
    wealth_group_category_description = serializers.CharField(
        source="wealth_group.wealth_group_category.description", read_only=True
    )

    def get_season_type_label(self, obj):
        return obj.livelihood_strategy.season.get_season_type_display() if obj.livelihood_strategy.season else ""

    strategy_type = serializers.CharField(source="livelihood_strategy.strategy_type", read_only=True)
    strategy_type_label = serializers.SerializerMethodField()

    def get_strategy_type_label(self, obj):
        return obj.livelihood_strategy.get_strategy_type_display()

    community_name = serializers.CharField(source="community.name", read_only=True)
    strategy_label = serializers.SerializerMethodField()

    def get_strategy_label(self, obj):
        return obj.get_strategy_display()

    wealth_group_label = serializers.SerializerMethodField()

    def get_wealth_group_label(self, obj):
        return str(obj.wealth_group)


class DictQuerySetField(rest_framework_fields.SerializerMethodField):
    def __init__(self, field_name=None, **kwargs):
        self.field_name = field_name
        super().__init__(**kwargs)

    def to_representation(self, obj):
        return self.parent.get_field(obj, self.field_name)


class LivelihoodZoneBaselineReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = LivelihoodZoneBaseline
        fields = (
            "id",
            "name",
            "description",
            "source_organization",
            "source_organization_name",
            "livelihood_zone",
            "livelihood_zone_name",
            "country_pk",
            "country_iso_en_name",
            "main_livelihood_category",
            "bss",
            "currency",
            "reference_year_start_date",
            "reference_year_end_date",
            "valid_from_date",
            "valid_to_date",  # to display "is latest" / "is historic" in the UI for each ref yr
            "population_source",
            "population_estimate",
            "livelihoodzone_pk",
            "livelihood_strategy_pk",
            "strategy_type",
            "livelihood_activity_pk",
            "wealth_group_category_code",
            "population_estimate",
            "product_cpc",
            "product_common_name",
            "slice_sum_kcals_consumed",
            "sum_kcals_consumed",
            "kcals_consumed_percent",
            "sum_income",
            "slice_sum_income",
            "income_percent",
            "sum_expenditure",
            "slice_sum_expenditure",
            "expenditure_percent",
        )

    # For each of these aggregates the following calculation columns are added:
    #   (a) Total at the LZB level (filtered by population, wealth group, etc), eg, sum_kcals_consumed.
    #   (b) Total for the selected product/strategy type slice, eg, slice_sum_kcals_consumed.
    #   (c) The percentage the slice represents of the whole, eg, kcals_consumed_percent.
    # Filters are automatically created, eg, min_kcals_consumed_percent and max_kcals_consumed_percent.
    # If no ordering is specified by the FilterSet, the results are ordered by percent descending in the order here.
    aggregates = {
        "kcals_consumed": Sum,
        "income": Sum,
        "expenditure": Sum,
    }

    # For each of these pairs, a URL parameter is created "slice_{field}", eg, ?slice_product=
    # They can appear zero, one or multiple times in the URL, and define a sub-slice of the row-level data.
    # A slice includes activities with ANY of the products, AND, ANY of the strategy types.
    # For example: (product=R0 OR product=L0) AND (strategy_type=MilkProd OR strategy_type=CropProd)
    slice_fields = {
        "product": "livelihood_strategies__product__cpc__istartswith",
        # this parameter must be set to one of values (not labels) from LivelihoodStrategyType, eg, MilkProduction
        "strategy_type": "livelihood_strategies__strategy_type__iexact",
        # TODO: Support filter expressions on the right here, so we can slice on, for example, a
        #  WealthGroupCharacteristicValue where WealthGroupCharacteristic is some hard-coded value,
        #  eg, the slice on WGCV where WGC=PhoneOwnership, or on WGCV > 3 where WGC=HouseholdSize, eg:
        #  {"phone_ownership": lambda val: Q(wgcv__path=val, wgc__path__code="PhoneOwnership")}
    }

    livelihood_zone_name = DictQuerySetField("livelihood_zone_name")
    source_organization_name = DictQuerySetField("source_organization_pk")
    country_pk = DictQuerySetField("country_pk")
    country_iso_en_name = DictQuerySetField("country_iso_en_name")
    livelihoodzone_pk = DictQuerySetField("livelihoodzone_pk")
    livelihood_strategy_pk = DictQuerySetField("livelihood_strategy_pk")
    livelihood_activity_pk = DictQuerySetField("livelihood_activity_pk")
    wealth_group_category_code = DictQuerySetField("wealth_group_category_code")
    id = DictQuerySetField("id")
    name = DictQuerySetField("name")
    description = DictQuerySetField("description")
    source_organization = DictQuerySetField("source_organization")
    livelihood_zone = DictQuerySetField("livelihood_zone")
    main_livelihood_category = DictQuerySetField("main_livelihood_category")
    bss = DictQuerySetField("bss")
    currency = DictQuerySetField("currency")
    reference_year_start_date = DictQuerySetField("reference_year_start_date")
    reference_year_end_date = DictQuerySetField("reference_year_end_date")
    valid_from_date = DictQuerySetField("valid_from_date")
    valid_to_date = DictQuerySetField("valid_to_date")
    population_source = DictQuerySetField("population_source")
    population_estimate = DictQuerySetField("population_estimate")
    product_cpc = DictQuerySetField("product_cpc")
    product_common_name = DictQuerySetField("product_common_name")
    strategy_type = DictQuerySetField("strategy_type")

    slice_sum_kcals_consumed = DictQuerySetField("slice_sum_kcals_consumed")
    sum_kcals_consumed = DictQuerySetField("sum_kcals_consumed")
    kcals_consumed_percent = DictQuerySetField("kcals_consumed_percent")

    slice_sum_income = DictQuerySetField("slice_sum_income")
    sum_income = DictQuerySetField("sum_income")
    income_percent = DictQuerySetField("income_percent")

    slice_sum_expenditure = DictQuerySetField("slice_sum_expenditure")
    sum_expenditure = DictQuerySetField("sum_expenditure")
    expenditure_percent = DictQuerySetField("expenditure_percent")

    def get_fields(self):
        """
        User can specify fields= parameter to specify a field list, comma-delimited.

        If the fields parameter is not passed or does not match fields, defaults to self.Meta.fields.

        The aggregated fields self.aggregates are added regardless of user field selection.
        """
        field_list = "request" in self.context and self.context["request"].query_params.get("fields", None)
        if not field_list:
            return super().get_fields()

        # User-provided list of fields
        field_names = set(field_list.split(","))

        # Add the aggregates that are always returned
        for field_name, aggregate in self.aggregates.items():
            field_names |= {
                field_name,
                self.aggregate_field_name(field_name, aggregate),
                self.slice_aggregate_field_name(field_name, aggregate),
                self.slice_percent_field_name(field_name, aggregate),
            }

        # Add the ordering field if specified
        ordering = self.context["request"].query_params.get("ordering")
        if ordering:
            field_names.add(ordering)

        # Remove any that don't match a field as a dict
        return {k: v for k, v in super().get_fields().items() if k in field_names}

    def get_field(self, obj, field_name):
        """
        Aggregated querysets are a list of dicts.
        This is called by AggregatedQuerysetField to get the value from the row dict.
        """
        db_field = self.field_to_database_path(field_name)
        value = obj.get(db_field, "")
        # Get the readable, translated string from the choice key.
        if field_name == "strategy_type" and value:
            return dict(LivelihoodStrategyType.choices).get(value, value)
        return value

    @staticmethod
    def field_to_database_path(field_name):
        language_code = translation.get_language()
        return {
            "livelihoodzone_pk": "pk",
            "name": f"name_{language_code}",
            "description": f"description_{language_code}",
            "valid_to_date": "valid_to_date",
            "livelihood_strategy_pk": "livelihood_strategies__pk",
            "livelihood_activity_pk": "livelihood_strategies__livelihoodactivity__pk",
            "wealth_group_category_code": "livelihood_strategies__livelihoodactivity__wealth_group__wealth_group_category__code",  # NOQA: E501
            "kcals_consumed": "livelihood_strategies__livelihoodactivity__kcals_consumed",
            "income": "livelihood_strategies__livelihoodactivity__income",
            "expenditure": "livelihood_strategies__livelihoodactivity__expenditure",
            "percentage_kcals": "livelihood_strategies__livelihoodactivity__percentage_kcals",
            "livelihood_zone_name": f"livelihood_zone__name_{language_code}",
            "source_organization_pk": "source_organization__pk",
            "source_organization_name": "source_organization__name",
            "country_pk": "livelihood_zone__country__pk",
            "country_iso_en_name": "livelihood_zone__country__iso_en_name",
            "product_cpc": "livelihood_strategies__product__cpc",
            "strategy_type": "livelihood_strategies__strategy_type",
            "product_common_name": f"livelihood_strategies__product__common_name_{language_code}",
        }.get(field_name, field_name)

    @staticmethod
    def aggregate_field_name(field_name, aggregate):
        return f"{aggregate.name.lower()}_{field_name}"  # eg, sum_kcals_consumed

    @staticmethod
    def slice_aggregate_field_name(field_name, aggregate):
        return f"slice_{aggregate.name.lower()}_{field_name}"  # eg, slice_sum_kcals_consumed

    @staticmethod
    def slice_percent_field_name(field_name, aggregate):
        return f"{field_name}_percent"  # eg, kcals_consumed_percent
