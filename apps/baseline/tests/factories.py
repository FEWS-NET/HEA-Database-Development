import datetime

import factory
import pytz

from ..models import (
    BaselineWealthGroup,
    ButterProduction,
    Community,
    CommunityWealthGroup,
    CropProduction,
    Fishing,
    FoodPurchase,
    LivelihoodStrategy,
    LivelihoodZone,
    LivelihoodZoneBaseline,
    LivestockSales,
    MeatProduction,
    MilkProduction,
    OtherCashIncome,
    OtherPurchases,
    PaymentInKind,
    ReliefGiftsOther,
    SourceOrganization,
    WealthGroupCharacteristicValue,
    WildFoodGathering,
)


class SourceOrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SourceOrganization

    created = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    modified = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    name = factory.Sequence(lambda n: f"n{n}")
    full_name = factory.Sequence(lambda n: f"f{n}")
    description = factory.Sequence(lambda n: f"d{n}")


class LivelihoodZoneFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LivelihoodZone

    created = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    modified = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    code = factory.Sequence(lambda n: f"c{n}")
    name = factory.Sequence(lambda n: f"n{n}")
    description = factory.Sequence(lambda n: f"d{n}")
    country = factory.SubFactory("common.tests.factories.CountryFactory")


class LivelihoodZoneBaselineFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LivelihoodZoneBaseline

    created = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    modified = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    livelihood_zone = factory.SubFactory("baseline.tests.factories.LivelihoodZoneFactory")
    geography = None
    main_livelihood_category = factory.SubFactory("metadata.tests.factories.LivelihoodCategoryFactory")
    source_organization = factory.SubFactory("baseline.tests.factories.SourceOrganizationFactory")
    bss = None
    reference_year_start_date = factory.Sequence(lambda n: datetime.date(1900, 1, 1) + datetime.timedelta(days=n))
    reference_year_end_date = factory.Sequence(lambda n: datetime.date(1900, 1, 1) + datetime.timedelta(days=n))
    valid_from_date = factory.Sequence(lambda n: datetime.date(1900, 1, 1) + datetime.timedelta(days=n))
    valid_to_date = factory.Sequence(lambda n: datetime.date(1900, 1, 1) + datetime.timedelta(days=n))
    population_source = factory.Sequence(lambda n: f"p{n}")
    population_estimate = factory.Sequence(lambda n: n + 1)


class CommunityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Community

    created = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    modified = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    name = factory.Sequence(lambda n: f"n{n}")
    livelihood_zone_baseline = factory.SubFactory("baseline.tests.factories.LivelihoodZoneBaselineFactory")
    geography = None
    interview_number = factory.Sequence(lambda n: f"i{n}")
    interviewers = factory.Sequence(lambda n: f"i{n}")


class BaselineWealthGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BaselineWealthGroup

    created = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    modified = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    livelihood_zone_baseline = factory.SubFactory("baseline.tests.factories.LivelihoodZoneBaselineFactory")
    community = None
    wealth_category = factory.SubFactory("metadata.tests.factories.WealthCategoryFactory")
    percentage_of_households = factory.Sequence(lambda n: n + 1)
    average_household_size = factory.Sequence(lambda n: n + 1)


class CommunityWealthGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CommunityWealthGroup

    created = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    modified = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    livelihood_zone_baseline = factory.SubFactory("baseline.tests.factories.LivelihoodZoneBaselineFactory")
    community = factory.SubFactory("baseline.tests.factories.CommunityFactory")
    wealth_category = factory.SubFactory("metadata.tests.factories.WealthCategoryFactory")
    percentage_of_households = factory.Sequence(lambda n: n + 1)
    average_household_size = factory.Sequence(lambda n: n + 1)


class WealthGroupCharacteristicValueFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WealthGroupCharacteristicValue

    created = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    modified = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    wealth_group = factory.SubFactory("baseline.tests.factories.WealthGroupFactory")
    wealth_characteristic = factory.SubFactory("metadata.tests.factories.WealthCharacteristicFactory")
    value = factory.Sequence(lambda n: n)
    min_value = factory.Sequence(lambda n: n)
    max_value = factory.Sequence(lambda n: n)


class LivelihoodStrategyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LivelihoodStrategy

    created = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    modified = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    livelihood_zone_baseline = factory.SubFactory("baseline.tests.factories.LivelihoodZoneBaselineFactory")
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
    season = factory.SubFactory("metadata.tests.factories.SeasonFactory")
    product__unit_of_measure = factory.SelfAttribute("unit_of_measure")
    product = factory.RelatedFactory("common.tests.factories.ClassifiedProductFactory")
    unit_of_measure = factory.SubFactory("common.tests.factories.UnitOfMeasureFactory")
    currency = factory.SubFactory("common.tests.factories.CurrencyFactory")
    additional_identifier = factory.Sequence(lambda n: f"a{n}")
    household_labor_provider = factory.Iterator(["men", "women", "children", "all"])


class MilkProductionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MilkProduction

    created = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    modified = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    livelihood_strategy = factory.SubFactory("baseline.tests.factories.LivelihoodStrategyFactory")
    livelihood_zone_baseline = factory.SubFactory("baseline.tests.factories.LivelihoodZoneBaselineFactory")
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
    wealth_group = factory.SubFactory("baseline.tests.factories.WealthGroupFactory")
    quantity_produced = factory.Sequence(lambda n: n + 100)
    quantity_sold = factory.Sequence(lambda n: n + 1)
    quantity_other_uses = factory.Sequence(lambda n: n + 1)
    quantity_consumed = factory.LazyAttribute(lambda o: o.quantity_produced - o.quantity_sold - o.quantity_other_uses)
    price = factory.Sequence(lambda n: n + 1)
    income = factory.LazyAttribute(lambda o: o.quantity_sold * o.price)
    expenditure = factory.LazyAttribute(lambda o: o.quantity_produced * o.price)
    kcals_consumed = factory.Sequence(lambda n: n + 1)
    percentage_kcals = factory.Sequence(lambda n: n + 1)
    milking_animals = factory.Sequence(lambda n: n + 1)
    lactation_days = factory.Sequence(lambda n: n + 1)
    daily_production = factory.Sequence(lambda n: n + 1)
    type_of_milk_sold_or_other_uses = factory.Iterator(["skim", "whole"])


class ButterProductionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ButterProduction

    created = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    modified = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    livelihood_strategy__livelihood_zone_baseline = factory.SelfAttribute("livelihood_zone_baseline")
    livelihood_strategy = factory.SubFactory("baseline.tests.factories.LivelihoodStrategyFactory")
    livelihood_zone_baseline = factory.SubFactory("baseline.tests.factories.LivelihoodZoneBaselineFactory")
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
    wealth_group = factory.SubFactory("baseline.tests.factories.WealthGroupFactory")
    quantity_produced = factory.Sequence(lambda n: n + 100)
    quantity_sold = factory.Sequence(lambda n: n + 1)
    quantity_other_uses = factory.Sequence(lambda n: n + 1)
    quantity_consumed = factory.Sequence(lambda n: n + 1)
    price = factory.Sequence(lambda n: n + 1)
    income = factory.Sequence(lambda n: n + 1)
    expenditure = factory.Sequence(lambda n: n + 1)
    kcals_consumed = factory.Sequence(lambda n: n + 1)
    percentage_kcals = factory.Sequence(lambda n: n + 1)


class MeatProductionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MeatProduction

    created = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    modified = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    livelihood_strategy = factory.SubFactory("baseline.tests.factories.LivelihoodStrategyFactory")
    livelihood_zone_baseline = factory.SubFactory("baseline.tests.factories.LivelihoodZoneBaselineFactory")
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
    wealth_group = factory.SubFactory("baseline.tests.factories.WealthGroupFactory")
    quantity_produced = factory.Sequence(lambda n: n + 100)
    quantity_sold = factory.Sequence(lambda n: n + 1)
    quantity_other_uses = factory.Sequence(lambda n: n + 1)
    quantity_consumed = factory.Sequence(lambda n: n + 1)
    price = factory.Sequence(lambda n: n + 1)
    income = factory.Sequence(lambda n: n + 1)
    expenditure = factory.Sequence(lambda n: n + 1)
    kcals_consumed = factory.Sequence(lambda n: n + 1)
    percentage_kcals = factory.Sequence(lambda n: n + 1)
    animals_slaughtered = factory.Sequence(lambda n: n + 1)
    carcass_weight = factory.Sequence(lambda n: n + 1)


class LivestockSalesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LivestockSales

    created = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    modified = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    livelihood_strategy = factory.SubFactory("baseline.tests.factories.LivelihoodStrategyFactory")
    livelihood_zone_baseline = factory.SubFactory("baseline.tests.factories.LivelihoodZoneBaselineFactory")
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
    wealth_group = factory.SubFactory("baseline.tests.factories.WealthGroupFactory")
    quantity_produced = factory.Sequence(lambda n: n + 100)
    quantity_sold = factory.Sequence(lambda n: n + 1)
    quantity_other_uses = factory.Sequence(lambda n: n + 1)
    quantity_consumed = factory.Sequence(lambda n: n + 1)
    price = factory.Sequence(lambda n: n + 1)
    income = factory.Sequence(lambda n: n + 1)
    expenditure = factory.Sequence(lambda n: n + 1)
    kcals_consumed = factory.Sequence(lambda n: n + 1)
    percentage_kcals = factory.Sequence(lambda n: n + 1)


class CropProductionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CropProduction

    created = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    modified = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    livelihood_strategy = factory.SubFactory("baseline.tests.factories.LivelihoodStrategyFactory")
    livelihood_zone_baseline = factory.SubFactory("baseline.tests.factories.LivelihoodZoneBaselineFactory")
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
    wealth_group = factory.SubFactory("baseline.tests.factories.WealthGroupFactory")
    quantity_produced = factory.Sequence(lambda n: n + 100)
    quantity_sold = factory.Sequence(lambda n: n + 1)
    quantity_other_uses = factory.Sequence(lambda n: n + 1)
    quantity_consumed = factory.Sequence(lambda n: n + 1)
    price = factory.Sequence(lambda n: n + 1)
    income = factory.Sequence(lambda n: n + 1)
    expenditure = factory.Sequence(lambda n: n + 1)
    kcals_consumed = factory.Sequence(lambda n: n + 1)
    percentage_kcals = factory.Sequence(lambda n: n + 1)


class FoodPurchaseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FoodPurchase

    created = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    modified = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    livelihood_strategy = factory.SubFactory("baseline.tests.factories.LivelihoodStrategyFactory")
    livelihood_zone_baseline = factory.SubFactory("baseline.tests.factories.LivelihoodZoneBaselineFactory")
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
    wealth_group = factory.SubFactory("baseline.tests.factories.WealthGroupFactory")
    quantity_produced = factory.Sequence(lambda n: n + 100)
    quantity_sold = factory.Sequence(lambda n: n + 1)
    quantity_other_uses = factory.Sequence(lambda n: n + 1)
    quantity_consumed = factory.Sequence(lambda n: n + 1)
    price = factory.Sequence(lambda n: n + 1)
    income = factory.Sequence(lambda n: n + 1)
    expenditure = factory.Sequence(lambda n: n + 1)
    kcals_consumed = factory.Sequence(lambda n: n + 1)
    percentage_kcals = factory.Sequence(lambda n: n + 1)
    unit_multiple = factory.Sequence(lambda n: n + 1)
    purchases_per_month = factory.Sequence(lambda n: n + 1)
    months_per_year = factory.Sequence(lambda n: n + 1)


class PaymentInKindFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PaymentInKind

    created = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    modified = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    livelihood_strategy = factory.SubFactory("baseline.tests.factories.LivelihoodStrategyFactory")
    livelihood_zone_baseline = factory.SubFactory("baseline.tests.factories.LivelihoodZoneBaselineFactory")
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
    wealth_group = factory.SubFactory("baseline.tests.factories.WealthGroupFactory")
    quantity_produced = factory.Sequence(lambda n: n + 100)
    quantity_sold = factory.Sequence(lambda n: n + 1)
    quantity_other_uses = factory.Sequence(lambda n: n + 1)
    quantity_consumed = factory.Sequence(lambda n: n + 1)
    price = factory.Sequence(lambda n: n + 1)
    income = factory.Sequence(lambda n: n + 1)
    expenditure = factory.Sequence(lambda n: n + 1)
    kcals_consumed = factory.Sequence(lambda n: n + 1)
    percentage_kcals = factory.Sequence(lambda n: n + 1)
    payment_per_time = factory.Sequence(lambda n: n + 1)
    people_per_hh = factory.Sequence(lambda n: n + 1)
    labor_per_month = factory.Sequence(lambda n: n + 1)
    months_per_year = factory.Sequence(lambda n: n + 1)


class ReliefGiftsOtherFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ReliefGiftsOther

    created = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    modified = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    livelihood_strategy = factory.SubFactory("baseline.tests.factories.LivelihoodStrategyFactory")
    livelihood_zone_baseline = factory.SubFactory("baseline.tests.factories.LivelihoodZoneBaselineFactory")
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
    wealth_group = factory.SubFactory("baseline.tests.factories.WealthGroupFactory")
    quantity_produced = factory.Sequence(lambda n: n + 100)
    quantity_sold = factory.Sequence(lambda n: n + 1)
    quantity_other_uses = factory.Sequence(lambda n: n + 1)
    quantity_consumed = factory.Sequence(lambda n: n + 1)
    price = factory.Sequence(lambda n: n + 1)
    income = factory.Sequence(lambda n: n + 1)
    expenditure = factory.Sequence(lambda n: n + 1)
    kcals_consumed = factory.Sequence(lambda n: n + 1)
    percentage_kcals = factory.Sequence(lambda n: n + 1)
    unit_multiple = factory.Sequence(lambda n: n + 1)
    received_per_year = factory.Sequence(lambda n: n + 1)


class FishingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Fishing

    created = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    modified = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    livelihood_strategy = factory.SubFactory("baseline.tests.factories.LivelihoodStrategyFactory")
    livelihood_zone_baseline = factory.SubFactory("baseline.tests.factories.LivelihoodZoneBaselineFactory")
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
    wealth_group = factory.SubFactory("baseline.tests.factories.WealthGroupFactory")
    quantity_produced = factory.Sequence(lambda n: n + 100)
    quantity_sold = factory.Sequence(lambda n: n + 1)
    quantity_other_uses = factory.Sequence(lambda n: n + 1)
    quantity_consumed = factory.Sequence(lambda n: n + 1)
    price = factory.Sequence(lambda n: n + 1)
    income = factory.Sequence(lambda n: n + 1)
    expenditure = factory.Sequence(lambda n: n + 1)
    kcals_consumed = factory.Sequence(lambda n: n + 1)
    percentage_kcals = factory.Sequence(lambda n: n + 1)


class WildFoodGatheringFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WildFoodGathering

    created = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    modified = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    livelihood_strategy = factory.SubFactory("baseline.tests.factories.LivelihoodStrategyFactory")
    livelihood_zone_baseline = factory.SubFactory("baseline.tests.factories.LivelihoodZoneBaselineFactory")
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
    wealth_group = factory.SubFactory("baseline.tests.factories.WealthGroupFactory")
    quantity_produced = factory.Sequence(lambda n: n + 100)
    quantity_sold = factory.Sequence(lambda n: n + 1)
    quantity_other_uses = factory.Sequence(lambda n: n + 1)
    quantity_consumed = factory.Sequence(lambda n: n + 1)
    price = factory.Sequence(lambda n: n + 1)
    income = factory.Sequence(lambda n: n + 1)
    expenditure = factory.Sequence(lambda n: n + 1)
    kcals_consumed = factory.Sequence(lambda n: n + 1)
    percentage_kcals = factory.Sequence(lambda n: n + 1)


class OtherCashIncomeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OtherCashIncome

    created = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    modified = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    livelihood_strategy = factory.SubFactory("baseline.tests.factories.LivelihoodStrategyFactory")
    livelihood_zone_baseline = factory.SubFactory("baseline.tests.factories.LivelihoodZoneBaselineFactory")
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
    wealth_group = factory.SubFactory("baseline.tests.factories.WealthGroupFactory")
    quantity_produced = factory.Sequence(lambda n: n + 100)
    quantity_sold = factory.Sequence(lambda n: n + 1)
    quantity_other_uses = factory.Sequence(lambda n: n + 1)
    quantity_consumed = factory.Sequence(lambda n: n + 1)
    price = factory.Sequence(lambda n: n + 1)
    income = factory.Sequence(lambda n: n + 1)
    expenditure = factory.Sequence(lambda n: n + 1)
    kcals_consumed = factory.Sequence(lambda n: n + 1)
    percentage_kcals = factory.Sequence(lambda n: n + 1)
    payment_per_time = factory.Sequence(lambda n: n + 1)
    people_per_hh = factory.Sequence(lambda n: n + 1)
    labor_per_month = factory.Sequence(lambda n: n + 1)
    months_per_year = factory.Sequence(lambda n: n + 1)
    times_per_year = factory.Sequence(lambda n: n + 1)


class OtherPurchasesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OtherPurchases

    created = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    modified = factory.Sequence(
        lambda n: datetime.datetime(2000, 1, 1, tzinfo=pytz.UTC) + datetime.timedelta(days=n, minutes=n)
    )
    livelihood_strategy = factory.SubFactory("baseline.tests.factories.LivelihoodStrategyFactory")
    livelihood_zone_baseline = factory.SubFactory("baseline.tests.factories.LivelihoodZoneBaselineFactory")
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
    wealth_group = factory.SubFactory("baseline.tests.factories.WealthGroupFactory")
    quantity_produced = factory.Sequence(lambda n: n + 100)
    quantity_sold = factory.Sequence(lambda n: n + 1)
    quantity_other_uses = factory.Sequence(lambda n: n + 1)
    quantity_consumed = factory.Sequence(lambda n: n + 1)
    price = factory.Sequence(lambda n: n + 1)
    income = factory.Sequence(lambda n: n + 1)
    expenditure = factory.Sequence(lambda n: n + 1)
    kcals_consumed = factory.Sequence(lambda n: n + 1)
    percentage_kcals = factory.Sequence(lambda n: n + 1)
    unit_multiple = factory.Sequence(lambda n: n + 1)
    purchases_per_month = factory.Sequence(lambda n: n + 1)
    months_per_year = factory.Sequence(lambda n: n + 1)
