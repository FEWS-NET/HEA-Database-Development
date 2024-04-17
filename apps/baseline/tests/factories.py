import datetime
import random
import string

import factory
from factory import fuzzy

from baseline.models import (
    BaselineLivelihoodActivity,
    BaselineWealthGroup,
    ButterProduction,
    Community,
    CommunityCropProduction,
    CommunityLivestock,
    CommunityWealthGroup,
    CopingStrategy,
    CropProduction,
    Event,
    ExpandabilityFactor,
    Fishing,
    FoodPurchase,
    Hazard,
    Hunting,
    LivelihoodActivity,
    LivelihoodProductCategory,
    LivelihoodStrategy,
    LivelihoodZone,
    LivelihoodZoneBaseline,
    LivestockSale,
    MarketPrice,
    MeatProduction,
    MilkProduction,
    OtherCashIncome,
    OtherPurchase,
    PaymentInKind,
    ReliefGiftOther,
    ResponseLivelihoodActivity,
    SeasonalActivity,
    SeasonalActivityOccurrence,
    SeasonalProductionPerformance,
    SourceOrganization,
    WealthGroup,
    WealthGroupCharacteristicValue,
    WildFoodGathering,
)
from common.tests.factories import (
    ClassifiedProductFactory,
    CountryFactory,
    CurrencyFactory,
    UnitOfMeasureFactory,
)
from metadata.models import LivelihoodActivityScenario
from metadata.tests.factories import (
    HazardCategoryFactory,
    LivelihoodCategoryFactory,
    MarketFactory,
    SeasonalActivityTypeFactory,
    SeasonFactory,
    WealthCharacteristicFactory,
    WealthGroupCategoryFactory,
)


class SourceOrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SourceOrganization
        django_get_or_create = [
            "name",
        ]

    name = factory.Sequence(lambda n: f"SourceOrganization {n} name")
    full_name = factory.LazyAttribute(lambda o: f"{o.name} full_name")
    description = factory.LazyAttribute(lambda o: f"{o.name} description")


class LivelihoodZoneFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LivelihoodZone
        django_get_or_create = [
            "code",
        ]

    code = factory.LazyAttributeSequence(lambda o, n: f"{o.country.pk}{n:04d}")
    alternate_code = factory.LazyAttribute(
        lambda o: f"{o.country.pk}{''.join(random.choice(string.ascii_uppercase) for _ in range(3))}"
    )
    name_en = factory.LazyAttribute(lambda o: f"{o.code} name EN")
    name_fr = factory.LazyAttribute(lambda o: f"{o.code} name FR")
    name_es = factory.LazyAttribute(lambda o: f"{o.code} name ES")
    name_pt = factory.LazyAttribute(lambda o: f"{o.code} name PT")
    name_ar = factory.LazyAttribute(lambda o: f"{o.code} name AR")
    description_en = factory.LazyAttribute(lambda o: f"{o.code} description EN")
    description_fr = factory.LazyAttribute(lambda o: f"{o.code} description FR")
    description_es = factory.LazyAttribute(lambda o: f"{o.code} description ES")
    description_pt = factory.LazyAttribute(lambda o: f"{o.code} description PT")
    description_ar = factory.LazyAttribute(lambda o: f"{o.code} description AR")
    country = factory.SubFactory(CountryFactory)


class LivelihoodZoneBaselineFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LivelihoodZoneBaseline
        django_get_or_create = [
            "livelihood_zone",
            "source_organization",
        ]

    name_en = factory.LazyAttribute(lambda lz: f"Baseline {lz.livelihood_zone}")
    name_fr = factory.LazyAttribute(lambda lz: f"Baseline {lz.livelihood_zone}")
    name_es = factory.LazyAttribute(lambda lz: f"Baseline {lz.livelihood_zone}")
    name_pt = factory.LazyAttribute(lambda lz: f"Baseline {lz.livelihood_zone}")
    name_ar = factory.LazyAttribute(lambda lz: f"Baseline {lz.livelihood_zone}")
    livelihood_zone = factory.SubFactory(LivelihoodZoneFactory)
    main_livelihood_category = factory.SubFactory(LivelihoodCategoryFactory)
    source_organization = factory.SubFactory(SourceOrganizationFactory)
    bss_language = factory.Iterator(["en", "pt", "es", "ar", "fr"])
    reference_year_start_date = factory.Sequence(lambda n: datetime.date(1900, 1, 1) + datetime.timedelta(days=n))
    reference_year_end_date = factory.Sequence(lambda n: datetime.date(1900, 1, 1) + datetime.timedelta(days=n + 10))
    valid_from_date = factory.Sequence(lambda n: datetime.date(1900, 1, 1) + datetime.timedelta(days=n))
    valid_to_date = factory.Sequence(lambda n: datetime.date(1900, 1, 1) + datetime.timedelta(days=n + 10))
    population_source = factory.Sequence(lambda n: f"population_source {n}")
    population_estimate = fuzzy.FuzzyInteger(500, 1000000)
    currency = factory.SubFactory(CurrencyFactory)


class LivelihoodProductCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LivelihoodProductCategory
        django_get_or_create = [
            "livelihood_zone_baseline",
            "product",
            "basket",
        ]

    livelihood_zone_baseline = factory.SubFactory(LivelihoodZoneBaselineFactory)
    product = factory.SubFactory(ClassifiedProductFactory)
    basket = factory.Iterator(["1", "2", "3", "4"])


class CommunityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Community
        django_get_or_create = [
            "name",
            "livelihood_zone_baseline",
        ]

    code = factory.Sequence(lambda n: f"code{n}")
    name = factory.LazyAttribute(lambda o: f"Community {o.code} name")
    full_name = factory.LazyAttribute(lambda o: f"Community {o.code} full name")
    livelihood_zone_baseline = factory.SubFactory(LivelihoodZoneBaselineFactory)
    geography = None


class WealthGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WealthGroup
        django_get_or_create = [
            "livelihood_zone_baseline",
            "community",
            "wealth_group_category",
        ]

    livelihood_zone_baseline = factory.SubFactory(LivelihoodZoneBaselineFactory)
    community = factory.SubFactory(
        CommunityFactory,
        livelihood_zone_baseline=factory.SelfAttribute("..livelihood_zone_baseline"),
    )
    wealth_group_category = factory.SubFactory(WealthGroupCategoryFactory)
    percentage_of_households = fuzzy.FuzzyInteger(10, 91)
    average_household_size = fuzzy.FuzzyInteger(2, 31)


class BaselineWealthGroupFactory(WealthGroupFactory):
    class Meta:
        model = BaselineWealthGroup
        django_get_or_create = [
            "livelihood_zone_baseline",
            "community",
            "wealth_group_category",
        ]

    community = None


class CommunityWealthGroupFactory(WealthGroupFactory):
    class Meta:
        model = CommunityWealthGroup
        django_get_or_create = [
            "livelihood_zone_baseline",
            "community",
            "wealth_group_category",
        ]

    community = factory.SubFactory(CommunityFactory)


class WealthGroupCharacteristicValueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WealthGroupCharacteristicValue
        django_get_or_create = [
            "wealth_group",
            "wealth_characteristic",
        ]

    wealth_group = factory.SubFactory(WealthGroupFactory)
    wealth_characteristic = factory.SubFactory(WealthCharacteristicFactory)
    value = fuzzy.FuzzyInteger(0, 1000)
    min_value = factory.LazyAttribute(lambda o: o.value - 5)
    max_value = factory.LazyAttribute(lambda o: o.value + 5)

    @factory.lazy_attribute
    def reference_type(self):
        if not self.wealth_group.community:
            return WealthGroupCharacteristicValue.CharacteristicReference.SUMMARY
        else:
            return WealthGroupCharacteristicValue.CharacteristicReference.WEALTH_GROUP

    @factory.lazy_attribute
    def product(self):
        if self.wealth_characteristic.has_product:
            return ClassifiedProductFactory()
        else:
            return None

    @factory.lazy_attribute
    def unit_of_measure(self):
        if self.wealth_characteristic.has_unit_of_measure:
            return UnitOfMeasureFactory()
        else:
            return None


class LivelihoodStrategyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LivelihoodStrategy
        django_get_or_create = [
            "livelihood_zone_baseline",
            "strategy_type",
            "product",
            "additional_identifier",
        ]

    livelihood_zone_baseline = factory.SubFactory(LivelihoodZoneBaselineFactory)
    strategy_type = factory.Iterator(
        [
            "MilkProduction",
            "ButterProduction",
            "MeatProduction",
            "LivestockSale",
            "CropProduction",
            "FoodPurchase",
            "PaymentInKind",
            "ReliefGiftOther",
            "Fishing",
            "Hunting",
            "WildFoodGathering",
            "OtherCashIncome",
            "OtherPurchase",
        ]
    )
    season = factory.SubFactory(SeasonFactory)
    product = factory.SubFactory(ClassifiedProductFactory)
    unit_of_measure = factory.SelfAttribute("product.unit_of_measure")
    currency = factory.SubFactory(CurrencyFactory)
    additional_identifier = factory.Sequence(lambda n: f"additional_identifier {n}")


class LivelihoodActivityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LivelihoodActivity
        django_get_or_create = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
        ]

    livelihood_zone_baseline = factory.SubFactory(LivelihoodZoneBaselineFactory)
    strategy_type = factory.Iterator(
        [
            "MilkProduction",
            "ButterProduction",
            "MeatProduction",
            "LivestockSale",
            "CropProduction",
            "FoodPurchase",
            "PaymentInKind",
            "ReliefGiftOther",
            "Fishing",
            "Hunting",
            "WildFoodGathering",
            "OtherCashIncome",
            "OtherPurchase",
        ]
    )
    scenario = factory.Iterator(["baseline", "response"])
    quantity_produced = fuzzy.FuzzyInteger(201, 300)
    quantity_sold = fuzzy.FuzzyInteger(0, 50)
    quantity_other_uses = fuzzy.FuzzyInteger(0, 50)
    quantity_consumed = factory.LazyAttribute(
        lambda o: (o.quantity_produced or 0) - (o.quantity_sold or 0) - (o.quantity_other_uses or 0)
    )
    price = factory.Sequence(lambda n: n + 1)
    income = factory.LazyAttribute(lambda o: (o.quantity_sold or 0) * o.price)
    expenditure = factory.LazyAttribute(lambda o: (o.quantity_produced or 0) * o.price)
    kcals_consumed = factory.LazyAttribute(
        lambda o: (o.quantity_consumed or 0) * o.livelihood_strategy.product.kcals_per_unit
    )
    percentage_kcals = fuzzy.FuzzyInteger(1, 200)
    wealth_group = factory.SubFactory(
        WealthGroupFactory, livelihood_zone_baseline=factory.SelfAttribute("..livelihood_zone_baseline")
    )
    livelihood_strategy = factory.SubFactory(
        "baseline.tests.factories.LivelihoodStrategyFactory",
        livelihood_zone_baseline=factory.SelfAttribute("..wealth_group.livelihood_zone_baseline"),
        strategy_type=factory.SelfAttribute("..strategy_type"),
    )
    household_labor_provider = factory.Iterator(["men", "women", "children", "all"])
    extra = factory.Iterator(
        [
            {"name of local measure": "stone"},
            {"profit after fattening": 567},
            {"purchase price of animals before fattening": 123},
            {"number of months that green consumption occurs for": 8},
            {"percentage of calories that come from green consumption during that period": 15},
        ]
    )


class BaselineLivelihoodActivityFactory(LivelihoodActivityFactory):
    class Meta:
        model = BaselineLivelihoodActivity
        django_get_or_create = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
        ]

    scenario = LivelihoodActivityScenario.BASELINE


class ResponseLivelihoodActivityFactory(LivelihoodActivityFactory):
    class Meta:
        model = ResponseLivelihoodActivity
        django_get_or_create = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
        ]

    scenario = LivelihoodActivityScenario.RESPONSE


class MilkProductionFactory(LivelihoodActivityFactory):
    class Meta:
        model = MilkProduction
        django_get_or_create = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
        ]

    strategy_type = "MilkProduction"
    milking_animals = fuzzy.FuzzyInteger(1, 20)
    lactation_days = fuzzy.FuzzyInteger(1, 365)
    daily_production = fuzzy.FuzzyInteger(1, 20)
    type_of_milk_consumed = factory.Iterator(["skim", "whole"])
    type_of_milk_sold_or_other_uses = factory.Iterator(["skim", "whole"])


class ButterProductionFactory(LivelihoodActivityFactory):
    class Meta:
        model = ButterProduction
        django_get_or_create = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
        ]

    strategy_type = "ButterProduction"


class MeatProductionFactory(LivelihoodActivityFactory):
    class Meta:
        model = MeatProduction
        django_get_or_create = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
        ]

    strategy_type = "MeatProduction"
    quantity_produced = factory.LazyAttribute(lambda o: (o.animals_slaughtered or 0) * (o.carcass_weight or 0))
    animals_slaughtered = fuzzy.FuzzyInteger(2, 200)
    carcass_weight = fuzzy.FuzzyInteger(100, 150)


class LivestockSaleFactory(LivelihoodActivityFactory):
    class Meta:
        model = LivestockSale
        django_get_or_create = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
        ]

    strategy_type = "LivestockSale"


class CropProductionFactory(LivelihoodActivityFactory):
    class Meta:
        model = CropProduction
        django_get_or_create = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
        ]

    strategy_type = "CropProduction"


class FoodPurchaseFactory(LivelihoodActivityFactory):
    class Meta:
        model = FoodPurchase
        django_get_or_create = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
        ]

    strategy_type = "FoodPurchase"
    quantity_sold = None
    quantity_other_uses = None
    quantity_produced = factory.LazyAttribute(lambda o: o.unit_multiple * o.times_per_month * o.months_per_year)
    quantity_consumed = factory.LazyAttribute(
        lambda o: (o.quantity_produced or 0) - (o.quantity_sold or 0) - (o.quantity_other_uses or 0)
    )
    unit_multiple = fuzzy.FuzzyInteger(1, 500)
    times_per_month = fuzzy.FuzzyInteger(10, 50)
    times_per_year = fuzzy.FuzzyInteger(10, 160)
    months_per_year = fuzzy.FuzzyInteger(1, 12)


class PaymentInKindFactory(LivelihoodActivityFactory):
    class Meta:
        model = PaymentInKind
        django_get_or_create = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
        ]

    strategy_type = "PaymentInKind"
    quantity_sold = fuzzy.FuzzyInteger(1, 25)
    quantity_other_uses = fuzzy.FuzzyInteger(1, 25)
    quantity_produced = factory.LazyAttribute(
        lambda o: o.payment_per_time * o.people_per_household * o.times_per_month * o.months_per_year
    )
    payment_per_time = fuzzy.FuzzyInteger(10, 50)
    people_per_household = fuzzy.FuzzyInteger(1, 8)
    times_per_month = fuzzy.FuzzyInteger(1, 10)
    times_per_year = fuzzy.FuzzyInteger(10, 120)
    months_per_year = fuzzy.FuzzyInteger(10, 12)


class ReliefGiftOtherFactory(LivelihoodActivityFactory):
    class Meta:
        model = ReliefGiftOther
        django_get_or_create = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
        ]

    strategy_type = "ReliefGiftOther"
    quantity_sold = None
    quantity_other_uses = None
    quantity_produced = factory.LazyAttribute(lambda o: o.unit_multiple * o.times_per_year)
    unit_multiple = fuzzy.FuzzyInteger(10, 500)
    times_per_year = fuzzy.FuzzyInteger(1, 160)


class HuntingFactory(LivelihoodActivityFactory):
    class Meta:
        model = Hunting
        django_get_or_create = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
        ]

    strategy_type = "Hunting"


class FishingFactory(LivelihoodActivityFactory):
    class Meta:
        model = Fishing
        django_get_or_create = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
        ]

    strategy_type = "Fishing"


class WildFoodGatheringFactory(LivelihoodActivityFactory):
    class Meta:
        model = WildFoodGathering
        django_get_or_create = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
        ]

    strategy_type = "WildFoodGathering"


class OtherCashIncomeFactory(LivelihoodActivityFactory):
    class Meta:
        model = OtherCashIncome
        django_get_or_create = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
        ]

    strategy_type = "OtherCashIncome"
    income = factory.LazyAttribute(
        lambda o: o.payment_per_time * o.people_per_household * o.times_per_month * o.months_per_year
    )
    expenditure = factory.LazyAttribute(lambda o: (o.quantity_produced or 0) * o.price)
    kcals_consumed = factory.LazyAttribute(
        lambda o: (o.quantity_consumed or 0) * o.livelihood_strategy.product.kcals_per_unit
    )
    percentage_kcals = fuzzy.FuzzyInteger(1, 200)
    payment_per_time = fuzzy.FuzzyInteger(1, 10000)
    people_per_household = fuzzy.FuzzyInteger(1, 30)
    times_per_month = fuzzy.FuzzyInteger(1, 40)
    months_per_year = fuzzy.FuzzyInteger(1, 12)
    times_per_year = fuzzy.FuzzyInteger(1, 300)


class OtherPurchaseFactory(LivelihoodActivityFactory):
    class Meta:
        model = OtherPurchase
        django_get_or_create = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
        ]

    strategy_type = "OtherPurchase"
    income = factory.LazyAttribute(lambda o: o.quantity_sold * o.price)
    expenditure = factory.LazyAttribute(lambda o: o.price * o.unit_multiple * o.times_per_month * o.months_per_year)
    kcals_consumed = factory.LazyAttribute(
        lambda o: (o.quantity_consumed or 0) * o.livelihood_strategy.product.kcals_per_unit
    )
    percentage_kcals = fuzzy.FuzzyInteger(1, 200)
    unit_multiple = fuzzy.FuzzyInteger(1, 500)
    times_per_month = fuzzy.FuzzyInteger(1, 50)
    months_per_year = fuzzy.FuzzyInteger(1, 12)
    times_per_year = fuzzy.FuzzyInteger(1, 300)


class SeasonalActivityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SeasonalActivity
        django_get_or_create = [
            "livelihood_zone_baseline",
            "seasonal_activity_type",
            "product",
        ]

    livelihood_zone_baseline = factory.SubFactory(LivelihoodZoneBaselineFactory)
    seasonal_activity_type = factory.SubFactory(SeasonalActivityTypeFactory)
    product = factory.SubFactory(ClassifiedProductFactory)
    additional_identifier = factory.Sequence(lambda n: f"additional_identifier {n}")

    @factory.post_generation
    def seasons(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of dataseries were passed in, use them
            self.season.set(extracted)


class SeasonalActivityOccurrenceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SeasonalActivityOccurrence
        django_get_or_create = [
            "seasonal_activity",
            "livelihood_zone_baseline",
            "community",
        ]

    seasonal_activity = factory.SubFactory(SeasonalActivityFactory)
    livelihood_zone_baseline = factory.SubFactory(LivelihoodZoneBaselineFactory)
    community = factory.SubFactory(
        "baseline.tests.factories.CommunityFactory",
        livelihood_zone_baseline=factory.SelfAttribute("..seasonal_activity.livelihood_zone_baseline"),
    )
    start = fuzzy.FuzzyInteger(1, 365)
    end = fuzzy.FuzzyInteger(1, 365)


class CommunityCropProductionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CommunityCropProduction
        django_get_or_create = [
            "community",
            "crop",
            "crop_purpose",
            "season",
        ]

    community = factory.SubFactory(CommunityFactory)
    crop = factory.SubFactory(
        "common.tests.factories.ClassifiedProductFactory",
        cpc=factory.Iterator([f"R019{n}" for n in range(1, 10)]),
    )
    crop_purpose = factory.Iterator(["food", "cash"])
    season = factory.SubFactory(SeasonFactory)
    yield_with_inputs = fuzzy.FuzzyInteger(50, 10000)
    yield_without_inputs = fuzzy.FuzzyInteger(1, 10000)
    seed_requirement = fuzzy.FuzzyInteger(1, 100)
    crop_unit_of_measure = factory.SubFactory(UnitOfMeasureFactory)
    land_unit_of_measure = factory.SubFactory(UnitOfMeasureFactory)


class CommunityLivestockFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CommunityLivestock
        django_get_or_create = [
            "community",
            "livestock",
            "birth_interval",
            "additional_attributes",
        ]

    community = factory.SubFactory(CommunityFactory)
    livestock = factory.SubFactory(
        "common.tests.factories.ClassifiedProductFactory",
        cpc=factory.Iterator([f"L021{n}" for n in range(1, 10)]),
    )
    birth_interval = factory.Sequence(lambda n: n + 1)
    wet_season_lactation_period = fuzzy.FuzzyInteger(1, 80)
    wet_season_milk_production = fuzzy.FuzzyInteger(1, 20)
    dry_season_lactation_period = fuzzy.FuzzyInteger(1, 80)
    dry_season_milk_production = fuzzy.FuzzyInteger(1, 20)
    age_at_sale = factory.Sequence(lambda n: n + 1)
    additional_attributes = factory.Sequence(lambda n: n)


class MarketPriceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MarketPrice
        django_get_or_create = [
            "community",
            "product",
            "market",
        ]

    community = factory.SubFactory(CommunityFactory)
    product = factory.SubFactory(ClassifiedProductFactory)
    market = factory.SubFactory(MarketFactory)
    description = factory.Sequence(lambda n: f"MarketPrice {n} description")
    currency = factory.SubFactory(CurrencyFactory)
    unit_of_measure = factory.SubFactory(UnitOfMeasureFactory)
    low_price_start = fuzzy.FuzzyInteger(1, 180)
    low_price_end = fuzzy.FuzzyInteger(10, 190)
    low_price = factory.Sequence(lambda n: n + 1)
    high_price_start = fuzzy.FuzzyInteger(1, 180)
    high_price_end = fuzzy.FuzzyInteger(10, 190)
    high_price = factory.Sequence(lambda n: n + 10)


class SeasonalProductionPerformanceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SeasonalProductionPerformance
        django_get_or_create = [
            "community",
            "performance_year_start_date",
        ]

    community = factory.SubFactory(CommunityFactory)
    season = factory.SubFactory(SeasonFactory)
    performance_year_start_date = factory.Sequence(lambda n: datetime.date(1900, 1, 1) + datetime.timedelta(days=n))
    performance_year_end_date = factory.Sequence(lambda n: datetime.date(1900, 1, 1) + datetime.timedelta(days=n))
    seasonal_performance = factory.Iterator(["1", "2", "3", "4", "5"])


class HazardFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Hazard
        django_get_or_create = [
            "community",
            "chronic_or_periodic",
            "ranking",
            "hazard_category",
        ]

    community = factory.SubFactory(CommunityFactory)
    chronic_or_periodic = factory.Iterator(["chronic", "periodic"])
    ranking = factory.Iterator(["1", "2", "3"])
    hazard_category = factory.SubFactory(HazardCategoryFactory)
    description = factory.Sequence(lambda n: f"Hazard {n} description")


class EventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Event
        django_get_or_create = [
            "community",
            "event_year_start_date",
        ]

    community = factory.SubFactory(CommunityFactory)
    event_year_start_date = factory.Sequence(lambda n: datetime.date(1900, 1, 1) + datetime.timedelta(days=n))
    event_year_end_date = factory.Sequence(lambda n: datetime.date(1900, 1, 1) + datetime.timedelta(days=n))
    description = factory.Sequence(lambda n: f"Event {n} description")


class ExpandabilityFactorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExpandabilityFactor
        django_get_or_create = [
            "livelihood_strategy",
            "wealth_group",
        ]

    livelihood_strategy = factory.SubFactory(
        "baseline.tests.factories.LivelihoodStrategyFactory",
        livelihood_zone_baseline=factory.SelfAttribute("..wealth_group.livelihood_zone_baseline"),
    )
    wealth_group = factory.SubFactory(WealthGroupFactory)
    percentage_produced = fuzzy.FuzzyInteger(10, 200)
    percentage_sold = fuzzy.FuzzyInteger(0, 200)
    percentage_other_uses = fuzzy.FuzzyInteger(0, 200)
    percentage_consumed = fuzzy.FuzzyInteger(0, 200)
    percentage_income = fuzzy.FuzzyInteger(0, 200)
    percentage_expenditure = fuzzy.FuzzyInteger(0, 200)
    remark = factory.Sequence(lambda n: f"ExpandabilityFactor {n} remark")


class CopingStrategyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CopingStrategy
        django_get_or_create = [
            "community",
            "leaders",
            "wealth_group",
            "livelihood_strategy",
            "strategy",
        ]

    community = factory.SubFactory(CommunityFactory)
    leaders = factory.Sequence(lambda n: f"leader {n}")
    wealth_group = factory.SubFactory(WealthGroupFactory)
    livelihood_strategy = factory.SubFactory(
        "baseline.tests.factories.LivelihoodStrategyFactory",
        livelihood_zone_baseline=factory.SelfAttribute("..wealth_group.livelihood_zone_baseline"),
    )
    strategy = factory.Iterator(["reduce", "increase"])
    by_value = fuzzy.FuzzyInteger(0, 100)
