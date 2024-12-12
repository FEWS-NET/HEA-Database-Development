import importlib
import logging
from abc import ABC
from collections import defaultdict

import pandas as pd
from django.db import models
from django.forms import model_to_dict

from baseline.models import LivelihoodZoneBaseline
from ingestion.exceptions import ImportException
from ingestion.mappers import get_fully_qualified_field_name
from ingestion.models import (
    BssValueExtractor,
    ImportLog,
    ImportRun,
    ScanLog,
    SpreadsheetLocation,
)

logger = logging.getLogger(__name__)


class Importer(ABC):
    class Meta:
        model = None
        fields = []
        parent_model_fields = []
        dependent_model_fields = []

    def __init__(self, mapper_factory):
        self.mapper_factory = mapper_factory
        if not hasattr(self.Meta, "fields"):
            self.Meta.fields = []
        if not hasattr(self.Meta, "parent_model_fields"):
            self.Meta.parent_model_fields = []
        if not hasattr(self.Meta, "dependent_model_fields"):
            self.Meta.dependent_model_fields = []

    def ingest(self, field_def, parent_instances, import_run=None):
        if not isinstance(self, self.Meta.model.importer):
            raise ImportException(f"Importer has not been registered. Add @register to {type(self).__name__}.")

        if not import_run:
            import_run = ImportRun(livelihood_zone_baseline=parent_instances[LivelihoodZoneBaseline][0])
            import_run.save()

        # a dict {field_name: [spreadsheet_location_1, spreadsheet_location_2, ]} with successfully mapped mapped_values  # NOQA: E501
        successful_mappings = defaultdict(list)
        # a dict {sheet: {column: {row: {field_name: [{successful_mappings: , parent_instances: , field_def: , sheet_name: , column: , row: , source_value: ,}, ]}}}  # NOQA: E501
        failed_mappings = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
        # a dict {field_name: [bss_value_extractor_1, bss_value_extractor_2, ]} for all fields in Meta.model
        bss_value_extractors = self._get_bss_value_extractors()

        # Calls ingest_{field} for each field to populate successful_mappings[field_name] with a list of SpreadsheetLocations.  # NOQA: E501
        # Populates SpreadsheetLocation.mapped_value with the code/id/value to save on the Meta.model instance.
        successful_mappings, failed_mappings, parent_instances = self.ingest_fields(
            successful_mappings,
            failed_mappings,
            parent_instances,
            bss_value_extractors,
            import_run,
        )
        self.log(
            logging.INFO,
            f"Mapping report for table {self.Meta.model.__name__}:\n"
            f"Successful mappings\n{successful_mappings}\nFailed mappings\n{failed_mappings}",
            import_run,
        )

        # successful_mappings now contains a list of SpreadsheetLocation instances per field, with source, parsed and mapped values saved.  # NOQA: E501
        # {field_name: [spreadsheet_location_for_field_on_instance_1, spreadsheet_location_for_field_on_instance_2, ... ]}  # NOQA: E501

        # Iterate over the successful_mappings lists, saving a Meta.model instance for each, pulling from parent_instances as nec.  # NOQA: E501
        parent_instances = self._save_instances(successful_mappings, parent_instances, import_run)

        # Call dependent (child) model importers, passing in parents so far
        parent_instances = self._load_dependent_models(parent_instances, import_run)

        # Delete failed mapping logs after a successful import
        ImportLog.objects.filter(
            log_level=logging.INFO,
            import_run=import_run,
            message__startswith="Value parsed but lookup failed",
        ).delete()

        # Return instances to the parent importer
        return parent_instances

    def ingest_fields(
        self,
        successful_mappings,
        failed_mappings,
        parent_instances,
        bss_value_extractors,
        import_run,
    ):
        for field_name in self.Meta.fields:
            field_def = self.Meta.model._meta.get_field(field_name)
            ingest_method = getattr(self, f"ingest_{field_name}", None)
            if callable(ingest_method):
                successful_mappings, failed_mappings, parent_instances = ingest_method(
                    field_def,
                    successful_mappings,
                    failed_mappings,
                    parent_instances,
                    bss_value_extractors[field_name],
                    import_run,
                )
            else:
                self.log(
                    logging.ERROR,
                    f"Method not found to ingest field {field_def.model.__name__}.{field_def.name}. "
                    f"Implement ingest_{field_def.name} on {type(self).__name__}.",
                    import_run,
                )
        return successful_mappings, failed_mappings, parent_instances

    def attempt_load_from_cell(
        self,
        parent_instances,
        field_def,
        find_field,
        sheet_name,
        column,
        row,
        bss_value_extractors,
        successful_mappings,
        failed_mappings,
        import_run,
    ):
        alias = matching_re = mapped_value = bss_value_extractor = None
        sheet = parent_instances[LivelihoodZoneBaseline][0].load_sheet(sheet_name)

        # See if the current cell matches any of the regexes in this field's BssValueExtractors
        source_value = sheet.iloc[row, column]
        if pd.isna(source_value):
            source_value = ""
        extractors = [e for e in bss_value_extractors if e.find_field == find_field]
        found = self.mapper_factory(field_def, find_field).map(extractors, source_value)

        if found:
            bss_value_extractor, matching_re, alias, mapped_value = found
            sl = SpreadsheetLocation(
                bss_value_extractor=bss_value_extractor,
                import_run=import_run,
                app_label=field_def.model._meta.app_label,
                model=field_def.model.__name__,
                field=field_def.name,
                find_field=find_field,
                sheet_name=sheet_name,
                column=column,
                row=row,
                regex=bss_value_extractor.regex if bss_value_extractor else "",
                matching_re=matching_re,
                source_value=source_value,
                alias=alias,
                mapped_value=mapped_value,
                instance_number=len(successful_mappings[field_def.name]),
                # destination_instance will be set when instance saved by save_instances
            )
            sl.save()
            successful_mappings[field_def.name].append(sl)

            self.log(
                logging.INFO,
                f"Lookup Success. "
                f"Field {get_fully_qualified_field_name(field_def)}.\n"
                f"  Sheet {sheet_name} column {column} row {row} BSS\n"
                f"  source value {source_value} mapped value {mapped_value} "
                f"  matching re {matching_re} alias {alias}.",
                import_run,
            )
        else:
            # Diagnosis will be aided by seeing what has been scanned and not mapped.
            # It will be very common to have missing aliases, but log, even though most will be scanning a wrong cell.
            failed_mappings[sheet_name][column][row][field_def.name].append(
                {
                    "successful_mappings": successful_mappings,
                    "parent_instances": parent_instances,
                    "field_def": field_def,
                    "sheet_name": sheet_name,
                    "column": column,
                    "row": row,
                    "source_value": source_value,
                }
            )
            # These logs are deleted on import success.
            self.log(
                logging.INFO,
                f"Value parsed but lookup failed, for "
                f"field {get_fully_qualified_field_name(field_def)}.\n"
                f"  Sheet {sheet_name} column {column} row {row} BSS\n"
                f"  lzb {parent_instances[LivelihoodZoneBaseline][0]}\n"
                f"  bss {parent_instances[LivelihoodZoneBaseline][0].bss.path}\n"
                f"  source value {source_value}\n"
                f"  aliases {', '.join((str(s) for s in self.mapper_factory(field_def).all_aliases()))}\n"
                f"  this field's successful mappings so far {successful_mappings[field_def.name]}.",
                import_run,
            )
            sl = None  # No SpreadsheetLocation to return as mapping not successful

        ScanLog(
            bss_value_extractor=bss_value_extractor,
            import_run=import_run,
            sheet_name=sheet_name,
            column=column,
            row=row,
            app_label=field_def.model._meta.app_label,
            model=field_def.model.__name__,
            field=field_def.name,
            find_field=find_field,
            source_value=source_value,
            alias=alias,
            regex=getattr(bss_value_extractor, "regex", None),
            matching_re=matching_re,
            mapped_value=mapped_value,
        ).save()

        return sl, successful_mappings, failed_mappings

    def _save_instances(self, successful_mappings, parent_instances, import_run):
        """
        Instantiates and saves the self.Meta.model instances from the parents and field mappings.
        Consumes this model's successful_mappings.
        Returns parent_instances for future importers.
        """
        if self.Meta.model not in parent_instances:
            parent_instances[self.Meta.model] = []

        # all successful_mappings lists have a SpreadsheeLocation per instance
        if not successful_mappings:
            self.log(logging.WARNING, f"No successful mappings for {self}.", import_run)
            return parent_instances

        num_instances = len(successful_mappings[self.Meta.fields[0]])

        for key, value in successful_mappings.items():
            if len(value) != num_instances:
                self.log(
                    logging.WARNING,
                    f"Instance count mismatch. "
                    f"{num_instances} {self.Meta.fields[0]} mappings but {len(value)} {key} mappings for {self}.",
                    import_run,
                )
            return parent_instances

        for instance_number in range(num_instances):

            instance = self.Meta.model()
            instance, parent_instances = self._set_foreign_keys_to_parents(instance, parent_instances)
            instance_ss_locs = {field: successful_mappings[field][instance_number] for field in self.Meta.fields}
            instance = self._set_instance_values(instance, instance_ss_locs, instance_number)

            # model.report_warnings logs any warnings of suspicious data, eg, calc or missing value
            if callable(getattr(instance, "report_warnings", None)):
                instance.report_warnings(instance_number, instance_ss_locs.values())
            else:
                self.log(logging.INFO, f"No report_warnings method found on {type(instance).__name__}.", import_run)

            try:
                instance.save()
                # Store join to the saved instance on the instance's SpreadsheetLocations
                for ss_loc in instance_ss_locs.values():
                    ss_loc.destination_instance = instance  # generic foreign key
                    ss_loc.save()
            except Exception:
                self.log(logging.WARNING, f"Error occurred saving {instance} instance.", import_run, exc_info=True)
            parent_instances[self.Meta.model].append(instance)
        return parent_instances

    def _load_dependent_models(self, parent_instances, import_run):
        """
        Calls the importers of the dependent models.
        """
        for field in self.Meta.dependent_model_fields:
            field_def = self.Meta.model._meta.get_field(field)

            # Check this is an incoming relation field:
            if not isinstance(field_def, models.fields.reverse_related.ManyToOneRel):
                self.log(
                    logging.ERROR,
                    f"{type(self).__name__}.Meta.dependent_model_fields must be a list of "
                    f"reverse_related.ManyToOneRel fields (foreign keys on other models to this one).",
                    import_run,
                )
            # Check that the related model has an importer registered:
            if not issubclass(getattr(field_def.related_model, "importer", None), Importer):
                # Perhaps the importer.py hasn't been imported (which runs the @register decorator):
                try:
                    importlib.import_module(f"{field_def.related_model._meta.app_label}.importers")
                except ImportError:
                    self.log(
                        logging.ERROR,
                        f"Module not found: {field_def.related_model._meta.app_label}.importers",
                        import_run,
                    )
                if not issubclass(getattr(field_def.related_model, "importer", None), Importer):
                    self.log(
                        logging.ERROR,
                        f"Importer not found for dependent model. {field_def.related_model.__name__}Importer class "
                        f"needs declaring and registering.",
                        import_run,
                    )
            # Instantiate importer here. All cache and state are discarded after this import run.
            importer = field_def.related_model.importer(self.mapper_factory)
            parent_instances = importer.ingest(field_def, parent_instances, import_run)
        return parent_instances

    def _set_foreign_keys_to_parents(self, instance, parent_instances):
        for parent_field in self.Meta.parent_model_fields:
            field_def = self.Meta.model._meta.get_field(parent_field)
            setattr(instance, parent_field, parent_instances[field_def.related_model][0])
        return instance, parent_instances

    def _set_instance_values(self, instance, instance_values, instance_number):
        # set values parsed and mapped from bss, recorded while scanning as SpreadsheetLocation instances
        for field in self.Meta.fields:
            ss_loc = instance_values[field]
            setattr(instance, field, ss_loc.mapped_value)
        return instance

    def _get_bss_value_extractors(self):
        queryset = BssValueExtractor.objects.filter(
            app_label=self.Meta.model._meta.app_label,
            model=self.Meta.model.__name__,
        )
        bss_value_extractors = defaultdict(list)
        for bss_value_extractor in queryset:
            bss_value_extractors[bss_value_extractor.field].append(bss_value_extractor)
        return bss_value_extractors

    @staticmethod
    def log(
        log_level,
        message,
        import_run,
        instance=None,
        sheet_name=None,
        column=None,
        row=None,
        app_label=None,
        model=None,
        field=None,
        source_value=None,
        matching_re=None,
        mapped_value=None,
        bss_value_extractor=None,
        regex=None,
        aliases=None,
        successful_mappings=None,
        failed_mappings=None,
        exc_info=None,
    ):
        logger.log(log_level, message, exc_info=exc_info)

        # Prepare model instances for saving to JSONField
        for param in (instance, bss_value_extractor):
            if isinstance(param, models.Model):
                instance = model_to_dict(instance)
        successful_mappings_dicts = defaultdict(list)
        if successful_mappings:
            for field_name, spreadsheet_locations in successful_mappings.items():
                for spreadsheet_location in spreadsheet_locations:
                    successful_mappings_dicts[field_name] = model_to_dict(spreadsheet_location)

        # TODO: Add traceback field
        ImportLog(
            import_run=import_run,
            log_level=log_level,
            message=message,
            instance=instance,
            sheet_name=sheet_name,
            column=column,
            row=row,
            app_label=app_label,
            model=model,
            field=field,
            source_value=source_value,
            matching_re=matching_re,
            mapped_value=mapped_value,
            bss_value_extractor=bss_value_extractor,
            regex=regex,
            aliases=aliases,
            successful_mappings=successful_mappings_dicts,
            failed_mappings=failed_mappings,
        ).save()
