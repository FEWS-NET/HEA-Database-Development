from django.contrib.gis.db import models
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from . import CodeField, DescriptionField, NameField, PrecisionField  # noqa: F401


class TranslatableModel(models.Model):
    """
    Abstract base class that makes a model translatable.
    In many cases en_name will be overridden with custom properties.
    """

    en_name = NameField(
        blank=True,
        verbose_name=_("English name"),
        help_text=_("English name"),
    )
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
            return _(self.en_name)

    local_name.short_description = _("local name")

    class Meta:
        abstract = True
