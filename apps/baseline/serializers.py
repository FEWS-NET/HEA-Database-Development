from rest_framework import serializers

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


class SourceOrganizationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SourceOrganization
        fields = "__all__"


class LivelihoodZoneSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LivelihoodZone
        fields = "__all__"


class LivelihoodZoneBaselineSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LivelihoodZoneBaseline
        fields = "__all__"


class LivelihoodProductCategorySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LivelihoodProductCategory
        fields = "__all__"


class CommunitySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Community
        fields = "__all__"


class WealthGroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = WealthGroup
        fields = "__all__"


class BaselineWealthGroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = BaselineWealthGroup
        fields = "__all__"


class CommunityWealthGroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CommunityWealthGroup
        fields = "__all__"


class WealthGroupCharacteristicValueSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = WealthGroupCharacteristicValue
        fields = "__all__"


class LivelihoodStrategySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LivelihoodStrategy
        fields = "__all__"


class LivelihoodActivitySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LivelihoodActivity
        fields = "__all__"


class MilkProductionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MilkProduction
        fields = "__all__"


class ButterProductionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ButterProduction
        fields = "__all__"


class MeatProductionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MeatProduction
        fields = "__all__"


class LivestockSalesSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LivestockSales
        fields = "__all__"


class CropProductionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CropProduction
        fields = "__all__"


class FoodPurchaseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = FoodPurchase
        fields = "__all__"


class PaymentInKindSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PaymentInKind
        fields = "__all__"


class ReliefGiftsOtherSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ReliefGiftsOther
        fields = "__all__"


class FishingSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Fishing
        fields = "__all__"


class WildFoodGatheringSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = WildFoodGathering
        fields = "__all__"


class OtherCashIncomeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = OtherCashIncome
        fields = "__all__"


class OtherPurchasesSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = OtherPurchases
        fields = "__all__"


class SeasonalActivitySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SeasonalActivity
        fields = "__all__"


class SeasonalActivityOccurrenceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SeasonalActivityOccurrence
        fields = "__all__"


class CommunityCropProductionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CommunityCropProduction
        fields = "__all__"


class CommunityLivestockSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CommunityLivestock
        fields = "__all__"


class MarketPriceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = MarketPrice
        fields = "__all__"


class AnnualProductionPerformanceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = AnnualProductionPerformance
        fields = "__all__"


class HazardSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Hazard
        fields = "__all__"


class EventSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Event
        fields = "__all__"


class ExpandabilityFactorSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ExpandabilityFactor
        fields = "__all__"


class CopingStrategySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CopingStrategy
        fields = "__all__"
