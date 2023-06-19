from django.contrib import admin

from .models import (
    Community,
    CommunityCropProduction,
    CommunityLivestock,
    CropProductionModel,
    FoodPurchaseProductionModel,
    Hazard,
    LivelihoodZone,
    LivelihoodZoneBaseline,
    LivestockProductionModel,
    Market,
    MarketPrice,
    OtherCashIncomeSourcesProductionModel,
    PaymentInKindProductionModel,
    ProductionModel,
    Season,
    SeasonalActivity,
    SeasonalCalendar,
    SourceOrganization,
    Staple,
    WealthGroup,
    WealthGroupCharacteristicValue,
    WildFoodsAndFishingProductionModel,
)


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


@admin.register(ProductionModel)
class ProductionModelAdmin(admin.ModelAdmin):
    pass


@admin.register(LivestockProductionModel)
class LivestockProductionModelAdmin(admin.ModelAdmin):
    pass


@admin.register(CropProductionModel)
class CropProductionModelAdmin(admin.ModelAdmin):
    pass


@admin.register(FoodPurchaseProductionModel)
class FoodPurchaseProductionModelAdmin(admin.ModelAdmin):
    pass


@admin.register(PaymentInKindProductionModel)
class PaymentInKindProductionModelAdmin(admin.ModelAdmin):
    pass


@admin.register(OtherCashIncomeSourcesProductionModel)
class OtherCashIncomeSourcesProductionModelAdmin(admin.ModelAdmin):
    pass


@admin.register(WildFoodsAndFishingProductionModel)
class WildFoodsAndFishingProductionModelAdmin(admin.ModelAdmin):
    pass


@admin.register(SeasonalActivity)
class SeasonalActivityAdmin(admin.ModelAdmin):
    pass


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    pass


@admin.register(SeasonalCalendar)
class SeasonalCalendarAdmin(admin.ModelAdmin):
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
