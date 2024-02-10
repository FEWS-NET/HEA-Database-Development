import logging

from django.core.management.commands import loaddata
from django.forms.models import model_to_dict

logger = logging.getLogger(__name__)


class Command(loaddata.Command):
    """
    Django loaddata management command with additional logging.
    """

    def save_obj(self, obj):
        try:
            return super().save_obj(obj)
        except Exception as e:
            # Reraise the error with a serialized representation of the object that cauase the exception.
            # We can't use json.dumps because attributes such as datetime fields and the ModelState are not
            # serializable. Use Django Form's `model_to_dict` function to avoid these issues.
            raise RuntimeError(
                "Failed to save %s %s" % (obj.object._meta.verbose_name, model_to_dict(obj.object))
            ) from e
