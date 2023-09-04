# Will be baseline.pipelines.ingestion
# @TODO Review imports
# import datetime
# import hashlib
# import json
import logging
from pathlib import Path

import luigi
import pandas as pd
from django.core.management import call_command

# from django.conf import settings
from kiluigi import PipelineError
from kiluigi.targets import GoogleDriveTarget, IntermediateTarget, LocalTarget
from kiluigi.utils import class_from_name, path_from_task

# from luigi.task import TASK_ID_INVALID_CHAR_REGEX, TASK_ID_TRUNCATE_HASH
from luigi.util import requires

# Uncomment when moving to the codebase, for now JSON is defined in the previous cell
from common.pipelines.format import JSON

# from typing import Any, Dict, List, Optional, Union

# from slugify import slugify


logger = logging.getLogger(__name__)


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
                raise PipelineError("No local or Google Drive file matching %s" % self.path)
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


@requires(bss=GetBSS, metadata=GetBSSMetadata)
class NormalizeWB(luigi.Task):
    def output(self):
        return IntermediateTarget(path_from_task(self) + ".json", format=JSON, timeout=3600)

    def run(self):
        with self.input()["bss"].open() as input:
            data_df = pd.read_excel(input, "WB", header=None)
        with self.input()["metadata"].open() as input:
            metadata_df = pd.read_excel(input, "Metadata")

        # Find the metadata for this BSS
        path = f"{Path(self.bss_path).parent.name}/{Path(self.bss_path).name}"
        metadata = metadata_df[metadata_df.bss_path == path].iloc[0]

        data = self.process(data_df, metadata)

        with self.output().open("w") as output:
            output.write(data)

    def process(self, data_df: pd.DataFrame, metadata: pd.Series):
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
                    "country": metadata.country,
                    "code": metadata.code,
                    # Get the name from 'WB':B0
                    "name": data_df.iloc[0, 1],
                }
            ],
            "LivelihoodZoneBaseline": [
                {
                    "livelihood_zone": metadata.code,
                    "source_organization": [
                        metadata.source_organization,
                    ],  # natural key is always a list
                    "main_livelihood_category": metadata.main_livelihood_category,
                    "reference_year_start_date": metadata.reference_year_start_date.date().isoformat(),
                    "reference_year_end_date": metadata.reference_year_end_date.date().isoformat(),
                    "valid_from_date": metadata.valid_from_date.date().isoformat(),
                    "valid_to_date": None
                    if pd.isna(metadata.valid_to_date)
                    else metadata.valid_to_date.date().isoformat(),
                }
            ],
        }

        # Find the communities
        # Transpose to get data in columns
        community_df = data_df.iloc[2:7].transpose()
        # Check that the columns are what we expect
        expected_column_sets = (["WEALTH GROUP", "District", "Village", "Interview number:", "Interviewers"],)
        assert any(
            community_df.iloc[0].str.strip().tolist() == expected_columns for expected_columns in expected_column_sets
        )
        # Normalize the column names
        community_df.columns = ["wealth_category", "district", "name", "interview_number", "interviewers"]
        community_df = community_df[1:]
        # Find the initial set of Communities by only find rows that have both a `district` and a `community`,
        # and don't have a `wealth_category`. Also ignore the `Comments` row.
        community_df = (
            community_df[(community_df["district"] != "Comments") & (community_df["wealth_category"].isna())][
                ["district", "name", "interview_number", "interviewers"]
            ]
            .dropna(subset=["district", "name"])
            .drop_duplicates()
        )
        # Create the full_name from the community and district
        community_df["full_name"] = community_df.name.str.cat(community_df.district, sep=", ")
        community_df = community_df.drop(columns="district")
        # Add the natural key for the livelihood zone baseline
        community_df["livelihood_zone_baseline"] = community_df["full_name"].apply(
            lambda full_name: [metadata.code, metadata.reference_year_end_date.date().isoformat()]
        )

        # Replace NaN with "" ready for Django
        community_df = community_df.fillna("")
        result["Community"] = community_df.to_dict(orient="records")

        # Find the wealth category codes
        wealth_categories = data_df.iloc[5:, 1].dropna().drop_duplicates()
        result["WealthCategory"] = wealth_categories.tolist()

        # Find the percentage of households
        household_pct_df = pd.concat(
            [data_df.iloc[2:5].transpose(), data_df.iloc[8 : 8 + len(wealth_categories)].transpose()], axis="columns"
        )

        # Set the column names from Row 0 and Row 1, stripping any trailing spaces
        household_pct_df.columns = (
            household_pct_df.iloc[0, 0:3].str.strip().tolist() + household_pct_df.iloc[1, 3:].str.strip().tolist()
        )
        # Check that the columns are what we expect
        expected_column_sets = (["WEALTH GROUP", "District", "Village", "VP", "P", "M", "B/O"],)
        assert any(household_pct_df.columns.tolist() == expected_columns for expected_columns in expected_column_sets)
        # Normalize the column names
        household_pct_df.columns = ["wealth_category", "district", "community"] + household_pct_df.iloc[
            1, 3:
        ].str.strip().tolist()
        # Discard the header rows
        household_pct_df = household_pct_df[2:]
        # Find the initial set of Household Percentages by finding rows that have both a `district` and a `community`,
        # and don't have a `wealth_category`. Also ignore the `Comments` rows
        household_pct_df = household_pct_df[
            (household_pct_df["district"] != "Comments") & (household_pct_df["wealth_category"].isna())
        ].dropna(subset=["district", "community"])
        # Create the full_name from the community and district
        household_pct_df["full_name"] = household_pct_df.community.str.cat(household_pct_df.district, sep=", ")
        household_pct_df = household_pct_df.drop(columns=["district", "wealth_category"])
        # Replace NaN with "" ready for Django
        household_pct_df = household_pct_df.fillna("")
        # Melt the wealth categories in to a column
        household_pct_df = pd.melt(
            household_pct_df,
            id_vars=["community", "full_name"],
            value_vars=wealth_categories,
            var_name="wealth_category",
            value_name="percentage_of_households",
        )

        # Find the average household size

        # Find the index of the first matching string we can recognize as the Household Size
        # This works because in Pandas, True > False and idxmax() returns the first occurrence of the maximum value
        # of the series and isin() converts the column to a Series of True/False values.
        starting_row = data_df.iloc[:, 0].isin(["HH size"]).idxmax()

        household_size_df = pd.concat(
            [
                data_df.iloc[2:5].transpose(),
                data_df.iloc[starting_row : starting_row + len(wealth_categories)].transpose(),
            ],
            axis="columns",
        )
        # Set the column names from Row 0 and Row 1, stripping any trailing spaces
        household_size_df.columns = (
            household_size_df.iloc[0, 0:3].str.strip().tolist() + household_size_df.iloc[1, 3:].str.strip().tolist()
        )
        # Check that the columns are what we expect
        expected_column_sets = (["WEALTH GROUP", "District", "Village"] + wealth_categories.tolist(),)
        assert any(household_size_df.columns.tolist() == expected_columns for expected_columns in expected_column_sets)

        # Normalize the column names
        household_size_df.columns = ["wealth_category", "district", "community"] + household_size_df.iloc[
            1, 3:
        ].str.strip().tolist()
        # Discard the header rows
        household_size_df = household_size_df[2:]
        # Find the initial set of Household Percentages by finding rows that have both a `district` and a `community`,
        # and don't have a `wealth_category`. Also ignore the `Comments` rows
        household_size_df = household_size_df[
            (household_size_df["district"] != "Comments") & (household_size_df["wealth_category"].isna())
        ].dropna(subset=["district", "community"])
        # Create the full_name from the community and district
        household_size_df["full_name"] = household_size_df.community.str.cat(household_size_df.district, sep=", ")
        household_size_df = household_size_df.drop(columns=["district", "wealth_category"])
        # Replace NaN with "" ready for Django
        household_size_df = household_size_df.fillna("")
        # Melt the wealth categories in to a column
        household_size_df = pd.melt(
            household_size_df,
            id_vars=["community", "full_name"],
            value_vars=wealth_categories,
            var_name="wealth_category",
            value_name="average_household_size",
        )

        # Create the wealth groups by merging household_pct_df and household_size_df
        wealth_group_df = household_pct_df.merge(
            household_size_df, on=["community", "full_name", "wealth_category"], how="left"
        )
        # Add the natural key for the livelihood zone baseline and community
        # Add the natural key for the livelihood zone baseline
        wealth_group_df["livelihood_zone_baseline"] = wealth_group_df["full_name"].apply(
            lambda full_name: [metadata.code, metadata.reference_year_end_date.date().isoformat()]
        )
        wealth_group_df["community"] = wealth_group_df["full_name"].apply(
            lambda full_name: [metadata.code, metadata.reference_year_end_date.date().isoformat(), full_name]
            if full_name
            else None
        )
        wealth_group_df = wealth_group_df.drop(columns="full_name")
        result["WealthGroup"] = wealth_group_df.to_dict(orient="records")

        return result


@requires(normalize_wb=NormalizeWB)
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

        for model, instances in data.items():
            model = class_from_name(f"baseline.models.{model}")
            # Ignore non-`baseline` models.
            # The validated data can include other models, e.g. from `metadata`,
            # but those records must be loaded separately to ensure that they are properly reviewed.
            if model._meta.app_label == "baseline":
                print(model)
                print(instances)
                for field_values in instances:
                    print(field_values)
                    record = {
                        "model": str(model._meta),  # returns, e.g; baseline.livelihoodzone
                    }
                    if not hasattr(model, "natural_key"):
                        # This model doesn't use a natural key, so we need to specify the primary key separately
                        record["pk"] = field_values.pop(model._meta.pk.name)
                    record["fields"] = field_values
                    fixture.append(record)

        return fixture


@requires(BuildFixture)
class ImportBaseline(luigi.Task):
    """
    Import a Baseline, including all child tables from a JSON fixture created from aBSS.
    """

    def output(self):
        return IntermediateTarget(path_from_task(self) + ".json", format=JSON, timeout=3600)

    def run(self):
        result = call_command("loaddata", self.input().path, verbosity=3, format="verbose_json")

        with self.output().open("w") as output:
            # Data is a JSON object
            output.write(result)
