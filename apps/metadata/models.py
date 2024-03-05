import logging

from django.contrib.gis.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

import common.models as common_models
from common.fields import TranslatedField
from common.models import ClassifiedProduct, Country, Currency, UnitOfMeasure

logger = logging.getLogger(__name__)


class ReferenceData(common_models.Model):
    """
    Reference data for a model.

    Provides shared structure and functionality for reference data
    (e.g. categories or types) that are used as metadata lookups for other models.
    """

    code = common_models.CodeField(primary_key=True, verbose_name=_("Code"))
    name = TranslatedField(common_models.NameField())
    description = TranslatedField(common_models.DescriptionField())
    # Some reference data needs to be sorted in a custom (i.e. non-alphabetic) order.
    # For example, WealthGroupCategory needs to be VP, P, M, BO in most cases.
    ordering = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Ordering"),
        help_text=_("The order to display the items in when sorting by this field, if not obvious."),
    )
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
        identifier = ["name_en"]


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
        help_text=_(
            "Does a value for this characteristic also require a product? "
            "If True, then aliases may contain a <product> placeholder."
        ),
    )
    has_unit_of_measure = models.BooleanField(
        default=False,
        verbose_name=_("Has Unit Of Measure?"),
        help_text=_(
            "Does a value for this characteristic also require a unit_of_measure? "
            "If True, then aliases may contain a <unit_of_measure> placeholder."
        ),
    )
    variable_type = models.CharField(
        max_length=20,
        verbose_name=_(
            "Variable Type",
        ),
        choices=VariableType.choices,
        default=VariableType.STR,
        help_text=_("Whether the field is numeric, character, boolean, etc."),
    )

    class Meta:
        verbose_name = _("Wealth Characteristic")
        verbose_name_plural = _("Wealth Characteristics")


# Defined outside LivelihoodStrategy to make it easy to access from subclasses
# This is a hard-coded list of choices because additions to the list require
# matching custom subclasses of LivelihoodActivity anyway.
class LivelihoodStrategyType(models.TextChoices):
    MILK_PRODUCTION = "MilkProduction", _("Milk Production")
    BUTTER_PRODUCTION = "ButterProduction", _("Butter Production")
    MEAT_PRODUCTION = "MeatProduction", _("Meat Production")
    LIVESTOCK_SALE = "LivestockSale", _("Livestock Sale")
    CROP_PRODUCTION = "CropProduction", _("Crop Production")
    FOOD_PURCHASE = "FoodPurchase", _("Food Purchase")
    PAYMENT_IN_KIND = "PaymentInKind", _("Payment in Kind")
    RELIEF_GIFT_OTHER = "ReliefGiftOther", _("Relief, Gift or Other Food")
    FISHING = "Fishing", _("Fishing")
    WILD_FOOD_GATHERING = "WildFoodGathering", _("Wild Food Gathering")
    OTHER_CASH_INCOME = "OtherCashIncome", _("Other Cash Income")
    OTHER_PURCHASE = "OtherPurchase", _("Other Purchase")


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


class WealthGroupCategory(ReferenceData):
    """
    The local definitions of wealth group, common to all BSSes in an LHZ.

    Standardized from the BSS 'WB' worksheet in Column B and the 'Data'
    worksheet in Row 3, so that it can be shared across all BSS.
    """

    class Meta:
        verbose_name = _("Wealth Group Category")
        verbose_name_plural = _("Wealth Group Categories")


class MarketManager(common_models.IdentifierManager):
    def get_by_natural_key(self, full_name):
        return self.get(full_name=full_name)


class Market(common_models.Model):
    """
    A geographic point where :class:`baseline.models.MarketPrice` records are collected.
    """

    # The field definitions are structured to ensure compatibility with FDW spatial.models.GeographicUnit,
    # in case we need to match them, or move to a full Spatial setup later.
    country = models.ForeignKey(
        Country, db_column="country_code", blank=True, null=True, verbose_name=_("country"), on_delete=models.CASCADE
    )
    name = TranslatedField(common_models.NameField(max_length=250))
    code = models.CharField(
        max_length=25,
        blank=True,
        null=True,
        unique=True,
        verbose_name=_("code"),
        help_text=_("An identifier for the Unit, such as the FNID"),
    )
    full_name = TranslatedField(common_models.NameField(max_length=200, unique=True, verbose_name=_("full name")))
    description = TranslatedField(common_models.DescriptionField())
    aliases = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_("aliases"),
        help_text=_("A list of alternate names for the Market."),
    )
    geography = models.GeometryField(geography=True, dim=2, blank=True, null=True, verbose_name=_("geography"))

    objects = MarketManager()

    def natural_key(self):
        return (self.full_name,)

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


class SeasonManager(common_models.IdentifierManager):
    def get_by_natural_key(self, name_en: str) -> "Season":
        return self.get(name_en=name_en)


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
    name = TranslatedField(models.CharField(max_length=100, unique=True, verbose_name=_("Name")))
    description = TranslatedField(models.TextField(max_length=255, verbose_name=_("Description")))
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

    # @TODO Do we need `SeasonYear` or `SeasonGroup`to act as a parent of consecutive seasons that make up a 12 month period.  # NOQA: E501
    order = models.IntegerField(
        verbose_name=_("Order"),
        help_text=_("The order of the Season within the Season Year"),
    )
    aliases = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_("aliases"),
        help_text=_("A list of alternate names for the Season."),
    )

    objects = SeasonManager()

    def natural_key(self):
        return (self.name_en,)

    class Meta:
        verbose_name = _("Season")
        verbose_name_plural = _("Seasons")


class ActivityLabel(common_models.Model):
    """
    A label from Column A of the 'Data', 'Data2' or 'Data3' worksheet in a BSS and associated attributes.

    Used by the data ingestion pipeline for LivelihoodStrategy and LivelihoodActivity to determine the attributes for
    the LivelihoodStrategy and/or LivelihoodActivity for a given row in a BSS.
    """

    class LivelihoodActivityType(models.TextChoices):
        LIVELIHOOD_ACTIVITY = "LivelihoodActivity", _("Livelihod Activity")  # Labels from the 'Data' worksheet
        OTHER_CASH_INCOME = "OtherCashIncome", _("Other Cash Income")  # Labels from the 'Data2' worksheet
        WILD_FOODS = "WildFoods", _("Wild Foods")  # Labels from the 'Data3' worksheet

    activity_label = common_models.NameField(max_length=100, verbose_name=_("Activity Label"))
    activity_type = models.CharField(
        max_length=20,
        verbose_name=_("Activity Type"),
        choices=LivelihoodActivityType.choices,
        default=LivelihoodActivityType.LIVELIHOOD_ACTIVITY,
        help_text=_(
            "The type of Livelihood Activity, either a general Livelihood Activity, or an Other Cash Income "
            "activity from the 'Data2' worksheet, or a Wild Foods, Fishing or Hunting activity from the "
            "'Data3' worksheet."
        ),
    )
    is_start = models.BooleanField(
        default=False,
        verbose_name=_("Is Start?"),
        help_text=_("Indicates whether this Activity Label marks the start of a new Livelihood Strategy"),
    )
    strategy_type = models.CharField(
        max_length=30,
        blank=True,
        choices=LivelihoodStrategyType.choices,
        verbose_name=_("Strategy Type"),
        help_text=_("The type of livelihood strategy, such as crop production, or wild food gathering."),
    )
    product = models.ForeignKey(
        ClassifiedProduct,
        db_column="product_code",
        null=True,
        blank=True,
        on_delete=models.RESTRICT,
        related_name="activity_labels",
        verbose_name=_("Product"),
    )
    unit_of_measure = models.ForeignKey(
        UnitOfMeasure,
        db_column="unit_code",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_("Unit of Measure"),
        related_name="activity_labels",
    )
    currency = models.ForeignKey(
        Currency,
        db_column="currency_code",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_("Currency"),
    )
    season = models.CharField(max_length=60, blank=True, verbose_name=_("Season"))
    additional_identifier = models.CharField(max_length=60, blank=True, verbose_name=_("Season"))
    attribute = models.CharField(max_length=60, blank=True, verbose_name=_("Attribute"))

    class ExtraMeta:
        identifier = ["activity_label"]

    class Meta:
        verbose_name = _("Activity Label")
        verbose_name_plural = _("Activity Labels")
        constraints = [
            models.UniqueConstraint(Lower("activity_label"), "activity_type", name="unique_lower_name_category"),
        ]


class WealthCharacteristicLabel(common_models.Model):
    """
    A label from Column A of the 'WB' worksheet in a BSS and associated attributes.

    Used by the ingestion pipeline for WealthCharacteristicValue to determine the attributes for a given row in a BSS.
    """

    wealth_characteristic_label = common_models.NameField(
        max_length=100, unique=True, verbose_name=_("Wealth Characteristic Label")
    )
    # wealth_characteristic has to be nullable because there are some labels that we want to recognize
    # i.e. they need an entry in this table, but that we want to ignore completely. For example, sample text in blank
    # rows, etc. Those labels will have an entry in this table, but no other metadata items.
    wealth_characteristic = models.ForeignKey(
        WealthCharacteristic,
        db_column="wealth_characteristic_code",
        null=True,
        blank=True,
        on_delete=models.RESTRICT,
        related_name="wealth_characteristics",
        verbose_name=_("Wealth Characteristic"),
    )
    product = models.ForeignKey(
        ClassifiedProduct,
        db_column="product_code",
        null=True,
        blank=True,
        on_delete=models.RESTRICT,
        related_name="wealth_characteristics",
        verbose_name=_("Product"),
    )
    unit_of_measure = models.ForeignKey(
        UnitOfMeasure,
        db_column="unit_code",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_("Unit of Measure"),
        related_name="wealth_characteristics",
    )

    class ExtraMeta:
        identifier = ["wealth_characteristic_label"]

    class Meta:
        verbose_name = _("Wealth Characteristic Label")
        verbose_name_plural = _("Wealth Characteristics Labels")
