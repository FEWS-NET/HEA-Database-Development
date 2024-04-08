import logging
from inspect import isclass

from ingestion.exceptions import ImportException
from ingestion.importers import Importer

logger = logging.getLogger(__name__)


def register(importer_class=None):
    def report_invalid_importer(klass):
        raise ImportException(
            f"Attempted to @register an importer class which is not a sub-class of Importer. Class {klass.__name__}."
        )

    def attach_importer_to_model(importer_class):
        if isclass(importer_class) and issubclass(importer_class, Importer):
            importer_class.Meta.model.importer = importer_class
            print(
                f"Attached importer class to model. {importer_class.__name__} to {importer_class.Meta.model.__name__}"
            )
            return importer_class
        else:
            report_invalid_importer(importer_class)

    # Usage @register or register(Importer) (ie, without brackets or without @)
    if importer_class is not None:
        return attach_importer_to_model(importer_class)

    # Usage @register() (ie, with brackets and @)
    def inner(importer_class_inner):
        return attach_importer_to_model(importer_class)

    return inner
