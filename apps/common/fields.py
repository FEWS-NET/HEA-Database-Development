"""
Additional Model Fields
"""

from django.contrib.gis.db import models
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
