"""
Models for managing HEA Baseline Surveys
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

import common.models as common_models
from metadata.models import (
    ExpenditureCategory,
    FoodSource,
    IncomeSource,
    Item,
    LivelihoodCategory,
    LivestockType,
    UnitOfMeasure,
    WealthCategory,
    WealthGroupAttributeType,
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


# @TODO https://fewsnet.atlassian.net/browse/HEA-54
# Do we subclass GeographicUnit, in which case we don't need to worry
# about the geography field, or the way to capture the Admin units above the
# Village. If we keep this a bare Model without subclassing GeographicUnit then
# we need to add `location = common_models.LocationField()` and `full_name`
# (to capture the village name combined with the admin unit name)
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
    # @TODO Check if this need to be char.- Check Somalia
    interview_number = models.PositiveSmallIntegerField(
        verbose_name=_("Interview Number"),
        help_text=_("The interview number from 1 - 12 assigned to the Community"),
    )
    interviewers = models.CharField(
        verbose_name=_("Interviewers"),
        help_text=_("The names of interviewers who interviewed the Community, in case any clarification is neeeded."),
    )
    # @TODO is this valuable for doing cross-LHZ analysis even though it is not
    # in the BSS. Could be calculated from WorldPop or LandScan.
    population_estimate = models.PositiveIntegerField(
        verbose_name=_("Population Estimate"),
    )

    class Meta:
        verbose_name = _("Community")
        verbose_name_plural = _("Communities")


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
        verbose_name=_("Age at Sale"), help_text=_("Age in months at which the animal is typically sold")
    )
    # @TODO At implementation we need to ensure consistency across records
    # that means we either need a EAV table or validation at data entry.
    additional_attributes = models.JSONField()

    class Meta:
        verbose_name = _("Wealth Group Attribute")
        verbose_name_plural = _("Wealth Group Attributes")


class WealthGroupLivestock(models.Model):
    class Meta:
        verbose_name = _("Wealth Group Livestock")
        verbose_name_plural = _("Wealth Group Livestock")


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


class WealthGroupAttribute(models.Model):
    """
    An attribute of a Wealth Group such as the number of school-age children.
    """

    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.CASCADE, verbose_name=_("Wealth Group"))
    attribute_type = models.ForeignKey(
        WealthGroupAttributeType, on_delete=models.RESTRICT, verbose_name=_("Attribute Type")
    )
    value = models.IntegerField(verbose_name=_("Value"))

    class Meta:
        verbose_name = _("Wealth Group Attribute")
        verbose_name_plural = _("Wealth Group Attributes")


# @TODO IncomeSource makes sense for the metadata model. But what about
# expenditure? ExpenditureSource doesn't make sense. ExpenditureCategory or
# ExpenditureType. What about IncomeCategory then. Or ExpenditureDestination
# @TODO Discuss making this an generic model across Income, Expenditure, Food
# and Asset
class WealthGroupIncome(models.Model):
    """
    The total income for a Wealth Group from a specific Income Source during
    the reference period.
    """

    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.CASCADE, verbose_name=_("Wealth Group"))
    income_source = models.ForeignKey(IncomeSource, on_delete=models.CASCADE, verbose_name=_("Income Source"))
    amount = models.DecimalField(max_digits=9, decimal_places=2, verbose_name=_("Amount"))  # in local currency

    class Meta:
        verbose_name = _("Wealth Group Income")
        verbose_name_plural = _("Wealth Group Incomes")


class WealthGroupExpenditure(models.Model):
    """
    The WealthGroupExpenditure model represents the income of a wealth group,
    linked to specific sources of income and the amount sourced from each.
    """

    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.CASCADE, verbose_name=_("Wealth Group"))
    expenditure_category = models.ForeignKey(
        ExpenditureCategory, on_delete=models.CASCADE, verbose_name=_("Expenditure Category")
    )
    amount = models.DecimalField(max_digits=9, decimal_places=2, verbose_name=_("Amount"))  # in local currency

    class Meta:
        verbose_name = _("Wealth Group Income")
        verbose_name_plural = _("Wealth Group Incomes")


class WealthGroupFood(models.Model):
    """
    The WealthGroupFood model represents the food access of a wealth group,
    linked to specific sources of food and the amount sourced from each.
    """

    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.CASCADE, verbose_name=_("Wealth Group"))
    food_source = models.ForeignKey(FoodSource, on_delete=models.CASCADE, verbose_name=_("Food Source"))
    amount = models.DecimalField(max_digits=9, decimal_places=2, verbose_name=_("Amount"))  # in local currency

    class Meta:
        verbose_name = _("Wealth Group Food")
        verbose_name_plural = _("Wealth Group Foods")


class WealthGroupAsset(models.Model):
    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.CASCADE, verbose_name=_("Wealth Group"))
    # These fields item, unit, qty, qty_usd and qty_kcal to be refactored into a
    # common parent mixin or ABC `ItemInstance` (?)
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    unit = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT)
    quantity = common_models.PrecisionField()
    quantity_usd = common_models.PrecisionField()
    quantity_kcals = common_models.PrecisionField()


# @TODO Details TBA
'''
class AssetItemCharacteristic(models.Model):
    """
    Characteristics could be stored in wide tables with lots of nulls,
    eg, `LivestockAsset`, or in JsonFields, eg, `Asset.characteristics`,
    or we could create lots of Items (sex would require 2 variants, sex
    and is_mature require 4 variants, and so on). I think separated
    characteristic tables will be easier to filter, aggregate, group and
    order by.
    """

    asset = models.ForeignKey(WealthGroupAsset, on_delete=models.PROTECT)
    # These fields property and value probably also a mixin or ABC
    property = models.ForeignKey(Dimension, on_delete=models.PROTECT)
    value = models.JSONField(help_text=_("A single property value, eg, a float, str or list, not a dict of props."))


class TransferItemCharacteristic(models.Model):
    transfer = models.ForeignKey("baseline.Transfer", on_delete=models.PROTECT)
    # These fields property and value probably also a mixin or ABC
    property = models.ForeignKey(Dimension, on_delete=models.PROTECT)
    value = models.JSONField(help_text=_("A single property value, eg, a float, str or list, not a dict of props."))


class HouseholdCharacteristic(models.Model):
    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.CASCADE, verbose_name=_("Wealth Group"))
    # These fields property and value probably also a mixin or ABC
    property = models.ForeignKey(Dimension, on_delete=models.PROTECT)
    value = models.JSONField(help_text=_("A single property value, eg, a float, str or list, not a dict of props."))
'''
