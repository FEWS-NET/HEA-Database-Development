from modeltranslation.translator import TranslationOptions, translator

from .models import (
    HazardCategory,
    LivelihoodCategory,
    Market,
    Season,
    SeasonalActivityType,
    WealthCategory,
    WealthCharacteristic,
)


class AbstractReferenceDataTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "description",
    )


class LivelihoodCategoryTranslationOptions(AbstractReferenceDataTranslationOptions):
    pass


class WealthCharacteristicTranslationOptions(AbstractReferenceDataTranslationOptions):
    pass


class SeasonalActivityTypeTranslationOptions(AbstractReferenceDataTranslationOptions):
    pass


class WealthCategoryTranslationOptions(AbstractReferenceDataTranslationOptions):
    pass


class MarketTranslationOptions(AbstractReferenceDataTranslationOptions):
    pass


class HazardCategoryTranslationOptions(AbstractReferenceDataTranslationOptions):
    pass


class SeasonTranslationOptions(AbstractReferenceDataTranslationOptions):
    pass


translator.register(LivelihoodCategory, LivelihoodCategoryTranslationOptions)
translator.register(WealthCharacteristic, WealthCharacteristicTranslationOptions)
translator.register(SeasonalActivityType, SeasonalActivityTypeTranslationOptions)
translator.register(WealthCategory, WealthCategoryTranslationOptions)
translator.register(Market, MarketTranslationOptions)
translator.register(HazardCategory, HazardCategoryTranslationOptions)
translator.register(Season, SeasonTranslationOptions)
