from modeltranslation.translator import TranslationOptions, translator

from .models import (
    AnnualProductionPerformance,
    Community,
    Event,
    Hazard,
    LivelihoodZone,
    LivelihoodZoneBaseline,
    MarketPrice,
    SourceOrganization,
)


class SourceOrganizationTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "full_name",
        "description",
    )


class LivelihoodZoneTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "description",
    )


class LivelihoodZoneBaselineTranslationOptions(TranslationOptions):
    fields = ("population_source",)


class CommunityTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "full_name",
    )


class MarketPriceTranslationOptions(TranslationOptions):
    fields = ("description",)


class AnnualProductionPerformanceTranslationOptions(TranslationOptions):
    fields = ("description",)


class HazardTranslationOptions(TranslationOptions):
    fields = ("description",)


class EventTranslationOptions(TranslationOptions):
    fields = ("description",)


translator.register(SourceOrganization, SourceOrganizationTranslationOptions)
translator.register(LivelihoodZone, LivelihoodZoneTranslationOptions)
translator.register(LivelihoodZoneBaseline, LivelihoodZoneBaselineTranslationOptions)
translator.register(Community, CommunityTranslationOptions)
translator.register(MarketPrice, MarketPriceTranslationOptions)
translator.register(AnnualProductionPerformance, AnnualProductionPerformanceTranslationOptions)
translator.register(Hazard, HazardTranslationOptions)
translator.register(Event, EventTranslationOptions)
