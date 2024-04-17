from django.db import models
from django_filters import rest_framework as filters
from rest_framework import viewsets

from common.fields import translation_fields

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
from .serializers import (
    BaselineLivelihoodActivitySerializer,
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
    HuntingSerializer,
    LivelihoodActivitySerializer,
    LivelihoodProductCategorySerializer,
    LivelihoodStrategySerializer,
    LivelihoodZoneBaselineSerializer,
    LivelihoodZoneSerializer,
    LivestockSaleSerializer,
    MarketPriceSerializer,
    MeatProductionSerializer,
    MilkProductionSerializer,
    OtherCashIncomeSerializer,
    OtherPurchaseSerializer,
    PaymentInKindSerializer,
    ReliefGiftOtherSerializer,
    ResponseLivelihoodActivitySerializer,
    SeasonalActivityOccurrenceSerializer,
    SeasonalActivitySerializer,
    SeasonalProductionPerformanceSerializer,
    SourceOrganizationSerializer,
    WealthGroupCharacteristicValueSerializer,
    WealthGroupSerializer,
    WildFoodGatheringSerializer,
)


class SourceOrganizationFilterSet(filters.FilterSet):
    class Meta:
        model = SourceOrganization
        fields = [
            "name",
            "full_name",
            "description",
        ]


class SourceOrganizationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows source organizations to be viewed or edited.
    """

    queryset = SourceOrganization.objects.all()
    serializer_class = SourceOrganizationSerializer
    filterset_class = SourceOrganizationFilterSet
    search_fields = [
        "description",
        "full_name",
        "name",
    ]


class LivelihoodZoneFilterSet(filters.FilterSet):
    class Meta:
        model = LivelihoodZone
        fields = (
            "code",
            *translation_fields("description"),
            *translation_fields("name"),
            "country",
        )


class LivelihoodZoneViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows livelihood zones to be viewed or edited.
    """

    queryset = LivelihoodZone.objects.select_related(
        "country",
    )
    serializer_class = LivelihoodZoneSerializer
    filterset_class = LivelihoodZoneFilterSet
    search_fields = (
        "code",
        "alternate_code",
        *translation_fields("description"),
        *translation_fields("name"),
    )


class LivelihoodZoneBaselineFilterSet(filters.FilterSet):
    class Meta:
        model = LivelihoodZoneBaseline
        fields = (
            "livelihood_zone",
            "main_livelihood_category",
            "source_organization",
            "reference_year_start_date",
            "reference_year_end_date",
            "valid_from_date",
            "valid_to_date",
            "population_source",
            "population_estimate",
            *translation_fields("description"),
            *translation_fields("name"),
            "currency",
        )


class LivelihoodZoneBaselineViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows livelihood zone baselines to be viewed or edited.
    """

    queryset = LivelihoodZoneBaseline.objects.select_related(
        "livelihood_zone__country",
        "source_organization",
    )
    serializer_class = LivelihoodZoneBaselineSerializer
    filterset_class = LivelihoodZoneBaselineFilterSet
    search_fields = (
        *translation_fields("description"),
        *translation_fields("name"),
        "population_source",
    )


class LivelihoodProductCategoryFilterSet(filters.FilterSet):
    class Meta:
        model = LivelihoodProductCategory
        fields = [
            "livelihood_zone_baseline",
            "product",
            "basket",
        ]


class LivelihoodProductCategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows livelihood product categories to be viewed or edited.
    """

    queryset = LivelihoodProductCategory.objects.select_related(
        "livelihood_zone_baseline__livelihood_zone__country",
        "livelihood_zone_baseline__source_organization",
    )
    serializer_class = LivelihoodProductCategorySerializer
    filterset_class = LivelihoodProductCategoryFilterSet


class CommunityFilterSet(filters.FilterSet):
    class Meta:
        model = Community
        fields = [
            "code",
            "name",
            "full_name",
            "livelihood_zone_baseline",
        ]


class CommunityViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows communities to be viewed or edited.
    """

    queryset = Community.objects.select_related(
        "livelihood_zone_baseline__livelihood_zone__country",
        "livelihood_zone_baseline__source_organization",
    )
    serializer_class = CommunitySerializer
    filterset_class = CommunityFilterSet
    search_fields = [
        "code",
        "name",
    ]


class WealthGroupFilterSet(filters.FilterSet):
    class Meta:
        model = WealthGroup
        fields = [
            "livelihood_zone_baseline",
            "community",
            "wealth_group_category",
        ]


class WealthGroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows wealth groups to be viewed or edited.
    """

    queryset = WealthGroup.objects.select_related(
        # Normally it would be better to join to livelihood_zone_baseline via community,
        # but baseline wealth groups don't have a community join.
        "community",
        "livelihood_zone_baseline__livelihood_zone__country",
        "livelihood_zone_baseline__source_organization",
    )
    serializer_class = WealthGroupSerializer
    filterset_class = WealthGroupFilterSet


class BaselineWealthGroupFilterSet(filters.FilterSet):
    class Meta:
        model = BaselineWealthGroup
        fields = [
            "livelihood_zone_baseline",
            "wealth_group_category",
        ]


class BaselineWealthGroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows baseline wealth groups to be viewed or edited.
    """

    queryset = BaselineWealthGroup.objects.select_related(
        "livelihood_zone_baseline__livelihood_zone__country",
        "livelihood_zone_baseline__source_organization",
    )
    serializer_class = BaselineWealthGroupSerializer
    filterset_class = BaselineWealthGroupFilterSet


class CommunityWealthGroupFilterSet(filters.FilterSet):
    class Meta:
        model = CommunityWealthGroup
        fields = [
            "livelihood_zone_baseline",
            "community",
            "wealth_group_category",
        ]


class CommunityWealthGroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows community wealth groups to be viewed or edited.
    """

    queryset = CommunityWealthGroup.objects.select_related(
        "community__livelihood_zone_baseline__livelihood_zone__country",
        "community__livelihood_zone_baseline__source_organization",
    )
    serializer_class = CommunityWealthGroupSerializer
    filterset_class = CommunityWealthGroupFilterSet


class WealthGroupCharacteristicValueFilterSet(filters.FilterSet):
    class Meta:
        model = WealthGroupCharacteristicValue
        fields = [
            "wealth_characteristic",
            "wealth_group",
        ]


class WealthGroupCharacteristicValueViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows wealth characteristic values to be viewed or edited.
    """

    queryset = WealthGroupCharacteristicValue.objects.select_related(
        # Rule of thumb: When there is a choice of routes, eg, here we could use
        # "wealth_group__community__livelihood_zone_baseline" or
        # "wealth_group__livelihood_zone_baseline" (ie, not going via community),
        # favour the option with the lowest cardinality.
        # Here for example, if I use wealth_group__livelihood_zone_baseline, the
        # Django ORM will have to populate a LivelihoodZoneBaseline instance for
        # every WealthGroup instance. By going via the community join, the Django
        # ORM only has to populate a LivelihoodZoneBaseline per Community, which
        # will be 4 or 5 times fewer instances. We also remove the need for a third
        # select_related parameter "wealth_group__community". Performance is not
        # critical, but we need a rule of thumb so everything matches up.
        "wealth_characteristic",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = WealthGroupCharacteristicValueSerializer
    filterset_class = WealthGroupCharacteristicValueFilterSet


class LivelihoodStrategyFilterSet(filters.FilterSet):
    class Meta:
        model = LivelihoodStrategy
        fields = [
            "livelihood_zone_baseline",
            "strategy_type",
            "season",
            "product",
            "unit_of_measure",
            "currency",
            "additional_identifier",
        ]


class LivelihoodStrategyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows livelihood strategies to be viewed or edited.
    """

    queryset = LivelihoodStrategy.objects.select_related(
        "livelihood_zone_baseline__livelihood_zone__country",
        "livelihood_zone_baseline__source_organization",
        "season",
        "unit_of_measure",
    )
    serializer_class = LivelihoodStrategySerializer
    filterset_class = LivelihoodStrategyFilterSet
    search_fields = [
        "additional_identifier",
        "strategy_type",
    ]


class LivelihoodActivityFilterSet(filters.FilterSet):
    class Meta:
        model = LivelihoodActivity
        fields = [
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

    queryset = LivelihoodActivity.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = LivelihoodActivitySerializer
    filterset_class = LivelihoodActivityFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class BaselineLivelihoodActivityFilterSet(filters.FilterSet):
    class Meta:
        model = BaselineLivelihoodActivity
        fields = [
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


class BaselineLivelihoodActivityViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows baseline livelihood activities to be viewed or edited.
    """

    queryset = BaselineLivelihoodActivity.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = BaselineLivelihoodActivitySerializer
    filterset_class = BaselineLivelihoodActivityFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class ResponseLivelihoodActivityFilterSet(filters.FilterSet):
    class Meta:
        model = ResponseLivelihoodActivity
        fields = [
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


class ResponseLivelihoodActivityViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows response livelihood activities to be viewed or edited.
    """

    queryset = ResponseLivelihoodActivity.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = ResponseLivelihoodActivitySerializer
    filterset_class = ResponseLivelihoodActivityFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class MilkProductionFilterSet(filters.FilterSet):
    class Meta:
        model = MilkProduction
        fields = [
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
        ]


class MilkProductionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows milk production to be viewed or edited.
    """

    queryset = MilkProduction.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = MilkProductionSerializer
    filterset_class = MilkProductionFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
        "type_of_milk_sold_or_other_uses",
    ]


class ButterProductionFilterSet(filters.FilterSet):
    class Meta:
        model = ButterProduction
        fields = [
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


class ButterProductionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows butter production to be viewed or edited.
    """

    queryset = ButterProduction.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = ButterProductionSerializer
    filterset_class = ButterProductionFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class MeatProductionFilterSet(filters.FilterSet):
    class Meta:
        model = MeatProduction
        fields = [
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
        ]


class MeatProductionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows meat production to be viewed or edited.
    """

    queryset = MeatProduction.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = MeatProductionSerializer
    filterset_class = MeatProductionFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class LivestockSaleFilterSet(filters.FilterSet):
    class Meta:
        model = LivestockSale
        fields = [
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


class LivestockSaleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows livestock sales to be viewed or edited.
    """

    queryset = LivestockSale.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = LivestockSaleSerializer
    filterset_class = LivestockSaleFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class CropProductionFilterSet(filters.FilterSet):
    class Meta:
        model = CropProduction
        fields = [
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

    queryset = CropProduction.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = CropProductionSerializer
    filterset_class = CropProductionFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class FoodPurchaseFilterSet(filters.FilterSet):
    class Meta:
        model = FoodPurchase
        fields = [
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
            "times_per_month",
            "months_per_year",
        ]


class FoodPurchaseViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows food purchases to be viewed or edited.
    """

    queryset = FoodPurchase.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = FoodPurchaseSerializer
    filterset_class = FoodPurchaseFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class PaymentInKindFilterSet(filters.FilterSet):
    class Meta:
        model = PaymentInKind
        fields = [
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
            "people_per_household",
            "times_per_month",
            "months_per_year",
        ]


class PaymentInKindViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows payments in kind to be viewed or edited.
    """

    queryset = PaymentInKind.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = PaymentInKindSerializer
    filterset_class = PaymentInKindFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class ReliefGiftOtherFilterSet(filters.FilterSet):
    class Meta:
        model = ReliefGiftOther
        fields = [
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
            "times_per_year",
        ]


class ReliefGiftOtherViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows relief, gifts and other food to be viewed or edited.
    """

    queryset = ReliefGiftOther.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = ReliefGiftOtherSerializer
    filterset_class = ReliefGiftOtherFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class FishingFilterSet(filters.FilterSet):
    class Meta:
        model = Fishing
        fields = [
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


class HuntingFilterSet(filters.FilterSet):
    class Meta:
        model = Hunting
        fields = [
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


class HuntingViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows hunting to be viewed or edited when available
    """

    queryset = Hunting.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = HuntingSerializer
    filterset_class = HuntingFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class FishingViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows fishing to be viewed or edited.
    """

    queryset = Fishing.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = FishingSerializer
    filterset_class = FishingFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class WildFoodGatheringFilterSet(filters.FilterSet):
    class Meta:
        model = WildFoodGathering
        fields = [
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

    queryset = WildFoodGathering.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = WildFoodGatheringSerializer
    filterset_class = WildFoodGatheringFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class OtherCashIncomeFilterSet(filters.FilterSet):
    class Meta:
        model = OtherCashIncome
        fields = [
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
            "people_per_household",
            "times_per_month",
            "months_per_year",
            "times_per_year",
        ]


class OtherCashIncomeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows other cash income to be viewed or edited.
    """

    queryset = OtherCashIncome.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = OtherCashIncomeSerializer
    filterset_class = OtherCashIncomeFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class OtherPurchaseFilterSet(filters.FilterSet):
    class Meta:
        model = OtherPurchase
        fields = [
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
            "times_per_month",
            "months_per_year",
        ]


class OtherPurchaseViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows other purchases to be viewed or edited.
    """

    queryset = OtherPurchase.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = OtherPurchaseSerializer
    filterset_class = OtherPurchaseFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class SeasonalActivityFilterSet(filters.FilterSet):
    class Meta:
        model = SeasonalActivity
        fields = [
            "livelihood_zone_baseline",
            "seasonal_activity_type",
            "season",
            "product",
        ]


class SeasonalActivityViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows seasonal activities to be viewed or edited.
    """

    queryset = SeasonalActivity.objects.select_related(
        "seasonal_activity_type",
        "livelihood_zone_baseline__livelihood_zone__country",
        "livelihood_zone_baseline__source_organization",
        "livelihood_zone_baseline__source_organization",
        "product",
    ).prefetch_related("season")
    serializer_class = SeasonalActivitySerializer
    filterset_class = SeasonalActivityFilterSet


class SeasonalActivityOccurrenceFilterSet(filters.FilterSet):
    class Meta:
        model = SeasonalActivityOccurrence
        fields = [
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

    queryset = SeasonalActivityOccurrence.objects.select_related(
        "community",
        "livelihood_zone_baseline__livelihood_zone__country",
        "livelihood_zone_baseline__source_organization",
        "seasonal_activity__product",
    ).prefetch_related("seasonal_activity__season")
    serializer_class = SeasonalActivityOccurrenceSerializer
    filterset_class = SeasonalActivityOccurrenceFilterSet


class CommunityCropProductionFilterSet(filters.FilterSet):
    class Meta:
        model = CommunityCropProduction
        fields = [
            "community",
            "crop",
            "crop_purpose",
            "season",
            "yield_with_inputs",
            "yield_without_inputs",
            "seed_requirement",
            "crop_unit_of_measure",
            "land_unit_of_measure",
        ]


class CommunityCropProductionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows community crop productions to be viewed or edited.
    """

    queryset = CommunityCropProduction.objects.select_related(
        "community__livelihood_zone_baseline__livelihood_zone__country",
        "community__livelihood_zone_baseline__source_organization",
        "crop",
        "season",
        "crop_unit_of_measure",
        "land_unit_of_measure",
    )
    serializer_class = CommunityCropProductionSerializer
    filterset_class = CommunityCropProductionFilterSet
    search_fields = [
        "crop_purpose",
    ]


class CommunityLivestockFilterSet(filters.FilterSet):
    class Meta:
        model = CommunityLivestock
        fields = [
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

    queryset = CommunityLivestock.objects.select_related(
        "community__livelihood_zone_baseline__livelihood_zone__country",
        "community__livelihood_zone_baseline__source_organization",
        "livestock",
    )
    serializer_class = CommunityLivestockSerializer
    filterset_class = CommunityLivestockFilterSet


class MarketPriceFilterSet(filters.FilterSet):
    class Meta:
        model = MarketPrice
        fields = [
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

    queryset = MarketPrice.objects.select_related(
        "community__livelihood_zone_baseline__livelihood_zone__country",
        "community__livelihood_zone_baseline__source_organization",
        "market",
        "product",
        "unit_of_measure",
    )
    serializer_class = MarketPriceSerializer
    filterset_class = MarketPriceFilterSet
    search_fields = [
        "description",
    ]


class SeasonalProductionPerformanceFilterSet(filters.FilterSet):
    class Meta:
        model = SeasonalProductionPerformance
        fields = [
            "community",
            "performance_year_start_date",
            "performance_year_end_date",
            "seasonal_performance",
        ]


class SeasonalProductionPerformanceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows seasonal production performance to be viewed or edited.
    """

    queryset = SeasonalProductionPerformance.objects.select_related(
        "community__livelihood_zone_baseline__livelihood_zone__country",
        "community__livelihood_zone_baseline__source_organization",
    )
    serializer_class = SeasonalProductionPerformanceSerializer
    filterset_class = SeasonalProductionPerformanceFilterSet


class HazardFilterSet(filters.FilterSet):
    class Meta:
        model = Hazard
        fields = [
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

    queryset = Hazard.objects.select_related(
        "community__livelihood_zone_baseline__livelihood_zone__country",
        "community__livelihood_zone_baseline__source_organization",
        "hazard_category",
    )
    serializer_class = HazardSerializer
    filterset_class = HazardFilterSet
    search_fields = [
        "chronic_or_periodic",
        "description",
    ]


class EventFilterSet(filters.FilterSet):
    class Meta:
        model = Event
        fields = [
            "community",
            "event_year_start_date",
            "event_year_end_date",
            "description",
        ]


class EventViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows events to be viewed or edited.
    """

    queryset = Event.objects.select_related(
        "community__livelihood_zone_baseline__livelihood_zone__country",
        "community__livelihood_zone_baseline__source_organization",
    )
    serializer_class = EventSerializer
    filterset_class = EventFilterSet
    search_fields = [
        "description",
    ]


class ExpandabilityFactorFilterSet(filters.FilterSet):
    class Meta:
        model = ExpandabilityFactor
        fields = [
            "livelihood_strategy",
            "wealth_group",
            "percentage_produced",
            "percentage_sold",
            "percentage_other_uses",
            "percentage_consumed",
            "percentage_income",
            "percentage_expenditure",
            "remark",
        ]


class ExpandabilityFactorViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows expandability factors to be viewed or edited.
    """

    queryset = ExpandabilityFactor.objects.select_related(
        "livelihood_strategy__currency",
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = ExpandabilityFactorSerializer
    filterset_class = ExpandabilityFactorFilterSet
    search_fields = [
        "remark",
    ]


class CopingStrategyFilterSet(filters.FilterSet):
    class Meta:
        model = CopingStrategy
        fields = [
            "community",
            "leaders",
            "wealth_group",
            "livelihood_strategy",
            "strategy",
            "by_value",
        ]


class CopingStrategyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows coping strategies to be viewed or edited.
    """

    queryset = CopingStrategy.objects.select_related(
        "community__livelihood_zone_baseline__livelihood_zone__country",
        "community__livelihood_zone_baseline__livelihood_zone__country",
        "community__livelihood_zone_baseline__source_organization",
        "community__livelihood_zone_baseline__source_organization",
        "livelihood_strategy__currency",
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__wealth_group_category",
    )
    serializer_class = CopingStrategySerializer
    filterset_class = CopingStrategyFilterSet
    search_fields = [
        "leaders",
        "strategy",
    ]
