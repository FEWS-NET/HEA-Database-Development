from django.contrib import admin
from django.contrib.admin import RelatedFieldListFilter

from .models import (
    HazardCategory,
    LivelihoodCategory,
    Market,
    Season,
    SeasonalActivityType,
    WealthCharacteristic,
    WealthGroupCategory,
)


class DimensionAdmin(admin.ModelAdmin):
    fields = [
        "code",
        "name",
        "description",
        "aliases",
    ]
    list_display = (
        "code",
        "name",
        "description",
    )
    search_fields = (
        "name",
        "description",
        "aliases",
    )


class LivelihoodCategoryAdmin(DimensionAdmin):
    """
    A concrete admin for LivelihoodCategory
    """


class SeasonalActivityTypeAdmin(DimensionAdmin):
    """
    A concrete admin for  SeasonalActivityType
    """

    fields = (
        "code",
        "name",
        "activity_category",
        "description",
        "aliases",
    )


class WealthGroupCategoryAdmin(DimensionAdmin):
    """
    A concrete admin for WealthGroupCategory
    """


class WealthCharacteristicAdmin(DimensionAdmin):
    """
    A concrete admin for WealthCharacteristic
    """

    fields = (
        "code",
        "name",
        "variable_type",
        "description",
        "has_product",
        "has_unit_of_measure",
        "aliases",
    )

    list_filter = (
        "variable_type",
        "has_product",
        "has_unit_of_measure",
    )


class HazardCategoryAdmin(DimensionAdmin):
    """
    A concrete admin for HazardCategory
    """


class SeasonAdmin(admin.ModelAdmin):
    """
    A concrete admin for Season
    """

    fields = ("country", "name", "description", "season_type", "start", "end", "alignment", "order")
    list_display = ("country", "name", "season_type", "start", "end")
    search_fields = ("country__iso_en_ro_name", "name", "season_type")
    list_filter = (
        ("country", RelatedFieldListFilter),
        "season_type",
    )
    ordering = ("order",)


class MarketAdmin(DimensionAdmin):

    fields = [
        "code",
        "name",
        "country",
        "description",
        "aliases",
    ]

    list_filter = (("country", RelatedFieldListFilter),)


admin.site.register(LivelihoodCategory, LivelihoodCategoryAdmin)
admin.site.register(WealthGroupCategory, WealthGroupCategoryAdmin)
admin.site.register(SeasonalActivityType, SeasonalActivityTypeAdmin)

admin.site.register(Market, MarketAdmin)
admin.site.register(WealthCharacteristic, WealthCharacteristicAdmin)
admin.site.register(HazardCategory, HazardCategoryAdmin)
admin.site.register(Season, SeasonAdmin)
