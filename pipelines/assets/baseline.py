import json
import numbers
import os
import tempfile
from io import BytesIO, StringIO
from pathlib import Path

import django
import openpyxl
import pandas as pd
import xlrd
import xlwt
from dagster import (
    AssetExecutionContext,
    AssetMaterialization,
    Config,
    DynamicPartitionsDefinition,
    MetadataValue,
    Output,
    asset,
)
from django.core.management import call_command
from django.db import models
from openpyxl.comments import Comment
from openpyxl.utils.cell import coordinate_to_tuple, rows_from_range
from pydantic import Field
from xlutils.copy import copy as copy_xls

from ..utils import class_from_name

# set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hea.settings.production")

# Configure Django with our custom settings before importing any Django classes
django.setup()

from common.management.commands import verbose_load_data  # NOQA: E402

bss_files_partitions_def = DynamicPartitionsDefinition(name="bss_files")


class BSSMetadataConfig(Config):
    gdrive_id: str = Field(
        default="15XVXFjbom1sScVXbsetnbgAnPpRux2AgNy8w5U8bXdI", description="The id of the BSS Metadata Google Sheet."
    )
    bss_root_folder: str = Field(
        default="/home/roger/Temp/Baseline Storage Sheets (BSS)",
        description="The path of the root folder containing the BSSs",
    )
    preview_rows: int = Field(default=10, description="The number of rows to show in DataFrame previews")


@asset(required_resource_keys={"google_client"})
def bss_metadata(context: AssetExecutionContext, config: BSSMetadataConfig) -> Output[pd.DataFrame]:
    """
    A DataFrame containing the BSS Metadata.
    """
    gc = context.resources.google_client.get_gspread_client()
    sh = gc.open_by_key(config.gdrive_id)
    worksheet = sh.worksheet("Metadata")
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    return Output(df, metadata={"num_baselines": len(df)})


@asset
def completed_bss_metadata(config: BSSMetadataConfig, bss_metadata) -> Output[pd.DataFrame]:
    """
    A DataFrame containing the BSS Metadata that has been completed sufficiently to allow the BSS to be loaded.
    """
    required_columns = [
        "bss_path",
        "code",
        "country_id",
        "source_organization",
        "name_en",
        "main_livelihood_category_id",
        "currency_id",
        "reference_year_start_date",
        "reference_year_end_date",
        "valid_from_date",
    ]
    mask = bss_metadata[required_columns].applymap(lambda x: x == "")

    # Drop rows where any of the specified columns have empty strings
    df = bss_metadata[~mask.any(axis="columns")]
    return Output(
        df,
        metadata={"num_baselines": len(df), "preview": MetadataValue.md(df.head(config.preview_rows).to_markdown())},
    )


@asset(required_resource_keys={"google_client"})
def bss_corrections(context: AssetExecutionContext, config: BSSMetadataConfig) -> Output[pd.DataFrame]:
    """
    A DataFrame containing approved corrections to cells in BSS spreadsheets.
    """
    gc = context.resources.google_client.get_gspread_client()
    sh = gc.open_by_key(config.gdrive_id)
    worksheet = sh.worksheet("Corrections")
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    return Output(
        df,
        metadata={
            "num_baselines": df["bss_path"].nunique(),
            "num_corrections": len(df),
            "preview": MetadataValue.md(df.head(config.preview_rows).to_markdown()),
        },
    )


@asset(partitions_def=bss_files_partitions_def)
def bss_files_metadata():
    pass


@asset(partitions_def=bss_files_partitions_def)
def corrected_files(context: AssetExecutionContext, config: BSSMetadataConfig, bss_corrections) -> Output[BytesIO]:
    """
    BSS files with any necessary corrections applied.
    """
    partition_key = context.asset_partition_key_for_output()
    file_path = Path(config.bss_root_folder, partition_key)
    extension = None
    for extension in [".xls", ".xlsx"]:
        if file_path.with_suffix(extension).exists():
            file_path = file_path.with_suffix(extension)
            break
    assert extension, f"No BSS file found for {partition_key} in {config.bss_root_folder}"

    def validate_previous_value(cell, expected_prev_value, prev_value):
        """
        Inline function to validate the existing value of a cell is the expected one, prior to correcting it.
        """
        # "#N/A" is inconsistently loaded as nan, even when copied and pasted in Excel or GSheets
        if not isinstance(prev_value, numbers.Number):
            prev_value = str(prev_value).replace("None", "").replace("nan", "#N/A").strip()
            expected_prev_value = str(expected_prev_value)
        if expected_prev_value != prev_value:
            raise ValueError(
                "Unexpected prior value in source BSS. "
                f"BSS `{partition_key}`, cell `{cell}`, "
                f"value found `{prev_value}`, expected `{expected_prev_value}`."
            )

    # Find the corrections for this BSS
    corrections_df = bss_corrections[bss_corrections["bss_path"] == partition_key + extension]

    # Prepare the metadata for the output
    output_metadata = {"bss_path": file_path, "num_corrections": len(corrections_df)}

    if corrections_df.empty:
        # No corrections, so just leave the file unaltered
        with open(file_path, "rb") as fh:
            return Output(BytesIO(fh.read()), metadata=output_metadata)
    else:
        if file_path.suffix == ".xls":
            # xlrd can only read XLS files, so we need to use xlutils.copy_xls to create something we can edit
            xlrd_wb = xlrd.open_workbook(file_path, formatting_info=True, on_demand=True)
            wb = copy_xls(xlrd_wb)
        else:
            xlrd_wb = None  # Required to suppress spurious unbound variable errors from Pyright
            # Need data_only=True to get the values of cells that contain formulas
            wb = openpyxl.load_workbook(file_path, data_only=True)
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
                        validate_previous_value(cell, correction.prev_value, prev_value)
                        # xlwt uses 0-based indexes, but coordinate_to_tuple uses 1-based, so offset the values
                        wb.get_sheet(correction.worksheet_name).write(row - 1, col - 1, correction.value)
                    else:
                        cell = wb[correction.worksheet_name][cell]
                        validate_previous_value(cell, correction.prev_value, cell.value)
                        cell.value = correction.value
                        cell.comment = Comment(
                            f"{correction.author} on {correction.correction_date}: {correction.comment}",  # NOQA: E501
                            author=correction.author,
                        )

        buffer = BytesIO()
        wb.save(buffer)
        return Output(buffer, metadata=output_metadata)


@asset(partitions_def=bss_files_partitions_def, io_manager_key="json_io_manager")
def baseline_fixture(
    context: AssetExecutionContext, config: BSSMetadataConfig, completed_bss_metadata, corrected_files
) -> Output[dict]:
    """
    Django fixtures for the LivelihoodZone, LivelihoodZoneBaseline and Community records in the BSSs.

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
    partition_key = context.asset_partition_key_for_output()

    data_df = pd.read_excel(corrected_files, "WB", header=None)

    # Find the metadata for this BSS
    try:
        metadata = completed_bss_metadata[completed_bss_metadata["bss_path"].str.startswith(partition_key)].iloc[0]
    except IndexError:
        raise ValueError("No complete entry in the BSS Metadata worksheet for %s" % partition_key)

    # Key in the result dict must match the name of the model class they will be imported to.
    # The value must be a list of instances to import into that model, where each instance
    # is a dict of field names and values.
    # If the field is a foreign key to a model that supports a natural key (i.e. the model has a `natural_key`
    # method), then the field value should be a list of components to the natural key.
    result = {
        "LivelihoodZone": [
            {
                # Get country and code from the filename
                "country_id": metadata["country_id"],
                "code": metadata["code"],
                "name_en": metadata["name_en"],
                "name_es": metadata["name_es"],
                "name_fr": metadata["name_fr"],
                "name_pt": metadata["name_pt"],
                "name_ar": metadata["name_ar"],
                "description_en": metadata["description_en"],
                "description_es": metadata["description_es"],
                "description_fr": metadata["description_fr"],
                "description_pt": metadata["description_pt"],
                "description_ar": metadata["description_ar"],
            }
        ],
        "LivelihoodZoneBaseline": [
            {
                "livelihood_zone_id": metadata["code"],
                "name_en": metadata["name_en"],
                "name_es": metadata["name_es"],
                "name_fr": metadata["name_fr"],
                "name_pt": metadata["name_pt"],
                "name_ar": metadata["name_ar"],
                "description_en": metadata["description_en"],
                "description_es": metadata["description_es"],
                "description_fr": metadata["description_fr"],
                "description_pt": metadata["description_pt"],
                "description_ar": metadata["description_ar"],
                "source_organization": [
                    metadata["source_organization"],
                ],  # natural key is always a list
                "main_livelihood_category_id": str(metadata["main_livelihood_category_id"]).lower(),
                "reference_year_start_date": metadata["reference_year_start_date"],
                "reference_year_end_date": metadata["reference_year_end_date"],
                "valid_from_date": metadata["valid_from_date"],
                "valid_to_date": metadata["valid_to_date"] if metadata["valid_to_date"] else None,
                "data_collection_start_date": (
                    metadata["data_collection_start_date"] if metadata["data_collection_start_date"] else None
                ),
                "data_collection_end_date": (
                    metadata["data_collection_end_date"] if metadata["data_collection_end_date"] else None
                ),
                "publication_date": metadata["publication_date"] if metadata["publication_date"] else None,
                "bss": partition_key,
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
        raise ValueError("Cannot identify Communities from columns %s" % ", ".join(found_columns))
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
    community_df["full_name"] = community_df.name.str.cat(community_df.district, sep=", ").fillna(community_df.name)
    community_df = community_df.drop(columns="district")
    # Add the natural key for the livelihood zone baseline
    community_df["livelihood_zone_baseline"] = community_df["full_name"].apply(
        lambda full_name: [metadata["code"], metadata["reference_year_end_date"]]
    )

    # Replace NaN with "" ready for Django
    community_df = community_df.fillna("")
    result["Community"] = community_df.to_dict(orient="records")

    return Output(
        result,
        metadata={
            "num_communities": len(community_df),
            "preview": MetadataValue.md(f"```json\n{json.dumps(result, indent=4)}\n```"),
        },
    )


@asset(partitions_def=bss_files_partitions_def, io_manager_key="json_io_manager")
def consolidated_instances(
    baseline_fixture,
    livelihood_activity_fixture,
    wealth_characteristic_fixture,
) -> Output[dict]:
    """
    Consolidated record instances from a BSS, ready to be validated.
    """
    # Build a dict of all the models, and their instances, that are to be loaded
    consolidated_instances = {
        **baseline_fixture,
        # Put the wealth_characteristic_fixture immediately after the baseline_fixture, because it loads the
        # WealthGroup instances, which are needed as a foreign key from LivelihoodActivity, etc.
        **wealth_characteristic_fixture,
        **livelihood_activity_fixture,
    }
    metadata = {f"num_{key.lower()}": len(value) for key, value in consolidated_instances.items()}
    metadata["total_instances"] = sum(len(value) for value in consolidated_instances.values())
    metadata["preview"] = MetadataValue.md(f"```json\n{json.dumps(consolidated_instances, indent=4)}\n```")
    return Output(
        consolidated_instances,
        metadata=metadata,
    )


@asset(partitions_def=bss_files_partitions_def, io_manager_key="json_io_manager")
def validated_instances(
    consolidated_instances,
) -> Output[list[dict]]:
    """
    Validated record instances from a BSS, ready to be loaded via a Django fixture.
    """
    # Create a dict of all the models, and a dataframe of their instances
    errors = []
    dfs = {}
    for model_name, instances in consolidated_instances.items():
        model = class_from_name(f"baseline.models.{model_name}")
        df = pd.DataFrame.from_records(instances)

        # Add the key to the instances for this model, so we can validate foreign keys within the fixture
        if model_name == "LivelihoodZone":
            df["key"] = df["code"]
        elif model_name == "LivelihoodZoneBaseline":
            df["key"] = df[["livelihood_zone_id", "reference_year_end_date"]].apply(
                lambda x: [x[0], x[1]], axis="columns"
            )
        elif model_name == "Community":
            df["key"] = df[["livelihood_zone_baseline", "full_name"]].apply(lambda x: x[0] + [x[1]], axis="columns")
        elif model_name == "WealthGroup":
            df["key"] = df[["livelihood_zone_baseline", "wealth_group_category", "community"]].apply(
                lambda x: x[0] + [x[1], x[2][-1] if x[2] else ""], axis="columns"
            )
        elif model_name == "LivelihoodStrategy":
            df["key"] = df[
                ["livelihood_zone_baseline", "strategy_type", "season", "product_id", "additional_identifier"]
            ].apply(lambda x: x[0] + [x[1], x[2][0] if x[2] else "", x[3], x[4]], axis="columns")

        # Save the model and dataframe so we can use them validate natural foreign keys later
        dfs[model_name] = (model, df)

        # Ensure the consolidated instances contain valid parent references for foreign keys
        for field in model._meta.concrete_fields:
            if isinstance(field, models.ForeignKey):
                column = field.name if field.name in df else field.get_attname()
                if column not in df:
                    error = f"Missing mandatory foreign key {column} for {model_name}"
                    errors.append(error)
                    continue
                if not field.null:
                    for row in df[df[column].isnull()].itertuples():
                        error = f"Missing mandatory foreign key {column} for {model_name} in row {row.Index} {row._asdict()}"  # NOQA: E501
                        errors.append(error)
                # Validate foreign key values
                if field.related_model.__name__ in dfs:
                    # The model is part of the fixture, so use the saved key from the dataframe
                    remote_keys = dfs[field.related_model.__name__][1]["key"]
                else:
                    # The model is not in the fixture, so use the primary and natural keys for already saved instances
                    remote_keys = [instance.pk for instance in field.related_model.objects.all()]
                    if "natural_key" in dir(field.related_model):
                        remote_keys += [list(instance.natural_key()) for instance in field.related_model.objects.all()]
                # Check the non-null foreign key values are in the remote keys
                for row in df[df[column].notna() & ~df[column].isin(remote_keys)].itertuples():
                    error = (
                        f"Unrecognized foreign key {getattr(row, column)} "
                        f"in column '{column}' for {model_name} instance "
                        f'{str({k: v for k,v in row._asdict().items() if k != "Index"})}'
                    )
                    errors.append(error)

    if errors:
        errors = "\n".join(errors)
        raise RuntimeError("Missing or inconsistent metadata in BSS:\n%s" % errors)

    metadata = {f"num_{key.lower()}": len(value) for key, value in consolidated_instances.items()}
    metadata["total_instances"] = sum(len(value) for value in consolidated_instances.values())
    metadata["preview"] = MetadataValue.md(f"```json\n{json.dumps(consolidated_instances, indent=4)}\n```")
    return Output(
        consolidated_instances,
        metadata=metadata,
    )


@asset(partitions_def=bss_files_partitions_def, io_manager_key="json_io_manager")
def consolidated_fixture(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    validated_instances,
) -> Output[list[dict]]:
    """
    Consolidated Django fixture for a BSS, including Livelihood Activities and Wealth Group Characteristic Values.
    """
    # Concatenate the individual fixtures into a single dict
    fixture = []
    for model_name, instances in validated_instances.items():
        try:
            model = class_from_name(f"baseline.models.{model_name}")
            valid_field_names = [field.name for field in model._meta.concrete_fields]
            # Also include values that point directly to the primary key of related objects
            valid_field_names += [
                field.get_attname()
                for field in model._meta.concrete_fields
                if field.get_attname() not in valid_field_names
            ]
        except ModuleNotFoundError:
            # Ignore non-`baseline` models.
            # The validated data can include other models, e.g. from `metadata`,
            # but those records must be loaded separately to ensure that they are properly reviewed.
            continue
        except Exception:
            raise

        for field_values in instances:
            record = {
                "model": str(model._meta),  # returns, e.g; baseline.livelihoodzone
            }
            if not hasattr(model, "natural_key"):
                # This model doesn't use a natural key, so we need to specify the primary key separately
                try:
                    record["pk"] = field_values.pop(model._meta.pk.name)
                except KeyError:
                    raise ValueError(
                        "Model %s doesn't support natural keys, and the data doesn't contain the primary key field '%s'"  # NOQA: E501
                        % (model_name, model._meta.pk.name)
                    )
            # Discard any fields that aren't in model - they are probably left over from dataframe
            # manipulation, such as the "_original" fields from metadata lookups, or trouble-shooting fields like
            # "column" and "row". Django raises FieldDoesNotExist if it encounters an unexpected field.
            record["fields"] = {}
            for field, value in field_values.items():
                if field in valid_field_names:
                    try:
                        # In Django, blank char fields should contain "" but blank numeric fields should contain None,
                        # so replace NaN, or numeric fields containing "", with None.
                        if pd.isna(value) or (
                            value == ""
                            and model._meta.get_field(field).get_internal_type() not in ["CharField", "TextField"]
                        ):
                            value = None
                    except ValueError:
                        # value is a list, probably a natural key, and raises:
                        # "The truth value of an array with more than one element is ambiguous"
                        pass
                    record["fields"][field] = value
            fixture.append(record)

    metadata = {f"num_{key.lower()}": len(value) for key, value in validated_instances.items()}
    metadata["total_instances"] = len(fixture)
    metadata["preview"] = MetadataValue.md(f"```json\n{json.dumps(fixture, indent=4)}\n```")
    return Output(
        fixture,
        metadata=metadata,
    )


@asset(partitions_def=bss_files_partitions_def)
def imported_baseline(
    consolidated_fixture,
) -> None:
    """
    Imported Django fixtures for a BSS, added to the Django database.
    """
    output_buffer = StringIO()

    # We need to use a .verbose_json format for Django to use the correct serializer.
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".verbose_json") as f:
        # Write the fixture to a temporary file so that Django can access it
        f.write(json.dumps(consolidated_fixture))
        f.seek(0)
        call_command(verbose_load_data.Command(), f.name, verbosity=2, format="verbose_json", stdout=output_buffer)

    # Emit an AssetMaterialization to provide runtime metadata
    yield AssetMaterialization(
        description="Loaded Django fixture for the BSS into the database.",
        metadata={
            "instances_created": len(consolidated_fixture),
            "output": MetadataValue.md(f"```\n{output_buffer.get_value()}\n```"),
        },
    )
