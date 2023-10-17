"""
Models for managing HEA Baseline Surveys
"""
import numbers

from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _
from model_utils.managers import InheritanceManager

import common.models as common_models
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
    WealthCategory,
    WealthCharacteristic,
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
            return (self.livelihood_zone.code, self.reference_year_end_date.isoformat())
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

    class ExtraMeta:
        identifier = [
            "livelihood_zone",
            "reference_year_start_date",
            "reference_year_end_date",
        ]


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
        help_text=_("The full name the Community, including the parent administrative units."),
    )
    livelihood_zone_baseline = models.ForeignKey(
        LivelihoodZoneBaseline,
        on_delete=models.CASCADE,
        related_name="communities",
        verbose_name=_("Livelihood Zone Baseline"),
    )
    geography = models.GeometryField(geography=True, dim=2, blank=True, null=True, verbose_name=_("geography"))

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
    def get_by_natural_key(self, code: str, reference_year_end_date: str, wealth_category: str, full_name: str):
        if full_name:
            return self.get(
                livelihood_zone_baseline__livelihood_zone__code=code,
                livelihood_zone_baseline__reference_year_end_date=reference_year_end_date,
                wealth_category__code=wealth_category,
                community__full_name=full_name,
            )
        else:
            return self.get(
                livelihood_zone_baseline__livelihood_zone__code=code,
                livelihood_zone_baseline__reference_year_end_date=reference_year_end_date,
                wealth_category__code=wealth_category,
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
    # within that Community in the specified Wealth Category. If the Community
    # is null, then the Wealth Group represents the households with that
    # Wealth Category for the whole Livelihood Zone Baseline.
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
    wealth_category = models.ForeignKey(
        WealthCategory,
        on_delete=models.CASCADE,
        verbose_name=_("Wealth Category"),
        help_text=_("Wealth Category, e.g. Poor or Better Off"),
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
            f"{str(self.community)} {str(self.wealth_category)}"
            if self.community
            else f"{str(self.livelihood_zone_baseline)} {str(self.wealth_category)}"
        )

    def natural_key(self):
        return (
            self.livelihood_zone_baseline.livelihood_zone_id,
            self.livelihood_zone_baseline.reference_year_end_date.isoformat(),
            self.wealth_category.code,
            self.community.full_name if self.community else "",
        )

    class Meta:
        verbose_name = _("Wealth Group")
        verbose_name_plural = _("Wealth Groups")
        constraints = [
            models.UniqueConstraint(
                fields=("livelihood_zone_baseline", "wealth_category", "community"),
                name="baseline_wealthgroup_livelihood_zone_baseline_wealth_category_community_uniq",
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
        wealth_category: str,
        wealth_characteristic: str,
        source: str = "baseline_summary",
        product: str = "",
        full_name: str = "",
    ):
        criteria = {
            "wealth_characteristic__code": wealth_characteristic,
            "source": source,
            "wealth_group__livelihood_zone_baseline__livelihood_zone__code": code,
            "wealth_group__livelihood_zone_baseline__reference_year_end_date": reference_year_end_date,
            "wealth_group__wealth_category__code": wealth_category,
        }
        if full_name:
            criteria["wealth_group__community__full_name"] = full_name
        else:
            criteria["wealth_group__community__isnull"] = True
        if product:
            criteria["product__cpcv2"] = product
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
    """

    class CharacteristicSource(models.TextChoices):
        COMMUNITY = "community_interview", _("Community Interview (Form 3)")
        WEALTH_GROUP = "wealth_group_interview", _("Wealth Group Interview (Form 4)")
        SUMMARY = "baseline_summary", _("Baseline Summary")

    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.RESTRICT, verbose_name=_("Wealth Group"))
    wealth_characteristic = models.ForeignKey(
        WealthCharacteristic, on_delete=models.RESTRICT, verbose_name=_("Wealth Characteristic")
    )
    source = models.CharField(
        max_length=30,
        choices=CharacteristicSource.choices,
        db_index=True,
        verbose_name=_("Characteristic Source"),
        help_text=_(
            "The source of this Wealth Group Characteristic Value, such as a Community Interview (Form 3), or the Baseline Summary"  # NOQA: E501
        ),
    )
    product = models.ForeignKey(
        ClassifiedProduct,
        db_column="product_code",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_("Product"),
        help_text=_("Product, e.g. Cattle"),
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
        # Validate `source`
        if self.source == self.CharacteristicSource.SUMMARY:
            if self.wealth_group.community:
                raise ValidationError(
                    _(
                        "A Wealth Group Characteristic Value from a Baseline Summary must be for a Baseline Wealth Group"  # NOQA: E501
                    )
                )
        elif not self.wealth_group.community:
            raise ValidationError(
                _("A Wealth Group Characteristic Value from a %s must be for a Community Wealth Group")
                % self.CharacteristicSource(self.source).label
            )
        # Validate `product`
        if self.wealth_characteristic.has_product:
            if not self.product:
                raise ValidationError(
                    _("A Wealth Group Characteristic Value for %s must have a product" % self.wealth_characteristic)
                )
        elif self.product:
            raise ValidationError(
                _("A Wealth Group Characteristic Value for %s must not have a product" % self.wealth_characteristic)
                % self.CharacteristicSource(self.source).label
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
            self.wealth_group.wealth_category.code,
            self.wealth_characteristic_id,
            self.source,
            self.product_id if self.product_id else "",
            self.wealth_group.community.full_name if self.wealth_group.community else "",
        )

    class Meta:
        verbose_name = _("Wealth Characteristic Value")
        verbose_name_plural = _("Wealth Characteristic Values")
        constraints = [
            # Create a unique constraint on wealth_group, wealth_characteristic, product and source.
            # We can only have one value from each Source (Form 3, Form 4, Summary) for each Wealth Group
            # for each Characteristic (including the Product if appropriate).
            models.UniqueConstraint(
                fields=["wealth_group", "wealth_characteristic", "source", "product"],
                name="baseline_wealthgroupcharacteristicvalue_group_characteristic_source_product_uniq",
            ),
        ]


# @TODO https://fewsnet.atlassian.net/browse/HEA-93
# Does this name cause confusion for people who think Strategy === Coping Strategy?
class LivelihoodStrategy(common_models.Model):
    """
    An activity undertaken by households in a Livelihood Zone that produces food or income or requires expenditure.

    A Livelihood Strategy is not necessarily used by all Wealth Groups within the Livelihood Zone.

    Implicit in the BSS 'Data' worksheet in Column A.
    """

    # The 'Graphs' worksheet in NE01(BIL) and MG2 adds a `qui?` lookup in
    # Column F that tracks which household members are primarily responsible
    # for Livelihood Strategies that generate food and income.
    class HouseholdLaborProvider(models.TextChoices):
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
        choices=LivelihoodStrategyType.choices,
        db_index=True,
        verbose_name=_("Strategy Type"),
        help_text=_("The type of livelihood strategy, such as crop production, or wild food gathering."),
    )
    # We will need a "Year Round" or "Annual" season to account for Livelihood Strategies
    # that have equal distribution across the year, such as purchase of tea and
    # sugar, or remittances.
    season = models.ForeignKey(Season, on_delete=models.PROTECT, verbose_name=_("Season"))
    # @TODO For OtherCashIncome, there is no Product. I think we want:
    # quantity_produced = null (or maybe 0)
    # quantity_sold = null (or maybe 0)
    # quantity_other_uses = null (or maybe 0)
    # income = XXX
    # expenditure = 0 (or maybe null)
    # Similarly, for OtherPurchases. I think we want:
    # quantity_produced = null (or maybe 0)
    # quantity_sold = null (or maybe 0)
    # quantity_other_uses = null (or maybe 0)
    # income = 0 (or maybe null)
    # expenditure = XXX
    # Do we make product nullable here?
    # Dave: How do we tell what Remittances are, if we can't look it up as a product?
    # Or maybe to Item with an attribute for cpcv2
    # Dave, Girum, Roger: Null rather 0
    product = models.ForeignKey(
        ClassifiedProduct,
        db_column="product_code",
        on_delete=models.PROTECT,
        verbose_name=_("Product"),
        help_text=_("Product, e.g. full fat milk"),
        related_name="livelihood_strategies",
    )
    unit_of_measure = models.ForeignKey(
        UnitOfMeasure, db_column="unit_code", on_delete=models.PROTECT, verbose_name=_("Unit of Measure")
    )
    currency = models.ForeignKey(
        Currency, db_column="currency_code", on_delete=models.PROTECT, verbose_name=_("Currency")
    )
    # In Somalia they track export/local sales separately - see SO18 Data:B178 and also B770
    # In many BSS they store separate data for Rainfed and Irrigated production of staple crops.
    # @TODO See https://fewsnet.atlassian.net/browse/HEA-67
    # Are there other types than rainfed and irrigated?
    additional_identifier = models.CharField(
        blank=True,
        verbose_name=_("Additional Identifer"),
        help_text=_("Additional text identifying the livelihood strategy"),
    )
    # Not all BSS track this, and it isn't tracked for expenditures, so
    # the field must be `blank=True`.
    household_labor_provider = models.CharField(
        choices=HouseholdLaborProvider.choices, blank=True, verbose_name=_("Activity done by")
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

    class ExtraMeta:
        identifier = ["livelihood_zone_baseline", "product", "additional_identifier"]


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
    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.PROTECT, help_text=_("Wealth Group"))

    quantity_produced = models.PositiveIntegerField(blank=True, null=True, verbose_name=_("Quantity Produced"))
    quantity_sold = models.PositiveIntegerField(blank=True, null=True, verbose_name=_("Quantity Sold/Exchanged"))
    quantity_other_uses = models.PositiveIntegerField(blank=True, null=True, verbose_name=_("Quantity Other Uses"))
    # Can normally be calculated / validated as `quantity_received - quantity_sold - quantity_other_uses`
    quantity_consumed = models.PositiveIntegerField(blank=True, null=True, verbose_name=_("Quantity Consumed"))

    price = models.FloatField(blank=True, null=True, verbose_name=_("Price"), help_text=_("Price per unit"))
    # Can be calculated / validated as `quantity_sold * price` for livelihood strategies that involve the sale of
    # a proportion of the household's own production.
    income = models.FloatField(blank=True, null=True, help_text=_("Income"))
    # Can be calculated / validated as `quantity_consumed * price` for livelihood strategies that involve the purchase
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
    percentage_kcals = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Percentage of required kcals"),
        help_text=_("Percentage of annual household kcal requirement provided by this livelihood strategy"),
    )

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
        if self.quantity_consumed != self.quantity_produced - self.quantity_sold - self.quantity_other_uses:
            raise ValidationError(
                _(
                    "Quantity consumed for a Livelihood Activity must be quantity produced - quantity sold - quantity used for other things"  # NOQA: E501
                )
            )

    def validate_income(self):
        if self.income != self.quantity_sold * self.price:
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
        if self.expenditure and self.expenditure != self.quantity_produced * self.price:
            raise ValidationError(
                _("Expenditure for a Livelihood Activity must be quantity produced multiplied by price")
            )

    def validate_kcals_consumed(self):
        conversion_factor = UnitOfMeasureConversion.objects.get_conversion_factor(
            from_unit=self.livelihood_strategy.unit_of_measure,
            to_unit=self.livelihood_strategy.product.unit_of_measure,
        )
        kcals_per_unit = self.livelihood_strategy.product.kcals_per_unit
        if self.kcals_consumed != self.quantity_consumed * conversion_factor * kcals_per_unit:
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
    lactation_days = models.PositiveSmallIntegerField(verbose_name=_("Average number or days of lactation"))
    daily_production = models.PositiveSmallIntegerField(verbose_name=_("Average daily milk production per animal"))

    # @TODO see https://fewsnet.atlassian.net/browse/HEA-65
    # This is not required for scenario development and is only used for the kcal calculations in the BSS.
    # Do we need to store it in the database?.
    type_of_milk_sold_or_other_uses = models.CharField(
        choices=MilkType.choices, verbose_name=_("Skim or whole milk sold or used")
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


class LivestockSales(LivelihoodActivity):
    """
    Sale of livestock by households in a Wealth Group for cash income.

    Stored on the BSS 'Data' worksheet in the 'Livestock Production' section, typically starting around Row 181.
    """

    # @TODO Do we need validation around offtake (animals_sold) to make sure
    # that they are not selling and killing more animals than they own.
    class Meta:
        verbose_name = LivelihoodStrategyType.LIVESTOCK_SALES.label
        verbose_name_plural = LivelihoodStrategyType.LIVESTOCK_SALES.label
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

    def validate_quantity_produced(self):
        if self.quantity_produced != self.unit_multiple * self.purchases_per_month * self.months_per_year:
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

    # Production calculation/validation is `people_per_hh * labor_per_month * months_per_year`
    payment_per_time = models.PositiveSmallIntegerField(
        verbose_name=_("Payment per time"), help_text=_("Amount of item received each time the labor is performed")
    )
    people_per_hh = models.PositiveSmallIntegerField(
        verbose_name=_("People per household"), help_text=_("Number of household members who perform the labor")
    )
    labor_per_month = models.PositiveSmallIntegerField(verbose_name=_("Labor per month"))
    months_per_year = models.PositiveSmallIntegerField(
        verbose_name=_("Months per year"), help_text=_("Number of months in a year that the labor is performed")
    )

    def validate_quantity_produced(self):
        if (
            self.quantity_produced
            != self.payment_per_time * self.people_per_hh * self.labor_per_month * self.months_per_year
        ):
            raise ValidationError(
                _(
                    "Quantity produced for Payment In Kind must be payment per time * number of people * labor per month * months per year"  # NOQA: E501
                )
            )

    class Meta:
        verbose_name = LivelihoodStrategyType.PAYMENT_IN_KIND.label
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

    def validate_quantity_produced(self):
        if self.quantity_produced != self.unit_multiple * self.received_per_year:
            raise ValidationError(
                _("Quantity produced for Relief, Gifts, Other must be amount received * times per year")
            )

    class Meta:
        verbose_name = LivelihoodStrategyType.RELIEF_GIFTS_OTHER.label
        verbose_name_plural = LivelihoodStrategyType.RELIEF_GIFTS_OTHER.label


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

    # Production calculation/validation is `people_per_hh * labor_per_month * months_per_year`
    # However, some other income (e.g. Remittances) just has a number of times per year and is not calculated from
    # people_per_hh, etc. Therefore those fields must be nullable, and we must store the total number of times per year
    # as a separate field
    payment_per_time = models.PositiveSmallIntegerField(
        verbose_name=_("Payment per time"), help_text=_("Amount of money received each time the labor is performed")
    )
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

    def validate_income(self):
        if (
            self.people_per_hh
            and self.income != self.payment_per_time * self.people_per_hh * self.labor_per_month * self.months_per_year
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
        self.times_per_year = self.people_per_hh * self.labor_per_month * self.months_per_year
        super().calculate_fields()

    class Meta:
        verbose_name = LivelihoodStrategyType.OTHER_CASH_INCOME.label
        verbose_name_plural = LivelihoodStrategyType.OTHER_CASH_INCOME.label


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

    def validate_expenditure(self):
        if self.expenditure != self.price * self.unit_multiple * self.purchases_per_month * self.months_per_year:
            raise ValidationError(
                _(
                    "Expenditure for Other Purchases must be price * unit multiple * purchases per month * months per year"  # NOQA: E501
                )
            )

    class Meta:
        verbose_name = LivelihoodStrategyType.OTHER_PURCHASES.label
        verbose_name_plural = LivelihoodStrategyType.OTHER_PURCHASES.label


class SeasonalActivity(common_models.Model):
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
        db_column="product_code",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        verbose_name=_("Product"),
        help_text=_("Product, e.g. full fat milk"),
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

    class ExtraMeta:
        identifier = ["activity_type", "season", "product"]


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
            # keys for Community and Baseline Seasonal Activity that include the livelihood_zone_baseline.
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
    season = models.ForeignKey(Season, on_delete=models.RESTRICT, verbose_name=_("Season"))
    yield_with_inputs = models.FloatField(
        verbose_name=_("Yield with inputs"),
        help_text=_("Yield in reference period with inputs (seeds and fertilizer)"),
    )
    yield_without_inputs = models.FloatField(
        verbose_name=_("Yield without inputs"),
        help_text=_("Yield in reference period without inputs (seeds and fertilizer)"),
    )
    seed_requirement = models.FloatField(verbose_name=_("Seed requirement"))
    unit_of_measure = models.ForeignKey(
        UnitOfMeasure, db_column="unit_code", on_delete=models.RESTRICT, verbose_name=_("Unit of Measure")
    )

    # @TODO We need to store the harvest month for each crop, because it is needed
    # to calculate the per month food, income and expenditure shown in Table 4 of the LIAS Sheet S

    # @TODO Do we need to add UnitOfMeasure and parse it out of `6x50kg bags`, etc. or can we just store it as text.

    def clean(self):
        if not self.crop_id.startswith("R01"):
            raise ValidationError(
                _(
                    "Crop type for Community Crop Production must have a CPCv2 code beginning R01 (Agriculture Products)"  # NOQA: E501
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
    additional_attributes = models.JSONField()

    def clean(self):
        if not self.livestock_id.startswith("L021"):
            raise ValidationError(
                _("Livestock type for Community Livestock must have a CPCv2 code beginning L021 (Live animals)")
            )
        super().clean()

    def save(self, *args, **kwargs):
        # No need to enforce foreign keys or uniqueness because database constraints will do it anyway
        self.full_clean(
            exclude=[field.name for field in self._meta.fields if isinstance(field, models.ForeignKey)],
            validate_unique=False,
        )
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Wealth Group Attribute")
        verbose_name_plural = _("Wealth Group Attributes")


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
class AnnualProductionPerformance(common_models.Model):
    """
    Relative production performance and resulting food security experienced
    in a recent year prior to the reference year.

    Stored on the BSS 'Timeline' worksheet based on responses to the Form 3.
    """

    class Performance(models.IntegerChoices):
        VERY_POOR = 1, _("Very Poor")
        POOR = 2, _("Poor")
        MEDIUM = 3, _("Medium")
        GOOD = 4, _("Good")
        VERY_GOOD = 5, _("Very Good")

    community = models.ForeignKey(Community, on_delete=models.RESTRICT, verbose_name=_("Community or Village"))
    performance_year_start_date = models.DateField(
        verbose_name=_("Performance Year Start Date"),
        help_text=_("The first day of the month of the start month in the performance year"),
    )
    performance_year_end_date = models.DateField(
        verbose_name=_("Performance Year End Date"),
        help_text=_("The last day of the month of the end month in the performance year"),
    )
    annual_performance = models.SmallIntegerField(
        blank=True,
        null=True,
        choices=Performance.choices,
        validators=[
            MinValueValidator(1, message="Performance rating must be at least 1."),
            MaxValueValidator(5, message="Performance rating must be at most 5."),
        ],
        verbose_name=_("Seasonal Performance"),
        help_text=_("Rating of the annual production performance from Very Poor (1) to Very Good (5)"),
    )
    # @TODO SN05 https://docs.google.com/spreadsheets/d/1Su_1HMb7kkq5YXDtdETCnSuD6-goA4aA/edit#gid=54536490
    # contains text descriptions for the seasonal performance.
    description = common_models.DescriptionField()

    class Meta:
        verbose_name = _("Annual Production Performance")
        verbose_name_plural = _("Annual Production Performance")


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
    chronic_or_periodic = models.CharField(choices=ChronicOrPeriodic.choices, verbose_name=_("Chronic or Periodic"))
    ranking = models.PositiveSmallIntegerField(
        choices=HazardRanking.choices,
        validators=[
            MinValueValidator(1, message="Performance rank must be at least 1."),
            MaxValueValidator(5, message="Performance rank must be at most 5."),
        ],
        verbose_name=_("Ranking"),
    )
    hazard_category = models.ForeignKey(HazardCategory, on_delete=models.RESTRICT, verbose_name=_("Hazard Category"))
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

    community = models.ForeignKey(Community, on_delete=models.RESTRICT, verbose_name=_("Community or Village"))
    event_year_start_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Event Year Start Date"),
        help_text=_("The first day of the month of the start month in the event year"),
    )
    event_year_end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Event Year End Date"),
        help_text=_("The last day of the month of the end month in the event year"),
    )
    # @TODO MG23 https://docs.google.com/spreadsheets/d/18Y85UKXGehudt2YX5Oc_adw2TUxo6nY7/edit#gid=1565100920
    # contains additional information on Events and Responses by year in the Timeline worksheet.
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
