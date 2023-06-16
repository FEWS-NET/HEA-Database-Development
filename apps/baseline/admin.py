from django.contrib import admin

from .models import (
    Community,
    CommunityCropProduction,
    CommunityLivestock,
    Hazard,
    LivelihoodZone,
    LivelihoodZoneBaseline,
    Market,
    MarketPrice,
    Season,
    SeasonalActivity,
    SeasonalCalendar,
    SourceOrganization,
    WealthGroup,
    WealthGroupAsset,
    WealthGroupAttribute,
    WealthGroupExpenditure,
    WealthGroupFood,
    WealthGroupIncome,
    WealthGroupLivestock,
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


@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    pass


@admin.register(CommunityLivestock)
class CommunityLivestockAdmin(admin.ModelAdmin):
    pass


@admin.register(WealthGroupLivestock)
class WealthGroupLivestockAdmin(admin.ModelAdmin):
    pass


@admin.register(WealthGroup)
class WealthGroupAdmin(admin.ModelAdmin):
    pass


@admin.register(WealthGroupAttribute)
class WealthGroupAttributeAdmin(admin.ModelAdmin):
    pass


@admin.register(WealthGroupIncome)
class WealthGroupIncomeAdmin(admin.ModelAdmin):
    pass


@admin.register(WealthGroupExpenditure)
class WealthGroupExpenditureAdmin(admin.ModelAdmin):
    pass


@admin.register(WealthGroupFood)
class WealthGroupFoodAdmin(admin.ModelAdmin):
    pass


@admin.register(WealthGroupAsset)
class WealthGroupAssetAdmin(admin.ModelAdmin):
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


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    pass


@admin.register(MarketPrice)
class MarketPriceAdmin(admin.ModelAdmin):
    pass


@admin.register(Hazard)
class HazardAdmin(admin.ModelAdmin):
    pass
