import contextlib
import csv
import importlib
import logging
import re
from copy import deepcopy
from datetime import datetime, timedelta
from io import BytesIO, StringIO
from pathlib import Path

import pandas as pd
from dateutil.relativedelta import relativedelta
from django.apps import apps
from django.db.migrations.operations.base import Operation
from django.forms.models import modelform_factory
from openpyxl.utils import get_column_letter
from treebeard.mp_tree import MP_Node

logger = logging.getLogger(__name__)


DEFAULT_DATES = {
    "ten_years_ago": lambda: datetime.date.today() + relativedelta(years=-10, day=1),
    "five_years_ago": lambda: datetime.date.today() + relativedelta(years=-5, day=1),
    "three_years_ago": lambda: datetime.date.today() + relativedelta(years=-3, day=1),
    "two_years_ago": lambda: datetime.date.today() + relativedelta(years=-2, day=1),
    "one_year_ago": lambda: datetime.date.today() + relativedelta(years=-1, day=1),
    "last_month_start": lambda: datetime.date.today() + relativedelta(months=-1, day=1),
    "last_month": lambda: datetime.date.today().replace(day=1) - datetime.timedelta(days=1),
    "second_last_month_start": lambda: datetime.date.today() + relativedelta(months=-2, day=1),
    "second_last_month": lambda: datetime.date.today() + relativedelta(months=-2, day=31),
    "third_last_month": lambda: datetime.date.today() + relativedelta(months=-3, day=31),
    "fourth_last_month": lambda: datetime.date.today() + relativedelta(months=-4, day=31),
    "sixth_last_month": lambda: datetime.date.today() + relativedelta(months=-6, day=31),
    "today": lambda: datetime.date.today(),
    "tomorrow": lambda: datetime.date.today() + relativedelta(days=1),
}


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


def class_from_name(full_name):
    """
    Load a class from a dot-notation string name
    """
    try:
        module_name, class_name = full_name.rsplit(".", 1)
    except ValueError as e:
        raise ValueError(f"Can't extract separate module and class names from '{full_name}'") from e
    # load the module, will raise ImportError if module cannot be loaded
    m = importlib.import_module(module_name)
    # get the class, will raise AttributeError if class cannot be found
    c = getattr(m, class_name)
    return c


def get_frozen_treebeard_model(model):
    """
    Create a new model class from a frozen orm model that also contains the Treebeard functions
    """
    # Build a new base model that we can alter
    BaseModel = deepcopy(model)
    BaseModel._meta = deepcopy(model._meta)
    BaseModel._meta.abstract = True
    BaseModel._meta.local_fields = [
        field for field in model._meta.local_fields if field.name not in ("path", "depth", "numchild")
    ]

    # Make sure  that we also set the node_order_by. It's OK to copy this from
    # the current version of the model, because it is not allowed to change
    # once there is any data in the table.
    CurrentModel = class_from_name(".".join((model._meta.app_label, "models", model.__name__)))

    # Create a new class with MP_Node functionality and the fields currently
    # in the database
    class Frozen_MP_Model(MP_Node, BaseModel):  # noqa: N801
        node_order_by = getattr(CurrentModel, "node_order_by", None)

        class Meta:
            app_label = model._meta.app_label
            db_table = model._meta.db_table
            ordering = ()  # Required for correct ordering of Treebeard subclasses
            abstract = False

    if not hasattr(apps, "frozen_models_registry"):
        apps.frozen_models_registry = []
    apps.frozen_models_registry.append((model._meta.app_label, Frozen_MP_Model))

    # We don't want to cache the model
    del apps.all_models[model._meta.app_label]["frozen_mp_model"]

    return Frozen_MP_Model


@contextlib.contextmanager
def conditional_logging(logger=None, flush_level=logging.ERROR, capacity=500):
    """
    A context manager that logs messages to a buffer and only outputs them if one of the messages is at or above
    the flush_level.

    """
    if not isinstance(logger, logging.Logger):
        logger = logging.getLogger(logger)

    old_handlers = [handler for handler in logger.handlers]
    for handler in old_handlers:
        logger.removeHandler(handler)

    new_handlers = [
        logging.handlers.MemoryHandler(capacity, flushLevel=flush_level, target=handler, flushOnClose=False)
        for handler in old_handlers
    ]
    for handler in new_handlers:
        logger.addHandler(handler)

    try:
        yield
    except Exception:
        for handler in new_handlers:
            handler.flush()
        raise
    finally:
        for handler in old_handlers:
            logger.addHandler(handler)
        for handler in new_handlers:
            logger.removeHandler(handler)


def get_month_from_day_number(day_number):
    first_day_of_year = datetime(datetime.today().year, 1, 1)
    _date = first_day_of_year + timedelta(days=day_number - 1)  # timedelta uses 0 based index
    return _date.month


def b74encode(n):
    """Generates short, unique strings from a sequence number, for test data for short CharFields
    (5,476 codes in two characters instead of the 100 that 00-99 permits)."""
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_`\"!$'()*,-+"
    if n == 0:
        return alphabet[n]
    encoded = ""
    while n > 0:
        n, r = divmod(n, len(alphabet))
        encoded = alphabet[r] + encoded
    return encoded


def markdown_to_data(table: str):
    """
    Convert a Markdown table to list of rows.
    """
    data = []
    for line in StringIO(table).readlines():
        line = line.strip()
        # Ignore blank lines, they aren't part of the table, just part of the string formatting
        # And lines consisting only of |-:, which are a Markdown table header
        if line and not re.match(r"^[\|:-]+$", line):
            # Remove the trailing \n and split the line on the cell separator, dropping the first and last columns
            # (which are before and after the actual data)
            line = line.split("|")[1:-1]
            row = [float(x.strip(" ")) if x.strip(" ").isnumeric() else x.strip(" ") for x in line]
            data.append(row)
    return data


def markdown_to_dataframe(table: str):
    """
    Return a Pandas DataFrame dataset converted from a Markdown table.

    Typically used to prepare test data for unit tests based on spreadsheets.
    """
    return pd.DataFrame(markdown_to_data(table))


def markdown_to_excel(tables: str | list[str] | dict[str, str]):
    """
    Return a BytesIO containing .xlsx workbook converted from an iterable of Markdown tables, or a single table.

    Typically used to prepare test data for unit tests based on spreadsheets.
    """
    if isinstance(tables, str):
        # single table
        tables = {"Sheet1": tables}
    elif not isinstance(tables, dict):
        # A list or other iterable, so enumerate the sheets
        tables = {f"Sheet{i+1}": table for i, table in enumerate(tables)}

    with BytesIO() as book:
        writer = pd.ExcelWriter(book, engine="openpyxl")
        for name, table in tables.items():
            df = markdown_to_dataframe(table)
            # Write the dataframe to the buffer
            df.to_excel(writer, sheet_name=name, header=False, index=False)
        writer.save()
        return book.getvalue()


def excel_to_markdown(
    filepath_or_buffer, sheet_name=None, rows: int = 10, columns: int = 10, include_row_number=False
):
    """
    Convert an Excel workbook to a dict of Markdown table strings

    Typically used to prepare test data for unit tests based on spreadsheets.

    Usage:
        tables = excel_to_markdown(filename)
        print(list(tables.values())[0])
        print(tables["Other Sheet"])
    """
    tables = {}
    with pd.ExcelFile(filepath_or_buffer) as book:
        sheet_names = [sheet_name] if sheet_name else book.sheet_names
        for sheet_name in sheet_names:
            df = pd.read_excel(book, sheet_name=sheet_name, header=None).fillna("")
            # Set the column names to match Excel
            df.columns = [get_column_letter(col + 1) for col in df.columns]
            # Use a 1-based index to match the Excel Row Number
            df.index += 1
            tables[sheet_name] = df.iloc[:rows, :columns].to_markdown(index=include_row_number)

    return tables[sheet_names[0]] if len(sheet_names) == 1 else tables


def get_all_subclasses(cls):
    """
    Recursively get all subclasses of a class.

    :param cls: The class for which to find all subclasses.
    :return: A set of all subclasses.
    """
    subclasses = set(cls.__subclasses__())
    for subclass in subclasses.copy():
        subclasses.update(get_all_subclasses(subclass))
    return subclasses


# fmt: off
normal_map = {'À': 'A', 'Á': 'A', 'Â': 'A', 'Ã': 'A', 'Ä': 'A',
             'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a', 'ª': 'A',
             'È': 'E', 'É': 'E', 'Ê': 'E', 'Ë': 'E',
             'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
             'Í': 'I', 'Ì': 'I', 'Î': 'I', 'Ï': 'I',
             'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
             'Ò': 'O', 'Ó': 'O', 'Ô': 'O', 'Õ': 'O', 'Ö': 'O',
             'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o', 'º': 'O',
             'Ù': 'U', 'Ú': 'U', 'Û': 'U', 'Ü': 'U',
             'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
             'Ñ': 'N', 'ñ': 'n',
              'Ç': 'C', 'ç': 'c',
              '§': 'S', '³': '3', '²': '2', '¹': '1'}
# fmt: on

# Minimal normalization, doesn't attempt to coerce characters such as æ, which are locale-dependent.
# Example usage: "café".translate(normalize)
normalize = str.maketrans(normal_map)
