"""
Models for managing HEA Baseline Surveys
"""
from datetime import datetime

from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.dates import MONTHS
from django.utils.translation import gettext_lazy as _
from model_utils.managers import InheritanceManager

import common.models as common_models
from common.models import ClassifiedProduct, Country, Currency, UnitOfMeasure
from metadata.models import (
    CropType,
    HazardCategory,
    LivelihoodCategory,
    LivelihoodStrategyTypes,
    LivestockType,
    Season,
    SeasonalActivityType,
    WealthCategory,
    WealthCharacteristic,
)


class SourceOrganization(models.Model):
    """
    An Organization that provides HEA Baselines.
    """

    name = common_models.NameField(max_length=200, unique=True)
    full_name = common_models.NameField(verbose_name=_("full name"), max_length=300, unique=True)
    description = common_models.DescriptionField()

    class Meta:
        verbose_name = _("Source Organization")
        verbose_name_plural = _("Source Organizations")

    class ExtraMeta:
        identifier = ["name"]


class LivelihoodZone(models.Model):
    """
    A geographical area within a Country in which people share broadly the same
    patterns of access to food and income, and have the same access to markets.
    """

    code = models.CharField(
        max_length=25,
        verbose_name=_("code"),
        primary_key=True,
        help_text=_("Primary identifier for the Livelihood Zone"),
    )
    name = common_models.NameField()
    description = common_models.DescriptionField()
    country = models.ForeignKey(Country, verbose_name=_("Country"), db_column="country_code", on_delete=models.PROTECT)

    class Meta:
        verbose_name = _("Livelihood Zone")
        verbose_name_plural = _("Livelihood Zones")

    class ExtraMeta:
        identifier = [
            "code",
        ]


class LivelihoodZoneBaseline(models.Model):
    """
    An HEA Baseline for a LivelihoodZone in a given reference year.

    Each LivelihoodZoneVersion contains the uploaded BSS that was used to
    create it.

    The reference year is a consumption year, the beginning and the end of the
    year depends on the livelihood zone. For non-Urban Livelihood Zones it is
    aligned with the Seasons.

    For agricultural and agropastoral Livelihood Zones, the reference year
    begins with the first month of the harvest and runs until the end of the
    lean season. For example, this is from October 2022 to September 2023 for
    the Sahel countries.

    For pastoralist Livelihood Zones, the reference year begins with the month
    in which the livestock have enough fodder (providing good milk yield) and
    runs until the end of lean season for livestock. Example from July 2022 to
    June 2023 for the Sahel countries.
    """

    livelihood_zone = models.ForeignKey(LivelihoodZone, on_delete=models.RESTRICT, verbose_name=_("Livelihood Zone"))
    geography = models.MultiPolygonField(geography=True, dim=2, blank=True, null=True, verbose_name=_("geography"))

    main_livelihood_category = models.ForeignKey(
        LivelihoodCategory, on_delete=models.RESTRICT, verbose_name=_("Livelihood Zone Type")
    )
    source_organization = models.ForeignKey(
        SourceOrganization, on_delete=models.RESTRICT, verbose_name=_("Source Organization")
    )
    bss = models.FileField(upload_to="baseline/bss", verbose_name=_("BSS Excel file"))
    reference_year_start_date = models.DateField(
        verbose_name=_("Reference Year Start Date"),
        help_text=_("The first day of the month of the start month in the reference year"),
    )
    reference_year_end_date = models.DateField(
        verbose_name=_("Reference Year End Date"),
        help_text=_("The last day of the month of the end month in the reference year"),
    )
    valid_from_date = models.DateField(
        verbose_name=_("Valid From Date"),
        help_text=_("The first day of the month that this baseline is valid from"),
    )
    valid_to_date = models.DateField(
        verbose_name=_("Valid To Date"),
        help_text=_("The last day of the month that this baseline is valid until"),
    )
    # Although different organizations may choose to use alternate sources of
    # population data when conducting outcome analysis, it is common for the
    # organization that conducts the baseline survey to provide a population
    # estimate for the livelihood zone at the time of the baseline.
    # Organizations using other sources for the current estimated population
    # may prefer to use the estimate of the population from that source for the
    # reference year rather than the value stored in the here.
    population_source = models.CharField(
        max_length=120,
        blank=True,
        verbose_name=_("Population Source"),
        help_text=_("The data source for the Population Estimate, e.g. National Bureau of Statistics"),
    )
    population_estimate = models.PositiveIntegerField(
        blank=True,
        verbose_name=_("Population Estimate"),
        help_text=_("The estimated population of the Livelihood Zone during the reference year"),
    )

    class Meta:
        verbose_name = _("Livelihood Zone Baseline")
        verbose_name_plural = _("Livelihood Zone Baselines")

    class ExtraMeta:
        identifier = [
            "livelihood_zone",
            "reference_year_start_date",
            "reference_year_end_date",
        ]


class Staple(models.Model):
    """
    Stores the main staples for a LivelihoodZoneBaseline.
    Does not store 'other' staples as I've not seen a need to, but could do with a CHOICE field.
    """

    livelihood_zone_baseline = models.ForeignKey(
        LivelihoodZoneBaseline,
        on_delete=models.RESTRICT,
        related_name="staple_foods",
        verbose_name=_("Livelihood Zone Baseline"),
    )
    product = models.ForeignKey(
        ClassifiedProduct, on_delete=models.RESTRICT, related_name="staple_foods", verbose_name=_("Item")
    )


# @TODO https://fewsnet.atlassian.net/browse/HEA-54
# Do we subclass GeographicUnit, in which case we don't need to worry
# about the geography field, or the way to capture the Admin units above the
# Village. If we keep this a bare Model without subclassing GeographicUnit then
# we need to add `location = models.LocationField()` and `full_name`
# (to capture the village name combined with the admin unit name)
# I favor joining to geography, even if this is one-to-one. I also favor
# putting interview details in a different table, as they are not properties
# of the Community/Village (although better still I think remove the fields to
# simplify ingestion).
# Dave: `Community(GeographicUnit)` would be the most FDW-like approach
# Girum: We need to be able to link Community to Admin2, etc. LIAS uses the
# Admin/LHZ intersect.
# Chris: 1:1 Relationship to GeographicUnit
class Community(models.Model):
    """
    A representative location within the Livelihood Zone whose population was
    surveyed to produce the Baseline.

    In a rural Livelihood Zone this is typically a Village. In an urban
    Livelihood Zone for a Francophone Country it might be a quartier within an
    arrondissement.
    """

    name = common_models.NameField()
    livelihood_zone_baseline = models.ForeignKey(
        LivelihoodZoneBaseline,
        on_delete=models.CASCADE,
        related_name="communities",
        verbose_name=_("Livelihood Zone Baseline"),
    )
    geography = models.GeometryField(geography=True, dim=2, blank=True, null=True, verbose_name=_("geography"))
    # Typicallly a number, but sometimes a code, e.g. SO03_NWA_26Nov15
    # See https://docs.google.com/spreadsheets/d/1wuXjjmQXW9qG5AV8MRKHVadrFUhleUGN/
    interview_number = models.CharField(
        max_length=10,
        verbose_name=_("Interview Number"),
        help_text=_("The interview number from 1 - 12 or interview code assigned to the Community"),
    )
    interviewers = models.CharField(
        verbose_name=_("Interviewers"),
        help_text=_("The names of interviewers who interviewed the Community, in case any clarification is neeeded."),
    )

    class Meta:
        verbose_name = _("Community")
        verbose_name_plural = _("Communities")
        constraints = [
            # Create a unique constraint on id and livelihood_zone_baseline, so that we can use it as a target for a
            # composite foreign key from Seasonal Activity, which in turn allows us to ensure that the Community
            # and the Baseline Seasonal Activity for a Seasonal Activity both have the same Livelihood Baseline.
            # We also use it as a target from WealthGroup when the Community is specified.
            models.UniqueConstraint(
                fields=["id", "livelihood_zone_baseline"],
                name="baseline_community_id_livelihood_zone_baseline_uniq",
            )
        ]


# @TODO Should this be SocioEconomicGroup, or maybe PopulationGroup,
# given female-headed households, etc.
# Jenny will check with P3 on preferred English naming. In French, it is something else anyway, I think.
class WealthGroup(models.Model):
    """
    Households within a Livelihood Zone with similar capacity to exploit the available food and income options.

    Typically, rural Livelihood Zones contain Very Poor, Poor, Medium and
    Better Off Wealth Groups.

    Note that although most Wealth Groups are based on income and assets,
    i.e. wealth, that is not always the case. For example female-headed
    households may be a surveyed Wealth Group.

    Implicit in the BSS 'WB' worksheet in Column B and the 'Data' worksheet in
    Row 3.
    """

    name = models.CharField(max_length=100, verbose_name=_("Name"))
    livelihood_zone_baseline = models.ForeignKey(
        LivelihoodZoneBaseline,
        on_delete=models.CASCADE,
        related_name="wealth_groups",
        verbose_name=_("Livelihood Zone Baseline"),
    )
    # If Community is specified then the Wealth Group represents the households
    # within that Community in the specified Wealth Category. If the Community
    # is null, then the Wealth Group represents the households with that
    # Wealth Category for the whole Livelihood Zone Baseline.
    # @TODO Or make this a mandatory geographic_unit
    # In which case we move validation out of here and into the spatial hierarchy.
    community = models.ForeignKey(
        Community, blank=True, null=True, on_delete=models.CASCADE, verbose_name=_("Community")
    )
    wealth_category = models.ForeignKey(
        WealthCategory,
        on_delete=models.CASCADE,
        verbose_name=_("Wealth Category"),
        help_text=_("Wealth Category, e.g. Poor or Better Off"),
    )
    percentage_of_households = models.PositiveSmallIntegerField(
        verbose_name=_("Percentage of households"),
        help_text=_("Percentage of households in the Community or Livelihood Zone that are in this Wealth Group"),
    )
    average_household_size = models.PositiveSmallIntegerField(verbose_name=_("Average household size"))

    def calculate_fields(self):
        if self.community:
            self.livelihood_zone_baseline = self.community.livelihood_zone_baseline

    def save(self, *args, **kwargs):
        self.calculate_fields()
        # No need to enforce foreign keys or uniqueness because database constraints will do it anyway
        self.full_clean(
            exclude=[field.name for field in self._meta.fields if isinstance(field, models.ForeignKey)],
            validate_unique=False,
        )
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Wealth Group")
        verbose_name_plural = _("Wealth Groups")
        constraints = [
            # Create a unique constraint on id and livelihood_zone_baseline, so that we can use it as a target for a
            # composite foreign key from Livelhood Activity, which in turn allows us to ensure that the Wealth Group
            # and the Livelihood Strategy for a Livelihood Activity both have the same Livelihood Baseline.
            models.UniqueConstraint(
                fields=["id", "livelihood_zone_baseline"],
                name="baseline_wealthgroup_id_livelihood_zone_baseline_uniq",
            ),
        ]


class BaselineWealthGroupManager(InheritanceManager):
    def get_queryset(self):
        return super().get_queryset().filter(community__isnull=True).select_subclasses()


class BaselineWealthGroup(WealthGroup):
    """
    Households within a Livelihood Zone with similar capacity to exploit the available food and income options.
    """

    objects = BaselineWealthGroupManager()

    def clean(self):
        if self.community:
            raise ValidationError(_("A Baseline Wealth Group cannot have a Community"))
        super().clean()

    class Meta:
        verbose_name = _("Baseline Wealth Group")
        verbose_name_plural = _("Baseline Wealth Groups")
        proxy = True


class CommunityWealthGroupManager(InheritanceManager):
    def get_queryset(self):
        return super().get_queryset().exclude(community__isnull=True).select_subclasses()


class CommunityWealthGroup(WealthGroup):
    """
    Households within a Community with similar capacity to exploit the available food and income options.
    """

    objects = CommunityWealthGroupManager()

    def clean(self):
        if not self.community:
            raise ValidationError(_("A Community Wealth Group must have a Community"))
        super().clean()

    class Meta:
        verbose_name = _("Community Wealth Group")
        verbose_name_plural = _("Community Wealth Groups")
        proxy = True


class WealthGroupCharacteristicValue(models.Model):
    """
    An attribute of a Wealth Group such as the number of school-age children.

        Stored on the BSS 'WB' worksheet.
    """

    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.RESTRICT, verbose_name=_("Wealth Group"))
    wealth_characteristic = models.ForeignKey(
        WealthCharacteristic, on_delete=models.RESTRICT, verbose_name=_("Wealth Characteristic")
    )
    # @TODO Are we better off with a `value = JSONField()` or `num_value`, `str_value`, `bool_value` as separate fields
    # or a single `value=CharField()` that we just store the str representation of the value in.
    # Examples of the characteristics we need to support:
    # "has_motorcycle" (boolean)
    # "type_water" (one from well, faucet, river, etc.)
    # "main_cash_crops" (many from ClassifiedProduct, e.g. maize,coffee)
    # "land_area" (1 decimal point numeric value, maybe with a unit of measure, e.g. 10.3 acres)
    value = models.JSONField(
        verbose_name=_("value"), help_text=_("A single property value, eg, a float, str or list, not a dict of props.")
    )
    # @TODO Do we need `low_value`` and `high_value`` to store the range for a Baseline Wealth Group.

    class Meta:
        verbose_name = _("Wealth Characteristic Value")
        verbose_name_plural = _("Wealth Characteristic Values")


class LivelihoodStrategy(models.Model):
    """
    An activity undertaken by households in a Livelihood Zone that produces food or income or requires expenditure.

    A Livelihood Strategy is not necessarily used by all Wealth Groups within the Livelihood Zone.

    Implicit in the BSS 'Data' worksheet in Column A.
    """

    # The 'Graphs' worksheet in NE01(BIL) and MG2 adds a `qui?` lookup in
    # Column F that tracks which household members are primarily responsible
    # for Livelihood Strategies that generate food and income.
    class HouseholdLaborProviders(models.TextChoices):
        MEN = "men", _("Mainly Men")
        WOMEN = "women", _("Mainly Women")
        CHILDREN = "children", _("Mainly Children")
        ALL = "all", _("All Together")

    livelihood_zone_baseline = models.ForeignKey(
        LivelihoodZoneBaseline,
        on_delete=models.CASCADE,
        related_name="livelihood_strategies",
        verbose_name=_("Livelihood Zone Baseline"),
    )
    # This also acts as a discriminator column for LivelihoodActivity
    strategy_type = models.CharField(
        max_length=30,
        choices=LivelihoodStrategyTypes.choices,
        db_index=True,
        verbose_name=_("Strategy Type"),
        help_text=_("The type of livelihood strategy, such as crop production, or wild food gathering."),
    )
    # We will need a "Year Round" or "Annual" season to account for Livelihood Strategies
    # that have equal distribution across the year, such as purchase of tea and
    # sugar, or remittances.
    season = models.ForeignKey(Season, on_delete=models.PROTECT, verbose_name=_("Season"))
    product = models.ForeignKey(
        ClassifiedProduct,
        on_delete=models.PROTECT,
        verbose_name=_("Item"),
        help_text=_("Item Produced, eg, full fat milk"),
        related_name="livelihood_strategies",
    )
    # @TODO Moved from LivelihoodActivity to LivelihoodStrategy because it is
    # defined in Column A and applies to all Wealth Groups in the BSS.
    unit_of_measure = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, verbose_name=_("Unit of Measure"))
    additional_identifier = models.CharField(
        blank=True,
        verbose_name=_("Additional Identifer"),
        help_text=_("Additional text identifying the livelihood strategy"),
    )
    # Not all BSS track this, and it isn't tracked for expenditures, so
    # the field must be `blank=True`.
    household_labor_provider = models.CharField(
        choices=HouseholdLaborProviders.choices, blank=True, verbose_name=_("Activity done by")
    )

    class Meta:
        verbose_name = _("Livelihood Strategy")
        verbose_name_plural = _("Livelihood Strategies")
        constraints = [
            models.UniqueConstraint(
                fields=["livelihood_zone_baseline", "strategy_type", "season", "product", "additional_identifier"],
                name="baseline_livelihoodstrategy_uniq",
            ),
            # Create a unique constraint on id and livelihood_zone_baseline, so that we can use it as a target for a
            # composite foreign key from Livelhood Activity, which in turn allows us to ensure that the Wealth Group
            # and the Livelihood Strategy for a Livelihood Activity both have the same Livelihood Baseline.
            models.UniqueConstraint(
                fields=["id", "livelihood_zone_baseline"],
                name="baseline_livelihoodstrategy_id_livelihood_zone_baseline_uniq",
            ),
            # Create a unique constraint on id and season, so that we can use it as a target for a
            # composite foreign key from Seasonal Activity, which in turn allows us to ensure that the Livelihood
            # Strategy and the Baseline Seasonal Activity for a Seasonal Activity both have the same Season.
            models.UniqueConstraint(
                fields=["id", "season"],
                name="baseline_livelihoodstrategy_id_season_uniq",
            ),
        ]


class LivelihoodActivity(models.Model):
    """
    An activity undertaken by households in a Wealth Group that produces food or income or requires expenditure.

    A Livelihood Activity contains the outputs of a Livelihood Strategy
    employed by a Wealth Group in a Community in the reference year, or the
    outputs of a Wealth Group representing the Baseline as a whole in either
    the reference year (the Baseline scenario) or in response to a shock (the
    Response scenario).

    Stored on the BSS 'Data' worksheet.
    """

    class LivelihoodActivityScenario(models.TextChoices):
        BASELINE = "baseline", _("Baseline")
        RESPONSE = "response", _("Response")

    livelihood_strategy = models.ForeignKey(
        LivelihoodStrategy, on_delete=models.PROTECT, help_text=_("Livelihood Strategy")
    )
    # Inherited from Livelihood Strategy, the denormalization is necessary to
    # ensure that the Livelihood Strategy and the Wealth Group belong to the
    # same Livelihood Zone Baseline.
    livelihood_zone_baseline = models.ForeignKey(
        LivelihoodZoneBaseline,
        on_delete=models.CASCADE,
        related_name="livelihood_activities",
        verbose_name=_("Livelihood Zone Baseline"),
    )
    # Inherited from Livelihood Strategy to acts as a discriminator column.
    strategy_type = models.CharField(
        max_length=30,
        choices=LivelihoodStrategyTypes.choices,
        db_index=True,
        verbose_name=_("Strategy Type"),
        help_text=_("The type of livelihood strategy, such as crop production, or wild food gathering."),
    )
    # @TODO Rather that store expandability in additional columns in the row,
    # we could store a second row containing the values for a Response scenario.
    # if we go this route remove `expandability` below
    scenario = models.CharField(
        max_length=20,
        choices=LivelihoodActivityScenario.choices,
        verbose_name=_("Scenario"),
        help_text=_("The scenario in which the outputs of this Livelihood Activity apply, e.g. baseline or response."),
    )
    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.PROTECT, help_text=_("Wealth Group"))

    quantity_produced = models.PositiveSmallIntegerField(verbose_name=_("Quantity Produced"))
    quantity_sold = models.PositiveSmallIntegerField(verbose_name=_("Quantity Sold/Exchanged"))
    quantity_other_uses = models.PositiveSmallIntegerField(verbose_name=_("Quantity Other Uses"))
    # Can normally be calculated / validated as `quantity_received - quantity_sold - quantity_other_uses`
    quantity_consumed = models.PositiveSmallIntegerField(verbose_name=_("Quantity Consumed"))

    currency = models.ForeignKey(Currency, verbose_name=_("currency"), db_column="iso4217a3", on_delete=models.PROTECT)
    price = models.FloatField(blank=True, null=True, verbose_name=_("Price"), help_text=_("Price per unit"))
    # Can be calculated / validated as `quantity_sold * price` for livelihood strategies that involve the sale of
    # a proportion of the household's own production.
    income = models.FloatField(help_text=_("Income"))
    # Can be calculated / validated as `quantity_consumed * price` for livelihood strategies that involve the purchase
    # of external goods or services.
    expenditure = models.FloatField(help_text=_("Expenditure"))

    # Can normally be calculated  / validated as `quantity_consumed` * `kcals_per_unit`
    total_kcals_consumed = models.PositiveSmallIntegerField(
        verbose_name=_("Total kcals consumed"),
        help_text=_("Total kcals consumed by a household in the reference year from this livelihood strategy"),
    )
    # Can be calculated / validated as `total_kcals_consumed / DAILY_KCAL_REQUIRED (2100) / DAYS_PER_YEAR (365) / self.wealth_group.average_household_size`  # NOQA: E501
    percentage_kcals = models.PositiveSmallIntegerField(
        verbose_name=_("Percentage of required kcals"),
        help_text=_("Percentage of annual household kcal requirement provided by this livelihood strategy"),
    )

    # @TODO: if daily calorie level varies by LZB then save consumed_kcal_percent here too
    # We think that Daily KCal is fixed at 2100
    # Is this captured per Livelihood Strategy or is it only calculated/stored at the LHZ level.
    # It is stored in the Exp Factors worksheet in the BSS, which references an external worksheet.
    # It is also present in the LIAS.
    # expandability_kcals = models.FloatField(help_text=_("Expandability in Kilocalories"))

    def calculate_fields(self):
        self.livelihood_zone_baseline = self.livelihood_strategy.livelihood_zone_baseline
        self.strategy_type = self.livelihood_strategy.strategy_type

        # @TODO Roger: Do we calculate these values or just validate them. I.e. if they load a BSS where the
        # value exists but is incorrect, do we want to raise an error rather than ignore their value and calculate
        # our own.
        # @TODO To what extent do we need to validate? Or do we just accept.
        # Dave: Do we use Django Forms as a separate validation layer, and load the data from the dataframe into a Form
        # instance and then check whether it is valid.  See Two Scoops for an explanation.
        self.is_staple = self.wealth_group.community.livelihood_zone_baseline.staple_set(
            item=self.output_item
        ).exists()
        self.total_quantity_produced = self.calculate_total_quantity_produced()
        self.income = self.calculate_income()
        # We store in local currency and unit as well as USD, kg and kcal for transparency and traceability
        self.income_usd = self.production_unit_of_measure.convert_from(self.income, self.currency)
        self.kcals_consumed = self.calculate_kcals_consumed()
        self.expandibility_kcals = self.calculate_expandibility_kcals()

    # These formulae are copied directly from the BSS cells:

    def calculate_total_quantity_produced(self):
        return self.units_produced_per_period * self.duration

    def calculate_income(self):
        return self.calculate_total_quantity_produced() * self.quantity_sold * self.price

    def calculate_kcals_consumed(self):
        return self.calculate_total_quantity_produced() * self.quantity_consumed * self.kcals_per_unit

    # @TODO: if daily calory level varies by LZB then save consumed_kcal_percent here too
    # Is this captured per Wealth Group
    # def calculate_expandibility_kcals(self):
    #    # @TODO: This is a guess, the BSSes are much more complex than this (I hope the complexity is all validation).
    #    return (
    #        self.calculate_total_quantity_produced()
    #        * (self.quantity_sold + self.quantity_other_uses)
    #        * self.kcals_per_unit
    #    )

    def clean(self):
        if self.wealth_group.livelihood_zone_baseline != self.livelihood_strategy.livelihood_zone_baseline:
            raise ValidationError(
                _(
                    "Wealth Group and Livelihood Strategy for a Livelihood Activity must belong to the same Livelihood Zone Baseline"  # NOQA: E501
                )
            )
        super().clean()

    def save(self, *args, **kwargs):
        self.calculate_fields()
        # No need to enforce foreign keys or uniqueness because database constraints will do it anyway
        self.full_clean(
            exclude=[field.name for field in self._meta.fields if isinstance(field, models.ForeignKey)],
            validate_unique=False,
        )
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Livelihood Activity")
        verbose_name_plural = _("Livelihood Activities")
        constraints = [
            # @TODO Add constraints either declared here or in a custom migration that target the composite foreign
            # keys for Wealth Group and Livelihood Strategy that include the livelihood_zone_baseline.
        ]

    class ExtraMeta:
        identifier = ["wealth_group", "item", "additional_identifier"]


class MilkProduction(LivelihoodActivity):
    """
    Production of milk by households in a Wealth Group for their own consumption, for sale and for other uses.

    Stored on the BSS 'Data' worksheet in the 'Livestock Production' section, typically starting around Row 60.
    """

    SKIM = "skim"
    WHOLE = "whole"

    MILK_TYPE_CHOICES = (
        (SKIM, _("skim")),
        (WHOLE, _("whole")),
    )

    # Production calculation /validation is `lactation days * daily_production`
    milking_animals = models.PositiveSmallIntegerField(verbose_name=_("Number of milking animals"))
    lactation_days = models.PositiveSmallIntegerField(verbose_name=_("Average number or days of lactation"))
    daily_production = models.PositiveSmallIntegerField(verbose_name=_("Average daily milk production per animal"))

    # @TODO see https://fewsnet.atlassian.net/browse/HEA-65
    # This is not required for scenario development and is only used for the kcal calculations in the BSS.
    # Do we need to store it in the database?.
    type_of_milk_sold_or_other_uses = models.CharField(
        choices=MILK_TYPE_CHOICES, verbose_name=_("Skim or whole milk sold or used")
    )

    # @TODO See https://fewsnet.atlassian.net/browse/HEA-65
    # The BSS has a single cell for kcal_percentage that covers both the Milk and Butter/Ghee
    # livelihood strategies. Can we separate these out? If not, do we store Ghee as a sale only
    # and record all consumption against milk, which is how it is calculated. Or do we create a
    # combined `DairyProduction(LivelihoodStrategy)` so that there is only a single row in the db
    # but which contains extra metadata for the ghee production/sales/other_uses. Or do we split
    # production/sales/other_users/consumption into rows in a table rather than columns so that a
    # LivelihoodStrategy can have 0 or many of each type. I.e. adopt the TransferModel approach that
    # Chris proposed early on.
    class Meta:
        verbose_name = LivelihoodStrategyTypes.MILK_PRODUCTION.label
        verbose_name_plural = LivelihoodStrategyTypes.MILK_PRODUCTION.label


class ButterProduction(LivelihoodActivity):
    """
    Production of ghee/butter by households in a Wealth Group for their own consumption, for sale and for other uses.

    Stored on the BSS 'Data' worksheet in the 'Livestock Production' section, typically starting around Row 60.
    """

    # Note that although ButterProduction is a separate livelihood strategy
    # because it generates income (and other uses) at a different price to
    # milk production, the total calories may be 0 because the BSS calculates
    # combined consumption for all dairy products.

    # Additional metadata

    # @TODO See https://fewsnet.atlassian.net/browse/HEA-65
    # Production calculation /validation is in Data:B105
    # `=IF(SUM(B90,B98)=0,"",SUM(B90,-B91*B94,-B95*B94,B98,-B99*B102,-B103*B102)*0.04)`
    # = (
    #    season1_milk.quantity_produced
    #    - (season1_milk.quantity_sold if season1_milk.type_of_milk_sold_or_other_uses == "WHOLE" else 0)
    #    - (season1_milk.quantity_other_uses if season1_milk.type_of_milk_sold_or_other_uses == "WHOLE" else 0)
    #    + season2_milk.quantity_produced
    #    - (season2_milk.quantity_sold if season2_milk.type_of_milk_sold_or_other_uses == "WHOLE" else 0)
    #    - (season2_milk.quantity_other_uses if season2_milk.type_of_milk_sold_or_other_uses == "WHOLE" else 0)
    # ) * item_yield
    # The `yield` from litres of milk to kg of ghee varies by animal - camel milk yields 0.049 kg per l, cow milk
    # yields 0.04 kg per l. Ghee/butter has 7865 kcal/kg for both animals

    # @TODO see https://fewsnet.atlassian.net/browse/HEA-65
    # Note that the kcal formulae for butter don't follow the model of `input_quantity` * `item_yield` * `kcals_per_unit` / `DAILY_KCAL_REQUIRED` / `DAYS_PER_YEAR` / `self.wealth_group.average_household_size`  # NOQA: E501
    # The calorie available approach gives a different result to the (butter produced - butter sold/exchanged - butter other uses) * kcal per kg. # NOQA: E501
    # This might not matter if we are just storing the fields from the BSS and not calculating them
    # E.g. MWMSK Data AI110: `=IF(AI105="","",(SUM(AI90)*640-SUM(AI91,AI95)*(640-300*(AI94=0))-SUM(AI106,AI107)*7865)/2100/365/AI$40)`  # NOQA: E501
    # total_milk_production * 640 - (milk_sold_or_exchanged + milk_other_uses) * (640 - (300 if sold_other_use == "skim" else 0)) - (ghee_sold_or_exchanged + ghee_other_uses)*7865  # NOQA: E501
    # Doesn't reconcile with Ghee production, e.g. AI105 because that has:
    # =IF(SUM(AI90,AI98)=0,"",SUM(AI90,-AI91*AI94,-AI95*AI94,AI98,-AI99*AI102,-AI103*AI102)*0.04)

    class Meta:
        verbose_name = LivelihoodStrategyTypes.BUTTER_PRODUCTION.label
        verbose_name_plural = LivelihoodStrategyTypes.BUTTER_PRODUCTION.label


class MeatProduction(LivelihoodActivity):
    """
    Production of meat by households in a Wealth Group for their own consumption.

    Stored on the BSS 'Data' worksheet in the 'Livestock Production' section, typically starting around Row 172.
    """

    # Production calculation /validation is `input_quantity` * `item_yield`
    animals_slaughtered = models.PositiveSmallIntegerField(verbose_name=_("Number of animals slaughtered"))
    item_yield = models.FloatField(verbose_name=_("Carcass weight per animal"))

    class Meta:
        verbose_name = LivelihoodStrategyTypes.MEAT_PRODUCTION.label
        verbose_name_plural = LivelihoodStrategyTypes.MEAT_PRODUCTION.label


class LivestockSales(LivelihoodActivity):
    """
    Sale of livestock by households in a Wealth Group for cash income.

    Stored on the BSS 'Data' worksheet in the 'Livestock Production' section, typically starting around Row 181.
    """

    # In Somalia they track export/local sales separately - see SO18 Data:B178 and also B770
    # @TODO Do we need to keep this as a separate field, or can we create a generic field in LivelihoodStrategy for
    # `subtype` or similar.
    product_destination = models.CharField(
        verbose_name=_("Product Destination"), help_text=_("The product destination, e.g. local or export")
    )

    # Production calculation /validation is `input_quantity` * `item_yield`
    animals_sold = models.PositiveSmallIntegerField(verbose_name=_("Number of animals sold"))

    # @TODO Do we need validation around offtake (animals_sold) to make sure
    # that they are selling and killing more animals than they own.
    class Meta:
        verbose_name = LivelihoodStrategyTypes.LIVESTOCK_SALES.label
        verbose_name_plural = LivelihoodStrategyTypes.LIVESTOCK_SALES.label


class CropProduction(LivelihoodActivity):
    """
    Production of crops by households in a Wealth Group for their own consumption, for sale and for other uses.

    Stored on the BSS 'Data' worksheet in the 'Crop Production' section, typically starting around Row 221.

    This includes consumption of Green Maize, where we need to reverse engineer the quantity produced from the
    provided kcal_percentage and the kcal/kg.
    """

    # @TODO See https://fewsnet.atlassian.net/browse/HEA-67
    # Are there other types than rainfed and irrigated?
    # @TODO Do we need to keep this as a separate field, or can we create a generic field in LivelihoodStrategy for
    # `subtype` or similar.  The production system is combined with other modifiers like Green Consumption.
    # I.e. we have Rainfed, Green Consumption so perhaps subtype is necessary even if we have production_system as a
    # separate field. Although pehaps Green Maize is a different crop type - because the Kcal/kg will be different.
    production_system = models.CharField(
        max_length=60,
        default="rainfed",
        verbose_name=_("Production System"),
        help_text=_("Production system used to grow the crop, such as rainfed or irrigated"),
    )

    class Meta:
        verbose_name = LivelihoodStrategyTypes.CROP_PRODUCTION.label
        verbose_name_plural = LivelihoodStrategyTypes.CROP_PRODUCTION.label


class FoodPurchase(LivelihoodActivity):
    """
    Purchase of food items that contribute to nutrition by households in a Wealth Group.

    Stored on the BSS 'Data' worksheet in the 'Food Purchase' section, typically starting around Row 421.
    """

    # Production calculation/validation is `unit_of_measure * unit_multiple * purchases_per_month  * months_per_year`
    # Do we need this, or can we use combined units of measure like FDW, e.g. 5kg
    # NIO93 Row B422 tia = 2.5kg
    unit_multiple = models.PositiveSmallIntegerField(
        verbose_name=_("Unit Multiple"), help_text=_("Multiple of the unit of measure in a single purchase")
    )
    purchases_per_month = models.PositiveSmallIntegerField(verbose_name=_("Purchases per month"))
    months_per_year = models.PositiveSmallIntegerField(
        verbose_name=_("Months per year"), help_text=_("Number of months in a year that the product is purchased")
    )

    class Meta:
        verbose_name = LivelihoodStrategyTypes.FOOD_PURCHASE.label
        verbose_name_plural = _("Food Purchases")


class PaymentInKind(LivelihoodActivity):
    """
    Food items that contribute to nutrition by households in a Wealth Group received in exchange for labor.

    Stored on the BSS 'Data' worksheet in the 'Payment In Kind' section, typically starting around Row 514.
    """

    # Production calculation/validation is `people_per_hh * labor_per_month * months_per_year`
    people_per_hh = models.PositiveSmallIntegerField(
        verbose_name=_("People per household"), help_text=_("Number of household members who perform the labor")
    )
    labor_per_month = models.PositiveSmallIntegerField(verbose_name=_("Labor per month"))
    months_per_year = models.PositiveSmallIntegerField(
        verbose_name=_("Months per year"), help_text=_("Number of months in a year that the labor is performed")
    )

    class Meta:
        verbose_name = LivelihoodStrategyTypes.PAYMENT_IN_KIND.label
        verbose_name_plural = _("Payments in Kind")


class ReliefGiftsOther(LivelihoodActivity):
    """
    Food items that contribute to nutrition received by households in a Wealth Group as relief, gifts, etc.
    and which are not bought or exchanged.

    Stored on the BSS 'Data' worksheet in the 'Relief, Gifts and Other' section, typically starting around Row 533.
    """

    # Production calculation /validation is `unit_of_measure * unit_multiple * received_per_year`
    unit_multiple = models.PositiveSmallIntegerField(
        verbose_name=_("Unit Multiple"), help_text=_("Multiple of the unit of measure in a single gift")
    )
    received_per_year = models.PositiveSmallIntegerField(
        verbose_name=_("Gifts per year"), help_text=_("Number of times in a year that the item is received")
    )

    class Meta:
        verbose_name = LivelihoodStrategyTypes.RELIEF_GIFTS_OTHER.label
        verbose_name_plural = LivelihoodStrategyTypes.RELIEF_GIFTS_OTHER.label


class Fishing(LivelihoodActivity):
    """
    Fishing by households in a Wealth Group for their own consumption, for sale and for other uses.

    Stored on the BSS 'Data3' worksheet in the 'Fishing' section, typically starting around Row 48
    and summarized in the 'Data' worksheet in the 'Wild Foods' section, typically starting around Row 550.
    """

    class Meta:
        verbose_name = LivelihoodStrategyTypes.FISHING.label
        verbose_name_plural = LivelihoodStrategyTypes.FISHING.label
        proxy = True


class WildFoodGathering(LivelihoodActivity):
    """
    Gathering of wild food by households in a Wealth Group for their own consumption, for sale and for other uses.

    Stored on the BSS 'Data3' worksheet in the Wild Foods section, typically starting around Row 9
    and summarized in the 'Data' worksheet in the Wild Foods section, typically starting around Row 560.
    """

    class Meta:
        verbose_name = LivelihoodStrategyTypes.WILD_FOOD_GATHERING.label
        verbose_name_plural = LivelihoodStrategyTypes.WILD_FOOD_GATHERING.label
        proxy = True


class OtherCashIncome(LivelihoodActivity):
    """
    Income received by households in a Wealth Group as payment for labor or from self-employment, remittances, etc.

    Stored on the BSS 'Data2' worksheet and summarized in the 'Data' worksheet in the 'Other Cash Income' section,
    typically starting around Row 580.
    """

    # Production calculation/validation is `people_per_hh * labor_per_month * months_per_year`
    # However, some other income (e.g. Remittances) just has a number of times per year and is not calculated from
    # people_per_hh, etc. Therefore those fields must be nullable, and we must store the total number of times per year
    # as a separate field
    people_per_hh = models.PositiveSmallIntegerField(
        verbose_name=_("People per household"),
        blank=True,
        null=True,
        help_text=_("Number of household members who perform the labor"),
    )
    labor_per_month = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_("Labor per month"))
    months_per_year = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Months per year"),
        help_text=_("Number of months in a year that the labor is performed"),
    )
    times_per_year = models.PositiveSmallIntegerField(
        verbose_name=_("Times per year"),
        help_text=_("Number of times in a year that the income is received"),
    )

    class Meta:
        verbose_name = LivelihoodStrategyTypes.OTHER_CASH_INCOME.label
        verbose_name_plural = LivelihoodStrategyTypes.OTHER_CASH_INCOME.label


class OtherPurchases(LivelihoodActivity):
    """
    Expenditure by households in a Wealth Group on items that don't contribute to nutrition.

    Stored on the BSS 'Data' worksheet in the 'Other Purchases' section, typically starting around Row 646.
    """

    # Production calculation/validation is `unit_of_measure * unit_multiple * purchases_per_month  * months_per_year`
    # However, some other purchases total expenditure and is not calculated from individual fields, therefore the
    # individual fields must be nullable
    # Do we need this, or can we use combined units of measure like FDW, e.g. 5kg
    # NIO93 Row B422 tia = 2.5kg
    unit_multiple = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Unit Multiple"),
        help_text=_("Multiple of the unit of measure in a single purchase"),
    )
    purchases_per_month = models.PositiveSmallIntegerField(
        blank=True, null=True, verbose_name=_("Purchases per month")
    )
    months_per_year = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Months per year"),
        help_text=_("Number of months in a year that the product is purchased"),
    )

    class Meta:
        verbose_name = LivelihoodStrategyTypes.OTHER_PURCHASES.label
        verbose_name_plural = LivelihoodStrategyTypes.OTHER_PURCHASES.label


class SeasonalActivity(models.Model):
    """
    An activity or event undertaken/experienced by households in a Livelihood Zone at specific periods during the year.

    Implicit in the BSS 'Seas Cal' worksheet in Column A, if present.
    """

    livelihood_zone_baseline = models.ForeignKey(
        LivelihoodZoneBaseline,
        on_delete=models.RESTRICT,
        related_name="baseline_seasonal_activities",
        verbose_name=_("Livelihood Zone Baseline"),
    )
    activity_type = models.ForeignKey(
        SeasonalActivityType, on_delete=models.RESTRICT, verbose_name=_("Seasonal Activity Type")
    )
    # @TODO If the data means that we can't derive this, then maybe this goes away, but then we'd need to store a name.
    season = models.ForeignKey(Season, on_delete=models.PROTECT, verbose_name=_("Season"))
    product = models.ForeignKey(
        ClassifiedProduct,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_("Item"),
        help_text=_("Item Produced, eg, full fat milk"),
        related_name="baseline_seasonal_activities",
    )

    class Meta:
        verbose_name = _("Seasonal Activity")
        verbose_name_plural = _("Seasonal Activities")
        constraints = [
            # Create a unique constraint on id and livelihood_zone_baseline, so that we can use it as a target for a
            # composite foreign key from Seasonal Activity, which in turn allows us to ensure that the Community
            # and the Baseline Seasonal Activity for a Seasonal Activity both have the same Livelihood Baseline.
            models.UniqueConstraint(
                fields=["id", "livelihood_zone_baseline"],
                name="baseline_seasonalactivity_id_livelihood_zone_baseline_uniq",
            ),
            # Create a unique constraint on id and season, so that we can use it as a target for a
            # composite foreign key from Seasonal Activity, which in turn allows us to ensure that the Livelihood
            # Strategy and the Baseline Seasonal Activity for a Seasonal Activity both have the same Season.
            models.UniqueConstraint(
                fields=["id", "season"],
                name="baseline_seasonalactivity_id_season_uniq",
            ),
        ]


class SeasonalActivityOccurrence(models.Model):
    """
    The specific times when a Seasonal Activity is undertaken in a Community or in the Liveihood Zone as a whole.

    Stored in the BSS 'Seas Cal' worksheet, if present.
    """

    seasonal_activity = models.ForeignKey(
        SeasonalActivity, on_delete=models.RESTRICT, verbose_name=_("Seasonal Activity")
    )
    # Inherited from the Seasonal Activity, the denormalization is necessary to
    # ensure that the Seasonal Activity and the Community belong to the
    # same Livelihood Zone Baseline.
    livelihood_zone_baseline = models.ForeignKey(
        LivelihoodZoneBaseline,
        on_delete=models.RESTRICT,
        related_name="seasonal_activities",
        verbose_name=_("Livelihood Zone Baseline"),
    )
    # Community is optional so that we can store a Livelihood Zone-level Seasonal Calendar.
    community = models.ForeignKey(
        Community, blank=True, null=True, on_delete=models.RESTRICT, verbose_name=_("Community or Village")
    )

    # Tracks when the activity occurs (the month when the activity typically occurs)
    # We can have a validator here, put the month no - e.g. 9, 10, 11
    # @TODO I don't think we want a single month here, I think this model represents the row on the Seasonal Calendar
    # in Form 3 - it is an activity that occurs in multiple months.
    # @TODO Do we store the activities as months or as a start and end day to allow more granularity
    # See https://fewsnet.atlassian.net/browse/DATA-2709 for a discussion of day vs month for Crop Calendars in the
    # FDW Crop Production domain.
    # activity_occurence = models.JSONField(verbose_name=_("Activity occurrence"))

    # Distinct Start and End fields, one row per period
    # I don't think we will have multiple periods per season, so we end up with one row per community, plus an extra
    # one for the baseline.

    # We use day in the year instead of month to allow greater granularity,
    # and compatibility with the potential FDW Enhanced Crop Calendar output.
    # Note that if the occurrence goes over the year end, then the start day
    # will be larger than the end day.
    start = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(365), MinValueValidator(1)], verbose_name=_("Start Day")
    )
    end = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(365), MinValueValidator(1)], verbose_name=_("End Day")
    )

    def start_month(self):
        return self.get_month_from_day_number(self.start)

    def end_month(self):
        return self.get_month_from_day_number(self.end)

    def get_month_from_day_number(self, day_number):
        _date = datetime.date(self.livelihood_zone_baseline.reference_year_start_date.year(), 1, 1).fromordinal(
            day_number
        )
        return _date.month

    # @TODO Do any of these offer advantages, that aren't easily achieved
    # using calculated fields or queryset or serializer methods?
    """
    # OR

    start = models.PositiveSmallIntegerField(
        choices=MONTHS.items(), validators=[MaxValueValidator(12), MinValueValidator(1)], verbose_name=_("Start Month")
    )
    end = models.PositiveSmallIntegerField(
        choices=MONTHS.items(), validators=[MaxValueValidator(12), MinValueValidator(1)], verbose_name=_("End Month")
    )

    # OR

    # One row per month:
    month = models.PositiveSmallIntegerField(
        choices=MONTHS.items(), validators=[MaxValueValidator(12), MinValueValidator(1)], verbose_name=_("Month")
    )

    # OR

    # One column per month.
    # Pros: Easy to add up the  numbers by month required for the seasonal calendar summary, easy to explain
    # Cons: It is a denormalization - the "correct" model is a table for ActivityMonth
    january = models.BooleanField(
        default=False, verbose_name=_("January"), help_text=_("Is the activity undertaken in January?")
    )
    february = models.BooleanField(
        default=False, verbose_name=_("February"), help_text=_("Is the activity undertaken in February?")
    )
    march = models.BooleanField(
        default=False, verbose_name=_("March"), help_text=_("Is the activity undertaken in March?")
    )
    april = models.BooleanField(
        default=False, verbose_name=_("April"), help_text=_("Is the activity undertaken in April?")
    )
    may = models.BooleanField(default=False, verbose_name=_("May"), help_text=_("Is the activity undertaken in May?"))
    june = models.BooleanField(
        default=False, verbose_name=_("June"), help_text=_("Is the activity undertaken in June?")
    )
    july = models.BooleanField(
        default=False, verbose_name=_("July"), help_text=_("Is the activity undertaken in July?")
    )
    august = models.BooleanField(
        default=False, verbose_name=_("August"), help_text=_("Is the activity undertaken in August?")
    )
    september = models.BooleanField(
        default=False, verbose_name=_("September"), help_text=_("Is the activity undertaken in September?")
    )
    october = models.BooleanField(
        default=False, verbose_name=_("October"), help_text=_("Is the activity undertaken in October?")
    )
    november = models.BooleanField(
        default=False, verbose_name=_("November"), help_text=_("Is the activity undertaken in November?")
    )
    december = models.BooleanField(
        default=False, verbose_name=_("December"), help_text=_("Is the activity undertaken in December?")
    )

    # OR

    # Array field that contains the months:
    # Pros - less wordy
    # Cons - harder to validate, or aggregate, or display, and not database independent
    months = ArrayField(
        models.PositiveSmallIntegerField(validators=[MaxValueValidator(12), MinValueValidator(1)]),
        verbose_name=_("Months"),
        help_text=_("Months the activity is undertaken in"),
    )

    # OR

    # Array of booleans, same pros and cons, marginally easier to aggregate
    months = ArrayField(
        models.BooleanField(), size=12, verbose_name=_("Months"), help_text=_("Months the activity is undertaken in")
    )
    """

    def calculate_fields(self):
        self.livelihood_zone_baseline = self.seasonal_activity.livelihood_zone_baseline

    def clean(self):
        if (
            self.community
            and self.community.livelihood_zone_baseline != self.seasonal_activity.livelihood_zone_baseline
        ):
            raise ValidationError(
                _(
                    "Community and Seasonal Activity for a Seasonal Activity Occurrence must belong to the same Livelihood Zone Baseline"  # NOQA: E501
                )
            )
        super().clean()

    def save(self, *args, **kwargs):
        self.calculate_fields()
        # No need to enforce foreign keys or uniqueness because database constraints will do it anyway
        self.full_clean(
            exclude=[field.name for field in self._meta.fields if isinstance(field, models.ForeignKey)],
            validate_unique=False,
        )
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Seasonal Activity Occurrence")
        verbose_name_plural = _("Seasonal Activity Occurrences")
        constraints = [
            # @TODO Add constraints either declared here or in a custom migration that target the composite foreign
            # keys for Community and Baseline Seasonal Activity that include the livelihood_zone_baseline.
        ]


class CommunityCropProduction(models.Model):
    """
    The community crop production data for a crop producing community
    Form 3's CROP PRODUCTION is used for community-level interviews
    And the data goes to the BSS's 'Production' worksheet
    """

    CROP_PURPOSE = (
        ("main_crop", "Main Food Crop"),
        ("cash_crop", "Cash Crop"),
    )
    community = models.ForeignKey(Community, on_delete=models.RESTRICT, verbose_name=_("Community or Village"))
    crop_type = models.ForeignKey(CropType, on_delete=models.RESTRICT, verbose_name=_("Crop Type"))
    crop_purpose = models.CharField(max_length=20, choices=CROP_PURPOSE, verbose_name=_("Crop purpose"))
    season = models.ForeignKey(Season, on_delete=models.RESTRICT, verbose_name=_("Season"))
    production_with_inputs = models.FloatField(
        verbose_name=_("Production with input"),
        help_text=_("Yield in reference period with input (seed and fertilizer)"),
    )
    production_with_out_inputs = models.FloatField(
        verbose_name=_("Production with input"),
        help_text=_("Yield in reference period without input (seed and fertilizer)"),
    )
    seed_requirement = models.FloatField(verbose_name=_("Seed requirement"))
    unit_of_land = models.ForeignKey(UnitOfMeasure, on_delete=models.RESTRICT, verbose_name=_("Unit of land"))
    # @TODO We need to store the harvest month for each crop, because it is needed
    # to calculate the per month food, income and expenditure shown in Table 4 of the LIAS Sheet S

    class Meta:
        verbose_name = _("Community Crop Production")
        verbose_name_plural = _("Community Crop Productions")


# @TODO Are these fields from Form 3 required here on CommunityLivestock,
# or are they on WealthGroupLivestock as a result of the repition on Form 4
# These worksheets are locked in the BSS. They are important reference data even
# if the WealthGroup-level values are used for calculations.
class CommunityLivestock(models.Model):
    """
    An animal typically raised by households in a Community, with revelant additional attributes.

    This data is typically captured in Form 3 and stored in the Production worksheet in the BSS.
    """

    community = models.ForeignKey(Community, on_delete=models.CASCADE, verbose_name=_("Wealth Group"))
    livestock_type = models.ForeignKey(LivestockType, on_delete=models.RESTRICT, verbose_name=_("Livestock Type"))
    birth_interval = models.PositiveSmallIntegerField(
        verbose_name=_("Birth Interval"), help_text=_("Number of months between Births")
    )
    wet_season_lactation_period = models.PositiveSmallIntegerField(
        verbose_name=_("Wet Season Lactation Period"), help_text=_("Number of days of lactation during the wet season")
    )
    wet_season_milk_production = models.PositiveSmallIntegerField(
        verbose_name=_("Wet Season Milk Production"),
        help_text=_("Number of litres produced each day during the wet season"),
    )
    dry_season_lactation_period = models.PositiveSmallIntegerField(
        verbose_name=_("Dry Season Lactation Period"), help_text=_("Number of days of lactation during the dry season")
    )
    dry_season_milk_production = models.PositiveSmallIntegerField(
        verbose_name=_("Dry Season Milk Production"),
        help_text=_("Number of litres produced each day during the dry season"),
    )
    age_at_sale = models.PositiveSmallIntegerField(
        verbose_name=_("Age at Sale"), help_text=_("Age in months at which the animal is typically sold/exchanged")
    )
    # @TODO At implementation we need to ensure consistency across records
    # that means we either need a EAV table or validation at data entry.
    additional_attributes = models.JSONField()

    class Meta:
        verbose_name = _("Wealth Group Attribute")
        verbose_name_plural = _("Wealth Group Attributes")


class Market(models.Model):
    """
    The markets in the bss are just names
    TODO: should we make this spatial? and move it to spatial or metadata?
    """

    name = common_models.NameField(verbose_name=_("Name"))
    community = models.ForeignKey(Community, on_delete=models.RESTRICT, verbose_name=_("Community or Village"))

    class Meta:
        verbose_name = _("Market")
        verbose_name_plural = _("Markets")


class MarketPrice(models.Model):
    """
    Prices for the reference year are interviewed in Form 3
    Data is captured in 'prices' worksheet of the BSS
    """

    MONTHS = MONTHS.items()
    community = models.ForeignKey(Community, on_delete=models.RESTRICT, verbose_name=_("Community or Village"))
    # We need the item to reference it but the item can be Crop, Livestock, Other expenditure items
    # e.g. tea, coffee, sugar ..# do we need to have
    # a) something similar to Classified Product or
    # b) a reference model -
    # MarketItem with category as Main food, Cash crops Livestock ..
    product = models.ForeignKey(
        ClassifiedProduct,
        on_delete=models.RESTRICT,
        related_name="market_prices",
        help_text=_("Crop, livestock or other category of items"),
    )
    market = models.ForeignKey(Market, on_delete=models.RESTRICT)
    low_price = models.FloatField("Low price")
    low_price_month = models.SmallIntegerField(choices=list(MONTHS), verbose_name=_("Low Price Month"))
    high_price = models.FloatField("High price")
    high_price_month = models.SmallIntegerField(choices=list(MONTHS), verbose_name=_("High Price Month"))
    unit_of_measure = models.ForeignKey(UnitOfMeasure, on_delete=models.RESTRICT, verbose_name=_("Unit of measure"))

    class Meta:
        verbose_name = _("MarketPrice")
        verbose_name_plural = _("MarketPrices")


# LabourMarket?
# LivestockMigration
# The interview form has these but couldn't find it in the BSSs


class Hazard(models.Model):
    """
    A shock such as drought, flood, conflict or market disruption which is likely
    to have an impact on people’s livelihoods
    Form 3 interviews hazard information and the BSS has 'timeline' for capturing Chronic and Periodic Hazards
    """

    community = models.ForeignKey(Community, on_delete=models.RESTRICT, verbose_name=_("Community or Village"))
    hazard_category = models.ForeignKey(HazardCategory, on_delete=models.RESTRICT, verbose_name=_("Hazard Category"))
    is_chronic = models.BooleanField(verbose_name=_("Is Chronic"))
    year = models.IntegerField(
        validators=[
            MinValueValidator(1900, message="Year must be greater than or equal to 1900."),
            MaxValueValidator(2100, message="Year must be less than or equal to 2100."),
        ]
    )
    seasonal_performance = models.SmallIntegerField(
        validators=[
            MinValueValidator(1, message="Performance rank must be at least 1."),
            MaxValueValidator(5, message="Performance rank must be at most 5."),
        ]
    )
    event = common_models.DescriptionField(
        max_length=255, null=True, blank=True, verbose_name=_("Description of event(s)")
    )
    response = common_models.DescriptionField(
        max_length=255, null=True, blank=True, verbose_name=_("Description of event(s)")
    )

    class Meta:
        verbose_name = _("Hazard")
        verbose_name_plural = _("Hazards")
