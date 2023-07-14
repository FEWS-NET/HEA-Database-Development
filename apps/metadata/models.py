import logging

from django.db import models
from django.utils.dates import MONTHS
from django.utils.translation import gettext_lazy as _
from treebeard.mp_tree import MP_Node

import common.models as common_models
from common.models import Country

logger = logging.getLogger(__name__)


class DimensionType(common_models.TranslatableModel, models.Model):
    """
    Propose:
        Item
        UnitOfMeasure
        LivelihoodCategory
        WealthGroupCharacteristicType
        Currency
        WealthCategory

    This could be the top level MP_Node, but I think this is easier for developers.
    It could be a CHOICE, but as discussed below I'm hesitant to not be able to get these without routing
    through Python lookups.
    """

    code = common_models.CodeField()
    description = common_models.DescriptionField()


# @TODO Is LookupModel or ReferenceModel a better name than Dimension in the
# context of a normalized relational schema for an application, rather than a
# data warehouse.
class Dimension(MP_Node, common_models.TranslatableModel):
    """
    Dimension provides shared functionality to serve reference data via API,
    filter, aggregate, group, map, ingest, render, search, translate, convert.

    Most Dimensions will be a single list of values. However some need a hierarchy,
    particularly Item, also LivelihoodCategory, maybe WealthGroupCharacteristicType (rural/urban),
    maybe WealthCategory (to associate and report all v poor categories together).
    It therefore will be less LOE to make the hierarchy
    functionality available commonly for all Dimension types rather than implement only
    in the subclasses that need it. (It could be a mixin, but that would be harder to
    serve via generic DRF classes, for example.)

    The hierarchies cannot be fully captured in the model inheritance hierarchy, as some
    are multi-level, eg, item -> livestock -> poultry -> chicken -> female chicken
    """

    # @TODO not sure this is needed if we have an abstract base class
    dimension_type = models.ForeignKey(DimensionType, on_delete=models.PROTECT)
    code = common_models.CodeField()
    description = common_models.DescriptionField()
    default = models.BooleanField(default=False, help_text=_("The default value in a given sub-list."))
    # @TODO
    # Do we want to automatically add `aliases` to all Dimension subclasses.
    # Do we use ArrayField and bake in dependence on Postgres, or a more complex
    # solution that is cross-platform?
    # Chris:
    # I think ingestion will be easier and more flexible if we have an alias table.
    # I also think the majority of Dimensions will not need aliases.
    # Aliases may need to be specific to source organization or system (eg, FEG Kobo form codes).
    """
    aliases = common_models.ArrayField(
        models.CharField(max_length=60),
        blank=True,
        null=True,
        verbose_name=_("aliases"),
        help_text=_("A list of alternate names for the object."),
    )
    """

    # @TODO Dimension seems to be a code table, in which case I would much prefer
    # an abstract base model, like TranslatableModel, rather than something where
    # everything ends up in a single table.
    # We also don't need `DimensionType` is there is a concrete table called
    # LivelihoodZoneType rather than have to do `Dimension.objects.filter(dimension_type__pk="LivelihoodZoneType")`
    # Chris:
    # My intention for Dimension was a common and flexible place to collect code for serving reference data via API,
    # filter, aggregate, group, map,  ingest, render, search, translate, convert. I am not familiar with 'code tables',
    # but I think that is only part of it.
    # I think in many cases a Dimension will not need a sub-class - often they're just options available in a small
    # drop-down, such as LivelihoodZoneType. It could be a CHOICE field on Dimension, but then we can't get the
    # friendly names from the database, they're only in code. I am not sure if this is an issue.
    # I think an abstract Dimension is a tempting but bad idea. Will enough of the generic functionality work
    # efficiently, such as importing, translating, converting and querying via the ORM, across our Py packages?
    # Eg, we lose most advantages if sub-classes use different Postgres sequences for new IDs, so we don't have a
    # globally unique DimensionID, for example. (I haven't tested this particular characteristic, but just an example
    # of the sort of implementation detail that could trip us up). Dimension needs to be a complete stand-in for the
    # subclass, eg, converting a WeightUnit to a CurrencyUnit or rendering an auto-complete.
    # I therefore think non-abstract Dimension is less likely to cause surprise limitations or complexities.
    # I don't think we should use character primary keys unless there's a significant benefit - id and code are
    # more flexible, future-proof, and easier for developers not already immersed in the schema.
    # class Meta:
    #     abstract = True


class SourceSystem(Dimension):
    """
    Optionally restrict the aliases that are used for a given lookup.
    """


class Alias(models.Model):
    dimension = models.ForeignKey(Dimension, on_delete=models.PROTECT)
    synonym = common_models.NameField()
    source = models.ForeignKey(
        SourceSystem,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text=_("Optional filter for aliases specific to a source."),
        verbose_name=_("Source"),
        related_name="sources",
    )


class LivelihoodCategory(Dimension):
    """
    A type of Livelihood Zone, such as Pastoral or Rain-fed AgroPastoral, etc.
    """

    # @TODO We need a parent category so we can store the detail of Rain Fed AgriPastoral,
    # but still filter for all AgroPastoral
    # Roger: Is this true? Or is Rainfed a modifier for Crop rather than for LivelihoodCategory?

    class Meta:
        verbose_name = _("Livelihood Category")
        verbose_name_plural = _("Livelihood Category")


class WealthCharacteristic(Dimension):
    """
    A Characteristic of a Wealth Group, such as `Number of children at school`, etc.
    """

    class VariableType(models.TextChoices):
        NUM = "float", _("Numeric")
        STR = "str", _("String")
        BOOL = "bool", _("Boolean")
        # OTHER = "other", _("Other")

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


class UnitOfMeasure(Dimension):
    """
    For example kilograms, hectares, hours, kcal% or USD.
    """

    def convert_from(self, value, to_unit_of_measure=None, date=None, livelihood_zone_baseline=None):
        # @TODO: This should be replaced with two ORM joins in a custom model manager instead.
        #   Conversions must never require n+1 queries, as this does.
        conversion = self.conversions_from.all()
        if date:
            conversion = conversion.filter(to_date__gte=date, from_date__lte=date)
        else:
            conversion = conversion.filter(to_date__isnull=True, from_date__isnull=True)
        if livelihood_zone_baseline:
            conversion = conversion.filter(livelihood_zone_baseline=livelihood_zone_baseline)
        else:
            conversion = conversion.filter(livelihood_zone_baseline__isnull=True)
        if len(conversion) == 1:
            # Convert to the standard unit, eg, kg, USD:
            value = conversion[0].convert(value)
            # Then convert to to_unit if requested:
            if to_unit_of_measure and not to_unit_of_measure.default:
                conversion = UnitOfMeasureConversion.objects.filter(from_unit_of_measure=to_unit_of_measure)
                if date:
                    conversion = conversion.filter(to_date__gte=date, from_date__lte=date)
                else:
                    conversion = conversion.filter(to_date__isnull=True, from_date__isnull=True)
                if livelihood_zone_baseline:
                    conversion = conversion.filter(livelihood_zone_baseline=livelihood_zone_baseline)
                else:
                    conversion = conversion.filter(livelihood_zone_baseline__isnull=True)
                if len(conversion) == 1:
                    return conversion[0].convert(value, invert=True)
            else:
                return value
        logger.warning(
            f"{len(conversion) or 'No'} conversions found "
            f"from {self.code}, "
            f"to {to_unit_of_measure or 'std measure'}, "
            f"date {date or 'not specified'}, "
            f"livelihood zone baseline {livelihood_zone_baseline or 'not specified'}. "
            f"({', '.join((str(c.pk) for c in conversion)) or 'None found'}.)"
        )


class Currency(UnitOfMeasure):
    """
    The sub-set of UnitOfMeasures that are Currencies, for diagram clarity.
    """


class Item(Dimension):
    """
    A local thing that is collected, produced, traded and/or owned, including labor.
    """

    # Additional non-docstring comments
    """
    The top of the BSS Data sheet aggregates ProductionModels as follows:
        Food Summary: total (%)
            crops
            livestock products
            payment in kind
            purchase
            food aid
            other (gifts, wild food, fish etc)
        Income Summary: total (cash per year)
            crop sales
            livestock product sales
            livestock sales
            employment (e.g. labour) + remittances
            self-employment (e.g. firewood)
            petty trade or safety nets
            other (gifts, wild food sales, fishing, etc)
        Expenditure Summary: total (cash per year)
            staple food
            non-staple food
            HH items
            water
            inputs
            social serv.
            clothes
            tax
            gifts
            other

        Derived:
            staple/total income ( = income_total / expenditure_staples)
            income minus expenditure ( = income_total - expenditure_total)

    Food Summary is our kcal% output, broken down by output Item top level category.

    Income Summary is our income output where income is positive, aggregated/broken down by output Item
    category.

    Expenditure Summary is our income output where income is negative, aggregated/broken down by Item top
    level category and is_staple.
    """

    input_unit_of_measure = models.ForeignKey(
        UnitOfMeasure, on_delete=models.PROTECT, verbose_name=_("Input Unit of Measure")
    )
    kcals_per_unit = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_("Kcals per kg"))

    class Meta:
        verbose_name = _("Item")
        verbose_name_plural = _("Items")


class UnitOfMeasureConversion(models.Model):
    from_unit_of_measure = models.ForeignKey(
        UnitOfMeasure,
        on_delete=models.PROTECT,
        related_name="conversions_from",
        verbose_name=_("From Unit of Measure"),
    )
    # to_unit: Conversions are always stored against the default measure,
    # eg, for weight: kg, area: acre?, energy: kcal, ccy: USD.
    # from_unit is a default unit for conversions between unit types,
    # eg, kg maize to kcal or USD price.
    multiplier = common_models.PrecisionField(verbose_name=_("Multiplier"))
    offset = common_models.PrecisionField(verbose_name=_("Offset"))
    # Optional conversion validity filters:
    from_date = models.DateField(
        null=True, blank=True, verbose_name=_("From Date"), help_text=_("The first date this conversion is valid.")
    )
    to_date = models.DateField(
        null=True, blank=True, verbose_name=_("To Date"), help_text=_("The last date this conversion is valid.")
    )
    # TODO: This creates circular dependency
    # livelihood_zone_baseline = models.ForeignKey(
    #     LivelihoodZoneBaseline,
    #     on_delete=models.PROTECT,
    #     null=True,
    #     blank=True,
    #     verbose_name=_("Livelihood Zone Baseline"),
    #     help_text=_(
    #         "The Livelihood Zone Baseline for which this conversion is valid, if necessary, eg, local kcal %, price."
    #     ),
    # )
    from_item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("From Item"),
        help_text=_("The Item for which this conversion is valid, if necessary, eg, local kcal %, price."),
    )

    class Meta:
        verbose_name = _("Unit of Measure Conversion")
        verbose_name_plural = _("Unit of Measure Conversions")

    def convert(self, value, invert=False):
        if not invert:
            return value * self.multiplier + self.offset
        else:
            return (value - self.offset) / self.multiplier


class WealthCategory(Dimension):
    """
    The local definitions of wealth group, common to all BSSes in an LHZ.
    """


# @TODO We know we need to only support es, fr, pt and ar.
# Therefore, I propose we just add the fields to the models that need it via
# `TranslatableModel` and add local_name as a method on the model. I want to
# stay as close to Django standard as possible. Or maybe use
# https://django-modeltranslation.readthedocs.io/en/latest/usage.html
# I worry about a translation system that isn't context-aware - I can't tell
# whether this would be. Is "fr" a TranslationType? Is this a general purpose
# translation system for any model field? Or specific to language translations
# and aliases and lookups for Dimensions.

# Chris:
# I reckon Jenny confirmed that BSSes and their collection tools will only
# ever be written in those five languages, and our core analysts will only
# ever work in those five languages. I do not think Jenny was thinking about
# (not) providing reports or visualizations in other languages. However, there
# is no rollout-free translation approach I'm aware of, and the po file
# process is nasty. I therefore think we should look at
# django-modeltranslation, in particular ensuring it keeps ORM-generated
# SQL efficient, and is easy to use, and add an Alias model. If it is not
# efficient or easy, I vote for the TranslatableModel approach too.
# (I think I'd change name to name_en, and pt_name to name_pt, so field
# lists sort nicely, and we follow the convention of most important
# distinction first, sub-types after. But appreciate this is
# subjective (eg, autocomplete worse), so just delete this if you don't,
# no need to discuss.)


class TranslationType(Dimension):
    """
    Determines how the Translation is used,
    ie, whether it is the word we use to translate into
    another language, synonyms for a word in a language,
    aliases for ingestion, external system codes, eg,
    CPCV2, etc.

    Needn't be a Dimension subclass but should be a table. TBD.
    """


class Translation(models.Model):
    from_dimension = models.ForeignKey(Dimension, on_delete=models.PROTECT, related_name="translations_from")
    text = models.CharField()
    translation_type = models.ForeignKey(Dimension, on_delete=models.PROTECT, related_name="translations_of_type")


class LivestockType(Dimension):
    """
    A type of Livestock, such as Goat, Cow, Camel, etc.
    """

    class Meta:
        verbose_name = _("Livestock Type")
        verbose_name_plural = _("Livestock Types")


class CropType(Dimension):
    """
    A Crop Type, e.g. Maize, Sorghum, Sunflower ...
    """

    class Meta:
        verbose_name = _("Crop Type")
        verbose_name_plural = _("Crop Types")


class HazardCategory(Dimension):
    """
    Category of Hazards like: Drought, Epidemic crop disease,	Wild Animals, Flood, Epidemic livestock disease	...
    """

    class Meta:
        verbose_name = _("Hazard Category")
        verbose_name_plural = _("Hazard Categories")


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

    country = models.ForeignKey(Country, verbose_name=_("Country"), db_column="country_code", on_delete=models.PROTECT)
    # @TODO
    # geographic_unit - models.ForeignKey(GeographicUnit, verbose_name=_("Geographic Unit"), on_delete=models.RESTRICT)
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
