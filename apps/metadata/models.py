import logging

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

import common.models as common_models
from common.models import Country

logger = logging.getLogger(__name__)


class ReferenceData(common_models.Model):
    """
    Reference data for a model.

    Provides shared structure and functionality for reference data
    (e.g. categories or types) that are used as metadata lookups for other models.
    """

    code = common_models.CodeField(primary_key=True, verbose_name=_("Code"))
    name = common_models.NameField()
    description = common_models.DescriptionField()
    # Some reference data needs to be sorted in a custom (i.e. non-alphabetic) order.
    # For example, WealthCategory needs to be VP, P, M, BO in most cases.
    ordering = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Ordering"),
        help_text=_("The order to display the items in when sorting by this field, if not obvious."),
    )
    # @TODO ArrayField or JSONField?
    aliases = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_("aliases"),
        help_text=_("A list of alternate names for the object."),
    )

    def calculate_fields(self):
        # Ensure that aliases are lowercase and don't contain duplicates
        if self.aliases:
            self.aliases = list(sorted(set([alias.strip().lower() for alias in self.aliases if alias.strip()])))

    def save(self, *args, **kwargs):
        self.calculate_fields()
        # No need to enforce foreign keys or uniqueness because database constraints will do it anyway
        self.full_clean(
            exclude=[field.name for field in self._meta.fields if isinstance(field, models.ForeignKey)],
            validate_unique=False,
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code

    class Meta:
        abstract = True

    class ExtraMeta:
        identifier = ["name"]


class LivelihoodCategory(ReferenceData):
    """
    A type of Livelihood Zone, such as Pastoral or Rain-fed AgroPastoral, etc.
    """

    # @TODO Do we need a parent category so we can store the detail of Rain Fed AgriPastoral,
    # but still filter for all AgroPastoral
    # Roger: Is this true? Or is Rainfed a modifier for Crop rather than for LivelihoodCategory?

    class Meta:
        verbose_name = _("Livelihood Category")
        verbose_name_plural = _("Livelihood Categories")


class WealthCharacteristic(ReferenceData):
    """
    A Characteristic of a Wealth Group, such as `Number of children at school`, etc.

    Standardized from descriptions in the BSS 'WB' worksheet in Column A,
    so that it can be shared across all BSS.
    """

    class VariableType(models.TextChoices):
        NUM = "float", _("Numeric")
        STR = "str", _("String")
        BOOL = "bool", _("Boolean")
        # OTHER = "other", _("Other")

    has_product = models.BooleanField(
        default=False,
        verbose_name=_("Has Product?"),
        help_text=_("Does a value for this characteristic also require a product?"),
    )
    variable_type = models.CharField(
        verbose_name=_(
            "Variable Type",
        ),
        choices=VariableType.choices,
        default=VariableType.STR,
        help_text=_("Whether the field is numeric, character, boolean, etc."),
    )

    class Meta:
        verbose_name = _("Wealth Group Characteristic")
        verbose_name_plural = _("Wealth Group Characteristics")


# Defined outside LivelihoodStrategy to make it easy to access from subclasses
# This is a hard-coded list of choices because additions to the list require
# matching custom subclasses of LivelihoodActivity anyway.
class LivelihoodStrategyType(models.TextChoices):
    MILK_PRODUCTION = "MilkProduction", _("Milk Production")
    BUTTER_PRODUCTION = "ButterProduction", _("Butter Production")
    MEAT_PRODUCTION = "MeatProduction", _("Meat Production")
    LIVESTOCK_SALES = "LivestockSales", _("Livestock Sales")
    CROP_PRODUCTION = "CropProduction", _("Crop Production")
    FOOD_PURCHASE = "FoodPurchase", _("Food Purchase")
    PAYMENT_IN_KIND = "PaymentInKind", _("Payment in Kind")
    RELIEF_GIFTS_OTHER = "ReliefGiftsOther", _("Relief, Gifts and Other Food")
    FISHING = "Fishing", _("Fishing")
    WILD_FOOD_GATHERING = "WildFoodGathering", _("Wild Food Gathering")
    OTHER_CASH_INCOME = "OtherCashIncome", _("Other Cash Income")
    OTHER_PURCHASES = "OtherPurchases", _("Other Purchases")


# Defined outside LivelihoodActivity to make it easy to access from subclasses
class LivelihoodActivityScenario(models.TextChoices):
    BASELINE = "baseline", _("Baseline")
    RESPONSE = "response", _("Response")


class SeasonalActivityType(ReferenceData):
    """
    Seasonal activities for the various food and income activities.

    Includes standard activities and events supporting Livelihood Strategies,
    such as planting, weeding, harvesting for Crop Production and heat, birth
    milk production and sales for Livestock.

    It also includes other important periodic events such as recurring periods
    of high market prices or poor access to food.

    Standardized from descriptions in the BSS 'Seas Cal' worksheet in Column A,
    so that it can be shared across all BSS.
    """

    # @TODO What is the overlap with LivelihoodStrategyTypes? Can we reuse or share?
    class SeasonalActivityCategory(models.TextChoices):
        CROP = "crop", _("Crops")
        LIVESTOCK = "livestock", _("Livestock")
        GARDENING = "gardening", _("Gardening")
        FISHING = "fishing", _("Fishing")

    activity_category = models.CharField(
        max_length=20, choices=SeasonalActivityCategory.choices, verbose_name=_("Activity Category")
    )

    class Meta:
        verbose_name = _("Seasonal Activity Type")
        verbose_name_plural = _("Seasonal Activity Types")


class WealthCategory(ReferenceData):
    """
    The local definitions of wealth group, common to all BSSes in an LHZ.

    Standardized from the BSS 'WB' worksheet in Column B and the 'Data'
    worksheet in Row 3, so that it can be shared across all BSS.
    """

    class Meta:
        verbose_name = _("Wealth Category")
        verbose_name_plural = _("Wealth Categories")


class Market(ReferenceData):
    """
    The markets in the bss are just names
    TODO: should we make this spatial? and move it to spatial or metadata?
    """

    country = common_models.NameField(verbose_name=_("Name"))

    class Meta:
        verbose_name = _("Market")
        verbose_name_plural = _("Markets")


class HazardCategory(ReferenceData):
    """
    A category of Hazards such as drought, epidemic crop disease, epidemic livestock disease, floods, etc.

    The Form 3 template includes the following Hazard Categories:
      Drought, Frost, Wind, Epidemic crop disease, Wild Animalst, Flood, Hail,
      Crop Pests, Epidemic livestock disease, Market events.
    """

    class Meta:
        verbose_name = _("Hazard Category")
        verbose_name_plural = _("Hazard Categories")


class Season(common_models.Model):
    """
    A division of the year, marked by changes in weather, ecology, and associated livelihood zone
    activities for income generation.
    """

    class SeasonType(models.TextChoices):
        HARVEST = "Harvest", _("Harvest")
        LEAN = "Lean", _("Lean")
        WET = "Wet", _("Wet")
        DRY = "Dry", _("Dry")
        MILD = "Mild", _("Mild")
        SPRING = "Spring", pgettext_lazy("season", "Spring")
        SUMMER = "Summer", _("Summer")
        FALL = "Fall", pgettext_lazy("season", "Fall")
        WINTER = "Winter", _("Winter")
        MONSOON = "Monsoon", _("Monsoon")

    class YearAlignment(models.TextChoices):
        START = "Start", _("Start")
        END = "End", _("End")

    country = models.ForeignKey(Country, verbose_name=_("Country"), db_column="country_code", on_delete=models.PROTECT)
    # @TODO Uncomment if we have a full Spatial app.
    # geographic_unit - models.ForeignKey(GeographicUnit, verbose_name=_("Geographic Unit"), on_delete=models.RESTRICT)
    name = models.CharField(max_length=50, verbose_name=_("Name"))
    description = models.TextField(max_length=255, verbose_name=_("Description"))
    season_type = models.CharField(
        max_length=20,
        choices=SeasonType.choices,
        verbose_name=_("Season Type"),
        help_text=_(
            "Refers to the classification of a specific time of year based on weather patterns, temperature, and other factors"  # NOQA: E501
        ),
    )
    # We use day in the year instead of month to allow greater granularity,
    # and compatibility with the potential FDW Enhanced Crop Calendar output.
    # Note that if the season goes over the year end, then the start day
    # will be larger than the end day.
    start = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(365), MinValueValidator(1)], verbose_name=_("Start Day")
    )
    end = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(365), MinValueValidator(1)], verbose_name=_("End Day")
    )
    alignment = models.CharField(
        max_length=5,
        choices=YearAlignment.choices,
        default=YearAlignment.END,
        verbose_name=_("Year alignment"),
        help_text=_(
            "Whether a label for a season that contains a single year refers to the start year or the end year for that Season."  # NOQA: E501
        ),
    )

    class ExtraMeta:
        identifier = ["name"]

    # @TODO Do we need `SeasonYear` or `SeasonGroup`to act as a parent of consecutive seasons that make up a 12 month period.  # NOQA: E501
    order = models.IntegerField(
        verbose_name=_("Order"),
        help_text=_("The order of the Season within the Season Year"),
    )

    class Meta:
        verbose_name = _("Season")
        verbose_name_plural = _("Seasons")
