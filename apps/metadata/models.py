from common import models
from django.utils.translation import gettext_lazy as _


class DimensionType(models.Model):
    """
    Propose Activity, Item, UnitOfMeasure, maybe TranslationType.
    """

    code = models.CodeField()
    name = models.NameField()
    description = models.DescriptionField()


class Dimension(models.Model):
    """
    Dimension provides shared functionality to serve reference data via API,
    filter, aggregate, group, map, ingest, render, search, translate, convert.
    """

    dimension_type = models.ForeignKey(DimensionType, on_delete=models.PROTECT)
    code = models.CodeField()
    name = models.NameField()
    description = models.DescriptionField()


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


class WealthGroup(Dimension):
    """
    The local definitions of wealth group, common to all BSSes in an LHZ.
    """


class Household(models.Model):
    village = models.ForeignKey("spatial.LivelihoodZone", on_delete=models.PROTECT)
    wealth_group = models.ForeignKey(WealthGroup, on_delete=models.PROTECT)


class Asset(models.Model):
    household = models.ForeignKey(Household, on_delete=models.PROTECT)
    # These fields item, unit, qty, qty_usd and qty_kcal to be refactored into a
    # common parent mixin or ABC `ItemInstance` (?)
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    unit = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT)
    quantity = models.PrecisionField()
    quantity_usd = models.PrecisionField()
    quantity_kcals = models.PrecisionField()


class AssetItemCharacteristic(models.Model):
    """
    Characteristics could be stored in wide tables with lots of nulls,
    eg, `LivestockAsset`, or in JsonFields, eg, `Asset.characteristics`,
    or we could create lots of Items (sex would require 2 variants, sex
    and is_mature require 4 variants, and so on). I think separated
    characteristic tables will be easier to filter, aggregate, group and
    order by.
    """

    asset = models.ForeignKey(Asset, on_delete=models.PROTECT)
    # These fields property and value probably also a mixin or ABC
    property = models.ForeignKey(Dimension, on_delete=models.PROTECT)
    value = models.JSONField(help_text=_("A single property value, eg, a float, str or list, not a dict of props."))


class TransferItemCharacteristic(models.Model):
    transfer = models.ForeignKey("baseline.Transfer", on_delete=models.PROTECT)
    # These fields property and value probably also a mixin or ABC
    property = models.ForeignKey(Dimension, on_delete=models.PROTECT)
    value = models.JSONField(help_text=_("A single property value, eg, a float, str or list, not a dict of props."))


class HouseholdCharacteristic(models.Model):
    household = models.ForeignKey(Household, on_delete=models.PROTECT)
    # These fields property and value probably also a mixin or ABC
    property = models.ForeignKey(Dimension, on_delete=models.PROTECT)
    value = models.JSONField(help_text=_("A single property value, eg, a float, str or list, not a dict of props."))


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


class Conversion(models.Model):
    from_unit = models.ForeignKey(Dimension, on_delete=models.PROTECT, related_name="from_conversions")
    to_unit = models.ForeignKey(Dimension, on_delete=models.PROTECT, related_name="to_conversions")
    multiplier = models.PrecisionField()
    offset = models.PrecisionField()
    start = models.DateField()
    end = models.DateField()
    livelihood_zone = models.ForeignKey("spatial.LivelihoodZone", null=True, on_delete=models.PROTECT)
