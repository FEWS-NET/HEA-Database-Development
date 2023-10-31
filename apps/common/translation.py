from modeltranslation.translator import TranslationOptions, translator

from .models import ClassifiedProduct, Country, Currency, UnitOfMeasure


class CountryTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "iso_en_name",
        "iso_en_proper",
        "iso_en_ro_name",
        "iso_en_ro_proper",
    )


class CurrencyTranslationOptions(TranslationOptions):
    fields = ("iso_en_name",)


class UnitOfMeasureTranslationOptions(TranslationOptions):
    fields = ("description",)


class ClassifiedProductTranslationOptions(TranslationOptions):
    fields = (
        "description",
        "common_name",
        "scientific_name",
    )


translator.register(Country, CountryTranslationOptions)
translator.register(Currency, CurrencyTranslationOptions)
translator.register(UnitOfMeasure, UnitOfMeasureTranslationOptions)
translator.register(ClassifiedProduct, ClassifiedProductTranslationOptions)
