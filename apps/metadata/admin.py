from django.contrib import admin

from .models import (
    Alias,
    CropType,
    Currency,
    Dimension,
    DimensionType,
    HazardCategory,
    Item,
    LivelihoodCategory,
    LivestockType,
    SourceSystem,
    Translation,
    TranslationType,
    UnitOfMeasure,
    UnitOfMeasureConversion,
    WealthCharacteristic,
    WealthCategory,
)


@admin.register(DimensionType)
class DimensionTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Dimension)
class DimensionAdmin(admin.ModelAdmin):
    pass


@admin.register(SourceSystem)
class SourceSystemAdmin(admin.ModelAdmin):
    pass


@admin.register(Alias)
class AliasAdmin(admin.ModelAdmin):
    pass


@admin.register(LivelihoodCategory)
class LivelihoodCategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(WealthCategory)
class WealthCategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(WealthCharacteristic)
class WealthCharacteristicAdmin(admin.ModelAdmin):
    pass


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    pass


@admin.register(UnitOfMeasure)
class UnitOfMeasureAdmin(admin.ModelAdmin):
    pass


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    pass


@admin.register(UnitOfMeasureConversion)
class UnitOfMeasureConversionAdmin(admin.ModelAdmin):
    pass


@admin.register(TranslationType)
class TranslationTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    pass


@admin.register(LivestockType)
class LivestockTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(CropType)
class CropTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(HazardCategory)
class HazardCategoryAdmin(admin.ModelAdmin):
    pass
