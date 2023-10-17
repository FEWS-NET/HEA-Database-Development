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
        fields = [
            "id",
            "name",
            "full_name",
            "description",
        ]


class LivelihoodZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = LivelihoodZone
        fields = [
            "code",
            "name",
            "description",
            "country",
            "country_name",
        ]

    country_name = serializers.CharField(source="country.iso_en_ro_name", read_only=True)


class LivelihoodZoneBaselineSerializer(serializers.ModelSerializer):
    class Meta:
        model = LivelihoodZoneBaseline
        fields = [
            "id",
            "source_organization",
            "source_organization_name",
            "livelihood_zone",
            "livelihood_zone_name",
            "livelihood_zone_country",
            "livelihood_zone_country_name",
            "geography",
            "main_livelihood_category",
            "bss",
            "reference_year_start_date",
            "reference_year_end_date",
            "valid_from_date",
            "valid_to_date",
            "population_source",
            "population_estimate",
        ]

    livelihood_zone_name = serializers.CharField(source="livelihood_zone.name", read_only=True)
    source_organization_name = serializers.CharField(source="source_organization.pk", read_only=True)
    livelihood_zone_country = serializers.CharField(source="livelihood_zone.country.pk", read_only=True)
    livelihood_zone_country_name = serializers.CharField(source="livelihood_zone.country.name", read_only=True)


class LivelihoodProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = LivelihoodProductCategory
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
            "product",
            "product_common_name",
            "product_description",
            "basket",
            "basket_name",
        ]

    source_organization = serializers.CharField(
        source="livelihood_zone_baseline.source_organization.pk", read_only=True
    )
    source_organization_name = serializers.CharField(
        source="livelihood_zone_baseline.source_organization.name", read_only=True
    )
    livelihood_zone_baseline_label = serializers.SerializerMethodField()

    def get_livelihood_zone_baseline_label(self, obj):
        return str(obj.livelihood_zone_baseline)

    product_description = serializers.CharField(source="product.description", read_only=True)
    product_common_name = serializers.CharField(source="product.common_name", read_only=True)
    livelihood_zone_name = serializers.CharField(
        source="livelihood_zone_baseline.livelihood_zone.name", read_only=True
    )
    livelihood_zone = serializers.CharField(source="livelihood_zone_baseline.livelihood_zone.pk", read_only=True)
    source_organization_name = serializers.CharField(
        source="livelihood_zone_baseline.source_organization.name", read_only=True
    )
    livelihood_zone_country = serializers.CharField(
        source="livelihood_zone_baseline.livelihood_zone.country.pk", read_only=True
    )
    livelihood_zone_country_name = serializers.CharField(
        source="livelihood_zone_baseline.livelihood_zone.country.name", read_only=True
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
            "wealth_category",
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
            "wealth_category",
            "wealth_category_name",
            "wealth_category_description",
            "wealth_characteristic",
            "wealth_characteristic_name",
            "wealth_characteristic_description",
            "value",
            "min_value",
            "max_value",
        ]

    livelihood_zone_baseline_label = serializers.SerializerMethodField()

    def get_livelihood_zone_baseline_label(self, obj):
        return str(obj.wealth_group.community.livelihood_zone_baseline)

    wealth_group_label = serializers.SerializerMethodField()

    def get_wealth_group_label(self, obj):
        return str(obj.wealth_group)

    wealth_category = serializers.CharField(source="wealth_group.wealth_category.pk", read_only=True)
    wealth_category_name = serializers.CharField(source="wealth_group.wealth_category.name", read_only=True)
    wealth_category_description = serializers.CharField(
        source="wealth_group.wealth_category.description", read_only=True
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
            "household_labor_provider",
            "household_labor_provider_label",
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
        return obj.season.get_season_type_display()

    strategy_type_label = serializers.SerializerMethodField()

    def get_strategy_type_label(self, obj):
        return obj.get_strategy_type_display()

    household_labor_provider_label = serializers.SerializerMethodField()

    def get_household_labor_provider_label(self, obj):
        return obj.get_household_labor_provider_display()

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
            "household_labor_provider",
            "household_labor_provider_label",
            # End LivelihoodStrategy
            "scenario",
            "scenario_label",
            # WealthGroup
            "wealth_group",
            "wealth_group_label",
            "community",
            "community_name",
            "wealth_category",
            "wealth_category_name",
            "wealth_category_description",
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

    household_labor_provider = serializers.CharField(
        source="livelihood_strategy.household_labor_provider", read_only=True
    )
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
    wealth_category = serializers.CharField(source="wealth_group.wealth_category.pk", read_only=True)
    wealth_category_name = serializers.CharField(source="wealth_group.wealth_category.name", read_only=True)
    wealth_category_description = serializers.CharField(
        source="wealth_group.wealth_category.description", read_only=True
    )

    def get_season_type_label(self, obj):
        return obj.livelihood_strategy.season.get_season_type_display()

    strategy_type_label = serializers.SerializerMethodField()

    def get_strategy_type_label(self, obj):
        return obj.livelihood_strategy.get_strategy_type_display()

    household_labor_provider_label = serializers.SerializerMethodField()

    def get_household_labor_provider_label(self, obj):
        return obj.livelihood_strategy.get_household_labor_provider_display()

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


class LivestockSalesSerializer(LivelihoodActivitySerializer):
    class Meta:
        model = LivestockSales
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
            "purchases_per_month",
            "months_per_year",
        ]


class PaymentInKindSerializer(LivelihoodActivitySerializer):
    class Meta:
        model = PaymentInKind
        fields = LivelihoodActivitySerializer.Meta.fields + [
            "payment_per_time",
            "people_per_hh",
            "labor_per_month",
            "months_per_year",
        ]


class ReliefGiftsOtherSerializer(LivelihoodActivitySerializer):
    class Meta:
        model = ReliefGiftsOther
        fields = LivelihoodActivitySerializer.Meta.fields + [
            "unit_multiple",
            "received_per_year",
        ]


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
            "people_per_hh",
            "labor_per_month",
            "months_per_year",
            "times_per_year",
        ]


class OtherPurchasesSerializer(LivelihoodActivitySerializer):
    class Meta:
        model = OtherPurchases
        fields = LivelihoodActivitySerializer.Meta.fields + [
            "unit_multiple",
            "purchases_per_month",
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
            "activity_type",
            "activity_type_name",
            "activity_type_description",
            "activity_category",
            "activity_category_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
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
    activity_type_name = serializers.CharField(source="activity_type.name", read_only=True)
    activity_type_description = serializers.CharField(source="activity_type.description", read_only=True)
    activity_category = serializers.CharField(source="activity_type.activity_category", read_only=True)
    activity_category_label = serializers.SerializerMethodField()

    def get_activity_category_label(self, obj):
        return obj.activity_type.get_activity_category_display()

    season_name = serializers.CharField(source="season.name", read_only=True)
    season_description = serializers.CharField(source="season.description", read_only=True)
    season_type = serializers.CharField(source="season.season_type", read_only=True)
    season_type_label = serializers.SerializerMethodField()

    def get_season_type_label(self, obj):
        return obj.season.get_season_type_display()

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
            "activity_type",
            "activity_type_name",
            "activity_type_description",
            "activity_category",
            "activity_category_label",
            "season",
            "season_name",
            "season_description",
            "season_type",
            "season_type_label",
            "product",
            "product_common_name",
            "product_description",
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
    activity_type = serializers.CharField(source="seasonal_activity.activity_type.pk", read_only=True)
    activity_type_name = serializers.CharField(source="seasonal_activity.activity_type.name", read_only=True)
    activity_type_description = serializers.CharField(
        source="seasonal_activity.activity_type.description", read_only=True
    )
    activity_category = serializers.CharField(
        source="seasonal_activity.activity_type.activity_category", read_only=True
    )
    activity_category_label = serializers.SerializerMethodField()

    def get_activity_category_label(self, obj):
        return obj.seasonal_activity.activity_type.get_activity_category_display()

    season = serializers.CharField(source="seasonal_activity.season.pk", read_only=True)
    season_name = serializers.CharField(source="seasonal_activity.season.name", read_only=True)
    season_description = serializers.CharField(source="seasonal_activity.season.description", read_only=True)
    season_type = serializers.CharField(source="seasonal_activity.season.season_type", read_only=True)
    season_type_label = serializers.SerializerMethodField()

    def get_season_type_label(self, obj):
        return obj.seasonal_activity.season.get_season_type_display()


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
            "unit_of_measure",
            "unit_of_measure_name",
            "unit_of_measure_description",
        ]

    crop_common_name = serializers.CharField(source="crop.common_name", read_only=True)
    crop_description = serializers.CharField(source="crop.description", read_only=True)
    community_name = serializers.CharField(source="community.name", read_only=True)
    unit_of_measure_name = serializers.CharField(source="unit_of_measure.name", read_only=True)
    unit_of_measure_description = serializers.CharField(source="unit_of_measure.description", read_only=True)
    season_name = serializers.CharField(source="season.name", read_only=True)
    season_description = serializers.CharField(source="season.description", read_only=True)
    season_type = serializers.CharField(source="season.season_type", read_only=True)
    season_type_label = serializers.SerializerMethodField()

    def get_season_type_label(self, obj):
        return obj.season.get_season_type_display()

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


class AnnualProductionPerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnualProductionPerformance
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
            "annual_performance",
            "annual_performance_label",
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

    annual_performance_label = serializers.SerializerMethodField()

    def get_annual_performance_label(self, obj):
        return obj.get_annual_performance_display()


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
            "household_labor_provider",
            "household_labor_provider_label",
            # End LivelihoodStrategy
            # WealthGroup
            "wealth_group",
            "wealth_group_label",
            "wealth_category",
            "wealth_category_name",
            "wealth_category_description",
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

    household_labor_provider = serializers.CharField(
        source="livelihood_strategy.household_labor_provider", read_only=True
    )
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
    wealth_category = serializers.CharField(source="wealth_group.wealth_category.pk", read_only=True)
    wealth_category_name = serializers.CharField(source="wealth_group.wealth_category.name", read_only=True)
    wealth_category_description = serializers.CharField(
        source="wealth_group.wealth_category.description", read_only=True
    )

    def get_season_type_label(self, obj):
        return obj.livelihood_strategy.season.get_season_type_display()

    strategy_type = serializers.CharField(source="livelihood_strategy.strategy_type", read_only=True)
    strategy_type_label = serializers.SerializerMethodField()

    def get_strategy_type_label(self, obj):
        return obj.livelihood_strategy.get_strategy_type_display()

    household_labor_provider_label = serializers.SerializerMethodField()

    def get_household_labor_provider_label(self, obj):
        return obj.livelihood_strategy.get_household_labor_provider_display()

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
            "wealth_category",
            "wealth_category_name",
            "wealth_category_description",
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
            "household_labor_provider",
            "household_labor_provider_label",
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

    household_labor_provider = serializers.CharField(
        source="livelihood_strategy.household_labor_provider", read_only=True
    )
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
    wealth_category = serializers.CharField(source="wealth_group.wealth_category.pk", read_only=True)
    wealth_category_name = serializers.CharField(source="wealth_group.wealth_category.name", read_only=True)
    wealth_category_description = serializers.CharField(
        source="wealth_group.wealth_category.description", read_only=True
    )

    def get_season_type_label(self, obj):
        return obj.livelihood_strategy.season.get_season_type_display()

    strategy_type = serializers.CharField(source="livelihood_strategy.strategy_type", read_only=True)
    strategy_type_label = serializers.SerializerMethodField()

    def get_strategy_type_label(self, obj):
        return obj.livelihood_strategy.get_strategy_type_display()

    household_labor_provider_label = serializers.SerializerMethodField()

    def get_household_labor_provider_label(self, obj):
        return obj.livelihood_strategy.get_household_labor_provider_display()

    community_name = serializers.CharField(source="community.name", read_only=True)
    strategy_label = serializers.SerializerMethodField()

    def get_strategy_label(self, obj):
        return obj.get_strategy_display()

    wealth_group_label = serializers.SerializerMethodField()

    def get_wealth_group_label(self, obj):
        return str(obj.wealth_group)
