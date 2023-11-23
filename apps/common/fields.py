"""
Additional Model Fields
"""

from django.conf import settings
from django.contrib.gis.db import models
from django.utils import translation
from django.utils.translation import gettext_lazy as _


class CleaningCharField(models.CharField):
    """
    CharField that can perform common text operations to clean the value.

    """

    def __init__(self, strip=False, capitalize=False, lower=False, upper=False, *args, **kwargs):
        self.strip = strip
        self.capitalize = capitalize
        self.lower = lower
        self.upper = upper

        super().__init__(*args, **kwargs)

    def get_prep_value(self, value):
        try:
            if self.strip is True:
                value = value.strip()
            elif self.strip:
                value = value.strip(self.strip)
            if self.capitalize:
                value = value.capitalize()
            if self.lower:
                value = value.lower()
            if self.upper:
                value = value.upper()
        except AttributeError:
            pass

        return value


class PrecisionField(models.DecimalField):
    """
    Standard mathematical value field, to ensure calculations don't involve
    approximations caused by the use of FloatField.
    """

    def __init__(self, *args, **kwargs):
        defaults = {"max_digits": 38, "decimal_places": 16}
        defaults.update(kwargs)
        super().__init__(*args, **defaults)


class CodeField(models.CharField):
    """
    A short code that identifies an object, typically used as the primary key.
    """

    def __init__(self, *args, **kwargs):
        defaults = {"max_length": 60, "verbose_name": _("Code")}
        defaults.update(kwargs)
        super().__init__(*args, **defaults)


class NameField(models.CharField):
    """
    The name of an object

    """

    def __init__(self, *args, **kwargs):
        defaults = {"max_length": 60, "verbose_name": _("Name")}
        defaults.update(kwargs)
        super().__init__(*args, **defaults)


class DescriptionField(models.TextField):
    """
    The description for an object

    """

    def __init__(self, *args, **kwargs):
        defaults = {
            "max_length": 2000,
            "verbose_name": _("Description"),
            "blank": True,
            "help_text": ("Any extra information or detail that is relevant to the object."),
        }
        defaults.update(kwargs)
        super().__init__(*args, **defaults)


class LocationField(models.PointField):
    """
    Location of an object as a Latitude/Longitude Point

    """

    def __init__(self, *args, **kwargs):
        defaults = {
            "verbose_name": _("Location"),
            "blank": True,
            "null": True,
            "geography": True,
        }
        defaults.update(kwargs)
        super().__init__(*args, **defaults)


class BoundaryField(models.MultiPolygonField):
    """
    Location of an object as a Latitude/Longitude Point

    """

    def __init__(self, *args, **kwargs):
        defaults = {
            "verbose_name": _("Boundary"),
            "blank": True,
            "null": True,
            "geography": True,
        }
        defaults.update(kwargs)
        super().__init__(*args, **defaults)


def get_language_code():
    """
    Gets the two letter code of the currently selected language, or the default language if none specified.
    Language is set by Django LocaleMiddleware and common LanguageMiddleware
    """
    language = translation.get_language()
    if language is None:  # Django >= 1.8
        return settings.DEFAULT_LANGUAGE
    available_language_codes = set(code for code, _ in settings.LANGUAGES)
    if language not in available_language_codes and "-" in language:
        language = language.split("-")[0]
    if language in available_language_codes:
        return language
    return settings.DEFAULT_LANGUAGE


def translatable_field(field_name, field):
    """
    Decorator to add translated fields and property getter for current language to a Django model.

    Usage example:

        # models.py

        @translatable_field("name", NameField(blank=True, verbose_name=_("common name")))
        @translatable_field("description", DescriptionField())
        class Acme(models.Model):
            code = CodeField()

        # Usage:
        obj = Acme(code="abc", name_en="English name", name_pt="Nome português")
        obj.name
        >> "English name"
        translation.activate("pt")
        obj.name
        >> "Portuguese name"
    """

    def decorate(model):
        # Add translated fields to model, eg, name_en
        # Language code as suffix as users will primarily be looking for field, eg, name, desc, or some value field,
        # and only then look for a translation if available. Follows naming convention of type -> sub-type, eg, paths.
        for language_code, name in settings.LANGUAGES:
            model_field_name = f"{field_name}_{language_code}"
            field.clone().contribute_to_class(model, model_field_name)

        # Add property that returns local translation, eg, name
        def local_translation_getter(self):
            model_field = f"{field_name}_{get_language_code()}"
            return getattr(self, model_field, "")

        setattr(model, field_name, property(local_translation_getter))
        return model

    return decorate


def add_translatable_field_to_model(model, field_name, field):
    """
    TODO: For discussion - this is functionally identical, except usage syntax.
     I prefer the decorator over this, because it has to appear right next to the model definition, and decorating
     is a standard way of adding functionality to a class. It is also less verbose and easier to name.

    Example usage:

        # models.py
        class Acme(models.Model):
            code = CodeField()

        add_translatable_field_to_model(Acme, "name", NameField(blank=True, verbose_name=_("common name")))
        add_translatable_field_to_model(Acme, "description", DescriptionField())
    """
    for code, name in settings.LANGUAGES:
        field.clone().contribute_to_class(model, f"{field_name}_{code}")

    def local_translation_getter(self):
        language_code = get_language_code()
        return getattr(self, f"{field_name}_{language_code}", "")

    setattr(model, field_name, property(local_translation_getter))
