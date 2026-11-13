import json
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.core.management.commands import loaddata
from django.db import connection
from django.test import TestCase

from baseline.models import SourceOrganization
from baseline.tests.factories import SourceOrganizationFactory


def next_id(model) -> int:
    """
    Return the ID that the model's sequence will give the next row, without using it.

    Reads the sequence's state directly, because nextval would use up the ID.
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_get_serial_sequence(%s, %s)", [model._meta.db_table, model._meta.pk.column])
        sequence = cursor.fetchone()[0]
        cursor.execute(f"SELECT CASE WHEN is_called THEN last_value + 1 ELSE last_value END FROM {sequence}")
        return cursor.fetchone()[0]


class ResetSequencesTestCase(TestCase):
    """
    verbose_load_data moves each loaded table's ID sequence up to its highest ID.

    It never moves the sequence back below IDs that another load may have drawn without committing them yet.
    """

    def load(self, *records: dict):
        """
        Load the records with verbose_load_data, from a fixture file.

        Each record is a fixture entry without the model, which is always SourceOrganization.
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.json"
            path.write_text(json.dumps([{"model": "baseline.sourceorganization", **record} for record in records]))
            call_command("verbose_load_data", str(path), verbosity=0)

    @staticmethod
    def organization(name: str) -> dict:
        """
        Return an organization's fields, identified by its natural key, the name.

        The full name is derived from the name, because it must also be unique.
        """
        return {"name": name, "full_name": f"{name} full name", "description": ""}

    def test_explicit_id_moves_the_sequence_up(self):
        """
        A fixture with an explicit ID above the sequence moves the sequence past it.

        Otherwise the next new row would eventually reuse the loaded ID.
        """
        explicit = next_id(SourceOrganization) + 50
        self.load({"pk": explicit, "fields": self.organization("explicit")})
        self.assertEqual(next_id(SourceOrganization), explicit + 1)

    def test_never_moves_the_sequence_back(self):
        """
        A sequence ahead of the table stays ahead.

        This is the case when another load has drawn IDs that it hasn't committed yet.
        """
        kept = SourceOrganizationFactory(name="kept")
        drawn = SourceOrganizationFactory(name="drawn")
        drawn_id = drawn.pk
        # The table's highest ID is now below the IDs the sequence has given out
        drawn.delete()
        self.assertEqual(next_id(SourceOrganization), drawn_id + 1)
        # Django's own reset moves the sequence back to the table's highest ID, so the next row would reuse drawn's ID
        django_loaddata = loaddata.Command()
        django_loaddata.verbosity = 0
        django_loaddata.reset_sequences(connection, [SourceOrganization])
        self.assertEqual(next_id(SourceOrganization), kept.pk + 1)
        # Put the sequence back ahead of the table, then load with verbose_load_data, which leaves it there
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT setval(pg_get_serial_sequence(%s, %s), %s)",
                [SourceOrganization._meta.db_table, "id", drawn_id],
            )
        self.load({"fields": self.organization("kept")})
        self.assertEqual(next_id(SourceOrganization), drawn_id + 1)
