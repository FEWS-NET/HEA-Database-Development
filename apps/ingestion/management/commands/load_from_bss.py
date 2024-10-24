import datetime
import logging
import sys
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.templates import TemplateCommand

from baseline.importers import LivelihoodZoneBaselineImporter
from baseline.models import LivelihoodStrategy, LivelihoodZoneBaseline
from ingestion.mappers import MapperFactory

logger = logging.getLogger(__name__)


class Command(TemplateCommand):
    help = "Loads a BSS into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "pk",
            help=(
                "Optional: Livelihood Zone Baseline ID to import. If omitted, loads the most recently "
                "modified Livelihood Zone Baseline."
            ),
            nargs="*",
            default="",
        )
        # TODO: --verbose?

    def handle(self, pk, **options):
        # This will be called by an 'Refresh from BSS' button on the LivelihoodZoneBaseline admin detail screen.
        # parent_instances will contain the root, saved LivelihoodZoneBaseline parent with spreadsheet uploaded.
        # For now, check for lzb id on command line or use most recently modified.
        # (This is just an example, would need to initialize Django for this to work directly.)
        if sys.argv and sys.argv[0].isdigit():
            root_lzb = LivelihoodZoneBaseline.objects.get(pk=int(sys.argv[0]))
        else:
            root_lzb = LivelihoodZoneBaseline.objects.order_by("-modified").first()
        parent_instances = {
            LivelihoodZoneBaseline: [root_lzb],
        }
        field_def = LivelihoodStrategy._meta.get_field("livelihood_zone_baseline")

        # Instantiate importer and mapper factory here.
        # All cache and state are discarded after this import run.
        importer = LivelihoodZoneBaselineImporter(MapperFactory())

        try:
            importer.ingest(field_def, parent_instances)
            self.dump_run_db(root_lzb.pk)
        except Exception as e:
            logger.warning(f"Error occurred ingesting {root_lzb} id {root_lzb.pk}.", exc_info=e)
            self.dump_run_db(root_lzb.pk)
            raise  # so runner can detect success or failure

    @staticmethod
    def dump_run_db(lzb_pk):
        """
        Gives full traceability for a particular run.
        Also removes the risk of accidentally flushing aliases entered direct to the db while working on a BSS.
        """
        Path("import_run_data").mkdir(parents=True, exist_ok=True)
        call_command(
            "dumpdata",
            *settings.PROJECT_APPS,
            # The below tables contain aliases, but decided to dump everything as it is only a few hundred K gzipped:
            # "common.ClassifiedProduct",
            # "common.UnitOfMeasure",
            # "ingestion.BssValueExtractor",
            # "ingestion.SpreadsheetLocation",
            # "ingestion.ChoiceAlias",
            # "ingestion.FieldNameAlias",
            # "metadata.LivelihoodCategory",
            # "metadata.WealthCharacteristic",
            # "metadata.SeasonalActivityType",
            # "metadata.WealthGroupCategory",
            # "metadata.HazardCategory",
            # "metadata.Market",
            # "metadata.Season",
            indent=4,
            output=f"import_run_data/refdata_{datetime.datetime.now().isoformat()}_lzb_{lzb_pk}.json.gz",
        )
