"""
Models for managing HEA Baseline Surveys
"""
from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.dates import MONTHS
from django.utils.translation import gettext_lazy as _

import common.models as common_models
from common.models import Country, Currency
from metadata.models import (
    CropType,
    Dimension,
    HazardCategory,
    Item,
    LivelihoodCategory,
    LivestockType,
    SeasonalActivityCategory,
    UnitOfMeasure,
    WealthCategory,
    WealthGroupCharacteristic,
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


# @TODO Is this still necessary at implementation?
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
    country = models.ForeignKey(Country, verbose_name=_("country"), db_column="country_code", on_delete=models.PROTECT)
    geography = models.MultiPolygonField(geography=True, dim=2, blank=True, null=True, verbose_name=_("geography"))

    # @TODO is this valuable for doing cross-LHZ analysis even though it is not
    # in the BSS. Could be calculated from WorldPop or LandScan.
    # @TODO does this need to be calibrated against an external data source
    # @TODO do we need to be able to return the value for years other than the
    # current one?
    population_estimate = models.PositiveIntegerField(
        verbose_name=_("Population Estimate"),
    )

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
    # @TODO according to Form 1 this is the Main Livelihood Category. Therefore
    # I think we should rename this to `main_livelihood_category`. Should we
    # also rename the reference table to `LivelihoodCategory` or `MainLivelihoodCategory`,
    # or leave it as `LivelihoodZoneType`, or shorten it to `LivelihoodType`?
    # Or maybe Production System Category
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

    livelihood_zone = models.ForeignKey(LivelihoodZone, on_delete=models.RESTRICT, verbose_name=_("Livelihood Zone"))
    item = models.ForeignKey(Item, on_delete=models.RESTRICT, verbose_name=_("Item"))


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
        LivelihoodZoneBaseline, on_delete=models.CASCADE, verbose_name=_("Livelihood Zone")
    )
    geography = models.GeometryField(geography=True, dim=2, blank=True, null=True, verbose_name=_("geography"))
    # @TODO Check if this need to be char.- Check Somalia
    interview_number = models.PositiveSmallIntegerField(
        verbose_name=_("Interview Number"),
        help_text=_("The interview number from 1 - 12 assigned to the Community"),
    )
    interviewers = models.CharField(
        verbose_name=_("Interviewers"),
        help_text=_("The names of interviewers who interviewed the Community, in case any clarification is neeeded."),
    )

    class Meta:
        verbose_name = _("Community")
        verbose_name_plural = _("Communities")


# @TODO Should this be SocioEconomicGroup, or maybe PopulationGroup,
# given female-headed households, etc.
class WealthGroup(models.Model):
    """
    All the households within the same Community who share similar
    capacity to exploit the different food and income options within a
    particular Livelihood Zone.

    Normally, Livelihood Zone contains Very Poor, Poor, Medium and Better Off
    Wealth Groups.

    Note that although most Wealth Groups are based on income and assets,
    i.e. wealth, that is not always the case. For example female-headed
    households may be a surveyed Wealth Group.
    """

    name = models.CharField(max_length=100, verbose_name=_("Name"))
    community = models.ForeignKey(Community, on_delete=models.CASCADE, verbose_name=_("Community"))
    wealth_category = models.ForeignKey(WealthCategory, on_delete=models.CASCADE, verbose_name=_("Wealth Category"))
    percentage_of_households = models.PositiveSmallIntegerField(
        verbose_name=_("Percentage of households"),
        help_text=_("Percentage of households in the Community that are in this Wealth Group"),
    )
    average_household_size = models.PositiveSmallIntegerField(verbose_name=_("Average household size"))

    class Meta:
        verbose_name = _("Wealth Group")
        verbose_name_plural = _("Wealth Groups")


class WealthGroupCharacteristicValue(models.Model):
    """
    An attribute of a Wealth Group such as the number of school-age children.
    """

    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.RESTRICT, verbose_name=_("Wealth Group"))
    attribute_type = models.ForeignKey(
        WealthGroupCharacteristic, on_delete=models.RESTRICT, verbose_name=_("Attribute Type")
    )
    # @TODO What are the examples of a non-numeric `value`?
    value = models.JSONField(verbose_name=_("A single property value, eg, a float, str or list, not a dict of props."))

    class Meta:
        verbose_name = _("Wealth Group Characteristic")
        verbose_name_plural = _("Wealth Group Characteristics")


class ProductionModel(models.Model):
    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.PROTECT, help_text=_("Wealth Group"))
    season = models.PositiveSmallIntegerField(help_text=_("Season number 1 or 2"))
    input_item = models.ForeignKey(
        Item, on_delete=models.PROTECT, help_text=_("Item Used, eg, milking cow"), related_name="input_items"
    )
    input_quantity = common_models.PrecisionField(help_text=_("Input Quantity, eg, number of milking cows"))
    output_item = models.ForeignKey(
        Item, on_delete=models.PROTECT, help_text=_("Item Produced, eg, " "full fat milk"), related_name="output_items"
    )
    units_produced_per_period = common_models.PrecisionField(
        help_text=_("Quantity Produced, eg, litres of milk per milking day")
    )
    production_unit_of_measure = models.ForeignKey(
        UnitOfMeasure, on_delete=models.PROTECT, help_text=_("Production Unit of Measure, eg, litres")
    )
    duration = common_models.PrecisionField(help_text=_("Duration"))
    price = common_models.PrecisionField(help_text=_("Price"))
    currency = common_models.PrecisionField(help_text=_("Price Currency"))
    quantity_sold = common_models.PrecisionField(help_text=_("Quantity Sold/Exchanged"))
    quantity_consumed = common_models.PrecisionField(help_text=_("Quantity Consumed"))
    quantity_other_uses = common_models.PrecisionField(help_text=_("Quantity Other Uses"))
    kcals_per_unit = common_models.PrecisionField(help_text=_("Kcals per Unit"))
    total_quantity_produced = common_models.PrecisionField(help_text=_("Total Quantity Produced"))
    income = common_models.PrecisionField(help_text=_("Income"))
    income_usd = common_models.PrecisionField(help_text=_("Income (USD)"))
    consumed_kcals = common_models.PrecisionField(help_text=_("Kilocalories Consumed"))
    # @TODO: if daily calory level varies by LZB then save consumed_kcal_percent here too
    expandability_kcals = common_models.PrecisionField(help_text=_("Expandability in Kilocalories"))

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.calculate_fields()
        return super().save(force_insert, force_update, using, update_fields)

    def calculate_fields(self):
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

    def calculate_expandibility_kcals(self):
        # @TODO: This is a guess, the BSSes are much more complex than this (I hope the complexity is all validation).
        return (
            self.calculate_total_quantity_produced()
            * (self.quantity_sold + self.quantity_other_uses)
            * self.kcals_per_unit
        )


class MilkProduction(models.Model):
    """
    Production of milk by households in a Wealth Group for their own consumption, for sale and for other uses.

    Stored on the BSS Data sheet in the Livestock Production section, typically starting around Row 60.
    """

    SKIM = "skim"
    WHOLE = "whole"

    MILK_TYPE_CHOICES = (
        (SKIM, _("skim")),
        (WHOLE, _("whole")),
    )
    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.PROTECT, verbose_name=_("Wealth Group"))
    season = models.ForeignKey(Item, on_delete=models.PROTECT, verbose_name=_("Season"))
    # @TODO do we need both input and output item, we can't produce goat milk from cows.
    input_item = models.ForeignKey(
        Item, on_delete=models.PROTECT, verbose_name=_("Type of Animal"), related_name="milked_animals"
    )
    # Not required for MilkProduction, unit of measure is always `ea`
    # input_unit_of_measure = models.ForeignKey(
    #    UnitOfMeasure, on_delete=models.PROTECT, verbose_name=_("Input Unit of Measure")
    # )
    input_quantity = models.PositiveSmallIntegerField(verbose_name=_("Number of milking animals"))
    item = models.ForeignKey(
        Item, on_delete=models.PROTECT, verbose_name=_("Type of Milk"), related_name="milk_production"
    )
    # Not required because it is always `l`
    # unit_of_measure = models.ForeignKey(
    #    UnitOfMeasure, on_delete=models.PROTECT, verbose_name=_("Unit of Measure")
    # )
    laction_days = models.PositiveSmallIntegerField(verbose_name=_("Average number or days of laction"))
    daily_production = models.PositiveSmallIntegerField(verbose_name=_("Average daily milk production per animal"))
    # Can be calcuated as lactation days * daily_production
    # Exists logically but not a cell in the BSS
    # item_yield = models.PositiveSmallIntegerField(verbose_name=_("Average seasonal milk production per animal"))
    quantity_produced = models.PositiveSmallIntegerField(verbose_name=_("Quantity Produced"))
    quantity_sold = models.PositiveSmallIntegerField(verbose_name=_("Quantity Sold/Exchanged"))
    price = models.FloatField(verbose_name=_("Price"), help_text=_("Price per unit"))
    # @TODO should we store this at the level of the BSS rather than in each production model?
    currency = models.ForeignKey(Currency, verbose_name=_("currency"), db_column="iso4217a3", on_delete=models.PROTECT)
    # Can be calculated / validated as `quantity_sold * price`
    income = common_models.PrecisionField(help_text=_("Income"))
    quantity_other_uses = models.PositiveSmallIntegerField(verbose_name=_("Quantity Other Uses"))
    # Can be calculated / validated as `quantity_produced - quantity_sold - quantity_other_uses`
    quantity_consumed = models.PositiveSmallIntegerField(verbose_name=_("Quantity Consumed"))

    # @TODO is this required for scenario development? If we need it, then it seems to be specific to this
    # model and not required for other Production model subclasses.
    type_of_milk_sold_or_other_users = models.CharField(
        choices=MILK_TYPE_CHOICES, verbose_name=_("Skim or whole milk sold or used")
    )

    # Calculated field, or method
    # `quantity_consumed` * `kcals_per_unit`
    total_kcals_consumed = models.PositiveSmallIntegerField(verbose_name=_("Total kcals consumed"))
    # Calculated field, or method
    # E.g. MWMSK Data AN177: `=IF(AN176="","",AN175*AN176*1450/2100/365/AN$40)`
    # `input_quantity` * `item_yield` * `kcals_per_unit` / `DAILY_KCAL_REQUIRED` / `DAYS_PER_YEAR` / `self.wealth_group.average_household_size`  # NOQA: E501
    percentage_kcals = models.PositiveSmallIntegerField(verbose_name=_("Percentage of required kcals"))

    class Meta:
        verbose_name = _("Milk Production")
        verbose_name_plural = _("Milk Production")


class ButterProduction(models.Model):
    """
    Production of ghee/butter by households in a Wealth Group for their own consumption, for sale and for other uses.

    Stored on the BSS Data sheet in the Livestock Production section, typically starting around Row 60.
    """

    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.PROTECT, verbose_name=_("Wealth Group"))
    season = models.ForeignKey(Item, on_delete=models.PROTECT, verbose_name=_("Season"))
    # @TODO do we need both input and output item, we can't produce cow butter from goat milk.
    input_item = models.ForeignKey(
        Item, on_delete=models.PROTECT, verbose_name=_("Type of Milk"), related_name="butter_production_input"
    )
    # Not required for ButterProduction, unit of measure is always `l`
    # input_unit_of_measure = models.ForeignKey(
    #    UnitOfMeasure, on_delete=models.PROTECT, verbose_name=_("Input Unit of Measure")
    # )
    input_quantity = models.PositiveSmallIntegerField(verbose_name=_("Quantity of milk (l)"))
    item = models.ForeignKey(
        Item, on_delete=models.PROTECT, verbose_name=_("Type of Ghee/Butter"), related_name="butter_production"
    )
    # Not required because it is always `l`
    # unit_of_measure = models.ForeignKey(
    #    UnitOfMeasure, on_delete=models.PROTECT, verbose_name=_("Unit of Measure")
    # )

    item_yield = models.PositiveSmallIntegerField(verbose_name=_("butter (kg) per milk (l)"))
    quantity_produced = models.PositiveSmallIntegerField(verbose_name=_("Quantity Produced"))
    quantity_sold = models.PositiveSmallIntegerField(verbose_name=_("Quantity Sold/Exchanged"))
    price = models.FloatField(verbose_name=_("Price"), help_text=_("Price per unit"))
    currency = models.ForeignKey(Currency, verbose_name=_("currency"), db_column="iso4217a3", on_delete=models.PROTECT)
    # Can be calculated / validated as `quantity_sold * price`
    income = common_models.PrecisionField(help_text=_("Income"))
    quantity_other_uses = models.PositiveSmallIntegerField(verbose_name=_("Quantity Other Uses"))
    # Can be calculated / validated as `quantity_produced - quantity_sold - quantity_other_uses`
    quantity_consumed = models.PositiveSmallIntegerField(verbose_name=_("Quantity Consumed"))

    # @TODO see https://fewsnet.atlassian.net/browse/HEA-65
    # Note that the formulae for butter don't follow the model of `input_quantity` * `item_yield` * `kcals_per_unit` / `DAILY_KCAL_REQUIRED` / `DAYS_PER_YEAR` / `self.wealth_group.average_household_size`  # NOQA: E501
    # The calorie available approach gives a different result to the (butter produced - butter sold/exchanged - butter other uses) * kcal per kg. # NOQA: E501
    # This might not matter if we are just storing the fields from the BSS and not calculating them
    # Calculated field, or method
    # `input_quantity` * `item_yield` * `kcals_per_unit`
    total_kcals_consumed = models.PositiveSmallIntegerField(verbose_name=_("Total kcals consumed"))
    # Calculated field, or method
    # E.g. MWMSK Data AI110: `=IF(AI105="","",(SUM(AI90)*640-SUM(AI91,AI95)*(640-300*(AI94=0))-SUM(AI106,AI107)*7865)/2100/365/AI$40)`  # NOQA: E501
    # total_milk_production * 640 - (milk_sold_or_exchanged + milk_other_uses) * (640 - (300 if sold_other_use == "skim" else 0)) - (ghee_sold_or_exchanged + ghee_other_uses)*7865  # NOQA: E501
    percentage_kcals = models.PositiveSmallIntegerField(verbose_name=_("Percentage of required kcals"))

    class Meta:
        verbose_name = _("Butter Production")
        verbose_name_plural = _("Butter Production")


class MeatProduction(models.Model):
    """
    Production of meat by households in a Wealth Group for their own consumption.

    Stored on the BSS Data sheet in the Livestock Production section, typically starting around Row 60.
    """

    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.PROTECT, verbose_name=_("Wealth Group"))
    season = models.ForeignKey(Item, on_delete=models.PROTECT, verbose_name=_("Season"))
    # @TODO do we need both input and output item, we can't produce chicken meat from slaughtering cows.
    input_item = models.ForeignKey(
        Item, on_delete=models.PROTECT, verbose_name=_("Type of Animal"), related_name="animals_for_meat"
    )
    # Not required for MeatProduction, unit of measure is always `ea`
    # input_unit_of_measure = models.ForeignKey(
    #    UnitOfMeasure, on_delete=models.PROTECT, verbose_name=_("Input Unit of Measure")
    # )
    input_quantity = models.PositiveSmallIntegerField(verbose_name=_("Number of animals slaughtered"))
    item = models.ForeignKey(
        Item, on_delete=models.PROTECT, verbose_name=_("Type of Meat"), related_name="meat_production"
    )
    # Not required because it is always `kg`
    # unit_of_measure = models.ForeignKey(
    #    UnitOfMeasure, on_delete=models.PROTECT, verbose_name=_("Unit of Measure")
    # )
    item_yield = common_models.PrecisionField(verbose_name=_("Carcass weight per animal"))
    quantity_produced = models.PositiveSmallIntegerField(verbose_name=_("Quantity Produced"))
    # Do we have a BSS that shows meat sold/exchanged/other uses rather than live animal transfers
    quantity_sold = models.PositiveSmallIntegerField(verbose_name=_("Quantity Sold/Exchanged"))
    quantity_other_uses = models.PositiveSmallIntegerField(verbose_name=_("Quantity Other Uses"))
    # Can be calculated / validated as `quantity_produced - quantity_sold - quantity_other_uses`
    quantity_consumed = models.PositiveSmallIntegerField(verbose_name=_("Quantity Consumed"))

    # Calculated field, or method
    # `input_quantity` * `item_yield` * `kcals_per_unit`
    total_kcals_consumed = models.PositiveSmallIntegerField(verbose_name=_("Total kcals consumed"))
    # Calculated field, or method
    # E.g. MWMSK Data AN177: `=IF(AN176="","",AN175*AN176*1450/2100/365/AN$40)`
    # `input_quantity` * `item_yield` * `kcals_per_unit` / `DAILY_KCAL_REQUIRED` / `DAYS_PER_YEAR` / `self.wealth_group.average_household_size`  # NOQA: E501
    percentage_kcals = models.PositiveSmallIntegerField(verbose_name=_("Percentage of required kcals"))

    class Meta:
        verbose_name = _("Meat Production")
        verbose_name_plural = _("Meat Production")


class CropProduction(models.Model):
    """
    Production of crops by households in a Wealth Group for their own consumption, for sale and for other uses.

    Stored on the BSS Data sheet in the Crop Production section, typically starting around Row 221.
    """

    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.PROTECT, verbose_name=_("Wealth Group"))
    season = models.ForeignKey(Item, on_delete=models.PROTECT, verbose_name=_("Season"))
    # @TODO See https://fewsnet.atlassian.net/browse/HEA-67
    # Are there other types than rainfed and irrigated?
    # Is it important as an attribute even if there is only one crop.
    production_system = models.CharField(
        max_length=60,
        default="rainfed",
        verbose_name=_("Production System"),
        help_text=_("Production system used to grow the crop, such as rainfed or irrigated"),
    )
    # Not required for CropProduction - logically it is Land in ha, but this isn't tracked AFAIK
    # input_item = models.ForeignKey(
    #    Item, on_delete=models.PROTECT, verbose_name=_("Type of Milk"), related_name="butter_production_milk"
    # )
    # input_unit_of_measure = models.ForeignKey(
    #    UnitOfMeasure, on_delete=models.PROTECT, verbose_name=_("Input Unit of Measure")
    # )
    # input_quantity = models.PositiveSmallIntegerField(verbose_name=_("Quantity of milk (l)"))
    item = models.ForeignKey(
        Item, on_delete=models.PROTECT, verbose_name=_("Type of Crop"), related_name="crop_production"
    )
    # Not required for CropProduction, unit of measure is always `kg`
    # unit_of_measure = models.ForeignKey(
    #    UnitOfMeasure, on_delete=models.PROTECT, verbose_name=_("Unit of Measure")
    # )
    # item_yield = models.PositiveSmallIntegerField(verbose_name=_("crop (kg) per land area (ha)"))
    quantity_produced = models.PositiveSmallIntegerField(verbose_name=_("Quantity Produced"))
    quantity_sold = models.PositiveSmallIntegerField(verbose_name=_("Quantity Sold/Exchanged"))
    price = models.FloatField(verbose_name=_("Price"), help_text=_("Price per unit"))
    currency = models.ForeignKey(Currency, verbose_name=_("currency"), db_column="iso4217a3", on_delete=models.PROTECT)
    # Can be calculated / validated as `quantity_sold * price`
    income = common_models.PrecisionField(help_text=_("Income"))
    quantity_other_uses = models.PositiveSmallIntegerField(verbose_name=_("Quantity Other Uses"))
    # Can be calculated / validated as `quantity_produced - quantity_sold - quantity_other_uses`
    quantity_consumed = models.PositiveSmallIntegerField(verbose_name=_("Quantity Consumed"))

    # Calculated field, or method
    # `quantity_consumed` * `kcals_per_unit`
    total_kcals_consumed = models.PositiveSmallIntegerField(verbose_name=_("Total kcals consumed"))
    # Calculated field, or method
    percentage_kcals = models.PositiveSmallIntegerField(verbose_name=_("Percentage of required kcals"))

    class Meta:
        verbose_name = _("Crop Production")
        verbose_name_plural = _("Crop Production")


class FoodPurchase(models.Model):
    """
    Purchase of food items that contribute to nutrition by households in a Wealth Group.

    Stored on the BSS Data sheet in the Food Purchase section, typically starting around Row 421.
    """

    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.PROTECT, verbose_name=_("Wealth Group"))
    # The BSS doesn't capture which season food purchases occur in, so we can't really store it, even though
    # we know that 12 months means year round and 3-4 months probably means in the lean season.
    # season = models.ForeignKey(Item, on_delete=models.PROTECT, verbose_name=_("Season"))
    # Not required for FoodPurchase - in a transfer model approach it would be Money
    # input_item = models.ForeignKey(
    #    Item, on_delete=models.PROTECT, verbose_name=_("Type of Milk"), related_name="butter_production_milk"
    # )
    # input_unit_of_measure = models.ForeignKey(
    #    UnitOfMeasure, on_delete=models.PROTECT, verbose_name=_("Input Unit of Measure")
    # )
    # input_quantity = models.PositiveSmallIntegerField(verbose_name=_("Quantity of milk (l)"))
    item = models.ForeignKey(
        Item, on_delete=models.PROTECT, verbose_name=_("Type of Food"), related_name="food_purchases"
    )
    unit_of_measure = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, verbose_name=_("Unit of Measure"))
    # Not required for FoodPurchase, although could be repurposed for the unit_multiple
    # item_yield = models.PositiveSmallIntegerField(verbose_name=_("crop (kg) per land area (ha)"))
    unit_multiple = models.PositiveSmallIntegerField(
        verbose_name=_("Unit Multiple"), help_text=_("Multiple of the unit of measure in a single purchase")
    )
    purchases_per_month = models.PositiveSmallIntegerField(verbose_name=_("Purchases per month"))
    months_per_year = models.PositiveSmallIntegerField(
        verbose_name=_("Months per year"), help_text=_("Number of months in a year that the product is purchased")
    )
    # Not required for FoodPurchase - we don't track traders
    # quantity_produced = models.PositiveSmallIntegerField(verbose_name=_("Quantity Purchased"))
    # Not required for FoodPurchase - we don't track traders
    # quantity_sold = models.PositiveSmallIntegerField(verbose_name=_("Quantity Sold/Exchanged"))
    # Can be calculated / validated as `unit_multiple * purchases_per_month * months_per_year`
    # @TODO should we share a field with quantity_sold and use negatives for one or other.
    # Alternatively, we could reuse quantity_consumed, because we assume all of the purchase is being consumed
    # Users will expect to see positive numbers everywhere.
    quantity_purchased = models.PositiveSmallIntegerField(verbose_name=_("Quantity Purchased"))
    price = models.FloatField(verbose_name=_("Price"), help_text=_("Price per unit"))
    currency = models.ForeignKey(Currency, verbose_name=_("currency"), db_column="iso4217a3", on_delete=models.PROTECT)
    # Not required for Food Purchase
    # income = common_models.PrecisionField(help_text=_("Income"))
    # @TODO should we share a field with quantity_sold and use negatives for one or other.
    # Users will expect to see positive numbers everywhere.
    # Can be calculated / validated as `quantity_purchased * price`
    expenditure = common_models.PrecisionField(help_text=_("Income"))
    # Not required for Food Purchase
    # quantity_other_uses = models.PositiveSmallIntegerField(verbose_name=_("Quantity Other Uses"))
    # Not required for Food Purchase
    # quantity_consumed = models.PositiveSmallIntegerField(verbose_name=_("Quantity Consumed"))

    # Calculated field, or method
    # `quantity_consumed` * `kcals_per_unit`
    total_kcals_consumed = models.PositiveSmallIntegerField(verbose_name=_("Total kcals consumed"))
    # Calculated field, or method
    percentage_kcals = models.PositiveSmallIntegerField(verbose_name=_("Percentage of required kcals"))

    class Meta:
        verbose_name = _("Food Purchase")
        verbose_name_plural = _("Food Purchases")


class PaymentInKind(models.Model):
    """
    Food items that contribute to nutrition by households in a Wealth Group received in exchange for labor.

    Stored on the BSS Data sheet in the Payment In Kind section, typically starting around Row 514.
    """

    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.PROTECT, verbose_name=_("Wealth Group"))
    # The BSS doesn't capture which season payment in kind occurs in, so we can't really store it.
    # season = models.ForeignKey(Item, on_delete=models.PROTECT, verbose_name=_("Season"))
    input_item = models.ForeignKey(
        Item, on_delete=models.PROTECT, verbose_name=_("Type of Labor"), related_name="in_kind_labor"
    )
    # input_unit_of_measure = models.ForeignKey(
    #    UnitOfMeasure, on_delete=models.PROTECT, verbose_name=_("Input Unit of Measure")
    # )
    # input_quantity = models.PositiveSmallIntegerField(verbose_name=_("Quantity of milk (l)"))
    # The BSS doesn't show this explicitly but it is implicitly there because we need to look up the kcal/kg for the
    # item received
    item = models.ForeignKey(
        Item, on_delete=models.PROTECT, verbose_name=_("Type of Food"), related_name="in_kind_payment"
    )
    unit_of_measure = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, verbose_name=_("Unit of Measure"))
    # Not required for PaymentInKind, although could be repurposed for the unit_multiple
    # item_yield = models.PositiveSmallIntegerField(verbose_name=_("crop (kg) per land area (ha)"))
    people_per_hh = models.PositiveSmallIntegerField(
        verbose_name=_("People per household"), help_text=_("Number of household members who perform the labor")
    )
    labor_per_month = models.PositiveSmallIntegerField(verbose_name=_("Labor per month"))
    months_per_year = models.PositiveSmallIntegerField(
        verbose_name=_("Months per year"), help_text=_("Number of months in a year that the labor is performed")
    )
    # Not required for PaymentInKind - we don't track traders
    # quantity_produced = models.PositiveSmallIntegerField(verbose_name=_("Quantity Purchased"))
    # Not required for PaymentInKind - we don't track traders
    # quantity_sold = models.PositiveSmallIntegerField(verbose_name=_("Quantity Sold/Exchanged"))
    # Can be calculated / validated as `unit_multiple * purchases_per_month * months_per_year`
    # @TODO should we share a field with quantity_sold and use negatives for one or other.
    # Alternatively, we could reuse quantity_consumed, because we assume all of the payment in kind is being consumed
    # Users will expect to see positive numbers everywhere.
    quantity_received = models.PositiveSmallIntegerField(verbose_name=_("Quantity Received"))
    # Not required for PaymentInKind
    # price = models.FloatField(verbose_name=_("Price"), help_text=_("Price per unit"))
    # Not required for PaymentInKind
    # currency = models.ForeignKey(Currency, verbose_name=_("currency"), db_column="iso4217a3", on_delete=models.PROTECT)  # NOQA: E501
    # Not required for PaymentInKind
    # income = common_models.PrecisionField(help_text=_("Income"))
    # Not required for PaymentInKind
    # quantity_other_uses = models.PositiveSmallIntegerField(verbose_name=_("Quantity Other Uses"))
    # Not required for PaymentInKind
    # quantity_consumed = models.PositiveSmallIntegerField(verbose_name=_("Quantity Consumed"))

    # Calculated field, or method
    # `quantity_consumed` * `kcals_per_unit`
    total_kcals_consumed = models.PositiveSmallIntegerField(verbose_name=_("Total kcals consumed"))
    # Calculated field, or method
    percentage_kcals = models.PositiveSmallIntegerField(verbose_name=_("Percentage of required kcals"))

    class Meta:
        verbose_name = _("Payment in Kind")
        verbose_name_plural = _("Payments in Kind")


class ReliefGiftsOther(models.Model):
    """
    Food items that contribute to nutrition received by households in a Wealth Group as relief, gifts, etc.
    and which are not bought or exchanged.

    Stored on the BSS Data sheet in the Relief, Gifts and Other section, typically starting around Row 533.
    """

    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.PROTECT, verbose_name=_("Wealth Group"))
    # The BSS doesn't capture which season payment in kind occurs in, so we can't really store it.
    # season = models.ForeignKey(Item, on_delete=models.PROTECT, verbose_name=_("Season"))
    # Not required for ReliefGiftsOther
    # input_item = models.ForeignKey(
    #    Item, on_delete=models.PROTECT, verbose_name=_("Type of Labor"), related_name="in_kind_labor"
    # )
    # input_unit_of_measure = models.ForeignKey(
    #    UnitOfMeasure, on_delete=models.PROTECT, verbose_name=_("Input Unit of Measure")
    # )
    # input_quantity = models.PositiveSmallIntegerField(verbose_name=_("Quantity of milk (l)"))
    item = models.ForeignKey(Item, on_delete=models.PROTECT, verbose_name=_("Type of Food"), related_name="relief")
    unit_of_measure = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, verbose_name=_("Unit of Measure"))
    # Not required for ReliefGiftsOther, although could be repurposed for the unit_multiple
    # item_yield = models.PositiveSmallIntegerField(verbose_name=_("crop (kg) per land area (ha)"))
    unit_multiple = models.PositiveSmallIntegerField(
        verbose_name=_("Unit Multiple"), help_text=_("Multiple of the unit of measure in a single gift")
    )
    gifts_per_year = models.PositiveSmallIntegerField(
        verbose_name=_("Gifts per year"), help_text=_("Number of time in a year that the product is received")
    )
    # Not required for ReliefGiftsOther - we don't track traders
    # quantity_produced = models.PositiveSmallIntegerField(verbose_name=_("Quantity Purchased"))
    # Not required for ReliefGiftsOther - we don't track traders
    # quantity_sold = models.PositiveSmallIntegerField(verbose_name=_("Quantity Sold/Exchanged"))
    # Can be calculated / validated as `unit_multiple * purchases_per_month * months_per_year`
    # @TODO should we share a field with quantity_sold and use negatives for one or other.
    # Alternatively, we could reuse quantity_consumed, because we assume all of the gift is being consumed
    # Users will expect to see positive numbers everywhere.
    quantity_received = models.PositiveSmallIntegerField(verbose_name=_("Quantity Received"))
    # Not required for ReliefGiftsOther
    # price = models.FloatField(verbose_name=_("Price"), help_text=_("Price per unit"))
    # Not required for ReliefGiftsOther
    # currency = models.ForeignKey(Currency, verbose_name=_("currency"), db_column="iso4217a3", on_delete=models.PROTECT)  # NOQA: E501
    # Not required for ReliefGiftsOther
    # income = common_models.PrecisionField(help_text=_("Income"))
    # Not required for ReliefGiftsOther
    # quantity_other_uses = models.PositiveSmallIntegerField(verbose_name=_("Quantity Other Uses"))
    # Not required for ReliefGiftsOther
    # quantity_consumed = models.PositiveSmallIntegerField(verbose_name=_("Quantity Consumed"))

    # Calculated field, or method
    # `quantity_consumed` * `kcals_per_unit`
    total_kcals_consumed = models.PositiveSmallIntegerField(verbose_name=_("Total kcals consumed"))
    # Calculated field, or method
    percentage_kcals = models.PositiveSmallIntegerField(verbose_name=_("Percentage of required kcals"))

    class Meta:
        verbose_name = _("Relief, Gifts and Other Food")
        verbose_name_plural = _("Relief, Gifts and Other Food")


class Fishing(models.Model):
    """
    Fishing by households in a Wealth Group for their own consumption, for sale and for other uses.

    Stored on the BSS Data3 sheet in the Fishing section, typically starting around Row 48 and summarized in the
    Data sheet in the Wild Foods section, typically starting around Row 550.
    """

    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.PROTECT, verbose_name=_("Wealth Group"))
    # The BSS doesn't capture which season fishing occurs in, so we can't really store it.
    # season = models.ForeignKey(Item, on_delete=models.PROTECT, verbose_name=_("Season"))
    # Not required for Fishing
    # input_item = models.ForeignKey(
    #    Item, on_delete=models.PROTECT, verbose_name=_("Type of Labor"), related_name="in_kind_labor"
    # )
    # input_unit_of_measure = models.ForeignKey(
    #    UnitOfMeasure, on_delete=models.PROTECT, verbose_name=_("Input Unit of Measure")
    # )
    # input_quantity = models.PositiveSmallIntegerField(verbose_name=_("Quantity of milk (l)"))
    item = models.ForeignKey(Item, on_delete=models.PROTECT, verbose_name=_("Type of Fish"), related_name="fishing")
    # Not required for Fishing, unit of measure is always `kg`
    # unit_of_measure = models.ForeignKey(
    #    UnitOfMeasure, on_delete=models.PROTECT, verbose_name=_("Unit of Measure")
    # )
    # Not required for Fishing
    # item_yield = models.PositiveSmallIntegerField(verbose_name=_("crop (kg) per land area (ha)"))
    quantity_produced = models.PositiveSmallIntegerField(verbose_name=_("Quantity Caught"))
    quantity_sold = models.PositiveSmallIntegerField(verbose_name=_("Quantity Sold/Exchanged"))
    price = models.FloatField(verbose_name=_("Price"), help_text=_("Price per unit"))
    currency = models.ForeignKey(Currency, verbose_name=_("currency"), db_column="iso4217a3", on_delete=models.PROTECT)
    # Can be calculated / validated as `quantity_sold * price`
    income = common_models.PrecisionField(help_text=_("Income"))
    quantity_other_uses = models.PositiveSmallIntegerField(verbose_name=_("Quantity Other Uses"))
    # Can be calculated / validated as `quantity_gathered - quantity_sold - quantity_other_uses`
    quantity_consumed = models.PositiveSmallIntegerField(verbose_name=_("Quantity Consumed"))

    # Calculated field, or method
    # `quantity_consumed` * `kcals_per_unit`
    total_kcals_consumed = models.PositiveSmallIntegerField(verbose_name=_("Total kcals consumed"))
    # Calculated field, or method
    percentage_kcals = models.PositiveSmallIntegerField(verbose_name=_("Percentage of required kcals"))

    class Meta:
        verbose_name = _("Fishing")
        verbose_name_plural = _("Fishing")


class WildFood(models.Model):
    """
    Gathering of wild food by households in a Wealth Group for their own consumption, for sale and for other uses.

    Stored on the BSS Data3 sheet in the Wild Foods section, typically starting around Row 9 and summarized in the
    Data sheet in the Wild Foods section, typically starting around Row 560.
    """

    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.PROTECT, verbose_name=_("Wealth Group"))
    # The BSS doesn't capture which season wild foods are gathered in, so we can't really store it.
    # season = models.ForeignKey(Item, on_delete=models.PROTECT, verbose_name=_("Season"))
    # Not required for WildFood
    # input_item = models.ForeignKey(
    #    Item, on_delete=models.PROTECT, verbose_name=_("Type of Labor"), related_name="in_kind_labor"
    # )
    # input_unit_of_measure = models.ForeignKey(
    #    UnitOfMeasure, on_delete=models.PROTECT, verbose_name=_("Input Unit of Measure")
    # )
    # input_quantity = models.PositiveSmallIntegerField(verbose_name=_("Quantity of milk (l)"))
    item = models.ForeignKey(
        Item, on_delete=models.PROTECT, verbose_name=_("Type of Wild Food"), related_name="wild_food"
    )
    # Not required for WildFood, unit of measure is always `kg`
    # unit_of_measure = models.ForeignKey(
    #    UnitOfMeasure, on_delete=models.PROTECT, verbose_name=_("Unit of Measure")
    # )
    # Not required for WildFood
    # item_yield = models.PositiveSmallIntegerField(verbose_name=_("crop (kg) per land area (ha)"))
    quantity_produced = models.PositiveSmallIntegerField(verbose_name=_("Quantity Gathered"))
    quantity_sold = models.PositiveSmallIntegerField(verbose_name=_("Quantity Sold/Exchanged"))
    price = models.FloatField(verbose_name=_("Price"), help_text=_("Price per unit"))
    currency = models.ForeignKey(Currency, verbose_name=_("currency"), db_column="iso4217a3", on_delete=models.PROTECT)
    # Can be calculated / validated as `quantity_sold * price`
    income = common_models.PrecisionField(help_text=_("Income"))
    quantity_other_uses = models.PositiveSmallIntegerField(verbose_name=_("Quantity Other Uses"))
    # Can be calculated / validated as `quantity_gathered - quantity_sold - quantity_other_uses`
    quantity_consumed = models.PositiveSmallIntegerField(verbose_name=_("Quantity Consumed"))

    # Calculated field, or method
    # `quantity_consumed` * `kcals_per_unit`
    total_kcals_consumed = models.PositiveSmallIntegerField(verbose_name=_("Total kcals consumed"))
    # Calculated field, or method
    percentage_kcals = models.PositiveSmallIntegerField(verbose_name=_("Percentage of required kcals"))

    class Meta:
        verbose_name = _("Wild Food")
        verbose_name_plural = _("Wild Food")


class OtherCashIncome(models.Model):
    """
    Income received by households in a Wealth Group as payment for labor or from self-employment, remittances, etc.

    Stored on the BSS Data2 and summarized in the Data sheet in the Other Cash Income section, typically starting
    around Row 580.
    """

    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.PROTECT, verbose_name=_("Wealth Group"))
    # The BSS doesn't capture which season income occurs in, so we can't really store it.
    # season = models.ForeignKey(Item, on_delete=models.PROTECT, verbose_name=_("Season"))
    # @TODO Cash Income has an output item of cash and and input item of the type of labor. If we only have one item
    # for a Production model subclass, I think it would store the type of labor, so we wouldn't need the input_item
    # input_item = models.ForeignKey(
    #    Item, on_delete=models.PROTECT, verbose_name=_("Type of Labor"), related_name="in_kind_labor"
    # )
    # input_unit_of_measure = models.ForeignKey(
    #    UnitOfMeasure, on_delete=models.PROTECT, verbose_name=_("Input Unit of Measure")
    # )
    # input_quantity = models.PositiveSmallIntegerField(verbose_name=_("Quantity of milk (l)"))
    # The BSS doesn't show this explicitly but it is implicitly there because we need to look up the kcal/kg for the
    # item received
    item = models.ForeignKey(
        Item, on_delete=models.PROTECT, verbose_name=_("Type of Labor"), related_name="paid_labor"
    )
    # Not required for OtherCashIncome
    # unit_of_measure = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT, verbose_name=_("Unit of Measure"))
    # Not required for OtherCashIncome, although could be repurposed for the unit_multiple
    # item_yield = models.PositiveSmallIntegerField(verbose_name=_("crop (kg) per land area (ha)"))
    # Some other income (e.g. Remittances) just has a number of times per year and is not calculated from
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
        blank=True,
        null=True,
        verbose_name=_("Times per year"),
        help_text=_("Number of time in a year that the income is received"),
    )
    # Not required for OtherCashIncome
    # quantity_produced = models.PositiveSmallIntegerField(verbose_name=_("Quantity Purchased"))
    # Not required for OtherCashIncome
    # quantity_sold = models.PositiveSmallIntegerField(verbose_name=_("Quantity Sold/Exchanged"))
    # Not required for OtherCashIncome
    # quantity_received = models.PositiveSmallIntegerField(verbose_name=_("Quantity Received"))
    price = models.FloatField(verbose_name=_("Price"), help_text=_("Price per unit"))
    currency = models.ForeignKey(
        Currency, verbose_name=_("currency"), db_column="iso4217a3", on_delete=models.PROTECT
    )  # NOQA: E501
    income = common_models.PrecisionField(help_text=_("Income"))
    # Not required for OtherCashIncome
    # quantity_other_uses = models.PositiveSmallIntegerField(verbose_name=_("Quantity Other Uses"))
    # Not required for OtherCashIncome
    # quantity_consumed = models.PositiveSmallIntegerField(verbose_name=_("Quantity Consumed"))

    # Not required for OtherCashIncome
    # Calculated field, or method
    # `quantity_consumed` * `kcals_per_unit`
    # total_kcals_consumed = models.PositiveSmallIntegerField(verbose_name=_("Total kcals consumed"))
    # Not required for OtherCashIncome
    # Calculated field, or method
    # percentage_kcals = models.PositiveSmallIntegerField(verbose_name=_("Percentage of required kcals"))

    class Meta:
        verbose_name = _("Other Cash Income")
        verbose_name_plural = _("Other Cash Income")


class SeasonalActivity(Dimension):
    """
    Seasonal activities for the various food source/ income activities

    Activity Category can be Crops, Livestock, Gardening, Employment, Fishing
    And the actual activity can be e.g. for Employment category:
        On farm local labor
        Brick making
        Labor migration
    """

    activity_category = models.ForeignKey(
        SeasonalActivityCategory,
        on_delete=models.RESTRICT,
        verbose_name=_("Activity Category"),
    )
    is_weather_related = models.BooleanField(
        verbose_name=_("Weather related"),
        help_text=_("If the activity is a representation of the weather eg. rainy, dry"),
    )

    class Meta:
        verbose_name = _("Seasonal Activity")
        verbose_name_plural = _("Seasonal Activities")


class Season(models.Model):

    """
    A division of the year, marked by changes in weather, ecology, and associated livelihood zone
     activities for income generation. Season's vary by :`LivelihoodZone`
    """

    MONTHS = MONTHS.items()
    # Year Alignment
    START = "Start"
    END = "End"
    ALIGNMENT_CHOICES = ((START, _("Start")), (END, _("End")))

    livelihood_zone = models.ForeignKey(LivelihoodZone, verbose_name=_("livelihood zone"), on_delete=models.RESTRICT)
    name = models.CharField(max_length=50, verbose_name=_("Name"))
    description = models.TextField(max_length=255, verbose_name=_("Description"))
    start_month = models.IntegerField(
        choices=list(MONTHS),
        verbose_name=_("Start Month"),
        help_text=_("The typical first month of the Season"),
    )
    end_month = models.IntegerField(
        choices=list(MONTHS),
        verbose_name=_("End Month"),
        help_text=_("The typical end month of the Season"),
    )
    alignment = models.CharField(
        max_length=5,
        choices=ALIGNMENT_CHOICES,
        default=END,
        verbose_name=_("Year alignment"),
    )
    order = models.IntegerField(
        verbose_name=_("Order"),
        help_text=_("The order of the Season with the Season Year"),
    )
    rain_fall_record = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Rainfall record"))

    class Meta:
        verbose_name = _("Season")
        verbose_name_plural = _("Seasons")


class SeasonalCalendar(models.Model):
    """
    A graphical presentation of the months in which food and cash crop production and key food and income acquisition
    strategies take place, also showing key seasonal periods such as the rains, periods of peak illness and the hunger
     season.

    Form 3's SEASONAL CALENDAR for a typical year is used for the interview and BSS's 'Seas Cal' captures the data
    """

    ACTIVITY_DONE_BY = (
        ("men", "Men"),
        ("women", "Women"),
        ("children", "Children"),
        ("all", "All"),
    )

    community = models.ForeignKey(Community, on_delete=models.RESTRICT, verbose_name=_("Community or Village"))
    activity = models.ForeignKey(SeasonalActivity, on_delete=models.RESTRICT, verbose_name=_("Seasonal Activity"))

    # Tracks when the activity occurs (the month when the activity typically occurs)
    # We can have a validator here, put the month no - e.g. 9, 10, 11
    activity_occurence = models.JSONField(verbose_name=_("Activity occurrence"))

    # or as an alternative keep the Season model similar to FDW
    # if so, I think we need another Model with FK for SeasonalCalender and Season ?
    # season = models.ForeignKey(Season, on_delete=RESTRICT, verbose_name=_("Season"))

    # Who typically does the activity, Male, Female, Children ... We can make this a choice field?
    who_does_the_activity = models.CharField(choices=ACTIVITY_DONE_BY, verbose_name=_("Activity done by"))

    class Meta:
        verbose_name = _("Seasonal Calendar")
        verbose_name_plural = _("Seasonal Calendars")


class CommunityCropProduction(models.Model):
    """
    The community crop production data for a crop producing community
    Form 3's CROP PRODUCTION is used for community-level interviews
    And the data goes to the BSS's 'Production' sheet
    """

    CROP_PURPOSE = (
        ("main_crop", "Main Food Crop"),
        ("cash_crop", "Cash Crop"),
    )
    community = models.ForeignKey(Community, on_delete=models.RESTRICT, verbose_name=_("Community or Village"))
    crop_type = models.ForeignKey(CropType, on_delete=models.RESTRICT, verbose_name=_("Crop Type"))
    crop_purpose = models.CharField(max_length=20, choices=CROP_PURPOSE, verbose_name=_("Crop purpose"))
    season = models.ForeignKey(Season, on_delete=models.RESTRICT, verbose_name=_("Season"))
    production_with_inputs = common_models.PrecisionField(
        verbose_name=_("Production with input"),
        help_text=_("Yield in reference period with input (seed and fertilizer)"),
    )
    production_with_out_inputs = common_models.PrecisionField(
        verbose_name=_("Production with input"),
        help_text=_("Yield in reference period without input (seed and fertilizer)"),
    )
    seed_requirement = common_models.PrecisionField(verbose_name=_("Seed requirement"))
    unit_of_land = models.ForeignKey(UnitOfMeasure, on_delete=models.RESTRICT, verbose_name=_("Unit of land"))

    class Meta:
        verbose_name = _("Community Crop Production")
        verbose_name_plural = _("Community Crop Productions")


# @TODO Are these fields from Form 3 required here on CommunityLivestock,
# or are they on WealthGroupLivestock as a result of the repition on Form 4
# These sheets are locked in the BSS. They are important reference data even
# if the WealthGroup-level values are used for calculations.
class CommunityLivestock(models.Model):
    """
    An animal typically raised by households in a Community, with revelant additional attributes.

    This data is typically captured in Form 3 and stored in the Production sheet in the BSS.
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
    Data is captured in 'prices' sheet of the BSS
    """

    MONTHS = MONTHS.items()
    community = models.ForeignKey(Community, on_delete=models.RESTRICT, verbose_name=_("Community or Village"))
    # We need the item to reference it but the item can be Crop, Livestock, Other expenditure items
    # e.g. tea, coffee, sugar ..# do we need to have
    # a) something similar to Classified Product or
    # b) a reference model -
    # MarketItem with category as Main food, Cash crops Livestock ..
    item = models.ForeignKey(
        Item, on_delete=models.RESTRICT, help_text=_("Crop, livestock or other category of items")
    )
    market = models.ForeignKey(Market, on_delete=models.RESTRICT)
    low_price = common_models.PrecisionField("Low price")
    low_price_month = models.SmallIntegerField(choices=list(MONTHS), verbose_name=_("Low Price Month"))
    high_price = common_models.PrecisionField("High price")
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
