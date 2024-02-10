from django.contrib import admin
from django.contrib.admin import RelatedFieldListFilter

from common.fields import translation_fields

from .models import (
    ActivityLabel,
    HazardCategory,
    LivelihoodCategory,
    Market,
    Season,
    SeasonalActivityType,
    WealthCharacteristic,
    WealthCharacteristicLabel,
    WealthGroupCategory,
)


class ReferenceDataAdmin(admin.ModelAdmin):
    fields = (
        "code",
        *translation_fields("name"),
        *translation_fields("description"),
        "aliases",
    )
    list_display = (
        "code",
        "name",
        "description",
    )
    search_fields = (
        *translation_fields("name"),
        *translation_fields("description"),
        "aliases",
    )


class LivelihoodCategoryAdmin(ReferenceDataAdmin):
    """
    A concrete admin for LivelihoodCategory
    """


class SeasonalActivityTypeAdmin(ReferenceDataAdmin):
    """
    A concrete admin for  SeasonalActivityType
    """

    fields = (
        "code",
        *translation_fields("name"),
        "activity_category",
        *translation_fields("description"),
        "aliases",
    )


class WealthGroupCategoryAdmin(ReferenceDataAdmin):
    """
    A concrete admin for WealthGroupCategory
    """


class WealthCharacteristicAdmin(ReferenceDataAdmin):
    """
    A concrete admin for WealthCharacteristic
    """

    fields = (
        "code",
        *translation_fields("name"),
        "variable_type",
        *translation_fields("description"),
        "aliases",
    )
    list_filter = ("variable_type",)


class HazardCategoryAdmin(ReferenceDataAdmin):
    """
    A concrete admin for HazardCategory
    """


class SeasonAdmin(admin.ModelAdmin):
    """
    A concrete admin for Season
    """

    fields = (
        "country",
        *translation_fields("name"),
        *translation_fields("description"),
        "season_type",
        "start",
        "end",
        "alignment",
        "order",
        "aliases",
    )
    list_display = (
        "country",
        "name",
        "season_type",
        "start",
        "end",
        "aliases",
    )
    search_fields = (
        "country__iso_en_ro_name",
        *translation_fields("name"),
        "season_type",
    )
    list_filter = (
        ("country", RelatedFieldListFilter),
        "season_type",
    )
    ordering = ("order",)


class MarketAdmin(ReferenceDataAdmin):
    fields = (
        "code",
        *translation_fields("name"),
        "country",
        *translation_fields("description"),
        "aliases",
    )

    list_filter = (("country", RelatedFieldListFilter),)


class ActivityLabelAdmin(admin.ModelAdmin):
    fields = (
        "activity_label",
        "is_start",
        "strategy_type",
        "product",
        "unit_of_measure",
        "currency",
        "season",
        "additional_identifier",
        "attribute",
    )
    list_display = (
        "activity_label",
        "is_start",
        "strategy_type",
        "product",
        "unit_of_measure",
        "currency",
        "season",
        "additional_identifier",
        "attribute",
    )
    search_fields = (
        "activity_label",
        "product__cpc",
        *translation_fields("product__common_name"),
        *translation_fields("product__description"),
    )
    list_filter = ("strategy_type",)


class WealthCharacteristicLabelAdmin(admin.ModelAdmin):
    fields = (
        "wealth_characteristic_label",
        "wealth_characteristic",
        "product",
        "unit_of_measure",
    )
    list_display = (
        "wealth_characteristic_label",
        "wealth_characteristic",
        "product",
        "unit_of_measure",
    )
    search_fields = (
        "wealth_characteristic_label",
        "wealth_characteristic__code",
        *translation_fields("wealth_characteristic__name"),
        *translation_fields("product__common_name"),
        *translation_fields("product__description"),
    )
    list_filter = ("wealth_characteristic",)


admin.site.register(LivelihoodCategory, LivelihoodCategoryAdmin)
admin.site.register(WealthGroupCategory, WealthGroupCategoryAdmin)
admin.site.register(SeasonalActivityType, SeasonalActivityTypeAdmin)

admin.site.register(Market, MarketAdmin)
admin.site.register(WealthCharacteristic, WealthCharacteristicAdmin)
admin.site.register(HazardCategory, HazardCategoryAdmin)
admin.site.register(Season, SeasonAdmin)
admin.site.register(ActivityLabel, ActivityLabelAdmin)
admin.site.register(WealthCharacteristicLabel, WealthCharacteristicLabelAdmin)
