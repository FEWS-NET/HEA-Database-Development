from django.db import models
from django.utils.translation import gettext_lazy as _
from treebeard.mp_tree import MP_Node

from common import models as common_models
from metadata.models import Currency, Dimension


class Feature(models.Model):
    code = common_models.CodeField()
    name = common_models.NameField()
    # geography = models.GeometryField(
    #     geography=True, dim=2, blank=True, null=True, verbose_name=_("geography")
    # )


class Zone(MP_Node, models.Model):
    """
    The hierarchy of zones of interest to a Baseline study, from
    LivelihoodZone, which one BSS covers and whose children share
    a common set of WealthGroup definitions, to village at which
    Household Economy is defined.
    """

    feature = models.ForeignKey(Feature, on_delete=models.PROTECT)


class Country(Dimension):
    """
    Countries that have Baselines.

    feature = models.ForeignKey(Feature, on_delete=models.PROTECT) ?
    """

    default_currency = models.ForeignKey(Currency, verbose_name=_("Default currency"), on_delete=models.PROTECT)


class LivelihoodZone(Zone):
    """
    The top level Zone, each of which are covered in a single BSS.

    This is split out from Zone so that the diagram can show that a
    BSS and set of WealthGroups are defined for a LivelihoodZone.
    """


class Village(Zone):
    """
    The lowest level of the Zone hierarchy, at which the Household
    Economy is defined.

    This is separated from Zone so the diagram can show that a household is
    defined at the lowest Village level.
    """
