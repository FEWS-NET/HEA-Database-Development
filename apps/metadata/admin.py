from django.contrib import admin

from .models import (
    Alias,
    Conversion,
    CropType,
    Currency,
    Dimension,
    DimensionType,
    HazardCategory,
    Item,
    LivelihoodCategory,
    LivestockType,
    SeasonalActivityCategory,
    SourceSystem,
    Translation,
    TranslationType,
    UnitOfMeasure,
    WealthGroupCharacteristic,
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


@admin.register(WealthGroupCharacteristic)
class WealthGroupCharacteristicAdmin(admin.ModelAdmin):
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


@admin.register(Conversion)
class ConversionAdmin(admin.ModelAdmin):
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


@admin.register(SeasonalActivityCategory)
class SeasonalActivityCategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(HazardCategory)
class HazardCategoryAdmin(admin.ModelAdmin):
    pass
