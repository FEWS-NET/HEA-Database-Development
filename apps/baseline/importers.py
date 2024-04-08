import logging

from baseline.models import (
    Community,
    LivelihoodActivity,
    LivelihoodStrategy,
    LivelihoodZoneBaseline,
    WealthGroup,
)
from ingestion.decorators import register
from ingestion.importers import Importer
from ingestion.models import SpreadsheetLocation

logger = logging.getLogger(__name__)


@register
class LivelihoodZoneBaselineImporter(Importer):
    # Management command load_from_bss calls this importer's ingest() for a pre-saved LivelihoodZoneBaseline instance.

    class Meta:
        model = LivelihoodZoneBaseline
        dependent_model_fields = [
            "livelihood_strategies",
            "communities",
        ]


@register
class LivelihoodStrategyImporter(Importer):
    class Meta:
        model = LivelihoodStrategy
        fields = [
            "product",
            "strategy_type",
            "season",
            "unit_of_measure",
            "currency",
            "additional_identifier",
        ]
        parent_model_fields = [
            "livelihood_zone_baseline",
        ]
        dependent_model_fields = [
            "livelihoodactivity",
        ]

    def ingest_product(
        self,
        field_def,
        successful_mappings,
        failed_mappings,
        parent_instances,
        bss_value_extractors,
    ):
        # Scan down column A of the three Data sheets looking for a product alias.
        for sheet_name in ("Data", "Data2", "Data3"):
            row_count, column_count = parent_instances[LivelihoodZoneBaseline][0].load_sheet(sheet_name).shape
            for row in range(7, min(row_count, 3000)):
                new_spreadsheet_location, successful_mappings, failed_mappings = self.attempt_load_from_cell(
                    parent_instances=parent_instances,
                    field_def=field_def,
                    find_field=False,
                    sheet_name=sheet_name,
                    column=0,  # col A
                    row=row,
                    bss_value_extractors=bss_value_extractors,
                    successful_mappings=successful_mappings,
                    failed_mappings=failed_mappings,
                )
        return successful_mappings, failed_mappings, parent_instances

    def ingest_strategy_type(
        self,
        field_def,
        successful_mappings,
        failed_mappings,
        parent_instances,
        bss_value_extractors,
    ):
        # The products must already have been mapped, so we know how many LSes we have and which rows they're on.
        # This finds the strategy_types (~12), then generates a strategy_type SpreadsheetLocation per LS (~90).

        # 1. Identify SpreadsheetLocation of each strategy_type found in the BSS (approx 12):
        strategy_type_spreadsheet_locations = []
        for sheet_name in ("Data", "Data2", "Data3"):
            row_count, column_count = parent_instances[LivelihoodZoneBaseline][0].load_sheet(sheet_name).shape
            for row in range(10, min(row_count, 3000 + 1)):
                new_spreadsheet_location, successful_mappings, failed_mappings = self.attempt_load_from_cell(
                    parent_instances=parent_instances,
                    field_def=field_def,
                    find_field=False,
                    sheet_name=sheet_name,
                    column=0,  # all in column A
                    row=row,
                    bss_value_extractors=bss_value_extractors,
                    successful_mappings=successful_mappings,
                    failed_mappings=failed_mappings,
                )
                if new_spreadsheet_location:
                    strategy_type_spreadsheet_locations.append(new_spreadsheet_location)

        # 2. Generate a strategy_type SpreadsheetLocation per LivelihoodStrategy in the BSS (approx 90):
        # The first row of each LivelihoodStrategy has the product in col A, so we use product mappings to iterate LS.
        sl_per_livelihood_strategy = []
        for instance_number, product_sl in enumerate(successful_mappings["product"]):
            strategy_type_sl = self.get_strategy_type_for_instance(instance_number, successful_mappings)
            sl_per_livelihood_strategy.append(strategy_type_sl)

        # 3. Clean up working data:
        # Grab the PKs of the SLs not attached to any LS instance for deletion later
        sls_to_delete = [o.pk for o in strategy_type_spreadsheet_locations]

        # Generate a new SpreadsheetLocation per LivelihoodStrategy instance
        for instance_number, sl in enumerate(sl_per_livelihood_strategy):
            sl.pk = None
            sl.id = None
            sl.instance_number = instance_number
            sl.save()

        # Delete the strategy_type SpreadsheetLocations not attached to any LivelihoodStrategy instance
        SpreadsheetLocation.objects.filter(pk__in=sls_to_delete).delete()

        return successful_mappings, failed_mappings, parent_instances

    @staticmethod
    def get_strategy_type_for_instance(instance_number, successful_mappings):
        # The strategy type for a given LivelihoodStrategy instance is the one closest above it in the BSS:
        product = successful_mappings["product"][instance_number]
        strategy_types = successful_mappings["strategy_type"]
        st_index = 0
        while st_index < len(strategy_types) and (
            product.sheet_name != strategy_types[st_index].sheet_name or product.row < strategy_types[st_index].row
        ):
            st_index += 1
        return strategy_types[st_index]


@register
class CommunityImporter(Importer):
    class Meta:
        model = Community
        fields = [
            "name",
            "full_name",
            "code",
            "interview_number",
        ]
        dependent_model_fields = [
            "wealth_groups",
        ]

    def ingest_name(
        self,
        field_def,
        successful_mappings,
        failed_mappings,
        parent_instances,
        bss_value_extractors,
    ):
        # The community/village names are on row 4, repeated for each wealth category (on row 2).
        # So scan across the first wealth category accumulating village names.
        sheet_name = "Data"
        sheet = parent_instances[LivelihoodZoneBaseline][0].load_sheet(sheet_name)
        row = 4
        column = 1
        first_wc = sheet.iloc[2, column]
        while first_wc == sheet.iloc[2, column]:
            new_spreadsheet_location, successful_mappings, failed_mappings = self.attempt_load_from_cell(
                parent_instances=parent_instances,
                field_def=field_def,
                find_field=False,
                sheet_name=sheet_name,
                column=column,
                row=row,
                bss_value_extractors=bss_value_extractors,
                successful_mappings=successful_mappings,
                failed_mappings=failed_mappings,
            )
            column += 1
        return successful_mappings, failed_mappings, parent_instances

    def ingest_full_name(
        self,
        field_def,
        successful_mappings,
        failed_mappings,
        parent_instances,
        bss_value_extractors,
    ):
        # 1. Scan across Data sheet row 3 loading district names
        sheet_name = "Data"
        row = 3
        for name_loc in successful_mappings["name"]:
            new_spreadsheet_location, successful_mappings, failed_mappings = self.attempt_load_from_cell(
                parent_instances=parent_instances,
                field_def=field_def,
                find_field=False,
                sheet_name=sheet_name,
                column=name_loc.column,
                row=row,
                bss_value_extractors=bss_value_extractors,
                successful_mappings=successful_mappings,
                failed_mappings=failed_mappings,
            )
        # 2. Prefix the village names
        for i, full_name_loc in enumerate(successful_mappings[field_def.name]):
            village_loc = successful_mappings["name"][i]
            full_name_loc.mapped_value = ", ".join((village_loc.mapped_value, full_name_loc.mapped_value))
        return successful_mappings, failed_mappings, parent_instances

    def ingest_code(
        self,
        field_def,
        successful_mappings,
        failed_mappings,
        parent_instances,
        bss_value_extractors,
    ):
        # 1. Populate in the same way as the name field
        successful_mappings, failed_mappings, parent_instances = self.ingest_name(
            field_def,
            successful_mappings,
            failed_mappings,
            parent_instances,
            bss_value_extractors,
        )
        # 2. Convert to lower case
        for loc in successful_mappings[field_def.name]:
            loc.mapped_value = loc.mapped_value.lower()
        return successful_mappings, failed_mappings, parent_instances


@register
class LivelihoodActivityImporter(Importer):
    class Meta:
        model = LivelihoodActivity
        fields = [
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_purchased",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "household_labor_provider",
            "strategy_type",
        ]
        parent_model_fields = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
        ]
        dependent_model_fields = [
            "milkproduction",
            "butterproduction",
            "meatproduction",
            "livestocksale",
            "cropproduction",
            "foodpurchase",
            "paymentinkind",
            "reliefgiftother",
            "fishing",
            "wildfoodgathering",
            "othercashincome",
            "otherpurchase",
        ]

    def ingest_quantity_produced(
        self,
        field_def,
        successful_mappings,
        failed_mappings,
        parent_instances,
        bss_value_extractors,
    ):
        # The product is specified on the first row of each LS.
        # Use them to iterate over each LS's rows, looking for quantity_produced field name aliases
        for strategy_i, strategy_loc in enumerate(parent_instances[LivelihoodStrategy]["product"]):
            sheet = parent_instances[LivelihoodZoneBaseline][0].load_sheet(strategy_loc.sheet_name)
            row_count, column_count = sheet.shape
            row = strategy_loc.row

            # If there's a subsequent LS on the same sheet, scan col A until that row, otherwise scan to bottom
            if (
                strategy_i + 1 < len(parent_instances[LivelihoodStrategy]["product"])
                and parent_instances[LivelihoodStrategy]["product"][strategy_i + 1].sheet_name
                == strategy_loc.sheet_name
            ):
                last_row = parent_instances[LivelihoodStrategy]["product"][strategy_i + 1].row - 1
            else:
                last_row = min(row_count, 3000)

            # locate the field in col A
            while row < last_row:
                new_spreadsheet_location, successful_mappings, failed_mappings = self.attempt_load_from_cell(
                    parent_instances=parent_instances,
                    field_def=field_def,
                    find_field=True,
                    sheet_name=strategy_loc.sheet_name,
                    column=0,
                    row=row,
                    bss_value_extractors=bss_value_extractors,
                    successful_mappings=successful_mappings,
                    failed_mappings=failed_mappings,
                )
                # When we locate a quantity_produced field alias in col A, stop looking and load the values
                if new_spreadsheet_location:
                    break
                row += 1

            # get the value on row `row` for each LA.
            # There is 1 WealthGroup per WealthCategory per Community, plus 1 WG per WealthCategory with no Community
            for wg_i, wg_loc in enumerate(parent_instances[WealthGroup]["wealth_category"]):
                new_spreadsheet_location, successful_mappings, failed_mappings = self.attempt_load_from_cell(
                    parent_instances=parent_instances,
                    field_def=field_def,
                    find_field=False,
                    sheet_name=strategy_loc.sheet_name,
                    column=wg_loc.column,
                    row=row,
                    bss_value_extractors=bss_value_extractors,
                    successful_mappings=successful_mappings,
                    failed_mappings=failed_mappings,
                )
