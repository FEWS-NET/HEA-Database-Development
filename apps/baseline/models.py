"""
Models for managing HEA Baseline Surveys
"""

import numbers

from django.conf import settings
from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import F
from django.utils.translation import gettext_lazy as _
from model_utils.managers import InheritanceManager

import common.models as common_models
from common.fields import TranslatedField
from common.models import (
    ClassifiedProduct,
    Country,
    Currency,
    UnitOfMeasure,
    UnitOfMeasureConversion,
)
from common.utils import get_month_from_day_number
from metadata.models import (
    HazardCategory,
    LivelihoodActivityScenario,
    LivelihoodCategory,
    LivelihoodStrategyType,
    Market,
    Season,
    SeasonalActivityType,
    WealthCharacteristic,
    WealthGroupCategory,
)


class SourceOrganizationManager(common_models.IdentifierManager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class SourceOrganization(common_models.Model):
    """
    An Organization that provides HEA Baselines.
    """

    name = common_models.NameField(max_length=200, unique=True)
    full_name = common_models.NameField(verbose_name=_("full name"), max_length=300, unique=True)
    description = common_models.DescriptionField()

    objects = SourceOrganizationManager()

    def natural_key(self):
        return (self.name,)

    class Meta:
        verbose_name = _("Source Organization")
        verbose_name_plural = _("Source Organizations")

    class ExtraMeta:
        identifier = ["name"]


class LivelihoodZone(common_models.Model):
    """
    A geographical area within a Country in which people share broadly the same
    patterns of access to food and income, and have the same access to markets.

    Over time the livelihoods in the geographical area may change between one
    Baseline and the next, but if the group of people are the same then the
    Livelihood Zone is the same and both Baselines belong to the same
    Livelihood Zone.

    On the other hand, if the group of people between two Baselines are not the
    same, then they are for different Livelihood Zones and those Livelihood
    Zones must have different codes. For some historic Baselines, e.g. in
    Nigeria, the  same code may have been used for different locations and
    populations at different times. In that situation, the code should be
    revised when it is loaded into the database to include the reference year,
    so that we can distinguish, for example, between NG01-2012 and NG01-2017.
    """

    code = models.CharField(
        max_length=25,
        primary_key=True,
        verbose_name=_("code"),
        help_text=_("Primary identifier for the Livelihood Zone"),
    )
    alternate_code = models.CharField(
        max_length=25,
        blank=True,
        verbose_name=_("alternate code"),
        help_text=_(
            "Alternate identifier for the Livelihood Zone, typically a meaningful code based on the name of the Zone."
        ),  # NOQA: E501
    )
    name = TranslatedField(common_models.NameField(max_length=200, unique=True))
    description = TranslatedField(common_models.DescriptionField())
    country = models.ForeignKey(Country, verbose_name=_("Country"), db_column="country_code", on_delete=models.PROTECT)

    class Meta:
        verbose_name = _("Livelihood Zone")
        verbose_name_plural = _("Livelihood Zones")

    class ExtraMeta:
        identifier = ["code"]


class LivelihoodZoneBaselineManager(common_models.IdentifierManager):
    def get_by_natural_key(self, code: str, reference_year_end_date: str):
        return self.get(livelihood_zone__code=code, reference_year_end_date=reference_year_end_date)


class LivelihoodZoneBaseline(common_models.Model):
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

    class Language(models.TextChoices):
        # Choices are rendered to migrations, so we cannot base them dynamically on settings.LANGUAGES
        EN = "en", _("English")
        FR = "fr", _("French")
        ES = "es", _("Spanish")
        PT = "pt", _("Portuguese")
        AR = "ar", _("Arabic")

    name = TranslatedField(common_models.NameField(max_length=200, unique=True))
    description = TranslatedField(common_models.DescriptionField())
    livelihood_zone = models.ForeignKey(
        LivelihoodZone, db_column="livelihood_zone_code", on_delete=models.RESTRICT, verbose_name=_("Livelihood Zone")
    )
    geography = models.MultiPolygonField(geography=True, dim=2, blank=True, null=True, verbose_name=_("geography"))

    main_livelihood_category = models.ForeignKey(
        LivelihoodCategory,
        db_column="livelihood_category_code",
        on_delete=models.RESTRICT,
        verbose_name=_("Livelihood Zone Type"),
    )
    source_organization = models.ForeignKey(
        SourceOrganization, on_delete=models.RESTRICT, verbose_name=_("Source Organization")
    )
    bss = models.FileField(upload_to="livelihoodzonebaseline/bss", verbose_name=_("BSS Excel file"))
    bss_language = models.CharField(
        choices=Language.choices, blank=True, null=True, max_length=10, verbose_name=_("BSS Language")
    )
    profile_report = TranslatedField(
        models.FileField(
            upload_to="livelihoodzonebaseline/profile_report",
            blank=True,
            null=True,
            verbose_name=_("Profile Report PDF file"),
        )
    )
    reference_year_start_date = models.DateField(
        verbose_name=_("Reference Year Start Date"),
        help_text=_("The first day of the month of the start month in the reference year"),
    )
    reference_year_end_date = models.DateField(
        verbose_name=_("Reference Year End Date"),
        help_text=_("The last day of the month of the end month in the reference year"),
    )
    valid_from_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Valid From Date"),
        help_text=_("The first day of the month that this baseline is valid from"),
    )
    valid_to_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Valid To Date"),
        help_text=_("The last day of the month that this baseline is valid until"),
    )
    data_collection_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Data Collection Start Date"),
        help_text=_("The first day of data collection period"),
    )
    data_collection_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Data Collection End Date"),
        help_text=_("The last day of the data collection period"),
    )
    publication_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Publication Date"),
        help_text=_("The day that the baseline was published"),
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
        null=True,
        verbose_name=_("Population Estimate"),
        help_text=_("The estimated population of the Livelihood Zone during the reference year"),
    )

    objects = LivelihoodZoneBaselineManager()

    def natural_key(self):
        try:
            return (self.livelihood_zone_id, self.reference_year_end_date.isoformat())
        except Exception:
            print(self.__dict__)
            raise

    class Meta:
        verbose_name = _("Livelihood Zone Baseline")
        verbose_name_plural = _("Livelihood Zone Baselines")
        constraints = [
            models.UniqueConstraint(
                fields=("livelihood_zone", "reference_year_end_date"),
                name="baseline_livelihoodzonebaseline_livelihood_zone_reference_year_end_date_uniq",
            )
        ]


class LivelihoodZoneBaselineCorrection(common_models.Model):
    """
    Represents a correction entry for a livelihood zone baseline.
    Each correction stores information about the changed data,
    including the worksheet name, cell range, previous and new values,
    the date of correction, the author of the correction, and a comment explaining the change.
    """

    class WorksheetName(models.TextChoices):
        WB = "WB", _("WB")
        DATA = "Data", _("Data")
        DATA2 = "Data2", _("Data2")
        DATA3 = "Data3", _("Data3")

    livelihood_zone_baseline = models.ForeignKey(
        LivelihoodZoneBaseline,
        on_delete=models.CASCADE,
        related_name="corrections",
        verbose_name=_("Livelihood Zone Baseline"),
    )
    worksheet_name = models.CharField(max_length=20, choices=WorksheetName.choices, verbose_name=_("Worksheet name"))
    cell_range = models.CharField(max_length=10, verbose_name=_("Cell range"))
    previous_value = models.CharField(max_length=255, verbose_name=_("Previous value before correction"))
    value = models.CharField(max_length=255, verbose_name=_("Corrected value"))
    correction_date = models.DateTimeField(auto_now_add=True, verbose_name=_("Correction date"))
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("Correction author"))
    comment = models.TextField(
        max_length=255,
        verbose_name=_("Correction comments"),
        help_text=_("Required comment about the correction suggested"),
    )


# @TODO Can we have a better name.
class LivelihoodProductCategory(common_models.Model):
    """
    The usage category of the Product in the Livelihood Zone, such as staple food or livelihood protection.
    """

    class ProductBasket(models.IntegerChoices):
        MAIN_STAPLE = 1, _("Main Staple")
        OTHER_STAPLE = 2, _("Other Staple")
        SURVIVAL_NON_FOOD = 3, _("Non-food survival")
        LIVELIHOODS_PROTECTION = 4, _("Livelihoods Protection")

    livelihood_zone_baseline = models.ForeignKey(
        LivelihoodZoneBaseline,
        on_delete=models.RESTRICT,
        related_name="staple_foods",
        verbose_name=_("Livelihood Zone Baseline"),
    )
    product = models.ForeignKey(
        ClassifiedProduct,
        db_column="product_code",
        on_delete=models.RESTRICT,
        related_name="staple_foods",
        verbose_name=_("Product"),
    )
    basket = models.PositiveSmallIntegerField(choices=ProductBasket.choices, verbose_name=_("Product Basket"))

    class Meta:
        verbose_name = _("Livelihood Product Category")
        verbose_name_plural = _("Livelihood Product Categories")


class CommunityManager(common_models.IdentifierManager):
    def get_by_natural_key(self, code: str, reference_year_end_date: str, full_name: str):
        return self.get(
            livelihood_zone_baseline__livelihood_zone__code=code,
            livelihood_zone_baseline__reference_year_end_date=reference_year_end_date,
            full_name=full_name,
        )


class Community(common_models.Model):
    """
    A representative location within the Livelihood Zone whose population was
    surveyed to produce the Baseline.

    In a rural Livelihood Zone this is typically a Village. In an urban
    Livelihood Zone for a Francophone Country it might be a quartier within an
    arrondissement.
    """

    code = models.CharField(
        max_length=25,
        blank=True,
        null=True,
        verbose_name=_("Code"),
        help_text=_("A short identifier for the Community"),
    )
    name = common_models.NameField()
    full_name = common_models.NameField(
        max_length=200,
        verbose_name=_("Full Name"),
        help_text=_("The full name of the Community, including the parent administrative units."),
    )
    livelihood_zone_baseline = models.ForeignKey(
        LivelihoodZoneBaseline,
        on_delete=models.CASCADE,
        related_name="communities",
        verbose_name=_("Livelihood Zone Baseline"),
    )
    geography = models.GeometryField(geography=True, dim=2, blank=True, null=True, verbose_name=_("geography"))
    # Typicallly a number, but sometimes a code, e.g. SO03_NWA_26Nov15
    # See https://docs.google.com/spreadsheets/d/1wuXjjmQXW9qG5AV8MRKHVadrFUhleUGN/
    # If present, this can be used to validate the data reported for the Wealth Group (Form 4) interviews.
    interview_number = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name=_("Interview Number"),
        help_text=_("The interview number or interview code assigned to the Community"),
    )
    community_interview_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Community Interview Date"),
        help_text=_("The date that the Community Interview (Form 3) was conducted."),
    )
    wealth_group_interview_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Wealth Group Interview Date"),
        help_text=_("The date that the Wealth Group Interviews (Form 4) were conducted."),
    )
    objects = CommunityManager()

    def natural_key(self):
        return (
            self.livelihood_zone_baseline.livelihood_zone.code,
            self.livelihood_zone_baseline.reference_year_end_date.isoformat(),
            self.full_name,
        )

    class Meta:
        verbose_name = _("Community")
        verbose_name_plural = _("Communities")
        constraints = [
            models.UniqueConstraint(
                fields=("livelihood_zone_baseline", "full_name"),
                name="baseline_community_livelihood_zone_baseline_full_name_uniq",
            ),
            # Create a unique constraint on id and livelihood_zone_baseline, so that we can use it as a target for a
            # composite foreign key from Seasonal Activity, which in turn allows us to ensure that the Community
            # and the Baseline Seasonal Activity for a Seasonal Activity both have the same Livelihood Baseline.
            # We also use it as a target from WealthGroup when the Community is specified.
            models.UniqueConstraint(
                fields=["id", "livelihood_zone_baseline"],
                name="baseline_community_id_livelihood_zone_baseline_uniq",
            ),
        ]


class WealthGroupManager(common_models.IdentifierManager):
    def get_by_natural_key(self, code: str, reference_year_end_date: str, wealth_group_category: str, full_name: str):
        if full_name:
            return self.get(
                livelihood_zone_baseline__livelihood_zone__code=code,
                livelihood_zone_baseline__reference_year_end_date=reference_year_end_date,
                wealth_group_category__code=wealth_group_category,
                community__full_name=full_name,
            )
        else:
            return self.get(
                livelihood_zone_baseline__livelihood_zone__code=code,
                livelihood_zone_baseline__reference_year_end_date=reference_year_end_date,
                wealth_group_category__code=wealth_group_category,
                community__isnull=True,
            )


# @TODO https://fewsnet.atlassian.net/browse/HEA-92
# Should this be SocioEconomicGroup, or maybe PopulationGroup, given female-headed households, etc.
# Jenny will check with P3 on preferred English naming. In French, it is something else anyway, I think.
class WealthGroup(common_models.Model):
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

    livelihood_zone_baseline = models.ForeignKey(
        LivelihoodZoneBaseline,
        on_delete=models.CASCADE,
        related_name="wealth_groups",
        verbose_name=_("Livelihood Zone Baseline"),
    )
    # If Community is specified then the Wealth Group represents the households
    # within that Community in the specified Wealth Group Category. If the Community
    # is null, then the Wealth Group represents the households with that
    # Wealth Group Category for the whole Livelihood Zone Baseline.
    # @TODO Or make this a mandatory geographic_unit
    # In which case we move validation out of here and into the spatial hierarchy.
    # Roger: We need the `livelihood_zone_baseline` as a foreign key anyway,
    # so we can validate that Activity->Strategy->Baseline and Activity->WealthGroup->Baseline end up at the
    # same Baseline. Therefore we need the `livelihood_zone_baseline` as a separate column anyway. I think it
    # would be weird to have `livelihood_zone_baseline` and `geographic_unit` both pointing at the same object,
    # and it would be less obvious whether a WealthGroup is a BaselineWealthGroup or a CommunityWealthGroup.
    # Therefore, I think that the current approach with an optional `community` is preferable.
    community = models.ForeignKey(
        Community, blank=True, null=True, on_delete=models.CASCADE, verbose_name=_("Community")
    )
    wealth_group_category = models.ForeignKey(
        WealthGroupCategory,
        db_column="wealth_group_category_code",
        on_delete=models.CASCADE,
        verbose_name=_("Wealth Group Category"),
        help_text=_("Wealth Group Category, e.g. Poor or Better Off"),
    )
    percentage_of_households = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Percentage of households"),
        help_text=_("Percentage of households in the Community or Livelihood Zone that are in this Wealth Group"),
    )
    average_household_size = models.PositiveSmallIntegerField(
        blank=True, null=True, verbose_name=_("Average household size")
    )

    objects = WealthGroupManager()

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

    def __str__(self):
        return (
            f"{str(self.community)} {str(self.wealth_group_category)}"
            if self.community
            else f"{str(self.livelihood_zone_baseline)} {str(self.wealth_group_category)}"
        )

    def natural_key(self):
        return (
            self.livelihood_zone_baseline.livelihood_zone_id,
            self.livelihood_zone_baseline.reference_year_end_date.isoformat(),
            self.wealth_group_category.code,
            self.community.full_name if self.community else "",
        )

    class Meta:
        verbose_name = _("Wealth Group")
        verbose_name_plural = _("Wealth Groups")
        constraints = [
            models.UniqueConstraint(
                fields=("livelihood_zone_baseline", "wealth_group_category", "community"),
                name="baseline_wealthgroup_livelihood_zone_baseline_wealth_group_category_community_uniq",
            ),
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


class WealthGroupCharacteristicValueManager(common_models.IdentifierManager):
    def get_by_natural_key(
        self,
        code: str,
        reference_year_end_date: str,
        wealth_group_category: str,
        wealth_characteristic: str,
        reference_type: str = "baseline_summary",
        product: str = "",
        full_name: str = "",
    ):
        criteria = {
            "wealth_characteristic__code": wealth_characteristic,
            "reference_type": reference_type,
            "wealth_group__livelihood_zone_baseline__livelihood_zone__code": code,
            "wealth_group__livelihood_zone_baseline__reference_year_end_date": reference_year_end_date,
            "wealth_group__wealth_group_category__code": wealth_group_category,
        }
        if full_name:
            criteria["wealth_group__community__full_name"] = full_name
        else:
            criteria["wealth_group__community__isnull"] = True
        if product:
            criteria["product__cpc"] = product
        else:
            criteria["product__isnull"] = True

        return self.get(**criteria)


class WealthGroupCharacteristicValue(common_models.Model):
    """
    An attribute of a Wealth Group such as the number of school-age children.

    Stored on the BSS 'WB' worksheet, which contains many values for each Wealth Characteristic.

    The first set of columns contain values from the Community Interviews (Form 3).
    The second set of columns contain values from the Wealth Group Interviews in each Community (Form 4).
    The third set of columns contain the summary value and range that is considered representative for the Baseline,
    and is derived from the Community and Wealth Group Interviews as part of the baseline process.

    A Wealth Group Characteristic Value for a Baseline Wealth Group is always a Summary,
    but a Characteristic Value for a Community Wealth Group could be either from a
    Community Interview (Form 3) or a Wealth Group Interview (Form 4) with members
    of that specific Wealth Group.

    A Wealth Group Characteristic Value may have a Product and/or a Unit of Measure. For example, Wealth
    Characteristics related to the numbers or livestock owned will have a Product indicating the type of livestock.
    """

    # Note that the current model doesn't support data collected from a Wealth Group (Form 4) interview about a
    # different Wealth Group. The Form 4 breakdown of percentage of households in each Wealth Category Type that
    # was provided by a Wealth Group includes estimates of the percentage of households in the other Wealth Groups.
    # This is the only data in the BSS that cannot be loaded as a result of the current structure. We could support
    # this data by storing both the assessed_wealth_group_category and the interviewee_wealth_group_category. However,
    # Save the Children have confirmed that the Form 4 breakdown of percentage of households in each Wealth Category
    # Type is generally considered unreliable, and that there is a principle that Wealth Groups are not reliable
    # reporters of data about Wealth Groups other than their own.

    class CharacteristicReference(models.TextChoices):
        COMMUNITY = "community_interview", _("Community Interview (Form 3)")
        WEALTH_GROUP = "wealth_group_interview", _("Wealth Group Interview (Form 4)")
        SUMMARY = "baseline_summary", _("Baseline Summary")

    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.CASCADE, verbose_name=_("Wealth Group"))
    wealth_characteristic = models.ForeignKey(
        WealthCharacteristic,
        db_column="wealth_characteristic_code",
        on_delete=models.RESTRICT,
        verbose_name=_("Wealth Characteristic"),
    )
    reference_type = models.CharField(
        max_length=30,
        choices=CharacteristicReference.choices,
        db_index=True,
        verbose_name=_("Reference Type"),
        help_text=_(
            "The reference type of this Wealth Group Characteristic Value, such as a Community Interview (Form 3), "
            "Wealth Group Interview (Form 4) or the Baseline Summary"
        ),
    )
    product = models.ForeignKey(
        ClassifiedProduct,
        db_column="product_code",
        blank=True,
        null=True,
        on_delete=models.RESTRICT,
        verbose_name=_("Product"),
        help_text=_("Product, e.g. Cattle"),
        related_name="wealth_group_characteristic_values",
    )
    unit_of_measure = models.ForeignKey(
        UnitOfMeasure,
        db_column="unit_code",
        blank=True,
        null=True,
        on_delete=models.RESTRICT,
        verbose_name=_("Unit of Measure"),
        related_name="wealth_group_characteristic_values",
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
    # The Summary value for a Baseline Wealth Group also contains a min and max value for the Wealth Characteristic
    # E..g. See CD09_Final 'WB':$AS:$AT
    min_value = models.JSONField(
        verbose_name=_("min_value"),
        blank=True,
        null=True,
        help_text=_("The minimum value of the possible range for this value."),
    )
    max_value = models.JSONField(
        verbose_name=_("max_value"),
        blank=True,
        null=True,
        help_text=_("The maximum value of the possible range for this value."),
    )

    objects = WealthGroupCharacteristicValueManager()

    def clean(self):
        # Validate `reference_type`
        if self.reference_type == self.CharacteristicReference.SUMMARY:
            if self.wealth_group.community:
                raise ValidationError(
                    _(
                        "A Wealth Group Characteristic Value from a Baseline Summary must be for a Baseline Wealth Group"  # NOQA: E501
                    )
                )
        elif not self.wealth_group.community:
            raise ValidationError(
                _("A Wealth Group Characteristic Value from a %(ref)s must be for a Community Wealth Group")
                % {"ref": self.CharacteristicReference(self.reference_type).label}
            )
        # Validate `product`
        if self.wealth_characteristic.has_product:
            if not self.product:
                raise ValidationError(
                    _("A Wealth Group Characteristic Value for %(charac)s must have a product")
                    % {"charac": self.wealth_characteristic}
                )
        elif self.product:
            raise ValidationError(
                _("A Wealth Group Characteristic Value for %(charac)s must not have a product")
                % {"charac": self.wealth_characteristic}
            )
        # Validate `unit_of_measure`
        if self.wealth_characteristic.has_unit_of_measure:
            if not self.unit_of_measure:
                raise ValidationError(
                    _("A Wealth Group Characteristic Value for %(charac)s must have a unit of measure")
                    % {"charac": self.wealth_characteristic}
                )
        elif self.unit_of_measure:
            raise ValidationError(
                _("A Wealth Group Characteristic Value for %(charac)s must not have a unit of measure")
                % {"charac": self.CharacteristicReference(self.reference_type).label}
            )
        # Validate `value` is between min_value and max_value, if either are numerics (strings eg "1" not validated)
        if (
            isinstance(self.min_value, numbers.Number)
            and isinstance(self.value, numbers.Number)
            and self.min_value > self.value
        ):
            raise ValidationError(_("Value must be higher than min_value."))
        if (
            isinstance(self.max_value, numbers.Number)
            and isinstance(self.value, numbers.Number)
            and self.max_value < self.value
        ):
            raise ValidationError(_("Value must be lower than max_value."))
        super().clean()

    def save(self, *args, **kwargs):
        # No need to enforce foreign keys or uniqueness because database constraints will do it anyway
        self.full_clean(
            exclude=[field.name for field in self._meta.fields if isinstance(field, models.ForeignKey)],
            validate_unique=False,
        )
        super().save(*args, **kwargs)

    def natural_key(self):
        return (
            self.wealth_group.livelihood_zone_baseline.livelihood_zone_id,
            self.wealth_group.livelihood_zone_baseline.reference_year_end_date.isoformat(),
            self.wealth_group.wealth_group_category.code,
            self.wealth_characteristic_id,
            self.reference_type,
            self.product_id if self.product_id else "",
            self.wealth_group.community.full_name if self.wealth_group.community else "",
        )

    class Meta:
        verbose_name = _("Wealth Characteristic Value")
        verbose_name_plural = _("Wealth Characteristic Values")
        constraints = [
            # Create a unique constraint on wealth_group, wealth_characteristic, product and reference_type.
            # We can only have one value from each reference_type (Form 3, Form 4, Summary) for each Wealth Group
            # for each Characteristic (including the Product if appropriate).
            models.UniqueConstraint(
                fields=["wealth_group", "wealth_characteristic", "reference_type", "product"],
                name="baseline_wealthgroupcharacteristicvalue_group_characteristic_reference_type_product_uniq",
            ),
        ]


class LivelihoodStrategyManager(common_models.IdentifierManager):
    def get_by_natural_key(
        self,
        code: str,
        reference_year_end_date: str,
        strategy_type: str,
        season: str,
        product: str = "",
        additional_identifier: str = "",
    ):
        criteria = {
            "livelihood_zone_baseline__livelihood_zone__code": code,
            "livelihood_zone_baseline__reference_year_end_date": reference_year_end_date,
            "strategy_type": strategy_type,
            "additional_identifier": additional_identifier,
        }
        if season:
            criteria["season__name_en"] = season
            criteria["season__country"] = F("livelihood_zone_baseline__livelihood_zone__country")
        else:
            criteria["season__isnull"] = True
        if product:
            criteria["product__cpc"] = product
        else:
            criteria["product__isnull"] = True

        return self.get(**criteria)


class LivelihoodStrategy(common_models.Model):
    """
    An activity undertaken by households in a Livelihood Zone that produces food or income or requires expenditure.

    A Livelihood Strategy is not necessarily used by all Wealth Groups within the Livelihood Zone.

    Implicit in the BSS 'Data' worksheet in Column A.
    """

    livelihood_zone_baseline = models.ForeignKey(
        LivelihoodZoneBaseline,
        on_delete=models.CASCADE,
        related_name="livelihood_strategies",
        verbose_name=_("Livelihood Zone Baseline"),
    )
    # This also acts as a discriminator column for LivelihoodActivity
    strategy_type = models.CharField(
        max_length=30,
        choices=LivelihoodStrategyType.choices,
        db_index=True,
        verbose_name=_("Strategy Type"),
        help_text=_("The type of livelihood strategy, such as crop production, or wild food gathering."),
    )
    # Season is optional to allow for Livelihood Strategies that have equal distribution across the year,
    # such as purchase of tea and sugar, or remittances.
    season = models.ForeignKey(Season, blank=True, null=True, on_delete=models.PROTECT, verbose_name=_("Season"))
    # Product is optional to allow for Livelihood Strategies that don't have an obvious Product.
    # For example, many of the labor types in OtherCaseIncome are very specific and won't benefit from being
    # Products if we don't have any other data to cross-reference them with.
    product = models.ForeignKey(
        ClassifiedProduct,
        db_column="product_code",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_("Product"),
        help_text=_("Product, e.g. full fat milk"),
        related_name="livelihood_strategies",
    )
    unit_of_measure = models.ForeignKey(
        UnitOfMeasure,
        db_column="unit_code",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_("Unit of Measure"),
        help_text=_("Unit used to measure production from this Livelihood Strategy"),
    )
    currency = models.ForeignKey(
        Currency,
        db_column="currency_code",
        on_delete=models.PROTECT,
        verbose_name=_("Currency"),
        help_text=_("Currency of income or expenditure from this Livelihood Strategy"),
    )
    # In Somalia they track export/local sales separately - see SO18 Data:B178 and also B770
    # In many BSS they store separate data for Rainfed and Irrigated production of staple crops.
    # @TODO See https://fewsnet.atlassian.net/browse/HEA-67
    # Are there other types than rainfed and irrigated?
    additional_identifier = models.CharField(
        max_length=60,
        blank=True,
        verbose_name=_("Additional Identifer"),
        help_text=_("Additional text identifying the livelihood strategy"),
    )

    objects = LivelihoodStrategyManager()

    # List of Strategy Types that require a Product
    REQUIRES_PRODUCT = [
        "MilkProduction",
        "ButterProduction",
        "MeatProduction",
        "LivestockSale",
        "CropProduction",
        "OtherCashIncome",
        "WildFoodGathering",
    ]

    def clean(self):
        """
        Validate that product and season are not null for Livelihood Strategies that require them.
        """
        if self.strategy_type in self.REQUIRES_PRODUCT and not self.product:
            raise ValidationError(_("A %s Livelihood Strategy must have a Product" % self.strategy_type))
        if self.strategy_type in ["MilkProduction", "ButterProduction"] and not self.season:
            raise ValidationError(_("A %s Livelihood Strategy must have a Season" % self.strategy_type))
        super().clean()

    def save(self, *args, **kwargs):
        # No need to enforce foreign keys or uniqueness because database constraints will do it anyway
        self.full_clean(
            exclude=[field.name for field in self._meta.fields if isinstance(field, models.ForeignKey)],
            validate_unique=False,
        )
        super().save(*args, **kwargs)

    def natural_key(self):
        return (
            self.livelihood_zone_baseline.livelihood_zone_id,
            self.livelihood_zone_baseline.reference_year_end_date.isoformat(),
            self.strategy_type,
            self.season.name_en if self.season else "",
            self.product_id if self.product_id else "",
            self.additional_identifier,
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


class LivelihoodActivityManager(common_models.IdentifierManager):
    def get_by_natural_key(
        self,
        code: str,
        reference_year_end_date: str,
        wealth_group_category: str,
        strategy_type: str,
        season: str = "",
        product: str = "",
        additional_identifier: str = "",
        full_name: str = "",
    ):
        criteria = {
            "livelihood_zone_baseline__livelihood_zone__code": code,
            "livelihood_zone_baseline__reference_year_end_date": reference_year_end_date,
            "wealth_group__wealth_group_category__code": wealth_group_category,
            "strategy_type": strategy_type,
            "livelihood_strategy__additional_identifier": additional_identifier,
        }
        if season:
            criteria["livelihood_strategy__season__name_en"] = season
            criteria["livelihood_strategy__season__country"] = F("livelihood_zone_baseline__livelihood_zone__country")
        else:
            criteria["livelihood_strategy__season__isnull"] = True
        if product:
            criteria["livelihood_strategy__product__cpc"] = product
        else:
            criteria["livelihood_strategy__product__isnull"] = True
        if full_name:
            criteria["wealth_group__community__full_name"] = full_name
        else:
            criteria["wealth_group__community__isnull"] = True

        return self.get(**criteria)


class LivelihoodActivity(common_models.Model):
    """
    An activity undertaken by households in a Wealth Group that produces food or income or requires expenditure.

    A Livelihood Activity contains the outputs of a Livelihood Strategy
    employed by a Wealth Group in a Community in the reference year, or the
    outputs of a Wealth Group representing the Baseline as a whole in either
    the reference year (the Baseline scenario) or in response to a shock (the
    Response scenario).

    Stored on the BSS 'Data' worksheet.
    """

    livelihood_strategy = models.ForeignKey(
        LivelihoodStrategy, on_delete=models.CASCADE, help_text=_("Livelihood Strategy")
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
        choices=LivelihoodStrategyType.choices,
        db_index=True,
        verbose_name=_("Strategy Type"),
        help_text=_("The type of livelihood strategy, such as crop production, or wild food gathering."),
    )
    scenario = models.CharField(
        max_length=20,
        choices=LivelihoodActivityScenario.choices,
        verbose_name=_("Scenario"),
        help_text=_("The scenario in which the outputs of this Livelihood Activity apply, e.g. baseline or response."),
    )
    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.CASCADE, help_text=_("Wealth Group"))

    quantity_produced = models.PositiveIntegerField(blank=True, null=True, verbose_name=_("Quantity Produced"))
    quantity_purchased = models.PositiveIntegerField(blank=True, null=True, verbose_name=_("Quantity Purchased"))
    quantity_sold = models.PositiveIntegerField(blank=True, null=True, verbose_name=_("Quantity Sold/Exchanged"))
    quantity_other_uses = models.PositiveIntegerField(blank=True, null=True, verbose_name=_("Quantity Other Uses"))
    # Can normally be calculated / validated as `quantity_produced + quantity_purchased - quantity_sold - quantity_other_uses`  # NOQA: E501
    # but there are exceptions, such as MilkProduction, where there is also an amount used for ButterProduction
    quantity_consumed = models.PositiveIntegerField(blank=True, null=True, verbose_name=_("Quantity Consumed"))

    price = models.FloatField(blank=True, null=True, verbose_name=_("Price"), help_text=_("Price per unit"))
    # Can be calculated / validated as `quantity_sold * price` for livelihood strategies that involve the sale of
    # a proportion of the household's own production.
    income = models.FloatField(blank=True, null=True, help_text=_("Income"))
    # Can be calculated / validated as `quantity_purchased * price` for livelihood strategies that involve the purchase
    # of external goods or services.
    expenditure = models.FloatField(blank=True, null=True, help_text=_("Expenditure"))

    # Can normally be calculated  / validated as `quantity_consumed` * `kcals_per_unit`
    kcals_consumed = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Total kcals consumed"),
        help_text=_("Total kcals consumed by a household in the reference year from this livelihood strategy"),
    )
    # Can be calculated / validated as `total_kcals_consumed / DAILY_KCAL_REQUIRED (2100) / DAYS_PER_YEAR (365) / self.wealth_group.average_household_size`  # NOQA: E501
    # Note that although 2100 kcal per person per day is the WFP recommended amount,
    # some analyses may choose to use alternate thresholds and would need to calcuate
    # this value separately. For example, for program development some organizations
    # use 1900 kcal per person per day.
    percentage_kcals = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Percentage of required kcals"),
        help_text=_("Percentage of annual household kcal requirement provided by this livelihood strategy"),
    )

    # The 'Graphs' worksheet in NE01(BIL) and MG2 adds a `qui?` lookup in
    # Column F that tracks which household members are primarily responsible
    # for Livelihood Strategies that generate food and income.
    # Not all BSS track this, and it isn't tracked for expenditures, so
    # the field must be `blank=True`. If it is collected, then it is found in
    # the BSS 'Graphs' worksheet in column F. See NE01(BIL) for an example.
    # In its current location it is documented at the Livelihood Strategy-level.
    # However, we know from dicussions with Save the Children that in reality
    # the labor provider varies by wealth group category. Therefore, we store
    # this against the LivelihoodActivity, typically for Summary Livelihood
    # Activities only, with the same value for each Summary Wealth Group. In
    # future we may collect this data as part of Form 4, and store it for every
    # Wealth Group.
    class HouseholdLaborProvider(models.TextChoices):
        MEN = "men", _("Mainly Men")
        WOMEN = "women", _("Mainly Women")
        CHILDREN = "children", _("Mainly Children")
        ALL = "all", _("All Together")

    household_labor_provider = models.CharField(
        max_length=10, choices=HouseholdLaborProvider.choices, blank=True, verbose_name=_("Activity done by")
    )
    extra = models.JSONField(
        default=dict,
        blank=True,
        null=True,
        verbose_name=_("Extra attributes"),
        help_text=_("Additional attributes from the BSS for this Livelihood Activity"),
    )

    objects = LivelihoodActivityManager()

    def calculate_fields(self):
        self.livelihood_zone_baseline = self.livelihood_strategy.livelihood_zone_baseline
        self.strategy_type = self.livelihood_strategy.strategy_type

        # @TODO This hasn't been reviewed yet, and fix
        # self.is_staple = self.wealth_group.community.livelihood_zone_baseline.staple_set(
        #     item=self.output_item
        # ).exists()

    # These formulae are copied directly from the BSS cells:

    def validate_quantity_produced(self):
        """
        Validate the quantity_produced.

        In for many LivelihoodActivity subclasses the quantity_produced cannot
        be calculated from the data in the Baseline. In those cases this
        validation passes automatically.

        However, some LivelihoodActivity subclasses, such as MilkProduction,
        MeatProduction, etc. have additional fields that allow the
        quantity_produced to be validated. This method is overwritten in those
        subclasses.
        """
        pass

    def validate_quantity_consumed(self):
        # Default to 0 if any of the quantities are None
        quantity_produced = self.quantity_produced or 0
        quantity_sold = self.quantity_sold or 0
        quantity_other_uses = self.quantity_other_uses or 0

        # Calculate the expected quantity_consumed with default values considered
        expected_quantity_consumed = quantity_produced - quantity_sold - quantity_other_uses
        quantity_consumed = self.quantity_consumed or 0

        # Check if the actual quantity_consumed matches the expected quantity_consumed
        if self.quantity_consumed and quantity_consumed != expected_quantity_consumed:
            raise ValidationError(
                _(
                    "Quantity consumed for a Livelihood Activity must be quantity produced - quantity sold - quantity used for other things"  # NOQA: E501
                )
            )

    def validate_income(self):
        income = self.income or 0
        quantity_sold = self.quantity_sold or 0
        price = self.price or 0
        if self.income and income != quantity_sold * price:
            raise ValidationError(_("Income for a Livelihood Activity must be quantity sold multiplied by price"))

    def validate_expenditure(self):
        """
        Validate the expenditure.

        In for many LivelihoodActivity subclasses the quantity_produced is the
        result of labor rather than expenditure. In those cases this validation
        passes automatically.

        However, some LivelihoodActivity subclasses, such as FoodPurchase and
        OtherPurchase, involve spending money to acquire the item, in which
        case we must validate that expenditure = quantity_produced * price
        """
        quantity_produced = self.quantity_produced or 0
        price = self.price or 0
        expenditure = self.expenditure or 0

        if self.expenditure and expenditure != quantity_produced * price:
            raise ValidationError(
                _("Expenditure for a Livelihood Activity must be quantity produced multiplied by price")
            )

    def validate_kcals_consumed(self):
        conversion_factor = UnitOfMeasureConversion.objects.get_conversion_factor(
            from_unit=self.livelihood_strategy.unit_of_measure,
            to_unit=self.livelihood_strategy.product.unit_of_measure,
        )
        kcals_per_unit = self.livelihood_strategy.product.kcals_per_unit or 0
        quantity_consumed = self.quantity_consumed or 0
        kcals_consumed = self.kcals_consumed or 0
        if self.kcals_consumed and kcals_consumed != quantity_consumed * conversion_factor * kcals_per_unit:
            raise ValidationError(
                _("Kcals consumed for a Livelihood Activity must be quantity consumed multiplied by kcals per unit")
            )

    def validate_strategy_type(self):
        if (
            type(self) not in {LivelihoodActivity, BaselineLivelihoodActivity, ResponseLivelihoodActivity}
            and self.strategy_type != self._meta.object_name
        ):
            raise ValidationError(
                _(
                    f"Incorrect Livelihood Activity strategy type. Found {self.strategy_type}. Expected {self._meta.object_name}."  # NOQA: E501
                )
            )

    def validate_livelihood_zone_baseline(self):
        if not (
            self.wealth_group.livelihood_zone_baseline
            == self.livelihood_strategy.livelihood_zone_baseline
            == self.livelihood_zone_baseline
        ):
            raise ValidationError(
                _(
                    "Wealth Group and Livelihood Strategy for a Livelihood Activity must belong to the same Livelihood Zone Baseline"  # NOQA: E501
                )
            )

    # @TODO Do we use Django Forms as a separate validation layer, and load the data from the dataframe into a Form
    # instance and then check whether it is valid.  See Two Scoops for an explanation.
    def clean(self):
        self.validate_livelihood_zone_baseline()
        self.validate_strategy_type()
        self.validate_quantity_produced()
        self.validate_quantity_consumed()
        self.validate_income()
        self.validate_expenditure()
        self.validate_kcals_consumed()
        super().clean()

    def save(self, *args, **kwargs):
        self.calculate_fields()
        # No need to enforce foreign keys or uniqueness because database constraints will do it anyway
        self.full_clean(
            exclude=[field.name for field in self._meta.fields if isinstance(field, models.ForeignKey)],
            validate_unique=False,
        )
        super().save(*args, **kwargs)

    def natural_key(self):
        return (
            self.livelihood_zone_baseline.livelihood_zone_id,
            self.livelihood_zone_baseline.reference_year_end_date.isoformat(),
            self.wealth_group.wealth_group_category.code,
            self.strategy_type,
            self.livelihood_strategy.season.name_en if self.livelihood_strategy.season else "",
            self.livelihood_strategy.product_id if self.livelihood_strategy.product_id else "",
            self.livelihood_strategy.additional_identifier,
            self.wealth_group.community.full_name if self.wealth_group.community else "",
        )

    class Meta:
        verbose_name = _("Livelihood Activity")
        verbose_name_plural = _("Livelihood Activities")
        constraints = [
            # @TODO Add constraints either declared here or in a custom migration that target the composite foreign
            # keys for Wealth Group and Livelihood Strategy that include the livelihood_zone_baseline.
        ]

    class ExtraMeta:
        identifier = ["livelihood_strategy", "wealth_group", "scenario"]


class BaselineLivelihoodActivityManager(InheritanceManager):
    def get_queryset(self):
        return super().get_queryset().filter(scenario=LivelihoodActivityScenario.BASELINE).select_subclasses()


class BaselineLivelihoodActivity(LivelihoodActivity):
    """
    An activity undertaken by households in a Wealth Group that produces food or income or requires expenditure.

    A Baseline Livelihood Activity contains the outputs of a Livelihood Strategy
    employed by a Wealth Group in a Community or a Wealth Group representing
    the Baseline as a whole in the reference year.

    Stored on the BSS 'Data' worksheet.
    """

    objects = BaselineLivelihoodActivityManager()

    def clean(self):
        if self.scenario != LivelihoodActivityScenario.BASELINE:
            raise ValidationError(_("A Baseline Livelihood Activity must use the Baseline Scenario"))
        super().clean()

    class Meta:
        verbose_name = _("Baseline Livelihood Activity")
        verbose_name_plural = _("Baseline Livelihood Activities")
        proxy = True


class ResponseLivelihoodActivityManager(InheritanceManager):
    def get_queryset(self):
        return super().get_queryset().filter(scenario=LivelihoodActivityScenario.RESPONSE).select_subclasses()


class ResponseLivelihoodActivity(LivelihoodActivity):
    """
    An activity undertaken by households in a Wealth Group that produces food or income or requires expenditure.

    A Response Livelihood Activity contains the outputs of a Livelihood Strategy
    employed by a Wealth Group representing the Baseline as a whole during the
    response to a shock.

    Stored on the BSS 'Summ' worksheet.
    """

    # Note that the ResponseLivelihoodActivity contains the full set of attributes
    # for the Activity, including those values that are not explicitly entered
    # in the 'Summ' worksheet because they are implicitly inherited from the
    # matching BaselineLivelihoodActivity.
    objects = ResponseLivelihoodActivityManager()

    def clean(self):
        if self.scenario != LivelihoodActivityScenario.RESPONSE:
            raise ValidationError(_("A Response Livelihood Activity must use the Response Scenario"))
        super().clean()

    class Meta:
        verbose_name = _("Response Livelihood Activity")
        verbose_name_plural = _("Response Livelihood Activities")
        proxy = True


class MilkProduction(LivelihoodActivity):
    """
    Production of milk by households in a Wealth Group for their own consumption, for sale and for other uses.

    Stored on the BSS 'Data' worksheet in the 'Livestock Production' section, typically starting around Row 60.
    """

    class MilkType(models.TextChoices):
        SKIM = "skim", _("Skim")
        WHOLE = "whole", _("whole")

    # Production calculation /validation is `lactation days * daily_production`
    milking_animals = models.PositiveSmallIntegerField(verbose_name=_("Number of milking animals"))
    lactation_days = models.PositiveSmallIntegerField(
        blank=True, null=True, verbose_name=_("Average number of days of lactation")
    )
    daily_production = models.PositiveSmallIntegerField(
        blank=True, null=True, verbose_name=_("Average daily milk production per animal")
    )

    # @TODO see https://fewsnet.atlassian.net/browse/HEA-65
    # This is currently not required for scenario development and is only used for the kcal calculations in the BSS.
    # Save the Children confirmed that most communities consume Whole Milk, and then either sell Whole Milk, or make
    # Butter/Ghee and then sell the remaining Skim Milk (and also sell some proportion of the Butter/Ghee). The
    # current structure of the BSS supports these Livelihood Strategies. However, Save the Children have also confirmed
    # that  as a coping strategy a wealth group might choose to make butter from whole milk, consume skimmed milk
    # themselves, to ensure that they can sell more butter/ghee. To support this Livelihood Strategy we have added
    # `type_of_milk_consumed` even though this field isn't currently in the BSS. Records loaded from historic BSS
    # will have `type_of_milk_consumed = "whole"`.
    # Similarly, although the current BSS structure doesn't store explictly the amount of milk used to make butter. it
    # is implicit in the formula used to calculate the amount of butter produced, but we store it as a separate field.
    # It is also possible that a community will consume some amount of total milk production as whole milk, then make
    # butter, and then consume some amount of the resulting skimmed milk and sell the rest. It is not clear whether the
    # data collection process will be able accurately capture this level of detail, and we don't support it in the
    # current approach using a single MilkProduction and ButterProduction LivelihoodActivity for each animal. Should
    # this be required in the future, one approach would be to create a second MilkProduction LivelihoodActivity with a
    # product for the animal-specific skimmed milk, e.g. new products under P22212 - see
    # https://unstats.un.org/unsd/classifications/Econ/Detail/EN/1074/22110. That LivelihoodActivity would have a
    # `quantity_produced` equal to the amount of whole milk that was used for ButterProduction, and then the
    # quantity_sold and the quantity_consumed could be tracked separately.
    quantity_butter_production = models.PositiveIntegerField(
        blank=True, null=True, verbose_name=_("Quantity used for Butter Production")
    )  # NOQA: E501
    type_of_milk_consumed = models.CharField(
        max_length=10, choices=MilkType.choices, verbose_name=_("Skim or whole milk consumed")
    )
    type_of_milk_sold_or_other_uses = models.CharField(
        max_length=10, choices=MilkType.choices, verbose_name=_("Skim or whole milk sold or used for other purposes")
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
    def validate_quantity_produced(self):
        # @TODO Add validation
        pass

    def clean(self):
        super().clean()
        if self.milking_animals and not self.lactation_days:
            raise ValidationError(_("Lactation days must be provided if there are milking animals"))
        if self.milking_animals and not self.daily_production:
            raise ValidationError(_("Daily production must be provided if there are milking animals"))

    class Meta:
        verbose_name = LivelihoodStrategyType.MILK_PRODUCTION.label
        verbose_name_plural = LivelihoodStrategyType.MILK_PRODUCTION.label


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

    def validate_quantity_produced(self):
        # @TODO Add validation
        pass

    class Meta:
        verbose_name = LivelihoodStrategyType.BUTTER_PRODUCTION.label
        verbose_name_plural = LivelihoodStrategyType.BUTTER_PRODUCTION.label
        proxy: True


class MeatProduction(LivelihoodActivity):
    """
    Production of meat by households in a Wealth Group for their own consumption.

    Stored on the BSS 'Data' worksheet in the 'Livestock Production' section, typically starting around Row 172.
    """

    # Production calculation /validation is `input_quantity` * `item_yield`
    animals_slaughtered = models.PositiveSmallIntegerField(verbose_name=_("Number of animals slaughtered"))
    carcass_weight = models.FloatField(verbose_name=_("Carcass weight per animal"))

    def validate_quantity_produced(self):
        if self.quantity_produced != self.animals_slaughtered * self.carcass_weight:
            raise ValidationError(
                _("Quantity Produced for a Meat Production must be animals slaughtered multiplied by carcass weight")
            )

    class Meta:
        verbose_name = LivelihoodStrategyType.MEAT_PRODUCTION.label
        verbose_name_plural = LivelihoodStrategyType.MEAT_PRODUCTION.label


class LivestockSale(LivelihoodActivity):
    """
    Sale of livestock by households in a Wealth Group for cash income.

    Stored on the BSS 'Data' worksheet in the 'Livestock Production' section, typically starting around Row 181.
    """

    # @TODO Do we need validation around offtake (animals_sold) to make sure
    # that they are not selling and killing more animals than they own.
    class Meta:
        verbose_name = LivelihoodStrategyType.LIVESTOCK_SALE.label
        verbose_name_plural = _("Livestock Sales")
        proxy = True


class CropProduction(LivelihoodActivity):
    """
    Production of crops by households in a Wealth Group for their own consumption, for sale and for other uses.

    Stored on the BSS 'Data' worksheet in the 'Crop Production' section, typically starting around Row 221.

    This includes consumption of Green Maize, where we need to reverse engineer the quantity produced from the
    provided kcal_percentage and the kcal/kg.
    """

    class Meta:
        verbose_name = LivelihoodStrategyType.CROP_PRODUCTION.label
        verbose_name_plural = LivelihoodStrategyType.CROP_PRODUCTION.label
        proxy = True


class FoodPurchase(LivelihoodActivity):
    """
    Purchase of food items that contribute to nutrition by households in a Wealth Group.

    Stored on the BSS 'Data' worksheet in the 'Food Purchase' section, typically starting around Row 421.
    """

    # Production calculation/validation is `unit_of_measure * unit_multiple * times_per_month  * months_per_year`
    # Do we need this, or can we use combined units of measure like FDW, e.g. 5kg
    # NIO93 Row B422 tia = 2.5kg
    unit_multiple = models.PositiveSmallIntegerField(
        verbose_name=_("Unit Multiple"), help_text=_("Multiple of the unit of measure in a single purchase")
    )
    # This is a float field because data may be captured as "once per week",
    # which equates to "52 per year", which is "4.33 per month".
    times_per_month = models.FloatField(verbose_name=_("Purchases per month"))
    months_per_year = models.PositiveSmallIntegerField(
        verbose_name=_("Months per year"), help_text=_("Number of months in a year that the product is purchased")
    )
    times_per_year = models.PositiveSmallIntegerField(
        verbose_name=_("Times per year"),
        help_text=_("Number of times in a year that the purchase is made"),
    )

    def validate_quantity_produced(self):
        if self.quantity_produced != self.unit_multiple * self.times_per_month * self.months_per_year:
            raise ValidationError(
                _(
                    "Quantity produced for a Food Purchase must be purchase amount * purchases per month * months per year"  # NOQA: E501
                )
            )

    class Meta:
        verbose_name = LivelihoodStrategyType.FOOD_PURCHASE.label
        verbose_name_plural = _("Food Purchases")


class PaymentInKind(LivelihoodActivity):
    """
    Food items that contribute to nutrition by households in a Wealth Group received in exchange for labor.

    Stored on the BSS 'Data' worksheet in the 'Payment In Kind' section, typically starting around Row 514.
    """

    # Production calculation/validation is `people_per_household * times_per_month * months_per_year`
    payment_per_time = models.PositiveSmallIntegerField(
        verbose_name=_("Payment per time"), help_text=_("Amount of item received each time the labor is performed")
    )
    people_per_household = models.PositiveSmallIntegerField(
        verbose_name=_("People per household"), help_text=_("Number of household members who perform the labor")
    )
    # This is a float field because data may be captured as "once per week",
    # which equates to "52 per year", which is "4.33 per month".
    times_per_month = models.FloatField(verbose_name=_("Labor per month"))
    months_per_year = models.PositiveSmallIntegerField(
        verbose_name=_("Months per year"), help_text=_("Number of months in a year that the labor is performed")
    )
    times_per_year = models.PositiveSmallIntegerField(
        verbose_name=_("Times per year"),
        help_text=_("Number of times in a year that the labor is performed"),
    )

    def validate_quantity_produced(self):
        if (
            self.quantity_produced
            and self.quantity_produced
            != self.payment_per_time * self.people_per_household * self.times_per_month * self.months_per_year
        ):
            raise ValidationError(
                _(
                    "Quantity produced for Payment In Kind must be payment per time * number of people * labor per month * months per year"  # NOQA: E501
                )
            )

    class Meta:
        verbose_name = LivelihoodStrategyType.PAYMENT_IN_KIND.label
        verbose_name_plural = _("Payments in Kind")


class ReliefGiftOther(LivelihoodActivity):
    """
    Food items that contribute to nutrition received by households in a Wealth Group as relief, gifts, etc.
    and which are not bought or exchanged.

    Stored on the BSS 'Data' worksheet in the 'Relief, Gifts and Other' section, typically starting around Row 533.
    """

    # Production calculation /validation is `unit_of_measure * unit_multiple * times_per_year`
    unit_multiple = models.PositiveSmallIntegerField(
        verbose_name=_("Unit Multiple"), help_text=_("Multiple of the unit of measure received each time")
    )
    # This is a float field because data may be captured as "once per week",
    # which equates to "52 per year", which is "4.33 per month".
    times_per_month = models.FloatField(
        blank=True, null=True, verbose_name=_("Number of times per month the item is received")
    )
    months_per_year = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Months per year"),
        help_text=_("Number of months in a year that the item is received"),
    )
    times_per_year = models.PositiveSmallIntegerField(
        verbose_name=_("Times per year"), help_text=_("Number of times in a year that the item is received")
    )

    def validate_quantity_produced(self):
        if self.quantity_produced != self.unit_multiple * self.times_per_year:
            raise ValidationError(
                _("Quantity produced for Relief, Gifts, Other must be amount received * times per year")
            )

    class Meta:
        verbose_name = LivelihoodStrategyType.RELIEF_GIFT_OTHER.label
        verbose_name_plural = _("Relief, Gifts and Other Food")


class Hunting(LivelihoodActivity):
    """
    Hunting by some households in a Wealth Group for their own consumption, for sale and for other uses.
    Some BSS have hunting on the Data3 tab, for example, Madagascar/MG23

    Stored on the BSS 'Data3' worksheet in the 'Hunting' (Chasse) section, typically starting around Row 48
    """

    class Meta:
        verbose_name = LivelihoodStrategyType.HUNTING.label
        verbose_name_plural = LivelihoodStrategyType.HUNTING.label
        proxy = True


class Fishing(LivelihoodActivity):
    """
    Fishing by households in a Wealth Group for their own consumption, for sale and for other uses.

    Stored on the BSS 'Data3' worksheet in the 'Fishing' section, typically starting around Row 48
    and summarized in the 'Data' worksheet in the 'Wild Foods' section, typically starting around Row 550.
    """

    class Meta:
        verbose_name = LivelihoodStrategyType.FISHING.label
        verbose_name_plural = LivelihoodStrategyType.FISHING.label
        proxy = True


class WildFoodGathering(LivelihoodActivity):
    """
    Gathering of wild food by households in a Wealth Group for their own consumption, for sale and for other uses.

    Stored on the BSS 'Data3' worksheet in the Wild Foods section, typically starting around Row 9
    and summarized in the 'Data' worksheet in the Wild Foods section, typically starting around Row 560.
    """

    class Meta:
        verbose_name = LivelihoodStrategyType.WILD_FOOD_GATHERING.label
        verbose_name_plural = LivelihoodStrategyType.WILD_FOOD_GATHERING.label
        proxy = True


class OtherCashIncome(LivelihoodActivity):
    """
    Income received by households in a Wealth Group as payment for labor or from self-employment, remittances, etc.

    Stored on the BSS 'Data2' worksheet and summarized in the 'Data' worksheet in the 'Other Cash Income' section,
    typically starting around Row 580.
    """

    # Production calculation/validation is `people_per_household * times_per_month * months_per_year`
    # However, some other income (e.g. Remittances) just has a number of times per year and is not calculated from
    # people_per_household, etc. Therefore those fields must be nullable, and we must store the total number of times
    # per year as a separate field
    payment_per_time = models.PositiveSmallIntegerField(
        verbose_name=_("Payment per time"), help_text=_("Amount of money received each time the labor is performed")
    )
    people_per_household = models.PositiveSmallIntegerField(
        verbose_name=_("People per household"),
        blank=True,
        null=True,
        help_text=_("Number of household members who perform the labor"),
    )
    # This is a float field because data may be captured as "once per week",
    # which equates to "52 per year", which is "4.33 per month".
    times_per_month = models.FloatField(blank=True, null=True, verbose_name=_("Labor per month"))
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

    def validate_income(self):
        if (
            self.people_per_household
            and self.income
            != self.payment_per_time * self.people_per_household * self.times_per_month * self.months_per_year
        ):
            raise ValidationError(
                _(
                    "Quantity produced for Other Cash Income must be payment per time * number of people * labor per month * months per year"  # NOQA: E501
                )
            )
        if self.income != self.payment_per_time * self.times_per_year:
            raise ValidationError(
                _("Quantity produced for Other Cash Income must be payment per time * times per year")
            )

    def calculate_fields(self):
        self.times_per_year = self.people_per_household * self.times_per_month * self.months_per_year
        super().calculate_fields()

    class Meta:
        verbose_name = LivelihoodStrategyType.OTHER_CASH_INCOME.label
        verbose_name_plural = LivelihoodStrategyType.OTHER_CASH_INCOME.label


class OtherPurchase(LivelihoodActivity):
    """
    Expenditure by households in a Wealth Group on items that don't contribute to nutrition.

    Stored on the BSS 'Data' worksheet in the 'Other Purchases' section, typically starting around Row 646.
    """

    # Production calculation/validation is `unit_of_measure * unit_multiple * times_per_month  * months_per_year`
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
    # This is a float field because data may be captured as "once per week",
    # which equates to "52 per year", which is "4.33 per month".
    times_per_month = models.FloatField(blank=True, null=True, verbose_name=_("Purchases per month"))
    months_per_year = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name=_("Months per year"),
        help_text=_("Number of months in a year that the product is purchased"),
    )
    times_per_year = models.PositiveSmallIntegerField(
        verbose_name=_("Times per year"),
        help_text=_("Number of times in a year that the product is purchased"),
    )

    def validate_expenditure(self):
        if self.expenditure != self.price * self.unit_multiple * self.times_per_month * self.months_per_year:
            raise ValidationError(
                _(
                    "Expenditure for Other Purchases must be price * unit multiple * purchases per month * months per year"  # NOQA: E501
                )
            )

    class Meta:
        verbose_name = LivelihoodStrategyType.OTHER_PURCHASE.label
        verbose_name_plural = _("Other Purchases")


class SeasonalActivity(common_models.Model):
    """
    An activity or event undertaken/experienced by households in a Livelihood Zone at specific periods during the year.

    Implicit in the BSS 'Seas Cal' worksheet in Column A, if present.
    """

    # @TODO Should a Seasonal Activity have a foreign key (maybe optional) to a
    # LivelihoodStrategy? Logically such a thing exists - the BSS contains
    # seasonal activities related to growing Maize, and a livelihood strategy
    # for growing maize. It might also have to be a ManyToManyField because if
    # we have seasonal activities related to, say, sheep, then the livelihood
    # strategies for Sheep Milk Production, Sheep Livestock Production and
    # Sheep Sales would all be related.

    livelihood_zone_baseline = models.ForeignKey(
        LivelihoodZoneBaseline,
        on_delete=models.RESTRICT,
        related_name="baseline_seasonal_activities",
        verbose_name=_("Livelihood Zone Baseline"),
    )
    seasonal_activity_type = models.ForeignKey(
        SeasonalActivityType,
        db_column="seasonal_activity_type_code",
        on_delete=models.RESTRICT,
        verbose_name=_("Seasonal Activity Type"),
    )
    # A Seasonal Activity, such as Land Preparation can cover multiple seasons,
    # and obviously a Season can contain many Seasonal Activities, therefore
    # this must be M:M. Furthermore, although logically a Seasonal Activity
    # occurs in a particular time of year, and therefore can be linked to a
    # Season (or Seasons), that link is not explicit in historic BSS, and
    # therefore we may choose not to load it, at least to start with.
    # Therefore, the relationship must be optional.
    season = models.ManyToManyField(Season, verbose_name=_("Season"))
    product = models.ForeignKey(
        ClassifiedProduct,
        db_column="product_code",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_("Product"),
        help_text=_("Product, e.g. full fat milk"),
        related_name="baseline_seasonal_activities",
    )
    additional_identifier = models.CharField(
        max_length=60,
        blank=True,
        verbose_name=_("Additional Identifier"),
        help_text=_("Additional text identifying the seasonal activity"),
    )

    class Meta:
        verbose_name = _("Seasonal Activity")
        verbose_name_plural = _("Seasonal Activities")
        constraints = [
            # Create a unique constraint on id and livelihood_zone_baseline, so that we can use it as a target for a
            # composite foreign key from Seasonal Activity Ocurrence, which in turn allows us to ensure that the
            # Community and the Seasonal Activity for a Seasonal Activity Occurrence have the same Livelihood Baseline.
            models.UniqueConstraint(
                fields=["id", "livelihood_zone_baseline"],
                name="baseline_seasonalactivity_id_livelihood_zone_baseline_uniq",
            ),
        ]

    class ExtraMeta:
        identifier = ["livelihood_zone_baseline", "seasonal_activity_type", "product"]


class SeasonalActivityOccurrence(common_models.Model):
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
    # If Community is specified then the Seasonal Activity Occurrence contains the period
    # that the Activity occurred, as reported by that Community. If the Community is null,
    # then the Seasonal Activity Occurrence represents the consolidated and reconciled period
    # for that Seasonal Activity that is representative for the Livelihood Zone Baseline.
    community = models.ForeignKey(
        Community, blank=True, null=True, on_delete=models.RESTRICT, verbose_name=_("Community or Village")
    )

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
        return get_month_from_day_number(self.start)

    def end_month(self):
        return get_month_from_day_number(self.end)

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
            # keys for Community and Seasonal Activity that include the livelihood_zone_baseline.
        ]


# @TODO https://fewsnet.atlassian.net/browse/HEA-91
# What is this used for?
class CommunityCropProduction(common_models.Model):
    """
    The community crop production data for a crop producing community
    Form 3's CROP PRODUCTION is used for community-level interviews
    And the data goes to the BSS's 'Production' worksheet
    """

    # @TODO  CropPurpose is referring the 'Main food & cash crops...' in Form 3,
    #  but the BSS doesn't seem to contain this, should we keep this?
    class CropPurpose(models.TextChoices):
        FOOD = "food", _("Main Food Crop")
        CASH = "cash", _("Cash Crop")

    community = models.ForeignKey(Community, on_delete=models.RESTRICT, verbose_name=_("Community or Village"))
    crop = models.ForeignKey(
        ClassifiedProduct, db_column="crop_code", on_delete=models.RESTRICT, verbose_name=_("Crop Type")
    )
    crop_purpose = models.CharField(max_length=20, choices=CropPurpose.choices, verbose_name=_("Crop purpose"))
    # Although logically Crop Production must belong to a specific Season, that
    # link is not explicit in historic BSS, and therefore we may choose not to
    # load it, at least to start with. Therefore, the relationship must be optional.
    season = models.ForeignKey(Season, blank=True, null=True, on_delete=models.RESTRICT, verbose_name=_("Season"))
    yield_with_inputs = models.FloatField(
        verbose_name=_("Yield with inputs"),
        help_text=_("Yield in reference period with inputs (seeds and fertilizer)"),
    )
    yield_without_inputs = models.FloatField(
        verbose_name=_("Yield without inputs"),
        help_text=_("Yield in reference period without inputs (seeds and fertilizer)"),
    )
    seed_requirement = models.FloatField(verbose_name=_("Seed requirement"))
    crop_unit_of_measure = models.ForeignKey(
        UnitOfMeasure,
        db_column="crop_unit_code",
        on_delete=models.RESTRICT,
        related_name="crop_production_crop",
        verbose_name=_("Crop Unit of Measure"),
    )
    land_unit_of_measure = models.ForeignKey(
        UnitOfMeasure,
        db_column="land_unit_code",
        on_delete=models.RESTRICT,
        related_name="crop_production_land",
        verbose_name=_("Land Unit of Measure"),
    )

    # @TODO We need to store the harvest month for each crop, because it is needed
    # to calculate the per month food, income and expenditure shown in Table 4 of the LIAS Sheet S

    # @TODO Do we need to add UnitOfMeasure and parse it out of `6x50kg bags`, etc. or can we just store it as text.

    def clean(self):
        if not self.crop_id.startswith("R01"):
            raise ValidationError(
                _(
                    "Crop type for Community Crop Production must have a CPC code code beginning R01 (Agriculture Products)"  # NOQA: E501
                )
            )
        super().clean()

    def save(self, *args, **kwargs):
        # No need to enforce foreign keys or uniqueness because database constraints will do it anyway
        self.full_clean(
            exclude=[field.name for field in self._meta.fields if isinstance(field, models.ForeignKey)],
            validate_unique=False,
        )
        super().save(*args, **kwargs)

    class ExtraMeta:
        identifier = ["community", "crop"]

    class Meta:
        verbose_name = _("Community Crop Production")
        verbose_name_plural = _("Community Crop Productions")


# @TODO Are these fields from Form 3 required here on CommunityLivestock,
# or are they on WealthGroupLivestock as a result of the repition on Form 4
# These worksheets are locked in the BSS. They are important reference data even
# if the WealthGroup-level values are used for calculations.
class CommunityLivestock(common_models.Model):
    """
    An animal typically raised by households in a Community, with revelant additional attributes.

    This data is typically captured in Form 3 and stored in the Production worksheet in the BSS.
    """

    # @TODO It is probably not worth loading this data, it is never extracted as far as we can tell.
    # And it is filled in irregularly, e.g. MWBPH_30Sep15

    community = models.ForeignKey(Community, on_delete=models.CASCADE, verbose_name=_("Wealth Group"))
    livestock = models.ForeignKey(
        ClassifiedProduct, db_column="livestock_code", on_delete=models.RESTRICT, verbose_name=_("Livestock Type")
    )
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
    additional_attributes = models.JSONField(blank=True, null=True, verbose_name=_("Additional Attributes"))

    def clean(self):
        if not self.livestock_id.startswith("L021"):
            raise ValidationError(
                _("Livestock type for Community Livestock must have a CPC code code beginning L021 (Live animals)")
            )
        super().clean()

    def save(self, *args, **kwargs):
        # No need to enforce foreignf keys or uniqueness because database constraints will do it anyway
        self.full_clean(
            exclude=[field.name for field in self._meta.fields if isinstance(field, models.ForeignKey)],
            validate_unique=False,
        )
        super().save(*args, **kwargs)

    class ExtraMeta:
        identifier = ["community", "livestock"]

    class Meta:
        verbose_name = _("Community Livestock")
        verbose_name_plural = _("Community livestock")


class MarketPrice(common_models.Model):
    """
    Prices for the reference year are interviewed in Form 3

    Stored on the BSS 'Prices' worksheet.
    """

    community = models.ForeignKey(Community, on_delete=models.RESTRICT, verbose_name=_("Community or Village"))
    product = models.ForeignKey(
        ClassifiedProduct,
        db_column="product_code",
        on_delete=models.RESTRICT,
        related_name="market_prices",
        verbose_name=_("Product"),
        help_text=_("Product, e.g. full fat milk"),
    )
    # Sometimes the BSS has "farmgate" or "within the village" or "locally" as
    # the market. For example, MWSLA_30Sep15 (https://docs.google.com/spreadsheets/d/1AX6GGt7S1wAP_NlTBBK8FKbCN4kImgzY/edit#gid=2078095544)  # NOQA: E501
    # @TODO Should the market be nullable, or should we have a Market with the
    # same name and geography as the Community when that happens.
    market = models.ForeignKey(Market, blank=True, null=True, on_delete=models.RESTRICT)
    description = common_models.DescriptionField(max_length=100)
    currency = models.ForeignKey(
        Currency, db_column="currency_code", on_delete=models.RESTRICT, verbose_name=_("Currency")
    )
    unit_of_measure = models.ForeignKey(
        UnitOfMeasure, db_column="unit_code", on_delete=models.RESTRICT, verbose_name=_("Unit of Measure")
    )
    # We use day in the year instead of month to allow greater granularity,
    # and compatibility with the potential FDW Enhanced Crop Calendar output.
    # Note that if the occurrence goes over the year end, then the start day
    # will be larger than the end day.
    low_price_start = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(365), MinValueValidator(1)], verbose_name=_("Low Price Start Day")
    )
    low_price_end = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(365), MinValueValidator(1)], verbose_name=_("Low Price End Day")
    )
    low_price = models.FloatField(verbose_name=_("Low price"))
    high_price_start = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(365), MinValueValidator(1)], verbose_name=_("High Price Start Day")
    )
    high_price_end = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(365), MinValueValidator(1)], verbose_name=_("High Price End Day")
    )
    high_price = models.FloatField(verbose_name=_("High price"))

    def low_price_start_month(self):
        return get_month_from_day_number(self.low_price_start)

    def low_price_end_month(self):
        return get_month_from_day_number(self.low_price_end)

    def high_price_start_month(self):
        return get_month_from_day_number(self.high_price_start)

    def high_price_end_month(self):
        return get_month_from_day_number(self.high_price_end)

    class Meta:
        verbose_name = _("Market Price")
        verbose_name_plural = _("Market Prices")


# @TODO Ask Save what to call this
class SeasonalProductionPerformance(common_models.Model):
    """
    Relative production performance experienced in a specific season / year.

    Most BSSs contain the performance for the year as a whole and will use a
    'Main' or 'Annual' season. However, in Livelilood Zones with bimodal
    rainfall we can capture performance for each season individually.

    Stored on the BSS 'Timeline' worksheet based on responses to the Form 3.
    """

    class Performance(models.IntegerChoices):
        VERY_POOR = 1, _("Very Poor")
        POOR = 2, _("Poor")
        MEDIUM = 3, _("Medium")
        GOOD = 4, _("Good")
        VERY_GOOD = 5, _("Very Good")

    community = models.ForeignKey(Community, on_delete=models.RESTRICT, verbose_name=_("Community or Village"))
    season = models.ForeignKey(Season, on_delete=models.PROTECT, verbose_name=_("Season"))
    performance_year_start_date = models.DateField(
        verbose_name=_("Performance Year Start Date"),
        help_text=_("The first day of the month of the start month in the performance year"),
    )
    performance_year_end_date = models.DateField(
        verbose_name=_("Performance Year End Date"),
        help_text=_("The last day of the month of the end month in the performance year"),
    )
    seasonal_performance = models.SmallIntegerField(
        choices=Performance.choices,
        validators=[
            MinValueValidator(1, message="Performance rating must be at least 1."),
            MaxValueValidator(5, message="Performance rating must be at most 5."),
        ],
        verbose_name=_("Seasonal Performance"),
        help_text=_("Rating of the seasonal production performance from Very Poor (1) to Very Good (5)"),
    )

    class Meta:
        verbose_name = _("Seasonal Production Performance")
        verbose_name_plural = _("Seasonal Production Performance")


class Hazard(common_models.Model):
    """
    A shock such as drought, flood, conflict or market disruption which is likely
    to have an impact on people’s livelihoods.

    Hazards can be Chronic (every year) or Periodic hazards (not every year).

    Stored on the BSS 'Timeline' worksheet based on responses to the Form 3.
    """

    class ChronicOrPeriodic(models.TextChoices):
        CHRONIC = "chronic", _("Chronic")
        PERIODIC = "periodic", _("Periodic")

    # @TODO Is this risk, likelihood or impact?
    class HazardRanking(models.IntegerChoices):
        MOST_IMPORTANT = 1, _("Most Important")
        IMPORTANT = 2, _("Important")
        LESS_IMPORTANT = 3, _("Less Important")

    community = models.ForeignKey(Community, on_delete=models.RESTRICT, verbose_name=_("Community or Village"))
    chronic_or_periodic = models.CharField(
        max_length=10, choices=ChronicOrPeriodic.choices, verbose_name=_("Chronic or Periodic")
    )
    ranking = models.PositiveSmallIntegerField(
        choices=HazardRanking.choices,
        validators=[
            MinValueValidator(1, message="Performance rank must be at least 1."),
            MaxValueValidator(5, message="Performance rank must be at most 5."),
        ],
        verbose_name=_("Ranking"),
    )
    hazard_category = models.ForeignKey(
        HazardCategory, db_column="hazard_category_code", on_delete=models.RESTRICT, verbose_name=_("Hazard Category")
    )
    # @TODO MG23 https://docs.google.com/spreadsheets/d/18Y85UKXGehudt2YX5Oc_adw2TUxo6nY7/edit#gid=1565100920
    # contains additional information on Events and Responses by year in the Timeline worksheet.
    description = common_models.DescriptionField(
        max_length=255, verbose_name=_("Description of Event(s) and/or Response(s)")
    )

    class Meta:
        verbose_name = _("Hazard")
        verbose_name_plural = _("Hazards")


class Event(common_models.Model):
    """
    A shock such as drought, flood, conflict or market disruption which
    happened in a recent year prior to the reference year.

    Stored on the BSS 'Timeline' worksheet based on responses to the Form 3.
    """

    # See, for example, MG23.
    # SN05 also contains Events, but they are stored in the Seasonal Production Performance section.
    # Although logically Events can be split into Shocks and Responses, the way in the data is
    # currently stored in the BSSs doesn't support easy identification of the different types.
    # Therefore we store everything as an Event for now. We may choose to add a discriminator
    # column, i.e. `shock_or_response` if changes in the data collection process support easy
    # identification in the future.
    # Save the Children confirmed that a Periodic Hazard is a hazard that occurred in the Reference Year,
    # but which isn't a Chronic Hazard. There is logically some overlap between Perodic Hazards and Events,
    # but for now we load them into separate models so that users can find data in the places they are
    # expecting it.
    community = models.ForeignKey(Community, on_delete=models.RESTRICT, verbose_name=_("Community or Village"))
    # The `event_year_start_date` and the `event_year_end_date` should match
    # the day and month of the `reference_year`. For example if the
    # `reference_year_end_date` is 2020-09-30, then the event year might be
    # 2017-10-10 through 2018-09-30.
    event_year_start_date = models.DateField(
        verbose_name=_("Event Year Start Date"),
        help_text=_("The first day of the month of the start month in the event year"),
    )
    event_year_end_date = models.DateField(
        verbose_name=_("Event Year End Date"),
        help_text=_("The last day of the month of the end month in the event year"),
    )
    description = common_models.DescriptionField(
        max_length=255, verbose_name=_("Description of Event(s) and/or Response(s)")
    )

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")


class ExpandabilityFactor(models.Model):
    """
    The percentage of the quantity sold, income or expenditure which applies
    to a Livelihood Strategy in a response scenario.

    Stored on the BSS 'Exp factors' worksheet.
    """

    livelihood_strategy = models.ForeignKey(
        LivelihoodStrategy, on_delete=models.PROTECT, help_text=_("Livelihood Strategy")
    )
    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.RESTRICT, verbose_name=_("Wealth Group"))

    # @TODO make these percentages
    percentage_produced = models.PositiveIntegerField(blank=True, null=True, verbose_name=_("Quantity Produced"))
    percentage_sold = models.PositiveIntegerField(blank=True, null=True, verbose_name=_("Quantity Sold/Exchanged"))
    percentage_other_uses = models.PositiveIntegerField(blank=True, null=True, verbose_name=_("Quantity Other Uses"))
    # Can normally be calculated / validated as `quantity_received - quantity_sold - quantity_other_uses`
    percentage_consumed = models.PositiveIntegerField(blank=True, null=True, verbose_name=_("Quantity Consumed"))

    # Can be calculated / validated as `quantity_sold * price` for livelihood strategies that involve the sale of
    # a proportion of the household's own production.
    percentage_income = models.FloatField(blank=True, null=True, help_text=_("Income"))
    # Can be calculated / validated as `quantity_consumed * price` for livelihood strategies that involve the purchase
    # of external goods or services.
    percentage_expenditure = models.FloatField(blank=True, null=True, help_text=_("Expenditure"))

    # Sheet G contains some texts that seems describing where data is coming from, mostly 'Summ' sheet
    remark = models.TextField(max_length=255, verbose_name=_("Remark"), null=True, blank=True)

    class Meta:
        verbose_name = _("Expandability Factor")
        verbose_name_plural = _("Expandability Factor")


class CopingStrategy(models.Model):
    """
    The capacity of households to diversify and expand access to various sources of food and income,
    and thus to cope with a specified hazard

    Captured in the 'Coping' Sheet of the BSS whenever available

    Notably this sheet is not found in most BSSs, and whenever there is, the data seems an inconsistent text
    as opposed to the expected numeric values, and this may require us to parse the text during ingestion

    Coping Strategy also is better analysed during the outcome analysis stage, by taking into account the
    exact hazard/shock,

    In addition, at times in the literature, Coping seems used synonymous to Expandability,
    however it seems suitable to model the data in 'Coping' sheet - see Practitioners' guide page 137
    """

    # @TODO it is likely that the coping strategies are more formally modeled in the LIAS
    # and it would be better to update this model to resolve this and the other comments below,
    # before attempting load data into this model.
    # @TODO although this model currently has separate foreign keys to Community, Wealth Group and Livelihood Strategy
    # it might be better to instead have a single OneToOneField ro LivelihoodActivity. This is what was shown in the
    # final Logical Model Diagram.
    # @TODO we can also use negative values and avoid this enum but parsing the data like this my be clearer and
    # possibly easier to report ?
    class Strategy(models.TextChoices):
        REDUCE = "reduce", _("Reduce")
        INCREASE = "increase", _("Increase")

    community = models.ForeignKey(Community, on_delete=models.RESTRICT, verbose_name=_("Community or Village"))
    leaders = models.CharField(max_length=255, null=True, blank=True)
    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.RESTRICT, verbose_name=_("Wealth Group"))
    livelihood_strategy = models.ForeignKey(
        LivelihoodStrategy, on_delete=models.PROTECT, help_text=_("Livelihood Strategy")
    )
    strategy = models.CharField(max_length=20, choices=Strategy.choices, verbose_name=_("Strategy"))
    by_value = models.PositiveSmallIntegerField(
        verbose_name=_("Reduce or increase by"),
    )

    class Meta:
        verbose_name = _("Coping Strategy")
        verbose_name_plural = _("Coping Strategies")
