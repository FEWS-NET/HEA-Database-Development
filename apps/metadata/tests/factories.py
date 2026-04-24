import factory

from common.tests.factories import CountryFactory
from metadata.models import (
    CharacteristicGroup,
    Market,
    Season,
    SeasonalActivityType,
    WealthCharacteristic,
)


class LivelihoodCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "metadata.LivelihoodCategory"
        django_get_or_create = ("code",)

    code = factory.Iterator(["AG", "PA", "AP", "FI"])
    name_en = factory.LazyAttribute(lambda o: f"{o.code} Livelihood Category en")
    name_pt = factory.LazyAttribute(lambda o: f"{o.code} Livelihood Category pt")
    name_es = factory.LazyAttribute(lambda o: f"{o.code} Livelihood Category es")
    name_fr = factory.LazyAttribute(lambda o: f"{o.code} Livelihood Category fr")
    name_ar = factory.LazyAttribute(lambda o: f"{o.code} Livelihood Category ar")
    description_en = factory.LazyAttribute(lambda o: f"{o.code} Livelihood Category Description en")
    description_pt = factory.LazyAttribute(lambda o: f"{o.code} Livelihood Category Description pt")
    description_es = factory.LazyAttribute(lambda o: f"{o.code} Livelihood Category Description es")
    description_ar = factory.LazyAttribute(lambda o: f"{o.code} Livelihood Category Description ar")
    description_fr = factory.LazyAttribute(lambda o: f"{o.code} Livelihood Category Description fr")


class HazardCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "metadata.HazardCategory"
        django_get_or_create = ("code",)

    code = factory.Iterator(["HA1", "HA2", "HA3", "HA4"])
    name_en = factory.LazyAttribute(lambda o: f"{o.code} Hazard Category en")
    name_pt = factory.LazyAttribute(lambda o: f"{o.code} Hazard Category pt")
    name_es = factory.LazyAttribute(lambda o: f"{o.code} Hazard Category es")
    name_fr = factory.LazyAttribute(lambda o: f"{o.code} Hazard Category fr")
    name_ar = factory.LazyAttribute(lambda o: f"{o.code} Hazard Category ar")
    description_en = factory.LazyAttribute(lambda o: f"{o.code} Hazard Category Description en")
    description_pt = factory.LazyAttribute(lambda o: f"{o.code} Hazard Category Description pt")
    description_es = factory.LazyAttribute(lambda o: f"{o.code} Hazard Category Description es")
    description_ar = factory.LazyAttribute(lambda o: f"{o.code} Hazard Category Description ar")
    description_fr = factory.LazyAttribute(lambda o: f"{o.code} Hazard Category Description fr")


class WealthGroupCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "metadata.WealthGroupCategory"
        django_get_or_create = ("code",)

    code = factory.Iterator(["VP", "P", "M", "BO"])
    name_en = factory.Iterator(["Very Poor en", "Poor en", "Medium en", "Bettor Off en"])
    name_pt = factory.Iterator(["Muito pobre pt", "Pobre pt", "Médio pt", "Bom pt"])
    name_es = factory.Iterator(["Very Poor es", "Poor es", "Medium es", "Bettor Off es"])
    name_ar = factory.Iterator(["Very Poor ar", "Poor ar", "Medium ar", "Bettor Off ar"])
    name_fr = factory.Iterator(["Very Poor fr", "Poor fr", "Medium fr", "Bettor Off fr"])
    description_en = factory.LazyAttribute(lambda o: f"{o.name_en} Wealth Group Category Description en")
    description_pt = factory.LazyAttribute(lambda o: f"{o.name_pt} Wealth Group Category Description pt")
    description_es = factory.LazyAttribute(lambda o: f"{o.name_es} Wealth Group Category Description es")
    description_ar = factory.LazyAttribute(lambda o: f"{o.name_ar} Wealth Group Category Description ar")
    description_fr = factory.LazyAttribute(lambda o: f"{o.name_fr} Wealth Group Category Description fr")


class CharacteristicGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CharacteristicGroup
        django_get_or_create = ("code",)

    code = factory.Iterator(["Population", "Income", "Land", "Livestock", "Other assets"])
    name_en = factory.LazyAttribute(lambda o: f"{o.code}")
    name_pt = factory.LazyAttribute(lambda o: f"{o.code} pt")
    name_es = factory.LazyAttribute(lambda o: f"{o.code} es")
    name_fr = factory.LazyAttribute(lambda o: f"{o.code} fr")
    name_ar = factory.LazyAttribute(lambda o: f"{o.code} ar")
    description_en = factory.LazyAttribute(lambda o: f"{o.code} Description en")
    description_pt = factory.LazyAttribute(lambda o: f"{o.code} Description pt")
    description_es = factory.LazyAttribute(lambda o: f"{o.code} Description es")
    description_ar = factory.LazyAttribute(lambda o: f"{o.code} Description ar")
    description_fr = factory.LazyAttribute(lambda o: f"{o.code} Description fr")


class WealthCharacteristicFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "metadata.WealthCharacteristic"
        django_get_or_create = ("code",)

    code = factory.Iterator(["WC1", "WC2", "WC3", "WC4"])
    variable_type = factory.Iterator(
        [
            WealthCharacteristic.VariableType.STR,
            WealthCharacteristic.VariableType.BOOL,
            WealthCharacteristic.VariableType.NUM,
        ]
    )
    has_product = factory.Iterator([False, True])
    has_unit_of_measure = factory.Iterator([False, True])
    characteristic_group = factory.SubFactory(CharacteristicGroupFactory)
    name_en = factory.LazyAttribute(lambda o: f"{o.code} Wealth Characteristic en")
    name_pt = factory.LazyAttribute(lambda o: f"{o.code} Wealth Characteristic pt")
    name_es = factory.LazyAttribute(lambda o: f"{o.code} Wealth Characteristic es")
    name_fr = factory.LazyAttribute(lambda o: f"{o.code} Wealth Characteristic fr")
    name_ar = factory.LazyAttribute(lambda o: f"{o.code} Wealth Characteristic ar")
    description_en = factory.LazyAttribute(lambda o: f"{o.code} Wealth Characteristic Description en")
    description_pt = factory.LazyAttribute(lambda o: f"{o.code} Wealth Characteristic Description pt")
    description_es = factory.LazyAttribute(lambda o: f"{o.code} Wealth Characteristic Description es")
    description_ar = factory.LazyAttribute(lambda o: f"{o.code} Wealth Characteristic Description ar")
    description_fr = factory.LazyAttribute(lambda o: f"{o.code} Wealth Characteristic Description fr")


class SeasonalActivityTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "metadata.SeasonalActivityType"
        django_get_or_create = ("code",)

    code = factory.Iterator(["AC1", "AC2", "AC3", "AC4"])
    activity_category = factory.Iterator(
        [
            SeasonalActivityType.SeasonalActivityCategory.CROP,
            SeasonalActivityType.SeasonalActivityCategory.FISHING,
            SeasonalActivityType.SeasonalActivityCategory.LIVESTOCK,
            SeasonalActivityType.SeasonalActivityCategory.GARDENING,
        ]
    )
    name_en = factory.LazyAttribute(lambda o: f"{o.code} Seasonal Activity Type en")
    name_pt = factory.LazyAttribute(lambda o: f"{o.code} Seasonal Activity Type pt")
    name_es = factory.LazyAttribute(lambda o: f"{o.code} Seasonal Activity Type es")
    name_fr = factory.LazyAttribute(lambda o: f"{o.code} Seasonal Activity Type fr")
    name_ar = factory.LazyAttribute(lambda o: f"{o.code} Seasonal Activity Type ar")
    description_en = factory.LazyAttribute(lambda o: f"{o.code} Seasonal ActivityType Description en")
    description_pt = factory.LazyAttribute(lambda o: f"{o.code} Seasonal ActivityType Description pt")
    description_es = factory.LazyAttribute(lambda o: f"{o.code} Seasonal ActivityType Description es")
    description_ar = factory.LazyAttribute(lambda o: f"{o.code} Seasonal ActivityType Description ar")
    description_fr = factory.LazyAttribute(lambda o: f"{o.code} Seasonal ActivityType Description fr")


class SeasonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Season
        django_get_or_create = ("country", "name_en", "purpose")

    name_en = factory.LazyAttributeSequence(lambda o, n: f"{o.country.iso_en_ro_name}, Season {n}")
    name_es = factory.LazyAttributeSequence(lambda o, n: f"{o.country.iso_en_ro_name}, Season {n} es")
    name_fr = factory.LazyAttributeSequence(lambda o, n: f"{o.country.iso_en_ro_name}, Season {n} fr")
    name_pt = factory.LazyAttributeSequence(lambda o, n: f"{o.country.iso_en_ro_name}, Season {n} pt")
    name_ar = factory.LazyAttributeSequence(lambda o, n: f"{o.country.iso_en_ro_name}, Season {n} ar")
    description_en = factory.LazyAttribute(lambda o: f"Description {o.name_en} {o.season_type}")
    description_pt = factory.LazyAttribute(lambda o: f"Description {o.name_pt} {o.season_type}")
    description_es = factory.LazyAttribute(lambda o: f"Description {o.name_es} {o.season_type}")
    description_fr = factory.LazyAttribute(lambda o: f"Description {o.name_fr} {o.season_type}")
    description_ar = factory.LazyAttribute(lambda o: f"Description {o.name_ar} {o.season_type}")
    country = factory.SubFactory(CountryFactory)
    season_type = factory.Iterator([Season.SeasonType.WET, Season.SeasonType.DRY, Season.SeasonType.MILD])
    purpose = None
    order = factory.Iterator([1, 2, 3])
    start = factory.Iterator((25, 95, 200))
    end = factory.Iterator((95, 199, 360))


class MarketFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Market
        django_get_or_create = [
            "code",
            "country",
        ]

    code = factory.Sequence(lambda n: f"code{n}")
    name_en = factory.LazyAttribute(lambda o: f"{o.code} name en")
    name_pt = factory.LazyAttribute(lambda o: f"{o.code} name pt")
    name_es = factory.LazyAttribute(lambda o: f"{o.code} name es")
    name_fr = factory.LazyAttribute(lambda o: f"{o.code} name fr")
    name_ar = factory.LazyAttribute(lambda o: f"{o.code} name ar")
    full_name_en = factory.LazyAttribute(lambda o: f"{o.code} full name en")
    full_name_pt = factory.LazyAttribute(lambda o: f"{o.code} full name pt")
    full_name_es = factory.LazyAttribute(lambda o: f"{o.code} full name es")
    full_name_fr = factory.LazyAttribute(lambda o: f"{o.code} full name fr")
    full_name_ar = factory.LazyAttribute(lambda o: f"{o.code} full name ar")
    description_en = factory.LazyAttribute(lambda o: f"{o.code} description en")
    description_pt = factory.LazyAttribute(lambda o: f"{o.code} description pt")
    description_es = factory.LazyAttribute(lambda o: f"{o.code} description es")
    description_ar = factory.LazyAttribute(lambda o: f"{o.code} description ar")
    description_fr = factory.LazyAttribute(lambda o: f"{o.code} description fr")
    aliases = factory.Sequence(lambda n: [f"alias{n + i}" for i in range(n % 10)])
    country = factory.SubFactory(CountryFactory)
