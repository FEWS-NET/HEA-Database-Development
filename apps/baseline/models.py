"""
Models for managing HEA Baseline Surveys
"""
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.dates import MONTHS
from django.utils.translation import gettext_lazy as _

import common.models as common_models
from metadata.models import (
    CropType,
    Dimension,
    HazardCateogy,
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
    quantity_sold = common_models.PrecisionField(help_text=_("Quantity Sold"))
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


class LivestockProductionModel(ProductionModel):
    """
    Production models for livestock.

    Production models vary greatly in level of detail recorded. However they don't vary in level of detail by
    production model type, so much as by prominence in local livelihoods. This isn't therefore a useful
    distinction to make when implementing.

    Example BSS for cow's milk for rural Niger:

    BSS contains:
        no. milking animals
        season 1: lactation period (days)
        daily milk production per animal (litres)
        total production (litres)
        sold/exchanged (litres)
        price (cash)
        income (cash)
        type of milk sold/other use (skim=0, whole=1)
        other use (liters)

    Where ProductionModel values come from in the cows' milk BSS:
        input_item = Milking cow
        input_quantity = no. milking animals
        output_item = full fat milk
        units_produced_per_period = daily milk production
        unit = Litres
        season = 1
        duration = number of lactation days (in season)
        total_production = qty * duration * frequency (in BSS as total production (litres))
        quantity_sold = sold/exchanged (litres)
        price = price (cash)
        income = total_production * quantity_sold * price (in BSS as 'income')
        quantity_other_uses = Other use
        quantity_consumed = total production - quantity sold - quantity other uses
        kcals_consumed = quantity_consumed * kcals_per_unit

        Note that the BSSes are confusing here, converting some milk into ghee, by factor 0.04 (does this 4%
        include the proportion of the milk used for ghee?), then converted to kcals at 7,865, plus some
        milk at 640 kcals, to derive kcal% aggregated for both seasons. We will probably need to store the
        0.04 and 7865 once we understand where they come from.

    Example BSS for cow meat for rural Niger:

    BSS contains little detail, as this livelihood strategy (LS) is rarely employed:
        Cow meat: no. animals slaughtered
        carcass weight per animal (kg)
        kcals (%)

    ProductionModel values:
        input_item = cow
        input_quantity = no. animals slaughtered
        output_item = cow meat
        units_produced_per_period = carcass weight per animal (kg)
        unit = kg
        season = None
        duration = 1 (annual figure given)
        BSS only provides kcal%, and the cell formula assumes all cow meat is consumed, and provides 2350 kcal/kg, so:
            quantity_sold = 0
            quantity_other_uses = 0
            price = None
            total_production, income, etc. = as above

    """


class CropProductionModel(ProductionModel):
    """
    Production models for crops.

    BSS examples:
        Green cons - rainfed: no of months = 1 for poorer groups, 1.5 for richer ones.
        Proportion of months green consumption = 33% for all villages in LHZ
        kcals (%)

    There doesn't seem to be a unit here, the spreadsheet just calculates kcal% as:
        no of months / 12 * Proportion of months green consumption

    This suggests 'Proportion of months green consumption' is the amount of a person's diet this provides.
    This is therefore a crude approximation of annual yield in kcals % per household member.

    ProductionModel values:
        output_item = Green cons rainfed
        output_unit = kcal%
        units_produced_per_period = Proportion of months green consumption (0.333% for all communities in LHZ)
        duration = no of months, eg, 1
        none sold, none other uses

    Another BSS example with more detail:
        Maize irrigated: kg produced
        kcals per kg
        sold/exchanged (kg)
        price per kg (cash)
        income (cash)
        other use (kg)
        kcals (%)

    Another BSS example with different low detail:
        Cotton: kg sold
        price per kg (cash)
        income (cash)
    """


class FoodPurchaseProductionModel(ProductionModel):
    """
    Production models for the purchase of food.

    BSS example:
        Maize grain: name of meas.	Kg
        wt of measure	1
        no. meas per month	60
        no. months	4
        kg	240
        kcals/kg	3630  <- note this value is often just embedded in formulae so impossible to
        automatically read
        kcals (%)	19%
        price (per kg)	100
        expenditure	24,000
    """


class PaymentInKindProductionModel(ProductionModel):
    """
    Production models for payment in kind.

    BSS example:
        Labour: Weeding
        no. people per HH
        no. times per month
        no. months
        payment in kg per time (grain)
        kcals (%)
    """


class OtherCashIncomeSourcesProductionModel(ProductionModel):
    """
    Production models for other cash income sources, on sheet Data2. The level of detail is consistent across
    production models.

    BSS example:
        Land preparation
        no. people per HH
        no. times per month
        no. months
        price per unit
        income
    """


class WildFoodsAndFishingProductionModel(ProductionModel):
    """
    Production models for wild foods and fishing, on sheet Data3. The level of detail is consistent across
    production models.

    BSS example:
        Wild food type 1- Mphunga - kg gathered	8.6
        kcals per kg	3540
        sold/exchanged (kg)	0
        price (cash)
        income (cash)	0
        other use (kg)	0
        kcals (%)	1%
    """


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
        verbose_name=_("Age at Sale"), help_text=_("Age in months at which the animal is typically sold")
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
    hazard_category = models.ForeignKey(HazardCateogy, on_delete=models.RESTRICT, verbose_name=_("Hazard Category"))
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
