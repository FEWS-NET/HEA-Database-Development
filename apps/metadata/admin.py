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


class ReferenceDataAdmin(admin.ModelAdmin):
    fields = [
        "code",
        "name_en",
        "name_pt",
        "name_ar",
        "name_es",
        "name_fr",
        "description_en",
        "description_pt",
        "description_ar",
        "description_es",
        "description_fr",
        "aliases",
    ]
    list_display = (
        "code",
        "name",
        "description",
    )
    search_fields = (
        "name_en",
        "name_pt",
        "name_ar",
        "name_es",
        "name_fr",
        "description_en",
        "description_pt",
        "description_ar",
        "description_es",
        "description_fr",
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
        "name_en",
        "name_pt",
        "name_ar",
        "name_es",
        "name_fr",
        "activity_category",
        "description_en",
        "description_pt",
        "description_ar",
        "description_es",
        "description_fr",
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
        "name_en",
        "name_pt",
        "name_ar",
        "name_es",
        "name_fr",
        "variable_type",
        "description_en",
        "description_pt",
        "description_ar",
        "description_es",
        "description_fr",
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
        "name_en",
        "name_pt",
        "name_ar",
        "name_es",
        "name_fr",
        "description_en",
        "description_pt",
        "description_ar",
        "description_es",
        "description_fr",
        "season_type",
        "start",
        "end",
        "alignment",
        "order",
    )
    list_display = (
        "country",
        "name",
        "season_type",
        "start",
        "end",
    )
    search_fields = (
        "country__iso_en_ro_name",
        "name_en",
        "name_pt",
        "name_ar",
        "name_es",
        "name_fr",
        "season_type",
    )
    list_filter = (
        ("country", RelatedFieldListFilter),
        "season_type",
    )
    ordering = ("order",)


class MarketAdmin(ReferenceDataAdmin):

    fields = [
        "code",
        "name_en",
        "name_pt",
        "name_ar",
        "name_es",
        "name_fr",
        "country",
        "description_en",
        "description_pt",
        "description_ar",
        "description_es",
        "description_fr",
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
