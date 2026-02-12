from django import forms
from django.contrib import admin
from django.utils.html import format_html

from common.fields import translation_fields

from .models import (
    ActivityLabel,
    CharacteristicGroup,
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
        "aliases",
        *translation_fields("description"),
        "ordering",
    )
    list_display = (
        "code",
        "name",
        "aliases",
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

    list_display = ("code", "name", "aliases", "description", "color_display")
    fields = (
        "code",
        *translation_fields("name"),
        "aliases",
        "color",
        *translation_fields("description"),
    )

    # Override only the 'color' field to use the html5 color input
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "color":
            kwargs["widget"] = forms.TextInput(attrs={"type": "color"})
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    # Display color as a colored block in the list page
    def color_display(self, obj):
        return format_html('<div style="width: 60px; height: 20px; background-color: {};"></div>', obj.color)

    color_display.short_description = "Color"


class SeasonalActivityTypeAdmin(ReferenceDataAdmin):
    """
    A concrete admin for  SeasonalActivityType
    """

    fields = (
        "code",
        *translation_fields("name"),
        "activity_category",
        "aliases",
        *translation_fields("description"),
    )


class WealthGroupCategoryAdmin(ReferenceDataAdmin):
    """
    A concrete admin for WealthGroupCategory
    """


class CharacteristicGroupAdmin(ReferenceDataAdmin):
    """
    A concrete admin for CharacteristicGroup
    """


class WealthCharacteristicAdmin(ReferenceDataAdmin):
    """
    A concrete admin for WealthCharacteristic
    """

    fields = (
        "code",
        "variable_type",
        *translation_fields("name"),
        "aliases",
        *translation_fields("description"),
        "characteristic_group",
    )
    list_filter = ("variable_type", "characteristic_group")


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
        "aliases",
        *translation_fields("description"),
        "season_type",
        "purpose",
        "start",
        "end",
        "alignment",
        "order",
    )
    list_display = (
        "country",
        "name",
        "aliases",
        "season_type",
        "purpose",
        "start",
        "end",
    )
    search_fields = (
        "country__iso_en_ro_name",
        *translation_fields("name"),
        "season_type",
        "purpose",
    )
    list_filter = (
        ("country", admin.RelatedOnlyFieldListFilter),
        "season_type",
        "purpose",
    )
    ordering = ("country", "order")


class MarketAdmin(ReferenceDataAdmin):
    fields = (
        "code",
        *translation_fields("name"),
        "aliases",
        "country",
        *translation_fields("description"),
    )

    list_filter = (("country", admin.RelatedOnlyFieldListFilter),)


class ActivityLabelAdmin(admin.ModelAdmin):
    fields = (
        "activity_label",
        "activity_type",
        "status",
        "is_start",
        "strategy_type",
        "product",
        "unit_of_measure",
        "currency",
        "season",
        "additional_identifier",
        "attribute",
        "notes",
    )
    list_display = (
        "activity_label",
        "activity_type",
        "status",
        "is_start",
        "strategy_type",
        "product",
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
    list_filter = (
        "activity_type",
        "status",
        "strategy_type",
        "attribute",
    )


class WealthCharacteristicLabelAdmin(admin.ModelAdmin):
    fields = (
        "wealth_characteristic_label",
        "status",
        "wealth_characteristic",
        "product",
        "unit_of_measure",
        "notes",
    )
    list_display = (
        "wealth_characteristic_label",
        "status",
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
    list_filter = (
        "status",
        "wealth_characteristic",
    )


admin.site.register(LivelihoodCategory, LivelihoodCategoryAdmin)
admin.site.register(WealthGroupCategory, WealthGroupCategoryAdmin)
admin.site.register(CharacteristicGroup, CharacteristicGroupAdmin)
admin.site.register(SeasonalActivityType, SeasonalActivityTypeAdmin)

admin.site.register(Market, MarketAdmin)
admin.site.register(WealthCharacteristic, WealthCharacteristicAdmin)
admin.site.register(HazardCategory, HazardCategoryAdmin)
admin.site.register(Season, SeasonAdmin)
admin.site.register(ActivityLabel, ActivityLabelAdmin)
admin.site.register(WealthCharacteristicLabel, WealthCharacteristicLabelAdmin)
