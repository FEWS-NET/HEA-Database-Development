from common import models


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


class Activity(Dimension):
    """
    The verb part of a Livelihood Strategy, eg, grow crops, transact, paid labor.
    """


class LivelihoodStrategy(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.PROTECT)
    start = models.DateField()
    end = models.DateField()


class Transfer(models.Model):
    livelihood_strategy = models.ForeignKey(
        LivelihoodStrategy, on_delete=models.PROTECT
    )
    start = models.DateField()
    end = models.DateField()
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    unit = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT)
    quantity = models.PrecisionField()
    quantity_usd = models.PrecisionField()
    quantity_kcals = models.PrecisionField()
