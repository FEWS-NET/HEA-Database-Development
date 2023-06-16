
import common.models as common_models
from django.db import models
from django.utils.translation import gettext_lazy as _


class DimensionType(common_models.TranslatableModel, models.Model):
    """
    Propose Activity, Item, UnitOfMeasure, maybe TranslationType.
    """

    code = common_models.CodeField(primary_key=True)
    name = common_models.NameField()
    description = common_models.DescriptionField()


# @TODO Is LookupModel or ReferenceModel a better name than Dimension in the
# context of a normalized relational schema for an application, rather than a
# data warehouse.
class Dimension(common_models.TranslatableModel):
    """
    Dimension provides shared functionality to serve reference data via API,
    filter, aggregate, group, map, ingest, render, search, translate, convert.
    """

    # @TODO not sure this is needed if we have an abstract base class
    dimension_type = models.ForeignKey(DimensionType, on_delete=models.PROTECT)
    code = common_models.CodeField(primary_key=True)
    name = common_models.NameField()
    description = common_models.DescriptionField()
    # @TODO
    # Do we want to automatically add `aliases` to all Dimension subclasses.
    # Do we use ArrayField and bake in dependence on Postgres, or a more complex
    # solution that is cross-platform?
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
    class Meta:
        abstract = True


class LivelihoodCategory(Dimension):
    """
    A type of Livelihood Zone, such as Pastoral or Rain-fed AgroPastoral, etc.
    """

    # @TODO We need a parent category so we can store the detail of Rain Fed AgriPastoral,
    # but still filter for all AgroPastoral

    class Meta:
        verbose_name = _("Livelihood Category")
        verbose_name_plural = _("Livelihood Category")


class LivestockType(Dimension):
    """
    A type of Livestock, such as Goat, Cow, Camel, etc.
    """

    class Meta:
        verbose_name = _("Livestock Type")
        verbose_name_plural = _("Livestock Types")


class WealthGroupAttributeType(Dimension):
    """
    A type of Wealth Group Attribute, such as `Number of children at school`, etc.
    """

    class Meta:
        verbose_name = _("Wealth Group Attribute Type")
        verbose_name_plural = _("Wealth Group Attribute Types")


class ExpenditureCategory(Dimension):
    """
    A type of Wealth Group Attribute, such as `Number of children at school`, etc.
    """


class IncomeSource(Dimension):
    """
    A type of Wealth Group Attribute, such as `Number of children at school`, etc.
    """


class FoodSource(Dimension):
    """
    A type of Wealth Group Attribute, such as `Number of children at school`, etc.
    """


class Item(Dimension):
    """
    A local thing that is collected, produced, traded and/or owned, including labor.
    """


class UnitOfMeasure(Dimension):
    """
    For example kilograms, hectares, hours or USD.
    """


class Currency(UnitOfMeasure):
    """
    The sub-set of UnitOfMeasures that are Currencies, for diagram clarity.
    """


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
'''
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
'''


class CropType(Dimension):
    """
    A Crop Type, e.g. Maize, Sorghum, Sunflower ...
    """

    class Meta:
        verbose_name = _("Crop Type")
        verbose_name_plural = _("Crop Types")


class SeasonalActivityCategory(Dimension):
    """
    Seasonal Activity Category can be Crops, Livestock, Gardening, Employment, Fishing
    """

    class Meta:
        verbose_name = _("Seasonal Activity Category")
        verbose_name_plural = _("Seasonal Activity Categories")


class HazardCateogy(Dimension):
    """
    Category of Hazards like: Drought, Epidemic crop disease,	Wild Animals, Flood, Epidemic livestock disease	...
    """

    class Meta:
        verbose_name = _("Hazard Category")
        verbose_name_plural = _("Hazard Categories")
