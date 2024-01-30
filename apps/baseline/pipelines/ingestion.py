# Will be baseline.pipelines.ingestion
# @TODO Review imports
# import datetime
# import hashlib
import io
import itertools
import logging
import re
from collections.abc import Iterable
from pathlib import Path

import luigi
import openpyxl
import pandas as pd
import xlrd
import xlwt
from django.core.management import call_command
from django.db.models import ForeignKey
from kiluigi import PipelineError
from kiluigi.format import Pickle
from kiluigi.targets import GoogleDriveTarget, IntermediateTarget, LocalTarget
from kiluigi.utils import class_from_name, path_from_task

# from luigi.task import TASK_ID_INVALID_CHAR_REGEX, TASK_ID_TRUNCATE_HASH
from luigi.util import requires
from openpyxl.comments import Comment
from openpyxl.utils import get_column_letter
from openpyxl.utils.cell import coordinate_to_tuple, rows_from_range
from xlutils.copy import copy as copy_xls

from baseline.models import WealthGroupCharacteristicValue
from common.lookups import ClassifiedProductLookup, UnitOfMeasureLookup
from common.management.commands import verbose_load_data
from common.pipelines.format import JSON
from metadata.lookups import WealthCharacteristicLookup, WealthGroupCategoryLookup
from metadata.models import WealthCharacteristic

# from slugify import slugify


logger = logging.getLogger(__name__)


def get_index(search_text: str | list[str], data: pd.Series) -> tuple[int, int]:
    """
    Return the index of the first value in a Series that matches the text.

    Note that the search is case-insensitive.

    The text to search for can be a string or a list of strings, in which case the function
    returns the first cell that matches any of the supplied strings.
    """
    # Make sure we have an iterable that we can pass to `.isin()`
    if isinstance(search_text, str) or not isinstance(search_text, Iterable):
        search_text = [str(search_text)]
    # Make sure that the search terms are lowercase
    search_text = [str(search_term).lower() for search_term in search_text]
    # Convert the Series to a set of True/False values based on whether they match one of the
    # search_text values, and use idxmax to return the index of the first match.
    # This works because in Pandas True > False, so idxmax() returns the index of the first True.
    index = data.str.lower().isin(search_text).idxmax()
    return index


def get_unmatched_metadata(df: pd.DataFrame, column: str) -> pd.Series:
    """
    Return a series of original values that were not matched by a Lookup.
    """
    unmatched_metadata = (
        df[(df[column].isnull()) & ~((df[column + "_original"].isnull()) | (df[column + "_original"].eq("")))][
            column + "_original"
        ]
        .sort_values()
        .unique()
    )
    return unmatched_metadata


def verbose_pivot(df: pd.DataFrame, values: str | list[str], index: str | list[str], columns: str | list[str]):
    """
    Pivot a DataFrame, or log a detailed exception in the event of a failure

    Failures are typically caused by duplicate entries in the index.
    """
    # Make sure index and columns are lists so we can concatenate them in the error handler, if needed.
    if isinstance(index, str):
        index = [index]
    if isinstance(columns, str):
        columns = [columns]
    try:
        return pd.pivot(df, values=values, index=index, columns=columns).reset_index()
    except ValueError as e:
        # Need to fillna, otherwise the groupby returns an empty dataframe
        duplicates = df.fillna("").groupby(index + columns).size().reset_index(name="count")

        # Filter for the entries that appear more than once, i.e., duplicates
        duplicates = duplicates[duplicates["count"] > 1]

        error_df = pd.merge(df.fillna(""), duplicates[index + columns], on=index + columns)

        raise PipelineError(str(e) + "\n" + error_df.to_markdown()) from e


class GetBSS(luigi.ExternalTask):
    """
    External Task that returns a Target for accessing the BSS spreadsheet.
    """

    bss_path = luigi.Parameter(description="Path to the BSS file")

    def output(self):
        target = LocalTarget(Path(self.bss_path).expanduser().absolute(), format=luigi.format.Nop)
        if not target.exists():
            target = GoogleDriveTarget(
                self.bss_path,
                format=luigi.format.Nop,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            if not target.exists():
                raise PipelineError("No local or Google Drive file matching %s" % self.bss_path)
        return target


class GetBSSMetadata(luigi.ExternalTask):
    """
    External Task that returns a spreadsheet of metadata about all BSSs.
    """

    metadata_path = luigi.Parameter(description="Path to the BSS metadata")

    def output(self):
        target = LocalTarget(Path(self.metadata_path).expanduser().absolute(), format=luigi.format.Nop)
        if not target.exists():
            target = GoogleDriveTarget(
                self.metadata_path,
                format=luigi.format.Nop,
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            if not target.exists():
                raise PipelineError("No local or Google Drive file matching %s" % self.metadata_path)
        return target


class GetBSSCorrections(luigi.Task):
    """
    Return a DataFrame of corrections to make to one or more BSSs.
    """

    corrections_path = luigi.Parameter(default="", description="Path to the BSS corrections")

    def output(self):
        return IntermediateTarget(path_from_task(self) + ".pickle", format=Pickle, timeout=3600)

    def run(self):
        if self.corrections_path:
            target = LocalTarget(Path(self.corrections_path).expanduser().absolute(), format=luigi.format.Nop)
            if not target.exists():
                target = GoogleDriveTarget(
                    self.corrections_path,
                    format=luigi.format.Nop,
                    mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
                if not target.exists():
                    raise PipelineError("No local or Google Drive file matching %s" % self.corrections_path)
            with target.open() as input:
                corrections_df = pd.read_excel(input, "Corrections")
        else:
            corrections_df = pd.DataFrame(
                columns=[
                    "bss_path",
                    "worksheet_name",
                    "range",
                    "prev_value",
                    "value",
                    "correction_date",
                    "author",
                    "comment",
                ]
            )

        with self.output().open("w") as output:
            output.write(corrections_df)


@requires(bss=GetBSS, corrections=GetBSSCorrections)
class CorrectBSS(luigi.Task):
    def output(self):
        return IntermediateTarget(
            path_from_task(self) + Path(self.input()["bss"].path).suffix, format=luigi.format.Nop, timeout=3600
        )

    def run(self):
        with self.input()["corrections"].open() as input:
            corrections_df = input.read()

        # Find the <country>/<filename>.<ext> path to the file, relative to the root folder.
        path = f"{Path(self.bss_path).parent.name}/{Path(self.bss_path).name}"
        # Find the corrections for this BSS
        corrections_df = corrections_df[corrections_df["bss_path"] == path]

        if corrections_df.empty:
            # No corrections, so just leave the file unaltered
            with self.output().open("w") as output, self.input()["bss"].open() as input:
                output.write(input.read())

        else:
            if Path(self.input()["bss"].path).suffix == ".xls":
                # xlrd can only read XLS files, so we need to use xlutils.copy to create something we can edit
                with self.input()["bss"].open() as input:
                    wb = xlrd.open_workbook(file_contents=input.read(), formatting_info=True, on_demand=True)
            else:
                with self.input()["bss"].open() as input:
                    wb = openpyxl.load_workbook(input)
            wb = self.process(wb, corrections_df)
            with self.output().open("w") as output:
                wb.save(output)

    def process(
        self,
        wb: xlrd.book.Book | openpyxl.Workbook,
        corrections_df: pd.DataFrame,
    ) -> xlwt.Workbook | openpyxl.Workbook:
        """
        Process the Excel workbook and apply corrections and then return the corrected file.
        """
        if isinstance(wb, xlrd.book.Book):
            xlrd_wb = wb
            wb = copy_xls(wb)  # a writable workbook to be returned by this method
        else:
            xlrd_wb = None  # Required to suppress spurious unbound variable errors from Pyright
        for correction in corrections_df.itertuples():
            for row in rows_from_range(correction.range):
                for cell in row:
                    if isinstance(wb, xlwt.Workbook):
                        row, col = coordinate_to_tuple(cell)
                        prev_value = xlrd_wb.sheet_by_name(correction.worksheet_name).cell_value(row - 1, col - 1)
                        if (
                            xlrd_wb.sheet_by_name(correction.worksheet_name).cell(row - 1, col - 1).ctype
                            == xlrd.XL_CELL_ERROR
                        ):
                            # xlrd.error_text_from_code returns, eg, "#N/A"
                            prev_value = xlrd.error_text_from_code[
                                xlrd_wb.sheet_by_name(correction.worksheet_name).cell_value(row - 1, col - 1)
                            ]
                        self.validate_previous_value(cell, correction.prev_value, prev_value)
                        # xlwt uses 0-based indexes, but coordinate_to_tuple uses 1-based, so offset the values
                        wb.get_sheet(correction.worksheet_name).write(row - 1, col - 1, correction.value)
                    else:
                        cell = wb[correction.worksheet_name][cell]
                        self.validate_previous_value(cell, correction.prev_value, cell.value)
                        cell.value = correction.value
                        cell.comment = Comment(
                            f"{correction.author} on {correction.correction_date.date().isoformat()}: {correction.comment}",  # NOQA: E501
                            author=correction.author,
                        )

        return wb

    def validate_previous_value(self, cell, expected_prev_value, prev_value):
        # "#N/A" is inconsistently loaded as nan, even when copied and pasted in Excel or GSheets
        if (str(expected_prev_value) != str(prev_value)) & (
            {"nan", "#N/A"} != {str(expected_prev_value), str(prev_value)}
        ):
            raise PipelineError(
                "Unexpected prior value in source BSS. "
                f"BSS `{self.input()['bss'].name}`, cell `{cell}`, "
                f"value found `{prev_value}`, expected `{expected_prev_value}`."
            )


@requires(bss=CorrectBSS, metadata=GetBSSMetadata)
class NormalizeWB(luigi.Task):
    """
    Normalize the WB worksheet.

    Reads the WB worksheet and turns it into a nested dict that lists the LivelihoodZone, LivelihoodZoneBaseline,
    Community, WealthGroup and WealthGroupCharacteristicValue records, in the correct format for loading into the
    application via a Django Fixture.

    It uses Lookups to convert free text entries from the BSS into the correct metadata codes for WealthGroupCategory,
    WealthCharacteristic, Product, etc.
    """

    def output(self):
        return IntermediateTarget(path_from_task(self) + ".json", format=JSON, timeout=3600)

    def run(self):
        with self.input()["bss"].open() as input:
            data_df = pd.read_excel(input, "WB", header=None)
        with self.input()["metadata"].open() as input:
            metadata_df = pd.read_excel(input, "Metadata")

        # Find the <country>/<filename>.<ext> path to the file, relative to the root folder.
        path = f"{Path(self.bss_path).parent.name}/{Path(self.bss_path).name}"
        # Find the metadata for this BSS
        try:
            metadata = metadata_df[metadata_df["bss_path"] == path].iloc[0]
        except IndexError:
            raise PipelineError("No entry in BSS Metadata worksheet for %s" % path)

        data = self.process(data_df, metadata)

        with self.output().open("w") as output:
            output.write(data)

    def process(self, data_df: pd.DataFrame, metadata: pd.Series) -> dict:
        """
        Process the WB Sheet and return a Python dict of normalized data.

        The first rows of the sheet look like:
        | Row | A                         | B                   | C                                          | D                                          | E                                          | F                                          | G                |
        |-----|---------------------------|---------------------|--------------------------------------------|--------------------------------------------|--------------------------------------------|--------------------------------------------|------------------|
        |   0 | MALAWI HEA BASELINES 2015 | Southern Lakeshore  | Southern Lakeshore                         |                                            |                                            |                                            |                  |
        |   1 |                           |                     | Community interviews                       |                                            |                                            |                                            |                  |
        |   2 | WEALTH GROUP              |                     |                                            |                                            |                                            |                                            |                  |
        |   3 | District                  | Salima and Mangochi | Salima                                     | Salima                                     | Salima                                     | Salima                                     | Dedza            |
        |   4 | Village                   |                     | Mtika                                      | Pemba                                      | Ndembo                                     | Makanjira                                  | Kasakala         |
        |   5 | Interview number:         |                     | 1                                          | 2                                          | 3                                          | 4                                          | 5                |
        |   6 | Interviewers              |                     | Kandiwo, Ethel, Fyawupi, Daniel, Chipiliro | Kandiwo, Ethel, Fyawupi, Daniel, Chipiliro | Kandiwo, Ethel, Fyawupi, Chipiliro, Daniel | Kandiwo, Ethel, Fyawupi, Chipiliro, Daniel | Chipiliro, Imran |
        """  # NOQA: E501
        # Key in the result dict must match the name of the model class they will be imported to.
        # The value must be a list of instances to import into that model, where each instance
        # is a dict of field names and values.
        # If the field is a foreign key to a model that supports a natural key (i.e. the model has a `natural_key`
        # method), then the field value should be a list of components to the natural key.
        result = {
            "LivelihoodZone": [
                {
                    # Get country and code from the filename
                    "country": metadata["country"],
                    "code": metadata["code"],
                    "name": metadata["name"],
                }
            ],
            "LivelihoodZoneBaseline": [
                {
                    "livelihood_zone": metadata["code"],
                    "name": metadata["name"],
                    "source_organization": [
                        metadata["source_organization"],
                    ],  # natural key is always a list
                    "main_livelihood_category": str(metadata["main_livelihood_category"]).lower(),
                    "reference_year_start_date": metadata["reference_year_start_date"].date().isoformat(),
                    "reference_year_end_date": metadata["reference_year_end_date"].date().isoformat(),
                    "valid_from_date": metadata["valid_from_date"].date().isoformat(),
                    "valid_to_date": None
                    if pd.isna(metadata["valid_to_date"])
                    else metadata["valid_to_date"].date().isoformat(),
                    "data_collection_start_date": None
                    if pd.isna(metadata["data_collection_start_date"])
                    else metadata["data_collection_start_date"].date().isoformat(),
                    "data_collection_end_date": None
                    if pd.isna(metadata["data_collection_end_date"])
                    else metadata["data_collection_end_date"].date().isoformat(),
                    "publication_date": None
                    if pd.isna(metadata["publication_date"])
                    else metadata["publication_date"].date().isoformat(),
                }
            ],
        }

        # Find the communities
        # Transpose to get data in columns
        community_df = data_df.iloc[2:7].transpose()
        # Check that the columns are what we expect
        expected_column_sets = (["WEALTH GROUP", "District", "Village", "Interview number:", "Interviewers"],)
        found_columns = community_df.iloc[0].str.strip().tolist()
        if not any(found_columns == expected_columns for expected_columns in expected_column_sets):
            raise PipelineError("Cannot identify Communities from columns %s" % ", ".join(found_columns))
        # Normalize the column names
        community_df.columns = ["wealth_group_category", "district", "name", "interview_number", "interviewers"]
        community_df = community_df[1:]
        # Find the initial set of Communities by only finding rows that have both a `district` and a `community`,
        # and don't have a `wealth_group_category`. Also ignore the `Comments` row.
        community_df = (
            community_df[(community_df["district"] != "Comments") & (community_df["wealth_group_category"].isna())][
                ["district", "name", "interview_number", "interviewers"]
            ]
            .dropna(subset=["name"])
            .drop_duplicates()
        )
        # Create the full_name from the community and district, and fall back
        # to just the community name if the district is empty/nan.
        community_df["full_name"] = community_df.name.str.cat(community_df.district, sep=", ").fillna(
            community_df.name
        )
        community_df = community_df.drop(columns="district")
        # Add the natural key for the livelihood zone baseline
        community_df["livelihood_zone_baseline"] = community_df["full_name"].apply(
            lambda full_name: [metadata["code"], metadata["reference_year_end_date"].date().isoformat()]
        )

        # Replace NaN with "" ready for Django
        community_df = community_df.fillna("")
        result["Community"] = community_df.to_dict(orient="records")

        # Process the main part of the sheet to find the Wealth Group Characteristic Values

        # Find the column index of the last column that we are contains relevant data.
        # The final three relevant columns are Summary/From/To. Find Summary because
        # it is less likely to give a false positive than the From or To, and then add 2.
        last_col_index = get_index(["Summary"], data_df.iloc[3]) + 2

        # Create charactistics dataframe containing data from row 9 onwards and from column A
        # up to the summary/from/to columns
        char_df = data_df.iloc[8:, : last_col_index + 1]

        # Keep the row number to aid trouble-shooting.
        char_df["row"] = char_df.index + 1

        # Set the column names based on the interviewee wealth group category (Row 3)
        # and community full name (Rows 4 & 5)
        row_3_values = data_df.iloc[2, 2 : last_col_index - 2].values
        row_4_values = data_df.iloc[3, 2 : last_col_index - 2].values
        row_5_values = data_df.iloc[4, 2 : last_col_index - 2].values
        new_column_names = []
        for wealth_group_category, admin_name, community_name in zip(row_3_values, row_4_values, row_5_values):
            full_name = f"{community_name}, {admin_name}" if pd.notna(admin_name) else community_name
            wealth_group_category = wealth_group_category if pd.notna(wealth_group_category) else ""
            new_column_names.append(f"{full_name}:{wealth_group_category}")
        new_column_names = (
            ["characteristic_label", "wealth_group_category"]
            + new_column_names
            + ["summary", "min_value", "max_value", "row"]
        )
        char_df.columns = new_column_names

        # Fill NaN values in 'wealth_characteristic' from the previous non-null cell
        char_df["characteristic_label"] = char_df["characteristic_label"].fillna(method="ffill")

        # Get the 'wealth_characteristic', 'product' and 'unit_of_measure' from the 'characteristic_label'
        # We can't just use a regular WealthCharacteristicLookup.do_lookup() because we need to match the additional
        # 'product' and 'unit_of_measure' attributes using regexes. Therefore, we use regexes against the aliases to
        # set the product and/or unit_of_measure for those wealth characteristics where we expect those attributes to
        # be present, and then we use the regular WealthCharacteristicLookup.do_lookup() to match the remaining items.

        # Examples:
        # MWPHA_30Sep15: Land area cultivated - rainfed crops (acres)
        # NE01(BIL): Anes nbr possédés
        # NE01(BIL): Volaille nbr possédés
        # LR02: Oxen (no. owned)
        # SO18: Donkey number owned

        # Build a list of regex strings that map to a wealth characteristic, using the WealthCharacteristic.aliases
        # Each entry in the list is a tuple of the compiled regex and the code for the WealthCharacteristic.
        wealth_characteristic_regexes = []
        for wealth_characteristic in WealthCharacteristic.objects.exclude(
            has_product=False, has_unit_of_measure=False
        ).exclude(aliases__isnull=True):
            for alias in wealth_characteristic.aliases:
                alias = re.escape(alias)
                # replace the <product> or <unit_of_measure> placeholders with regex groups
                for attribute in "product", "unit_of_measure":
                    if attribute in alias:
                        alias = alias.replace(f"<{attribute}>", f"(?P<{attribute}>[a-z][a-z',/ \>\-\(\)]+)")
                alias = re.compile(alias)
                wealth_characteristic_regexes.append((alias, wealth_characteristic.code))

        # Define a function to return the wealth_characteristic, product and/or unit_of_measure from the label
        def get_attributes(characteristic_label: str):
            """
            Return a tuple of (wealth_characteristic, product, unit_of_measure) from a characteristic label.
            """
            attributes = {
                "wealth_characteristic": None,
                "product": None,
                "unit_of_measure": None,
            }
            for pattern, wealth_characteristic in wealth_characteristic_regexes:
                match = pattern.fullmatch(characteristic_label.lower().strip())
                if match:
                    attributes.update(match.groupdict())
                    attributes["wealth_characteristic"] = wealth_characteristic
                    # Return a Series so that Pandas will split the return value into multiple columns
                    return pd.Series(attributes)
            # No pattern matched
            # Return a Series so that Pandas will split the return value into multiple columns
            return pd.Series(attributes)

        # Extract the wealth_characteristic, product and unit_of_measure (if applicable) from the characteristic_label
        char_df[["wealth_characteristic", "product", "unit_of_measure"]] = char_df["characteristic_label"].apply(
            get_attributes
        )

        # Look up the metadata codes for WealthGroupCategory and WealthCharacteristic
        # We need to lookup the WealthCharacteristic before we can use it to mask the 'product' column below
        char_df = WealthGroupCategoryLookup().do_lookup(char_df, "wealth_group_category", "wealth_group_category")
        # Note that we use do_lookup(update=True) so that we don't overwrite the values that we matched using a regex
        # if there is no match. Also note that because the lookup runs after we have done the regex match, a wealth
        # characteristic that matches the characteristic label directly will overwrite a wealth characteristic that was
        # matched using a regex. This ensures that, for example, `Other: Motor Cycle` will match "Motor Cycle" and not
        # "Number Owned" (which has a regex to match "Other: <product>").
        char_df = WealthCharacteristicLookup().do_lookup(
            char_df, "characteristic_label", "wealth_characteristic", update=True
        )

        # Report any errors, because unmatched WealthCharacteristics that contain a product reference may cause errors
        # when reshaping the dataframe. Note that we don't raise an exception here - ValidateBaseline will do that if
        # we get that far. But we do print the error message to help with troubleshooting.
        for value in get_unmatched_metadata(char_df, "wealth_characteristic"):
            logger.warning(
                f"Unmatched imported metadata for WealthGroupCharacteristicValue with wealth_characteristic '{value}'"
            )  # NOQA: E501

        # Copy the product from the previous cell for rows that need a product but don't specify it.
        # We do this by setting the missing values to pd.NA and then using .ffill()
        # Note that we need to replace the None with something else during the ffill() so that it is only actual pd.NA
        # values that are replaced
        product_characteristics = WealthCharacteristic.objects.filter(has_product=True).values_list("code", flat=True)
        char_df["product"] = (
            char_df["product"]
            .replace({None: ""})
            .mask(
                char_df["wealth_characteristic"].isin(list(product_characteristics)) & pd.isna(char_df["product"]),
                pd.NA,
            )
            .ffill()
            .replace({"": None})
        )

        # Copy the unit_of_measure from the previous cell for rows that need a unit_of_measure but don't specify it.
        # We do this by setting the missing values to pd.NA and then using .ffill()
        # Note that we need to replace the None with something else during the ffill() so that it is only actual pd.NA
        # values that are replaced
        unit_of_measure_characteristics = WealthCharacteristic.objects.filter(has_unit_of_measure=True).values_list(
            "code", flat=True
        )
        char_df["unit_of_measure"] = (
            char_df["unit_of_measure"]
            .replace({None: ""})
            .mask(
                char_df["wealth_characteristic"].isin(list(unit_of_measure_characteristics))
                & pd.isna(char_df["unit_of_measure"]),
                pd.NA,
            )
            .ffill()
            .replace({"": None})
        )

        # It is possible that the characteristic label is just a bare product, e.g. "Chickens".
        # Note that we use do_lookup(update=True) so that we don't overwrite the values that we matched using a regex
        # if there is no match, and we set require_match=False because there may be no labels that are a bare product.
        char_df = ClassifiedProductLookup(require_match=False).do_lookup(
            char_df, "characteristic_label", "product", update=True
        )
        # Drop product_original to avoid "ValueError: Per-column arrays must each be 1-dimensional" caused by duplicate
        # product_original columns when applying pd.melt below.
        char_df = char_df.drop(columns="product_original")
        # If we matched a product but we haven't found a wealth characteristic yet, then the wealth characteristic is
        # "number owned".
        char_df["wealth_characteristic"] = char_df["wealth_characteristic"].mask(
            char_df["wealth_characteristic"].isna() & char_df["product"].notna(), "number owned"
        )

        # Lookup the CPC code from the product label
        char_df = ClassifiedProductLookup().do_lookup(char_df, "product", "product")

        # Lookup the Unit of Measure
        char_df = UnitOfMeasureLookup().do_lookup(char_df, "unit_of_measure", "unit_of_measure")

        # Melt the dataframe
        char_df = pd.melt(
            char_df,
            id_vars=[
                "row",
                "characteristic_label",
                "product_original",
                "product",
                "unit_of_measure_original",
                "unit_of_measure",
                "wealth_characteristic_original",
                "wealth_characteristic",
                "wealth_group_category_original",
                "wealth_group_category",
            ],
            value_vars=char_df.columns[2:-1],
            var_name="interview_label",
            value_name="value",
        )

        # Add a column containing the original column label, to aid trouble-shooting.
        mapping_dict = {value: get_column_letter(idx + 1) for idx, value in enumerate(new_column_names)}
        mapping_dict["row"] = None  # column 'row' was added by us and isn't a column in the workbook
        char_df["column"] = char_df["interview_label"].map(mapping_dict)

        # Split 'label' into 'interviewee_wealth_group_category' and 'full_name'
        char_df[["full_name", "interviewee_wealth_group_category"]] = char_df["interview_label"].str.split(
            ":", expand=True, n=1
        )

        # Drop rows where 'value' is NaN,
        # or wealth category is blank (which is the total row for percentage of households)
        char_df = char_df.dropna(subset=["value", "wealth_group_category"])

        # Also drop rows where there is no Community, and which aren't the summary.
        # These rows came from blank columns in the worksheet.from django.core.exceptions import ValidationError

        char_df = char_df[~char_df["interview_label"].eq("nan:")]

        # Drop rows where 'value' is NaN,
        # or wealth group category is blank (which is the total row for percentage of households)
        char_df = char_df.dropna(subset=["value", "wealth_group_category"])

        # Also drop rows containing the percentage of households estimate from a Wealth Group-level interview,
        # estimating the percentage for the other Wealth Categories. I.e. for the "VP" Wealth Group interview
        # we only store the percentage of households estimated for the "VP" Wealth Group Category, and not
        # those for P, M and B/O.
        char_df = char_df[
            ~(
                char_df["wealth_characteristic"].eq("percentage of households")
                & ~char_df["interviewee_wealth_group_category"].isna()
                & ~char_df["wealth_group_category_original"].eq(char_df["interviewee_wealth_group_category"])
            )
        ]

        # Split out the summary data
        summary_df = char_df[char_df["interview_label"].isin(["summary", "min_value", "max_value"])]
        # Drop unwanted columns
        summary_df = summary_df.drop(["full_name", "interviewee_wealth_group_category", "column"], axis="columns")
        # Pivot the value, min_value and max_value back into columns
        summary_df = verbose_pivot(
            summary_df,
            values="value",
            index=[col for col in summary_df.columns if col not in ["interview_label", "value"]],
            columns="interview_label",
        )
        summary_df.columns.name = None
        summary_df = summary_df.rename(columns={"summary": "value"})
        # Add the source column
        summary_df["reference_type"] = WealthGroupCharacteristicValue.CharacteristicReference.SUMMARY
        # Summary Wealth Group Characteristic Values don't have a community
        summary_df["full_name"] = None

        # Drop the summary data from the main dataframe
        char_df = char_df[~char_df["interview_label"].isin(["summary", "min_value", "max_value"])]

        # Add the source column to the main dataframe
        # Rows with an interviewee wealth group category are from the Wealth Group-level Form 4 interview.
        char_df["reference_type"] = char_df["interviewee_wealth_group_category"].where(
            char_df["interviewee_wealth_group_category"] == "",
            WealthGroupCharacteristicValue.CharacteristicReference.WEALTH_GROUP,
        )
        # Rows without an interviewee wealth group category are from the Community-level Form 3 interview.
        char_df["reference_type"] = char_df["reference_type"].mask(
            char_df["reference_type"] == "", WealthGroupCharacteristicValue.CharacteristicReference.COMMUNITY
        )

        # Community and Wealth Group interviews don't have min_value or max_value
        char_df["max_value"] = None
        char_df["min_value"] = None

        # Add the summary df back into the main df, keeping only the columns
        char_df = pd.concat([char_df, summary_df])

        # The percentage of households should be stored as a number between 1 and 100,
        # but may be stored in the BSS (particularly in the summary column) as a
        # decimal fraction between 0 and 1, so correct those values
        char_df.loc[
            char_df["wealth_characteristic"].eq("percentage of households")
            & (pd.to_numeric(char_df["value"], errors="coerce") < 1),
            "value",
        ] *= 100

        # Add the natural key for the Wealth Group
        char_df["wealth_group"] = char_df[["wealth_group_category", "full_name"]].apply(
            lambda row: [
                metadata["code"],
                metadata["reference_year_end_date"].date().isoformat(),
                row["wealth_group_category"],
                row["full_name"],
            ],
            axis="columns",
        )

        # The Wealth Groups also include the household size and percentage of households,
        # so derive them from the Wealth Group Characteristic Values. We want the rows from char_df
        # for those characteristics, where the source is either the Wealth Group Interview
        # or the Summary.
        wealth_group_df = char_df[
            char_df["wealth_characteristic"].isin(["percentage of households", "household size"])
            & char_df["reference_type"].isin(
                [
                    WealthGroupCharacteristicValue.CharacteristicReference.WEALTH_GROUP,
                    WealthGroupCharacteristicValue.CharacteristicReference.SUMMARY,
                ]
            )
        ]

        # Make sure that the names in the Wealth Group-level interviews match
        # the names in the in the Community-level interviews that were used to
        # create the Community records
        unmatched_full_names = wealth_group_df[
            pd.notna(wealth_group_df["full_name"]) & ~wealth_group_df["full_name"].isin(community_df.full_name)
        ][["full_name", "column", "row"]]
        if not unmatched_full_names.empty:
            raise PipelineError(
                "Unmatched Community.full_name in Wealth Group interviews:\n%s" % unmatched_full_names.to_markdown()
            )

        # Drop unwanted columns
        wealth_group_df = wealth_group_df.drop(
            ["wealth_characteristic_original", "product", "product_original"], axis="columns"
        )

        # Pivot the percentage of households and household size back into columns
        wealth_group_df = verbose_pivot(
            wealth_group_df,
            values="value",
            index=["wealth_group_category", "full_name"],
            columns="wealth_characteristic",
        )
        wealth_group_df = wealth_group_df.rename(
            columns={
                "percentage of households": "percentage_of_households",
                "household size": "average_household_size",
            }
        )

        # Make sure that we have a Wealth Group for every combination of Wealth Group Category and Community,
        # because sometimes there is no Wealth Group-level (Form 4) data but there is Community-level (Form 3)
        # data for the Wealth Group.
        # Generate all possible combinations of unique 'full_name' and 'wealth_group_category'
        all_combinations = pd.DataFrame(
            list(
                itertools.product(
                    wealth_group_df["full_name"].unique(), wealth_group_df["wealth_group_category"].unique()
                )
            ),
            columns=["full_name", "wealth_group_category"],
        )
        wealth_group_df = pd.merge(
            all_combinations, wealth_group_df, on=["full_name", "wealth_group_category"], how="outer"
        )

        # Add the natural key for the livelihood zone baseline and community
        wealth_group_df["livelihood_zone_baseline"] = wealth_group_df["full_name"].apply(
            lambda full_name: [metadata["code"], metadata["reference_year_end_date"].date().isoformat()]
        )
        wealth_group_df["community"] = wealth_group_df["full_name"].apply(
            lambda full_name: None
            if pd.isna(full_name)
            else [metadata["code"], metadata["reference_year_end_date"].date().isoformat(), full_name]
        )
        wealth_group_df = wealth_group_df.drop(columns="full_name")

        # Add the Wealth Groups to the result
        result["WealthGroup"] = wealth_group_df.to_dict(orient="records")

        # Add the Wealth Group Characteristic Values to the result
        result["WealthGroupCharacteristicValue"] = char_df.to_dict(orient="records")

        return result


@requires(bss=CorrectBSS, metadata=GetBSSMetadata)
class NormalizeData(luigi.Task):
    """
    Normalize the Data worksheet.

    Reads the WB worksheet and turns it into a nested dict that lists the LivelihoodStrategy and LivelihoodActivity
    records, in the correct format for loading into the application via a Django Fixture.

    It uses Lookups to convert free text entries from the BSS into the correct metadata codes for WealthGroupCategory,
    Product, UnitOfMeasure, etc.
    """

    def output(self):
        return IntermediateTarget(path_from_task(self) + ".json", format=JSON, timeout=3600)

    def run(self):
        with self.input()["bss"].open() as input:
            data_df = pd.read_excel(input, "Data", header=None)
        with self.input()["metadata"].open() as input:
            metadata_df = pd.read_excel(input, "Metadata")

        # Find the <country>/<filename>.<ext> path to the file, relative to the root folder.
        path = f"{Path(self.bss_path).parent.name}/{Path(self.bss_path).name}"
        # Find the metadata for this BSS
        metadata = metadata_df[metadata_df["bss_path"] == path].iloc[0]

        data = self.process(data_df, metadata)

        with self.output().open("w") as output:
            output.write(data)

    def process(self, data_df: pd.DataFrame, metadata: pd.Series) -> dict:
        """
        Process the Data worksheet and return a Python dict of normalized data.

        The Data worksheet contains Livelihood Stategy and Livelihood Activity data for the Baseline.

        The first rows of the sheet contain the Wealth Group metadata. The immediately following
        rows contains some summary information, and then data on the Livelihood Activities and
        Livelihood Strategies starts around row 57.

        |     | A                                             | M               | N               | O               | P               |
        |-----|-----------------------------------------------|-----------------|-----------------|-----------------|-----------------|
        | 0   | MALAWI HEA BASELINES 2015                     |                 |                 |                 |                 |
        | 1   |                                               |                 |                 |                 |                 |
        | 2   | WEALTH GROUP                                  | Middle          | Middle          | Middle          | Middle          |
        | 3   | District/Ward number                          | Kasungu         | Kasungu         | Mchinji         | Mchinji         |
        | 4   | Village                                       | Kalikokha       | Njobvu          | Maole           | Chikomeni       |
        | 5   | Interview number                              |                 |                 |                 |                 |
        | 6   | Interviewers                                  | Joseph Dimisoni | Joseph Dimisoni | Joseph Dimisoni | Joseph Dimisoni |
        | 7   | Reference year                                |                 |                 |                 |                 |
        | 8   | Currency                                      |                 |                 |                 |                 |
        | 57  | LIVESTOCK PRODUCTION:                         |                 |                 |                 |                 |
        | 85  | Cows' milk                                    |                 |                 |                 |                 |
        | 86  | no. milking animals                           | 2               | 0               | 1               | 2               |
        | 87  | season 1: lactation period (days)             | 120             |                 | 120             | 120             |
        | 88  | daily milk production per animal (litres)     | 2               |                 | 3               | 2               |
        | 89  | total production (litres)                     | 480             |                 | 360             | 480             |
        | 90  | sold/exchanged (litres)                       | 240             | 0               | 300             | 240             |
        | 91  | price (cash)                                  | 150             |                 | 65              | 500             |
        | 92  | income (cash)                                 | 36,000          | 0               | 19,500          | 120,000         |
        | 93  | type of milk sold/other use (skim=0, whole=1) | 1               | 1               | 1               | 1               |
        | 94  | other use (liters)                            | 0               |                 | 0               | 0               |
        | 95  | season 2: lactation period (days)             |                 |                 | 60              | 90              |
        | 96  | daily milk production per animal (litres)     |                 |                 | 2               | 1               |
        | 97  | total production (litres)                     |                 |                 | 120             | 180             |
        | 98  | sold/exchanged (litres)                       | 0               |                 | 100             | 90              |
        | 99  | price (cash)                                  |                 |                 | 70              | 500             |
        | 100 | income (cash)                                 | 0               |                 | 7,000           | 45,000          |
        | 101 | type of milk sold/other use (skim=0, whole=1) | 1               | 1               | 1               | 1               |
        | 102 | other use (liters)                            |                 |                 | 0               | 0               |
        | 103 | % cows' milk sold                             | 50%             |                 | 83%             | 50%             |
        | 104 | ghee/butter production (kg)                   | 9.6             |                 | 3.2             | 13.2            |
        | 105 | ghee/butter (other use)                       |                 |                 |                 |                 |
        | 106 | ghee/butter sales: kg sold                    |                 |                 |                 |                 |
        | 107 | ghee/butter price (cash)                      |                 |                 |                 |                 |
        | 108 | ghee/butter income (cash)                     |                 |                 |                 |                 |
        | 109 | milk+ghee/butter kcals (%) - 1st season       | 3%              |                 | 1%              | 3%              |
        | 110 | milk+ghee/butter kcals (%) - 2nd season       | 0%              |                 | 0%              | 1%              |
        | 111 | % cows' ghee/butter sold: ref year            | 0%              |                 | 0%              | 0%              |
        """  # NOQA: E501

        # Key in the result dict must match the name of the model class they will be imported to.
        # The value must be a list of instances to import into that model, where each instance
        # is a dict of field names and values.
        # If the field is a foreign key to a model that supports a natural key (i.e. the model has a `natural_key`
        # method), then the field value should be a list of components to the natural key.

        # Process the main part of the sheet to find the Livelihood Strategies and Livelihood Activities.

        # Replace NaN with "" ready for Django
        data_df = data_df.fillna("")

        # Find the column index of the first summary column, which is in row 2
        summary_start_col = get_index(["Summary", "SYNTHÈSE"], data_df.iloc[1])

        # Find the last column with data we need to capture, which is the last summary col.
        # There will be one summary column for each wealth category
        end_col = summary_start_col + data_df.iloc[2, 1:summary_start_col].dropna().nunique()

        # Find the row index of the start of the Livelihood Activities
        start_row = get_index(["LIVESTOCK PRODUCTION:"], data_df.iloc[:, 0]) + 1

        # Find the row index of the end of the Livelihood Activities
        end_row = get_index(["income minus expenditure", "Revenus moins dépenses"], data_df.iloc[start_row:, 0])

        # Prepare the lookups, so they cache the individual results
        wealthgroupcategorylookup = WealthGroupCategoryLookup()
        classifiedproductlookup = ClassifiedProductLookup()
        unitofmeasurelookup = UnitOfMeasureLookup()

        # The LivelihoodActivity is the intersection of a LivelihoodStrategy and a WealthGroup,
        # so build a list of the natural keys for the WealthGroups.
        wealth_groups = []
        for column in range(1, end_col):
            wealth_groups.append(
                [
                    metadata["code"],
                    metadata["reference_year_end_date"].date().isoformat(),
                    wealthgroupcategorylookup.get(data_df.iloc[2, column]),
                    ", ".join([str(data_df.iloc[4, column]), str(data_df.iloc[3, column])]),
                ]
            )

        # We can't easily recognize all the rows at once by applying functions to the DataFrame
        # because some values in Column A can appear in more than one LivelihoodStrategy, such as
        # PaymentInKind and OtherCashIncome - the labor description is the same but the compensation
        # is different. Therefore we read the rows in turn and take action based on the type of row
        strategy_type = None
        livelihood_strategy = None
        livelihood_strategies = []
        livelihood_activities = []
        livelihood_activities_for_strategy = []
        for row in range(start_row, end_row):
            attribute = data_df.iloc[row, 0]
            # A row might be the start of a new strategy type, or the start of a Livelihood Activity,
            # or additional attributes for the current Livelihood Activity
            if self.get_strategy_type(attribute):
                # We are starting a group of a Livelihood Strategies for a new Strategy Type
                strategy_type = attribute
            else:
                attributes = self.get_activity_attributes(attribute)
                if attributes:
                    # Some attributes imply a strategy type.
                    # For example, MilkProduction, ButterProduction, MeatProduction and LivestockSales
                    if attributes["strategy_type"]:
                        strategy_type = attributes.pop("strategy_type")
                    if attributes["product"]:
                        attributes["product_original"] = attributes["product"]
                        attributes["product"] = classifiedproductlookup.get(attributes["product"])
                    if attributes["unit_of_measure"]:
                        attributes["unit_of_measure_original"] = attributes["unit_of_measure"]
                        attributes["unit_of_measure"] = unitofmeasurelookup.get(attributes["unit_of_measure"])
                    # Some attributes signal the start of a new LivelihoodStrategy
                    start = attributes.pop("start")
                    if not start:
                        # We are adding additional attributes to the current LivelhoodStrategy
                        assert (
                            livelihood_strategy
                        ), f"Found additional attributes {attributes} from row {row} without an existing LivelihoodStrategy"  # NOQA: E501
                        # Only update expected keys, and only if we found a value for that attribute.
                        for key, value in attributes.items():
                            if key in livelihood_strategy and value:
                                if not livelihood_strategy[key]:
                                    livelihood_strategy[key] = value
                                else:
                                    # This value replacing an existing value, so it is a new LivelihoodStrategy
                                    start = True
                                    new_livelihood_strategy = livelihood_strategy.copy()
                                    for key, value in attributes.items():
                                        if key in new_livelihood_strategy and value:
                                            livelihood_strategy["key"] = value
                                    attributes = new_livelihood_strategy
                                    break
                    if start:
                        # We are starting a new livelihood activity, so append the previous livelihood strategy
                        # to the list, provided that it has at least one Livelihood Activity
                        if livelihood_strategy and livelihood_activities_for_strategy:
                            livelihood_strategies.append(livelihood_strategy)
                            # Add the natural keys for the livelihood strategy and the wealth group
                            # to the livelihood activities
                            for i, livelihood_activity in enumerate(livelihood_activities_for_strategy):
                                livelihood_activity["livelihood_strategy"] = [
                                    metadata["code"],
                                    metadata["reference_year_end_date"].date().isoformat(),
                                    livelihood_strategy["strategy_type"],
                                    livelihood_strategy["season_number"]
                                    if livelihood_strategy["season_number"]
                                    else "",
                                    livelihood_strategy["product"] if livelihood_strategy["product"] else "",
                                    livelihood_strategy["additional_identifier"],
                                ]
                                livelihood_activity["wealth_group"] = wealth_groups[i]

                            livelihood_activities += livelihood_activities_for_strategy
                        # and then initialize the new livelihood strategy from the attributes
                        livelihood_strategy = attributes
                        # Inherit the livelihood strategy from the current group
                        livelihood_strategy["strategy_type"] = strategy_type
                        # Set the natural key to the livelihood zone baseline
                        livelihood_strategy["livelihood_zone_baseline"] = [
                            metadata["code"],
                            metadata["reference_year_end_date"].date().isoformat(),
                        ]
                        # Save the row for this Activity, to aid trouble-shooting
                        livelihood_strategy["row"] = row
                        # Iniitialize the list of livelihood activities for this strategy
                        livelihood_activities_for_strategy = []
                    # When we get the values for the LivelihoodActivity records, we just want the actual attribute
                    # that the values in the row are for
                    attribute = attributes["attribute"]
                # Create the LivelihoodActivity records
                if any(value for value in data_df.iloc[row, 1:end_col]):
                    # Default the list of livelihood activities for this strategy if necessary
                    if not livelihood_activities_for_strategy:
                        livelihood_activities_for_strategy = []
                        for i, value in enumerate(data_df.iloc[row, 1:end_col]):
                            livelihood_activity = {attribute: value}
                            # Save the column and row, to aid trouble-shooting
                            # We need col_index + 1 to get the letter, and the enumerate is already starting from col B
                            livelihood_activity["column"] = get_column_letter(i + 2)
                            livelihood_activity["row"] = row

                            livelihood_activities_for_strategy.append(livelihood_activity)
                    else:
                        for i, livelihood_activity in enumerate(livelihood_activities_for_strategy):
                            livelihood_activity[attribute] = data_df.iloc[row, i + 1]

        result = {
            "LivelihoodStrategy": livelihood_strategies,
            "LivelihoodActivity": livelihood_activities,
        }
        return result

    @staticmethod
    def get_strategy_type(value: str) -> str | None:
        """
        Return the strategy_type for a header row within Column A of the 'Data' worksheet in a BSS.

        Note that this doesn't process the LivestockProduction header, because that needs
        to be split into MilkProduction, ButterProduction, MeatProduction and LivestockSales
        based on the actual values in the actual rows that make up the LivelihoodStrategy
        """
        value = value.strip(":").strip().lower()
        strategy_type_map = {
            "crop production": "CropProduction",
            "food purchase": "FoodPurchase",
            "payment in kind": "PaymentInKind",
            "relief, gifts and other": "ReliefGiftsOther",
            "fishing -- see worksheet data 3": "Fishing",
            "wild foods -- see worksheet data 3": "WildFoodGathering",
            "other cash income": "OtherCashIncome",
            "other purchase": "OtherPurchase",
        }
        return strategy_type_map.get(value, None)

    def get_livelihood_strategy_regexes() -> list:
        """
        Return a list of regex strings that identify the start of a Livelihood Strategy or other important metadata.

        Each entry in the list is a tuple of the compiled regex, the strategy_type and a True/False value
        that indicates whether the regex marks the start of a new Livelihood Activity.
        """
        # Create regex patterns for metadata attributes
        label_pattern = "[a-z][a-z',/ \>\-\(\)]+?"
        attribute_pattern = r"(?P<attribute>[a-z \.\(\)]+)"
        product_pattern = rf"(?P<product>{label_pattern})"
        season_number_pattern = r"(?P<season_number>[0-9])"
        additional_identifier_pattern = r"(?P<additional_identifier>rainfed|irrigated)"
        unit_of_measure_pattern = r"(?P<unit_of_measure>[a-z]+)"

        # Build the list of regexes, strategy types and start flags
        livelihood_strategy_regexes = [
            # Camels' milk
            (rf"(?P<product>{label_pattern} milk)", "MilkProduction", True),
            # season 1: lactation period (days)
            # season 2: no. milking animals
            (rf"season (?P<season_number>1): {attribute_pattern}", "MilkProduction", False),
            # Season 2 has to be a new Livelihood Strategy, so start=True
            (rf"season (?P<season_number>2): {attribute_pattern}", "MilkProduction", True),
            # ghee/butter production (kg)
            (r"ghee/butter (?P<attribute>production) \((?P<unit_of_measure>kg)\)", "ButterProduction", True),
            # ghee/butter sales: kg sold
            (r"ghee/butter (?P<attribute>sales): (?P<unit_of_measure>kg) sold", "ButterProduction", True),
            # milk+ghee/butter kcals (%) - 2nd season
            (
                rf"milk\+ghee/butter (?P<attribute>kcals \(%\)) - {season_number_pattern}(?:st|nd|rd) season",
                "ButterProduction",
                True,
            ),
            # Cow meat: no. animals slaughtered
            (rf"{product_pattern} meat: no. animals slaughtered", "MeatProduction", True),
            # Pig sales - local: no. sold
            (
                rf"{product_pattern} sales - {additional_identifier_pattern}: (?P<attribute>no. sold)",
                "LivestockSale",
                True,
            ),
            # Vente de moutons - locale: nb  venduss
            (
                rf"vente de {product_pattern} - {additional_identifier_pattern}: (?P<attribute>nb  venduss)",
                "LivestockSale",
                True,
            ),
            # Vente de poules: nb  venduses
            (rf"vente de {product_pattern}: (?P<attribute>nb  venduses)", "LivestockSale", True),
            # Green maize sold: quantity
            # This is actually a crop production string, but we need to include it here so that it can be
            # matched before the more generic "<product>: quantity" that is a LivestockSale (e.g. for eggs)
            (rf"(?P<product>green {label_pattern}):? (?P<attribute>quantity)", "CropProduction", True),
            # Other (Eggs): quantity
            # Other Eggs: quantity
            # Other (Eggs) quantity
            # Other Eggs quantity
            (rf"other \(?{product_pattern}\)?:? (?P<attribute>quantity)", "LivestockSale", True),
            # Other: quantity
            # Eggs: quantity
            # Eggs quantity
            (rf"{product_pattern}:? (?P<attribute>quantity)", "LivestockSale", True),
            # Crop Production
            (
                rf"{product_pattern} {additional_identifier_pattern}: {unit_of_measure_pattern} produced",
                "CropProduction",
                True,
            ),
            (rf"{product_pattern}: {unit_of_measure_pattern} produced", "CropProduction", True),
            (rf"{product_pattern} - {additional_identifier_pattern}: no of months", "CropProduction", True),
            (rf"{product_pattern}: no. local meas", "CropProduction", True),
            (rf"{product_pattern}: no. local measure", "CropProduction", True),
            (rf"other crop: \(?{product_pattern}\)?", "CropProduction", True),
            (rf"other cash crop: \(?{product_pattern}\)?", "CropProduction", True),
            (rf"{product_pattern}: ([a-z]+) sold", "CropProduction", True),
            (rf"{product_pattern}: ([a-z]+) sold: quantity", "CropProduction", True),
            # Food Purchase
            (rf"{product_pattern}: name of meas\.", "FoodPurchase", True),
            (rf"{product_pattern} purchase: {unit_of_measure_pattern}", "FoodPurchase", True),
            (rf"{product_pattern} purchase: quantity \({unit_of_measure_pattern}\)", "FoodPurchase", True),
            # Other Purchase
            (rf"other purchase: {product_pattern}", "OtherPurchase", True),
            (rf"other purchase: {additional_identifier_pattern}", "OtherPurchase", True),
            # Payment in Kind
            # Some rows in column A are duplicated for both the PaymentInKind
            # and OtherCashIncome strategy types, and so in those cases
            # get_activity_attributes doesn't return a strategy_type, and
            # instead we rely on the strategy_type detected from the section
            # header in column A, e.g. "PAYMENT IN KIND"
            (rf"labour: {additional_identifier_pattern}", None, True),
            # Relief, Gifts and Other
            (
                r"(?P<additional_identifier>school feeding \(cooked\)): no ?\. children",
                "ReliefGiftOther",
                True,
            ),
            (rf"other food: {additional_identifier_pattern}", "ReliefGiftOther", True),
            (
                rf"relief - {additional_identifier_pattern}: quantity \({unit_of_measure_pattern}\)?",
                "ReliefGiftOther",
                True,
            ),
            (rf"safety nets: {attribute_pattern}", "ReliefGiftOther", True),
            (rf"gifts: {additional_identifier_pattern}", "ReliefGiftOther", True),
            # Other Cash  Income
            (rf"(?P<additional_identifier>construction cash income \({label_pattern}\))", "OtherCashIncome", True),
            (
                rf"(?P<additional_identifier>self-employment \({label_pattern}\))",
                "OtherCashIncome",
                True,
            ),
            ("(?P<additional_identifier>remittances): (?P<attribute>no. times per year)", "OtherCashIncome", True),
        ]

        # Compile the regexes
        livelihood_strategy_regexes = [
            (re.compile(pattern), strategy_type, start)
            for pattern, strategy_type, start in livelihood_strategy_regexes
        ]

        return livelihood_strategy_regexes

    @classmethod
    def get_activity_attributes(cls, column_a_value: str) -> dict | None:
        """
        Return the attributes for a new LivelihoodActivity.

        Check a string from Column A of a Data worksheet to see if it marks the
        start of a new Livelihood Activity, and return a dict containing the
        matched attributes, including the strategy_type, and the product if
        applicable.

        If the string doesn't mark the start of a new LivelihoodActivity
        or contain any additional metadata, then return None.
        """
        attributes = {
            "strategy_type": None,
            "start": None,
            "attribute": None,
            "additional_identifier": None,
            "product": None,
            "unit_of_measure": None,
            "season_number": None,
        }
        for pattern, strategy_type, start in cls.get_livelihood_strategy_regexes():
            match = pattern.fullmatch(str(column_a_value).lower().strip())
            if match:
                attributes.update(match.groupdict())
                attributes["strategy_type"] = strategy_type
                attributes["start"] = start
                # Save the actual text to aid trouble-shooting
                attributes["text"] = str(column_a_value)
                # Cast the pattern to a string, so that it can be serialized
                attributes["pattern"] = str(pattern)
                return attributes
        # No pattern matched
        return None

    @staticmethod
    def get_product(str) -> str:
        """
        Return the CPC code for a product name or alias.

        Uses the ClassifiedProductLookup, but caches the result because this
        gets called for a single
        """
        # Lookup the CPC code

    @staticmethod
    def apply_strategy_lookups(livelihood_strategies: list[dict]) -> list[dict]:
        """
        Process the list of dicts containing LivelihoodStrategy records and return them with correct metadata codes.
        """
        df = pd.DataFrame.from_records(livelihood_strategies)

        # Lookup the CPC code
        df = ClassifiedProductLookup().do_lookup(df, "product", "product")

        # Lookup the Unit of Measure
        df = UnitOfMeasureLookup().do_lookup(df, "unit_of_measure", "unit_of_measure")

        livelihood_strategies = df.to_records("records")
        return livelihood_strategies

    @staticmethod
    def apply_activity_lookups(livelihood_activities: list[dict]) -> list[dict]:
        """
        Process the list of dicts containing LivelihoodActivity records and return them with correct metadata codes.
        """
        df = pd.DataFrame.from_records(livelihood_activities)

        livelihood_activities = df.to_records("records")
        return livelihood_activities


@requires(normalize_wb=NormalizeWB, normalize_data=NormalizeData)
class NormalizeBaseline(luigi.Task):
    """
    Normalize a Baseline read from a BSS into a standard format.
    """

    def output(self):
        return IntermediateTarget(path_from_task(self) + ".json", format=JSON, timeout=3600)

    def run(self):
        data = self.input()["normalize_wb"].open().read()

        with self.output().open("w") as output:
            output.write(data)


@requires(NormalizeBaseline)
class ValidateBaseline(luigi.Task):
    """
    Validate a Baseline read from a BSS, and raise an exception if the BSS cannot be imported.
    """

    def output(self):
        return IntermediateTarget(path_from_task(self) + ".json", format=JSON, timeout=3600)

    def run(self):
        data = self.input().open().read()

        # Run the validation
        self.validate(data)

        # Save the validated data
        with self.output().open("w") as output:
            output.write(data)

    def validate(self, data) -> None:
        """
        Validate the normalized data and raise a PipelineError if it isn't valid
        """
        errors = []
        for model_name, instances in data.items():
            model = class_from_name(f"baseline.models.{model_name}")
            # Ignore non-`baseline` models.
            # The normalized data can include other models, e.g. from `metadata`,
            # but those records must be loaded separately to ensure that they are properly reviewed.
            if model._meta.app_label == "baseline":
                df = pd.DataFrame.from_records(instances)

                for field in model._meta.get_fields():
                    # Only validate mandatory foreign keys to models that aren't in the baseline app.
                    # The data can contain natural key references to parent models within
                    # baseline, and the fixture will load the parent and the child in the
                    # same transaction in ImportBaseline below.
                    if (
                        not field.null
                        and isinstance(field, ForeignKey)
                        and field.related_model._meta.app_label != "baseline"
                    ):
                        column = field.name
                        if df[column].isnull().values.any():
                            unmatched_metadata = get_unmatched_metadata(df, column)
                            for value in unmatched_metadata:
                                error = f"Unmatched imported metadata for {model_name} with {column} '{value}'"
                                errors.append(error)

        if errors:
            raise PipelineError(f"{self}: Missing or inconsistent metadata in BSS", errors=errors)


@requires(ValidateBaseline)
class BuildFixture(luigi.Task):
    """
    Convert the validated data into a JSON-format Django fixture.
    """

    def output(self):
        # The file extension must be verbose_json to match the name of the serialization format that we want to use.
        return IntermediateTarget(path_from_task(self) + ".verbose_json", format=JSON, timeout=3600)

    def run(self):
        with self.input().open() as input:
            data = input.read()

        fixture = self.create_fixture(data)

        with self.output().open("w") as output:
            output.write(fixture)

    def create_fixture(self, data):
        """
        Convert the validated data into a JSON-format Django fixture.

        The resulting fixture can be loaded using `loaddata`. The fixture
        uses natural keys to allow it to load all the data in one call
        without needing sequentially insert model instances and keep track
        of the primary keys for each one.
        """
        fixture = []

        for model_name, instances in data.items():
            model = class_from_name(f"baseline.models.{model_name}")
            # Ignore non-`baseline` models.
            # The validated data can include other models, e.g. from `metadata`,
            # but those records must be loaded separately to ensure that they are properly reviewed.
            if model._meta.app_label == "baseline":
                valid_field_names = [field.name for field in model._meta.get_fields()]
                for field_values in instances:
                    record = {
                        "model": str(model._meta),  # returns, e.g; baseline.livelihoodzone
                    }
                    if not hasattr(model, "natural_key"):
                        # This model doesn't use a natural key, so we need to specify the primary key separately
                        try:
                            record["pk"] = field_values.pop(model._meta.pk.name)
                        except KeyError:
                            raise PipelineError(
                                "Model %s doesn't support natural keys, and the data doesn't contain the primary key field '%s'"  # NOQA: E501
                                % (model_name, model._meta.pk.name)
                            )
                    # Discard any fields that aren't in model - they are probably left over from dataframe
                    # manipulation, such as the "_original" fields from metadata lookups, and replace nan with None.
                    record["fields"] = {}
                    for field, value in field_values.items():
                        if field in valid_field_names:
                            try:
                                if pd.isna(value):
                                    value = None
                            except ValueError:
                                # value is a list, probably a natural key, and raises:
                                # "The truth value of an array with more than one element is ambiguous"
                                pass
                            record["fields"][field] = value
                    fixture.append(record)

        return fixture


@requires(BuildFixture)
class ImportBaseline(luigi.Task):
    """
    Import a Baseline, including all child tables from a JSON fixture created from a BSS.
    """

    def output(self):
        return IntermediateTarget(path_from_task(self) + ".json", format=JSON, timeout=3600)

    def run(self):
        buffer = io.StringIO()

        call_command(verbose_load_data.Command(), self.input().path, verbosity=2, format="verbose_json", stdout=buffer)

        with self.output().open("w") as output:
            # Data is a JSON object
            output.write(buffer.getvalue())


class ImportBaselines(luigi.WrapperTask):
    """
    Import multiple Baselines, including all child tables from a JSON fixture created from the BSSs.
    """

    bss_paths = luigi.ListParameter(default=[], description="List of path to the BSS files")
    metadata_path = luigi.Parameter(description="Path to the BSS metadata")
    corrections_path = luigi.Parameter(default="", description="Path to the BSS corrections")

    def requires(self):
        return [
            ImportBaseline(bss_path=bss_path, metadata_path=self.metadata_path, corrections_path=self.corrections_path)
            for bss_path in self.bss_paths
        ]


class ImportAllBaselines(luigi.WrapperTask):
    """
    Import all the Baselines stored as BSS files within a folder, including in subfolfders.
    """

    root_path = luigi.Parameter(description="Path to the root folder containing the BSSs")
    metadata_path = luigi.Parameter(description="Path to the BSS metadata")
    corrections_path = luigi.Parameter(default="", description="Path to the BSS corrections")

    def requires(self):
        root_target = LocalTarget(Path(self.root_path).expanduser().absolute(), format=luigi.format.Nop)
        if not root_target.exists():
            root_target = GoogleDriveTarget(
                self.root_path,
                format=luigi.format.Nop,
                mimetype="application/vnd.google-apps.folder",
            )
            if not root_target.exists():
                raise PipelineError("No local or Google Drive folder matching %s" % self.root_path)
        for path in root_target.fs.listdir(self.root_path):
            yield ImportBaseline(
                bss_path=path, metadata_path=self.metadata_path, corrections_path=self.corrections_path
            )
