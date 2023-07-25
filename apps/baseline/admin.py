from django.contrib import admin

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
    Staple,
    WealthGroup,
    WealthGroupCharacteristicValue,
    WildFoodGathering,
)

admin.site.site_header = "HEA Baseline Database Administration"
admin.site.index_title = "HEA Baseline"


@admin.register(SourceOrganization)
class SourceOrganizationAdmin(admin.ModelAdmin):
    pass


@admin.register(LivelihoodZone)
class LivelihoodZoneAdmin(admin.ModelAdmin):
    pass


@admin.register(LivelihoodZoneBaseline)
class LivelihoodZoneBaselineAdmin(admin.ModelAdmin):
    pass


@admin.register(Staple)
class StapleAdmin(admin.ModelAdmin):
    pass


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    pass


@admin.register(WealthGroup)
class WealthGroupAdmin(admin.ModelAdmin):
    pass


@admin.register(WealthGroupCharacteristicValue)
class WealthGroupCharacteristicValueAdmin(admin.ModelAdmin):
    pass


@admin.register(LivelihoodStrategy)
class LivelihoodStrategyAdmin(admin.ModelAdmin):
    pass


@admin.register(MilkProduction)
class MilkProductionAdmin(admin.ModelAdmin):
    pass


@admin.register(ButterProduction)
class ButterProductionAdmin(admin.ModelAdmin):
    pass


@admin.register(MeatProduction)
class MeatProductionAdmin(admin.ModelAdmin):
    pass


@admin.register(LivestockSales)
class LivestockSalesAdmin(admin.ModelAdmin):
    pass


@admin.register(CropProduction)
class CropProductionModelAdmin(admin.ModelAdmin):
    pass


@admin.register(FoodPurchase)
class FoodPurchaseProductionModelAdmin(admin.ModelAdmin):
    pass


@admin.register(PaymentInKind)
class PaymentInKindProductionModelAdmin(admin.ModelAdmin):
    pass


@admin.register(OtherCashIncome)
class OtherCashIncomeSourcesProductionModelAdmin(admin.ModelAdmin):
    pass


@admin.register(Fishing)
class FishingAdmin(admin.ModelAdmin):
    pass


@admin.register(WildFoodGathering)
class WildFoodGatheringAdmin(admin.ModelAdmin):
    pass


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
