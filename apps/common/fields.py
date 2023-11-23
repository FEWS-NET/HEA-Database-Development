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


def add_translatable_field_to_model(model, field_name, field):
    for code, name in settings.LANGUAGES:
        print(f"adding {field_name}_{code} to {model.__name__}")
        # model.add_to_class(f"{field_name}_{code}", field)
        field.clone().contribute_to_class(model, f"{field_name}_{code}")

    def accessor(self):
        language_code = get_language_code()
        return getattr(self, f"{field_name}_{language_code}", "")

    setattr(model, field_name, property(accessor))
