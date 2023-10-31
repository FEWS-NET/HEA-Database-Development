from modeltranslation.translator import TranslationOptions, translator

from .models import Currency


class CurrencyTranslationOptions(TranslationOptions):
    fields = ("iso_en_name",)


translator.register(Currency, CurrencyTranslationOptions)
