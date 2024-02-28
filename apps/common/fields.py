"""
Additional Model Fields
"""

from itertools import chain

from django.conf import settings
from django.contrib.gis.db import models
from django.utils import translation
from django.utils.text import format_lazy
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
            "help_text": _("Any extra information or detail that is relevant to the object."),
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


class TranslatedField:
    """
    A Django field that adds a field per supported language to a model, and a getter property that
    returns the translation for the language currently selected in Django (which is set by Django
    LocaleMiddleware or our LanguageMiddleware).

    Usage example:

        # models.py
        class Acme(models.Model):
            code = CodeField()
            common_name = TranslatedField(NameField(blank=True, verbose_name=_("common name")))
            description = TranslatedField(models.CharField(max_length=800, verbose_name=_("description")))

        # Usage:
        obj = Acme(code="abc", name_en="English name", name_pt="Nome português")
        obj.name
        >> "English name"
        translation.activate("pt")
        obj.name
        >> "Nome português"
    """

    def __init__(self, field):
        # Check that the field is of a string type.
        # The existing code is expected to work for other field types, but they are not currently supported
        # because they haven't been tested. If additional field types are required in the future, then they can
        # be added to this list and then tested. They may require selective application of properties on the
        # translation fields, as already done in `contribute_to_class` for .blank, .null, ._unique and .primary_key.
        # For example, non-text fields that have `null=False` may need to allow null in the non-default language
        # fields if sometimes not all are populated.
        assert isinstance(
            field, (models.CharField, models.TextField)
        ), f"Field {str(field)} is of unsupported type {str(type(field))}"
        self.field = field

    def contribute_to_class(self, cls, name, private_only=False):
        # Add language fields to cls and db, of type self.field, eg, obj.name_en = NameField()
        for language_code, language_name in settings.LANGUAGES:
            # Puts language code after field name, eg, name_en, because a user will be looking first for a
            # field - name, value, etc, and after that, whether there is a translation. Unlike FDW, translations
            # may be sparsely populated so checking for any will be easier if they sort together.
            model_field_name = f"{name}_{language_code}"
            field = self.field.clone()
            field.verbose_name = format_lazy("{} ({})", self.field.verbose_name, language_name)
            if language_code != settings.LANGUAGE_CODE:
                # If a field is unique or a primary key, apply that only on the default language
                field._unique = False
                field.primary_key = False
                # If a field is non-blank, apply that restriction only on the default language
                if getattr(field, "blank", None) is False:
                    field.blank = True
            field.contribute_to_class(cls=cls, name=model_field_name, private_only=private_only)

        # Add property that returns local translation, eg, obj.name == "Nome português"
        def local_translation_getter(obj):
            # translation.get_language() returns default (en) if none selected
            selected_language = translation.get_language()
            for code in chain((selected_language,), (code for code, n in settings.LANGUAGES)):
                translated_string = getattr(obj, f"{name}_{code}", "")
                if translated_string:
                    return translated_string
            return ""

        local_translation_getter.short_description = _(self.field.verbose_name)
        setattr(cls, name, property(local_translation_getter))


def translation_fields(base_fieldname):
    """
    Return a list of the language-specific field names for a base field.

    Convenience function for use in Admin and Viewset subclasses.
    """
    return (f"{base_fieldname}_{code}" for code, name in settings.LANGUAGES)
