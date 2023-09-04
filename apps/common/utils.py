import csv
import logging
from datetime import datetime, timedelta
from pathlib import Path

from django.apps import apps
from django.db.migrations.operations.base import Operation
from django.forms.models import modelform_factory

logger = logging.getLogger(__name__)


class UnicodeCsvReader(object):
    # TODO: Should check if it works without encoding and if this class needed on Python 3 at all.
    def __init__(self, f, encoding="utf-8", **kwargs):
        if "delimiter" in kwargs:
            kwargs["delimiter"] = str(kwargs["delimiter"])
        self.csv_reader = csv.reader(f, **kwargs)
        self.encoding = encoding

    def __iter__(self):
        return self

    def __next__(self):
        # read and split the csv row into fields
        row = next(self.csv_reader)
        # now decode
        return [str(cell) for cell in row]

    @property
    def line_num(self):
        return self.csv_reader.line_num


class UnicodeDictReader(csv.DictReader):
    def __init__(self, f, encoding="utf-8", fieldnames=None, **kwds):
        if "delimiter" in kwds:
            kwds["delimiter"] = str(kwds["delimiter"])
        csv.DictReader.__init__(self, f, fieldnames=fieldnames, **kwds)
        self.reader = UnicodeCsvReader(f, encoding=encoding, **kwds)


class LoadModelFromDict(Operation):
    """
    Load a model from a dict or a file

    If a string is passed, we assume it is a file name for a delimited file. The
    default delimiter is a ';' because that matches what pgadmin3 uses for query
    results. The file must have a first row containing the headers.
    """

    # If this is False, it means that this operation will be ignored by
    # sqlmigrate; if true, it will be run and the SQL collected for its output.
    reduces_to_sql = False

    # If this is False, Django will refuse to reverse past this operation.
    reversible = True

    def __init__(self, model, data, delimiter=";", update=False):
        # Operations are usually instantiated with arguments in migration
        # files. Store the values of them on self for later use.
        self.model = model
        self.data = data
        self.delimiter = delimiter
        self.update = update

    def state_forwards(self, app_label, state):
        # The Operation should take the 'state' parameter (an instance of
        # django.db.migrations.state.ProjectState) and mutate it to match
        # any schema changes that have occurred.
        pass

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        apps = to_state.apps
        model = apps.get_model(app_label, self.model)
        form = modelform_factory(model, exclude=[])

        records_added = 0
        records_updated = 0
        records_failed = 0

        if isinstance(self.data, (str, Path)):
            f = open(self.data, "r")
            data = UnicodeDictReader(f, delimiter=self.delimiter)
        else:
            data = self.data

        for row in data:
            if isinstance(row, tuple):
                # data is made up of namedtuple instances
                row = row._asdict()
            # Bind the row data to the form
            if self.update and row[model._meta.pk.name]:
                instance = model.objects.get(pk=row[model._meta.pk.name])
                bound_form = form(row, instance=instance)
            else:
                instance = None
                bound_form = form(row)
            # Check to see if the row data is valid.
            if bound_form.is_valid():
                # Row data is valid so save the record.
                bound_form.save()
                if instance:
                    records_updated += 1
                else:
                    records_added += 1
            else:
                logger.warning("Failed to load %s: %s" % (row, bound_form.errors.as_data()))
                records_failed += 1

        try:
            f.close()
        except UnboundLocalError:
            pass

        logger.info("%d records added" % records_added)
        logger.info("%d records updated" % records_updated)
        logger.info("%d records failed" % records_failed)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        # If reversible is True, this is called when the operation is reversed.
        pass

    def describe(self):
        # This is used to describe what the operation does in console output.
        return "Load data into a model from a list of dicts or a delimited file"


def get_month_from_day_number(day_number):
    first_day_of_year = datetime(datetime.today().year, 1, 1)
    _date = first_day_of_year + timedelta(days=day_number - 1)  # timedelta uses 0 based index
    return _date.month


def get_doc_strings_for_model(model_name):
    """
    Gets the doc strings defined in the model for references or help guide purposes

    model_name - have a format app_label:model e.g. baseline:community
    """
    app_label, model = model_name.split(":")
    model = apps.get_model(app_label=app_label, model_name=model)
    if model:
        return model.__doc__
    else:
        return f"Model '{model_name}' not found"
