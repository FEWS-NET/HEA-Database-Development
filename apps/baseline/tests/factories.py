import datetime

import factory

from baseline.models import (
    AnnualProductionPerformance,
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
    LivelihoodActivity,
    LivelihoodProductCategory,
    LivelihoodStrategy,
    LivelihoodZone,
    LivelihoodZoneBaseline,
    LivestockSales,
    MarketPrice,
    MeatProduction,
    MilkProduction,
    OtherCashIncome,
    OtherPurchases,
    PaymentInKind,
    ReliefGiftsOther,
    ResponseLivelihoodActivity,
    SeasonalActivity,
    SeasonalActivityOccurrence,
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
    WealthCategoryFactory,
    WealthCharacteristicFactory,
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
    name = factory.LazyAttribute(lambda o: f"{o.code} name")
    description = factory.LazyAttribute(lambda o: f"{o.code} description")
    country = factory.SubFactory(CountryFactory)


class LivelihoodZoneBaselineFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LivelihoodZoneBaseline
        django_get_or_create = [
            "livelihood_zone",
            "source_organization",
        ]

    livelihood_zone = factory.SubFactory(LivelihoodZoneFactory)
    geography = None
    main_livelihood_category = factory.SubFactory(LivelihoodCategoryFactory)
    source_organization = factory.SubFactory(SourceOrganizationFactory)
    bss = None
    reference_year_start_date = factory.Sequence(lambda n: datetime.date(1900, 1, 1) + datetime.timedelta(days=n))
    reference_year_end_date = factory.Sequence(lambda n: datetime.date(1900, 1, 1) + datetime.timedelta(days=n + 10))
    valid_from_date = factory.Sequence(lambda n: datetime.date(1900, 1, 1) + datetime.timedelta(days=n))
    valid_to_date = factory.Sequence(lambda n: datetime.date(1900, 1, 1) + datetime.timedelta(days=n + 10))
    population_source = factory.Sequence(lambda n: f"population_source {n}")
    population_estimate = factory.Sequence(lambda n: 500 + n % 1000000)


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

    name = factory.Sequence(lambda n: f"Community {n} name")
    livelihood_zone_baseline = factory.SubFactory(LivelihoodZoneBaselineFactory)
    geography = None
    interviewers = factory.Sequence(lambda n: ", ".join(f"interviewer {i}" for i in range(n)))
    interview_number = factory.Sequence(lambda n: f"i{n}")


class WealthGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WealthGroup
        django_get_or_create = [
            "livelihood_zone_baseline",
            "community",
            "wealth_category",
        ]

    livelihood_zone_baseline = factory.SubFactory(LivelihoodZoneBaselineFactory)
    community = factory.SubFactory(
        CommunityFactory,
        livelihood_zone_baseline=factory.SelfAttribute("..livelihood_zone_baseline"),
    )
    wealth_category = factory.SubFactory(WealthCategoryFactory)
    percentage_of_households = factory.Sequence(lambda n: 10 + n % 81)
    average_household_size = factory.Sequence(lambda n: 2 + n % 29)


class BaselineWealthGroupFactory(WealthGroupFactory):
    class Meta:
        model = BaselineWealthGroup
        django_get_or_create = [
            "livelihood_zone_baseline",
            "community",
            "wealth_category",
        ]

    community = None


class CommunityWealthGroupFactory(WealthGroupFactory):
    class Meta:
        model = CommunityWealthGroup
        django_get_or_create = [
            "livelihood_zone_baseline",
            "community",
            "wealth_category",
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
    value = factory.Sequence(lambda n: n % 1000)
    min_value = factory.LazyAttribute(lambda o: o.value - 5)
    max_value = factory.LazyAttribute(lambda o: o.value + 5)


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
            "LivestockSales",
            "CropProduction",
            "FoodPurchase",
            "PaymentInKind",
            "ReliefGiftsOther",
            "Fishing",
            "WildFoodGathering",
            "OtherCashIncome",
            "OtherPurchases",
        ]
    )
    season = factory.SubFactory(SeasonFactory)
    product = factory.SubFactory(ClassifiedProductFactory)
    unit_of_measure = factory.SelfAttribute("product.unit_of_measure")
    currency = factory.SubFactory(CurrencyFactory)
    additional_identifier = factory.Sequence(lambda n: f"additional_identifier {n}")
    household_labor_provider = factory.Iterator(["men", "women", "children", "all"])


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
            "LivestockSales",
            "CropProduction",
            "FoodPurchase",
            "PaymentInKind",
            "ReliefGiftsOther",
            "Fishing",
            "WildFoodGathering",
            "OtherCashIncome",
            "OtherPurchases",
        ]
    )
    scenario = factory.Iterator(["baseline", "response"])
    quantity_produced = factory.Sequence(lambda n: 100 + n % 100)
    quantity_sold = factory.Sequence(lambda n: n % 100)
    quantity_other_uses = factory.Sequence(lambda n: n % 100)
    quantity_consumed = factory.LazyAttribute(lambda o: o.quantity_produced - o.quantity_sold - o.quantity_other_uses)
    price = factory.Sequence(lambda n: n + 1)
    income = factory.LazyAttribute(lambda o: o.quantity_sold * o.price)
    expenditure = factory.LazyAttribute(lambda o: o.quantity_produced * o.price)
    kcals_consumed = factory.LazyAttribute(
        lambda o: o.quantity_consumed * o.livelihood_strategy.product.kcals_per_unit
    )
    percentage_kcals = factory.Sequence(lambda n: 1 + n % 200)
    wealth_group = factory.SubFactory(
        WealthGroupFactory, livelihood_zone_baseline=factory.SelfAttribute("..livelihood_zone_baseline")
    )
    livelihood_strategy = factory.SubFactory(
        "baseline.tests.factories.LivelihoodStrategyFactory",
        livelihood_zone_baseline=factory.SelfAttribute("..wealth_group.livelihood_zone_baseline"),
        strategy_type=factory.SelfAttribute("..strategy_type"),
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
    milking_animals = factory.Sequence(lambda n: 1 + n % 20)
    lactation_days = factory.Sequence(lambda n: 1 + n % 365)
    daily_production = factory.Sequence(lambda n: 1 + n % 20)
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
    quantity_produced = factory.LazyAttribute(lambda o: o.animals_slaughtered * o.carcass_weight)
    animals_slaughtered = factory.Sequence(lambda n: 100 + n % 100)
    carcass_weight = factory.Sequence(lambda n: 50 + n % 100)


class LivestockSalesFactory(LivelihoodActivityFactory):
    class Meta:
        model = LivestockSales
        django_get_or_create = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
        ]

    strategy_type = "LivestockSales"


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
    quantity_produced = factory.LazyAttribute(lambda o: o.unit_multiple * o.purchases_per_month * o.months_per_year)
    unit_multiple = factory.Sequence(lambda n: n + 10)
    purchases_per_month = factory.Sequence(lambda n: 10 + n % 40)
    months_per_year = factory.Sequence(lambda n: 1 + n % 12)


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
    quantity_produced = factory.LazyAttribute(
        lambda o: o.payment_per_time * o.people_per_hh * o.labor_per_month * o.months_per_year
    )
    payment_per_time = factory.Sequence(lambda n: 10 + n % 10)
    people_per_hh = factory.Sequence(lambda n: 1 + n % 15)
    labor_per_month = factory.Sequence(lambda n: 1 + n % 20)
    months_per_year = factory.Sequence(lambda n: 1 + n % 12)


class ReliefGiftsOtherFactory(LivelihoodActivityFactory):
    class Meta:
        model = ReliefGiftsOther
        django_get_or_create = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
        ]

    strategy_type = "ReliefGiftsOther"
    quantity_produced = factory.LazyAttribute(lambda o: o.unit_multiple * o.received_per_year)
    unit_multiple = factory.Sequence(lambda n: n + 10)
    received_per_year = factory.Sequence(lambda n: 10 + n % 150)


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
        lambda o: o.payment_per_time * o.people_per_hh * o.labor_per_month * o.months_per_year
    )
    expenditure = factory.LazyAttribute(lambda o: o.quantity_produced * o.price)
    kcals_consumed = factory.LazyAttribute(
        lambda o: o.quantity_consumed * o.livelihood_strategy.product.kcals_per_unit
    )
    percentage_kcals = factory.Sequence(lambda n: 1 + n % 200)
    payment_per_time = factory.Sequence(lambda n: 1 + n % 10000)
    people_per_hh = factory.Sequence(lambda n: 1 + n % 30)
    labor_per_month = factory.Sequence(lambda n: 1 + n % 40)
    months_per_year = factory.Sequence(lambda n: 1 + n % 12)
    times_per_year = factory.Sequence(lambda n: 1 + n % 300)


class OtherPurchasesFactory(LivelihoodActivityFactory):
    class Meta:
        model = OtherPurchases
        django_get_or_create = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
        ]

    strategy_type = "OtherPurchases"
    income = factory.LazyAttribute(lambda o: o.quantity_sold * o.price)
    expenditure = factory.LazyAttribute(
        lambda o: o.price * o.unit_multiple * o.purchases_per_month * o.months_per_year
    )
    kcals_consumed = factory.LazyAttribute(
        lambda o: o.quantity_consumed * o.livelihood_strategy.product.kcals_per_unit
    )
    percentage_kcals = factory.Sequence(lambda n: 1 + n % 200)
    unit_multiple = factory.Sequence(lambda n: 1 + n % 1000)
    purchases_per_month = factory.Sequence(lambda n: 1 + n % 50)
    months_per_year = factory.Sequence(lambda n: 1 + n % 12)


class SeasonalActivityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SeasonalActivity
        django_get_or_create = [
            "livelihood_zone_baseline",
            "activity_type",
            "season",
            "product",
        ]

    livelihood_zone_baseline = factory.SubFactory(LivelihoodZoneBaselineFactory)
    activity_type = factory.SubFactory(SeasonalActivityTypeFactory)
    season = factory.SubFactory(SeasonFactory)
    product = factory.SubFactory(ClassifiedProductFactory)


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
    start = factory.Sequence(lambda n: 1 + n % 365)
    end = factory.Sequence(lambda n: 1 + n % 365)


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
        cpcv2=factory.Iterator([f"R019{n}" for n in range(1, 10)]),
    )
    crop_purpose = factory.Iterator(["food", "cash"])
    season = factory.SubFactory(SeasonFactory)
    yield_with_inputs = factory.Sequence(lambda n: 50 + n % 10000)
    yield_without_inputs = factory.Sequence(lambda n: 1 + n % 10000)
    seed_requirement = factory.Sequence(lambda n: 1 + n % 100)
    unit_of_measure = factory.SubFactory(UnitOfMeasureFactory)


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
        cpcv2=factory.Iterator([f"L021{n}" for n in range(1, 10)]),
    )
    birth_interval = factory.Sequence(lambda n: n + 1)
    wet_season_lactation_period = factory.Sequence(lambda n: 1 + n % 80)
    wet_season_milk_production = factory.Sequence(lambda n: 1 + n % 20)
    dry_season_lactation_period = factory.Sequence(lambda n: 1 + n % 80)
    dry_season_milk_production = factory.Sequence(lambda n: 1 + n % 20)
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
    low_price_start = factory.Sequence(lambda n: 1 + n % 180)
    low_price_end = factory.Sequence(lambda n: 10 + n % 180)
    low_price = factory.Sequence(lambda n: n + 1)
    high_price_start = factory.Sequence(lambda n: 1 + n % 180)
    high_price_end = factory.Sequence(lambda n: 10 + n % 180)
    high_price = factory.Sequence(lambda n: n + 10)


class AnnualProductionPerformanceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AnnualProductionPerformance
        django_get_or_create = [
            "community",
            "performance_year_start_date",
        ]

    community = factory.SubFactory(CommunityFactory)
    performance_year_start_date = factory.Sequence(lambda n: datetime.date(1900, 1, 1) + datetime.timedelta(days=n))
    performance_year_end_date = factory.Sequence(lambda n: datetime.date(1900, 1, 1) + datetime.timedelta(days=n))
    annual_performance = factory.Iterator(["1", "2", "3", "4", "5"])
    description = factory.Sequence(lambda n: f"AnnualProductionPerformance {n} description")


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
    percentage_produced = factory.Sequence(lambda n: 10 + n % 91)
    percentage_sold = factory.Sequence(lambda n: n % 101)
    percentage_other_uses = factory.Sequence(lambda n: n % 101)
    percentage_consumed = factory.Sequence(lambda n: n % 101)
    percentage_income = factory.Sequence(lambda n: n % 101)
    percentage_expenditure = factory.Sequence(lambda n: n % 101)
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
    by_value = factory.Sequence(lambda n: n % 101)