# @TODO: Requires GDAL from django.contrib.gis.db.models import *
# Proposed architecture for common, used by replacing, for example:
# `from django.db import models` with `from common import models`
# (like `django.contrib.gis.db.models` does).
# Might encourage us to use common only for defaults, tweaks and
# extensions to libraries?
from django.db.models import *  # noqa: F403
from django.utils.translation import gettext_lazy as _


class PrecisionField(DecimalField):  # noqa: F405
    """
    Standard mathematical value field, to ensure calculations don't involve conversions.
    """

    def __init__(self, *args, **kwargs):
        defaults = {"max_digits": 38, "decimal_places": 16}
        defaults.update(kwargs)
        super().__init__(*args, **defaults)


class CodeField(CharField):  # noqa: F405
    """
    Code field defaults.
    """

    def __init__(self, *args, **kwargs):
        defaults = {"max_length": 60, "verbose_name": _("code")}
        defaults.update(kwargs)
        super().__init__(*args, **defaults)


class NameField(CharField):  # noqa: F405
    """
    Name field defaults.
    """

    def __init__(self, *args, **kwargs):
        defaults = {"max_length": 60, "verbose_name": _("name")}
        defaults.update(kwargs)
        super().__init__(*args, **defaults)


class DescriptionField(TextField):  # noqa: F405
    """
    Description field defaults.
    """

    def __init__(self, *args, **kwargs):
        defaults = {
            "max_length": 2000,
            "verbose_name": _("description"),
            "blank": True,
            "help_text": ("Any extra information or detail that is relevant to the object."),
        }
        defaults.update(kwargs)
        super().__init__(*args, **defaults)
