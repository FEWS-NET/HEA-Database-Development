from django.core import validators
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


class Country(models.Model):
    """
    A Country (or dependent territory or special area of geographical interest) included in ISO 3166.
    """

    iso3166a2 = models.CharField(max_length=2, primary_key=True, verbose_name="ISO 3166-1 Alpha-2")
    iso3166a3 = models.CharField(max_length=3, unique=True, verbose_name="ISO 3166-1 Alpha-3")
    iso3166n3 = models.IntegerField(
        unique=True,
        blank=True,
        null=True,
        validators=[validators.MinValueValidator(1), validators.MaxValueValidator(999)],
        verbose_name="ISO 3166-1 Numeric",
    )
    name = NameField(max_length=200, unique=True)
    iso_en_name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="ISO English ASCII name",
        help_text=_(
            "The name of the Country approved by the ISO 3166 Maintenance Agency with accented characters replaced by their ASCII equivalents"  # NOQA: E501
        ),
    )
    iso_en_proper = models.CharField(
        max_length=200,
        verbose_name="ISO English ASCII full name",
        help_text=_(
            "The full formal name of the Country approved by the ISO 3166 Maintenance Agency with accented characters replaced by their ASCII equivalents"  # NOQA: E501
        ),
    )
    iso_en_ro_name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="ISO English name",
        help_text=_("The name of the Country approved by the ISO 3166 Maintenance Agency"),
    )
    iso_en_ro_proper = models.CharField(
        max_length=200,
        verbose_name="ISO English full name",
        help_text=_("The full formal name of the Country approved by the ISO 3166 Maintenance Agency"),
    )
    iso_fr_name = models.CharField(
        max_length=200,
        verbose_name=_("ISO French name"),
        help_text=_("The name in French of the Country approved by the ISO 3166 Maintenance Agency"),
    )
    iso_fr_proper = models.CharField(
        max_length=200,
        verbose_name=_("ISO French full name"),
        help_text=_("The full formal name in French of the Country approved by the ISO 3166 Maintenance Agency"),
    )
    iso_es_name = models.CharField(
        max_length=200,
        verbose_name=_("ISO Spanish name"),
        help_text=_("The name in Spanish of the Country approved by the ISO 3166 Maintenance Agency"),
    )


class Currency(models.Model):
    """
    A monetary unit in common use and included in ISO 4217.
    """

    iso4217a3 = models.CharField(max_length=20, primary_key=True, verbose_name="ISO 4217 Alpha-3")
    iso4217n3 = models.IntegerField(unique=True, verbose_name="ISO 4217 Numeric", blank=True, null=True)
    iso_en_name = models.CharField(max_length=200, verbose_name=_("name"))

    class Meta:
        verbose_name = _("Currency")
        verbose_name_plural = _("Currencies")

    class ExtraMeta:
        identifier = ["iso4217a3"]
