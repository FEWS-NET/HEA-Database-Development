# Register your models here.
from django.contrib import admin
from django.contrib.admin.options import InlineModelAdmin
from treebeard.admin import TreeAdmin
from django.contrib.gis.admin import OSMGeoAdmin

from .forms import ClassifiedProductForm
from .models import (
    CountryClassifiedProductAliases,
    Currency,
    Country,
    ClassifiedProduct,
    UnitOfMeasureConversion,
    UnitOfMeasure,
)


class CurrencyAdmin(admin.ModelAdmin):

    list_display = ("iso4217a3", "iso4217n3", "iso_en_name")
    search_fields = ["iso4217a3", "iso4217n3", "iso_en_name"]


class CountryAdmin(admin.ModelAdmin):
    list_display = ("iso3166a2", "name", "iso3166a3", "iso3166n3", "iso_en_name", "iso_fr_name", "iso_es_name")
    ordering = ["iso3166a2",]


class CountryClassifiedProductAliasesInline(InlineModelAdmin):
    model = CountryClassifiedProductAliases
    fields = ("country",)  # "aliases")
    extra = 0


class ClassifiedProductAdmin(TreeAdmin):
    form = ClassifiedProductForm
    list_display = ("cpcv2", "description", "common_name", "scientific_name")
    ordering = ["cpcv2"]
    search_fields = [
        "^cpcv2",
        "description",
        "common_name",
        "scientific_name",
        "per_country_aliases__country__iso_en_ro_name",
        "per_country_aliases__country__iso_en_name",
        "per_country_aliases__country__iso_en_ro_proper",
        "per_country_aliases__country__iso_en_proper",
        "per_country_aliases__country__iso_fr_name",
        "per_country_aliases__country__iso_fr_proper",
        "per_country_aliases__country__iso_es_name",
        "per_country_aliases__country__bgn_name",
        "per_country_aliases__country__pcgn_name",
    ]


class UnitOfMeasureConversionInline(admin.TabularInline):
    model = UnitOfMeasureConversion
    fields = ("from_unit", "to_unit", "conversion_factor")
    fk_name = "from_unit"


class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = (
        "abbreviation",
        "description",
    )
    search_fields = [
        "abbreviation",
        "description",
    ]
    list_filter = ("unit_type",)
    inlines = [UnitOfMeasureConversionInline]


class GeoModelAdmin(OSMGeoAdmin, admin.ModelAdmin):
    """
    Enhanced OSMGeoAdmin class that:
    * Uses https connections to the CDN for OpenLayers JavaScript if the original
      page was requested using https

    """

    openlayers_url = "https://cdnjs.cloudflare.com/ajax/libs/openlayers/2.11/OpenLayers.js"


admin.site.register(Currency, CurrencyAdmin)
admin.site.register(ClassifiedProduct, ClassifiedProductAdmin)
admin.site.register(UnitOfMeasure, UnitOfMeasureAdmin)
admin.site.register(Country, CountryAdmin)
