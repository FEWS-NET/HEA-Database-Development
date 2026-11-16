import logging
from collections import defaultdict

from django.core.management.commands import loaddata
from django.db import models
from django.forms.models import model_to_dict

logger = logging.getLogger(__name__)


class Command(loaddata.Command):
    """
    Django loaddata management command with additional logging.

    The primary keys of the saved objects are recorded in `loaded_pks`, keyed by concrete model, so that callers can
    identify existing objects that are not present in the fixture.
    """

    def handle(self, *fixture_labels, **options):
        """
        Reset the record of loaded primary keys and load the fixtures.

        Callers can inspect `loaded_pks` after the command completes.
        """
        self.loaded_pks: defaultdict[type[models.Model], set] = defaultdict(set)
        return super().handle(*fixture_labels, **options)

    def save_obj(self, obj):
        """
        Save an object, recording its primary key and adding the object to any error message.

        Django resolves the natural key of an existing object to its primary key during deserialization, so the
        recorded primary key is the same whether the object was created or updated.
        """
        # Create an string representation of the object before attempting to save it.
        # If there is an error during the save, we won't be able to execute any additional queries after the fact.
        try:
            obj_repr = f'({", ".join([str(x) for x in obj.object.natural_key()])}) '
        except AttributeError:
            obj_repr = obj.object.pk if obj.object.pk else ""
        # We can't use json.dumps because attributes such as datetime fields and the ModelState are not
        # serializable. Use Django Form's `model_to_dict` function to avoid these issues.
        obj_repr += str(model_to_dict(obj.object))

        try:
            saved = super().save_obj(obj)
        except Exception as e:
            # Reraise the error with a serialized representation of the object that cauase the exception.
            raise RuntimeError("Failed to save %s %s" % (obj.object._meta.verbose_name, obj_repr)) from e

        if saved:
            self.loaded_pks[obj.object._meta.concrete_model].add(obj.object.pk)
        return saved
