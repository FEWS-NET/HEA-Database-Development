import logging

from django.core.management.commands import loaddata
from django.forms.models import model_to_dict

logger = logging.getLogger(__name__)


class Command(loaddata.Command):
    """
    Django loaddata management command with additional logging.
    """

    def save_obj(self, obj):
        # Create an string representation of the object before attempting to save it.
        # If there is an error during the save, we won't be able to execute any additional queries after the fact.
        try:
            obj_repr = f'({", ".join(obj.object.natural_key())}) '
        except AttributeError:
            obj_repr = obj.object.pk if obj.object.pk else ""
        # We can't use json.dumps because attributes such as datetime fields and the ModelState are not
        # serializable. Use Django Form's `model_to_dict` function to avoid these issues.
        obj_repr += str(model_to_dict(obj.object))

        try:
            return super().save_obj(obj)
        except Exception as e:
            # Reraise the error with a serialized representation of the object that cauase the exception.
            raise RuntimeError("Failed to save %s %s" % (obj.object._meta.verbose_name, obj_repr)) from e
