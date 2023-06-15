# @TODO: Requires GDAL from django.contrib.gis.db.models import *
# Proposed architecture for common, used by replacing, for example:
# `from django.db import models` with `from common import models`
# (like `django.contrib.gis.db.models` does).
# Might encourage us to use common only for defaults, tweaks and
# extensions to libraries?
from django.db import models
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from .fields import CodeField, DescriptionField, NameField, PrecisionField  # noqa: F401


class TranslatableModel(models.Model):
    """
    Abstract base class that makes a model translatable, assuming that it
    contains a `name` field.
    """

    es_name = NameField(
        blank=True,
        verbose_name=_("Spanish name"),
        help_text=_("Spanish name if different from the English name"),
    )
    fr_name = NameField(
        blank=True,
        verbose_name=_("French name"),
        help_text=_("French name if different from the English name"),
    )
    pt_name = NameField(
        blank=True,
        verbose_name=_("Portuguese name"),
        help_text=_("Portuguese name if different from the English name"),
    )
    ar_name = NameField(
        blank=True,
        verbose_name=_("Arabic name"),
        help_text=_("Arabic name if different from the English name"),
    )

    def local_name(self):
        """
        Return the translated display name for the model instance.
        """
        language = get_language()
        if language == "es" and self.es_name:
            return self.es_name
        elif language == "fr" and self.fr_name:
            return self.fr_name
        elif language == "pt" and self.pt_name:
            return self.pt_name
        elif language == "ar" and self.ar_name:
            return self.ar_name
        else:
            return _(self.name)

    local_name.short_description = _("local name")

    class Meta:
        abstract = True
