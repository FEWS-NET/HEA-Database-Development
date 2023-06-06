from common import models
from metadata.models import Dimension, Item, UnitOfMeasure
from spatial.models import Country


class Activity(Dimension):
    """
    The verb part of a Livelihood Strategy, eg, grow crops, transact, paid labor.
    """


class LivelihoodStrategy(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.PROTECT)
    start = models.DateField()
    end = models.DateField()


class Transfer(models.Model):
    livelihood_strategy = models.ForeignKey(LivelihoodStrategy, on_delete=models.PROTECT)
    start = models.DateField()
    end = models.DateField()
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    unit = models.ForeignKey(UnitOfMeasure, on_delete=models.PROTECT)
    quantity = models.PrecisionField()
    quantity_usd = models.PrecisionField()
    quantity_kcals = models.PrecisionField()


class Baseline(models.Model):
    """
    A baseline is performed for each country once a decade.
    """

    country = models.ForeignKey(Country, on_delete=models.PROTECT)
    year = models.PositiveSmallIntegerField()
