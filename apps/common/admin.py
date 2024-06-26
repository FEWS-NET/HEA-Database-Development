# Register your models here.
from django.contrib import admin
from django.contrib.admin.options import InlineModelAdmin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from .fields import translation_fields
from .models import (
    ClassifiedProduct,
    Country,
    CountryClassifiedProductAliases,
    Currency,
    UnitOfMeasure,
    UnitOfMeasureConversion,
)


class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("iso4217a3", "iso4217n3", "iso_en_name")
    search_fields = ["iso4217a3", "iso4217n3", "iso_en_name"]


class CountryAdmin(admin.ModelAdmin):
    list_display = ("iso3166a2", "name", "iso3166a3", "iso3166n3", "iso_en_name", "iso_fr_name", "iso_es_name")
    ordering = [
        "iso3166a2",
    ]


class CountryClassifiedProductAliasesInline(InlineModelAdmin):
    model = CountryClassifiedProductAliases
    fields = ("country",)  # "aliases")
    extra = 0


class ClassifiedProductAdmin(TreeAdmin):
    form = movenodeform_factory(ClassifiedProduct)
    fields = (
        "cpc",
        *translation_fields("description"),
        *translation_fields("common_name"),
        "scientific_name",
        "unit_of_measure",
        "kcals_per_unit",
        "aliases",
        "cpcv2",
        "hs2012",
        "_position",
        "_ref_node_id",
    )
    list_display = ("cpc", "description", "common_name", "aliases")
    ordering = ["path"]  # Required for correct ordering of the hierarchical tree
    search_fields = (
        "^cpc",
        *translation_fields("description"),
        *translation_fields("common_name"),
        "scientific_name",
        "cpcv2",
        "hs2012",
        "aliases",
        "kcals_per_unit",
        "per_country_aliases__country__iso_en_ro_name",
        "per_country_aliases__country__iso_en_name",
        "per_country_aliases__country__iso_en_ro_proper",
        "per_country_aliases__country__iso_en_proper",
        "per_country_aliases__country__iso_fr_name",
        "per_country_aliases__country__iso_fr_proper",
        "per_country_aliases__country__iso_es_name",
    )


class UnitOfMeasureConversionInline(admin.TabularInline):
    model = UnitOfMeasureConversion
    fields = ("from_unit", "to_unit", "conversion_factor")
    fk_name = "from_unit"


class UnitOfMeasureAdmin(admin.ModelAdmin):
    list_display = (
        "abbreviation",
        "description",
        "aliases",
    )
    search_fields = (
        "abbreviation",
        *translation_fields("description"),
        "aliases",
    )
    list_filter = ("unit_type",)
    inlines = [UnitOfMeasureConversionInline]


admin.site.register(Currency, CurrencyAdmin)
admin.site.register(ClassifiedProduct, ClassifiedProductAdmin)
admin.site.register(UnitOfMeasure, UnitOfMeasureAdmin)
admin.site.register(Country, CountryAdmin)
