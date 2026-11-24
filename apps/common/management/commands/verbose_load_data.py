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

    def reset_sequences(self, connection, models):
        """
        Move each loaded table's ID sequence up to its highest ID, never down.

        Django's own reset sets the sequence to the highest committed ID. A load running at the same time may have drawn
        higher IDs that it hasn't committed yet, so Django's reset can move the sequence back below them, and later
        inserts then reuse those IDs. A sequence's last value is outside transactions, so taking the higher of the two is
        safe, and still corrects a sequence that is behind the table, after a fixture with explicit IDs.

        As in Django, ``setval``'s third argument, ``is_called``, is false when the table is empty and the sequence
        hasn't been used, so the next ID is the sequence's first. The sequences of auto-created many-to-many tables
        aren't reset, because fixtures never give their rows explicit IDs.

        The reads and ``setval`` are one statement, so another load would have to draw an ID in the moment between them
        for the sequence to move back, rather than at any time before the load commits, as with Django's reset.
        """
        if connection.vendor != "postgresql":
            return super().reset_sequences(connection, models)
        with connection.cursor() as cursor:
            for model in models:
                table = connection.ops.quote_name(model._meta.db_table)
                column = model._meta.pk.column
                # The table is parsed as an SQL name, so it is quoted, but the column is read literally, so it isn't
                cursor.execute("SELECT pg_get_serial_sequence(%s, %s)", [table, column])
                sequence = cursor.fetchone()[0]
                if sequence is None:  # The primary key isn't generated from a sequence, such as a code
                    continue
                # The highest ID the sequence has handed out, if any, and the highest in the table. GREATEST ignores
                # NULLs, so the result is NULL only when there are neither.
                cursor.execute(
                    f"""
                    SELECT setval(%s, COALESCE(GREATEST(used, highest), 1), GREATEST(used, highest) IS NOT NULL)
                    FROM (SELECT CASE WHEN is_called THEN last_value END AS used FROM {sequence}) AS s,
                        (SELECT MAX({connection.ops.quote_name(column)}) AS highest FROM {table}) AS t
                    """,
                    [sequence],
                )
