import factory

from common.test.factories import CountryFactory
from metadata.models import Season, SeasonalActivityType, WealthCharacteristic


class LivelihoodCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "metadata.LivelihoodCategory"
        django_get_or_create = ("code", "name")

    code = factory.Iterator(["AG", "PA", "AP", "FI"])
    name = factory.LazyAttribute(lambda o: f"{o.code} Livelihood Category")
    description = factory.LazyAttribute(lambda o: f"{o.code} Livelihood Category Description")


class HazardCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "metadata.HazardCategory"
        django_get_or_create = ("code", "name")

    code = factory.Iterator(["HA1", "HA2", "HA3", "HA4"])
    name = factory.LazyAttribute(lambda o: f"{o.code} Hazard Category")
    description = factory.LazyAttribute(lambda o: f"{o.code} Hazard Category Description")


class WealthCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "metadata.WealthCategory"
        django_get_or_create = ("code", "name")

    code = factory.Iterator(["VP", "P", "M", "BO"])
    name = factory.Iterator(["Very Poor", "Poor", "Medium", "Bettor Off"])
    description = factory.LazyAttribute(lambda o: f"{o.name} Wealth Category Description")


class WealthCharacteristicFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "metadata.WealthCharacteristic"
        django_get_or_create = ("code", "name")

    code = factory.Iterator(["WC1", "WC2", "WC3", "WC4"])
    variable_type = factory.Iterator(
        [
            WealthCharacteristic.VariableType.STR,
            WealthCharacteristic.VariableType.BOOL,
            WealthCharacteristic.VariableType.NUM,
        ]
    )
    name = factory.LazyAttribute(lambda o: f"{o.code} Wealth Characteristic")
    description = factory.LazyAttribute(lambda o: f"{o.code} Wealth Characteristic Description")


class SeasonalActivityTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "metadata.SeasonalActivityType"
        django_get_or_create = ("code", "name")

    code = factory.Iterator(["AC1", "AC2", "AC3", "AC4"])
    activity_category = factory.Iterator(
        [
            SeasonalActivityType.SeasonalActivityCategory.CROP,
            SeasonalActivityType.SeasonalActivityCategory.FISHING,
            SeasonalActivityType.SeasonalActivityCategory.LIVESTOCK,
            SeasonalActivityType.SeasonalActivityCategory.GARDENING,
        ]
    )
    name = factory.LazyAttribute(lambda o: f"{o.code} Seasonal Activity Type")
    description = factory.LazyAttribute(lambda o: f"{o.code} Seasonal ActivityType Description")


class SeasonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "metadata.Season"
        django_get_or_create = ("country", "name")

    name = factory.Iterator(["Season 1", "Season 2", "Season 3"])
    country = factory.SubFactory(CountryFactory)
    season_type = factory.Iterator([Season.SeasonType.WET, Season.SeasonType.DRY, Season.SeasonType.MILD])
    order = factory.Iterator([1, 2, 3])
    start = factory.Iterator((25, 95, 200))
    end = factory.Iterator((95, 199, 360))
