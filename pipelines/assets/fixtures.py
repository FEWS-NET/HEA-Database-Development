import datetime
import json
import os
import tempfile
from collections import defaultdict
from io import StringIO

import django
import pandas as pd
from dagster import AssetExecutionContext, MetadataValue, Output, asset
from django.core.management import call_command
from django.db import models

from ..utils import class_from_name
from .baseline import BSSMetadataConfig, bss_files_partitions_def

# set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hea.settings.production")

# Configure Django with our custom settings before importing any Django classes
django.setup()

from common.lookups import ClassifiedProductLookup  # NOQA: E402
from common.management.commands import verbose_load_data  # NOQA: E402


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
) -> Output[dict]:
    """
    Validated record instances from a BSS, ready to be loaded via a Django fixture.
    """
    # Create a dict of all the models, and a dataframe of their instances
    errors = []
    dfs = {}
    for model_name, instances in consolidated_instances.items():
        model = class_from_name(f"baseline.models.{model_name}")
        valid_field_names = [field.name for field in model._meta.concrete_fields]
        # Also include values that point directly to the primary key of related objects
        valid_field_names += [
            field.get_attname()
            for field in model._meta.concrete_fields
            if field.get_attname() not in valid_field_names
        ]
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

        # Apply some model-level defaults
        if "created" in valid_field_names and "created" not in df:
            df["created"] = pd.Timestamp.now(datetime.timezone.utc)
        if "modified" in valid_field_names and "modified" not in df:
            df["modified"] = pd.Timestamp.now(datetime.timezone.utc)

        # Save the model and dataframe so we can use them validate natural foreign keys later
        dfs[model_name] = (model, df)

        # Apply field-level checks
        for field in model._meta.concrete_fields:
            column = field.name if field.name in df else field.get_attname()
            # Ensure that mandatory fields have values
            if not field.blank:
                if column not in df:
                    error = f"Missing mandatory field {field.name} for {model_name}"
                    errors.append(error)
                    continue
                else:
                    for row in df[df[column].isnull()].itertuples():
                        error = f"Missing value for mandatory field {column} for {model_name} in row {row.Index} {row._asdict()}"  # NOQA: E501
                        errors.append(error)
            # Ensure the consolidated instances contain valid parent references for foreign keys
            if isinstance(field, models.ForeignKey):
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

        # Check that the kcals/kg matches the values in the ClassifiedProduct model, if it's present in the BSS
        if model_name == "LivelihoodActivity" and "product__kcals_per_unit" in df:
            df["product"] = df["livelihood_strategy"].apply(lambda x: x[4])
            df = ClassifiedProductLookup().get_instances(df, "product", "product")
            df["reference_kcals_per_unit"] = df["product"].apply(lambda x: x.kcals_per_unit)
            df["reference_unit_of_measure"] = df["product"].apply(lambda x: x.unit_of_measure)
            for row in df[df["product__kcals_per_unit"] != df["reference_kcals_per_unit"]].itertuples():
                error = (
                    f"Non-standard value {row.product__kcals_per_unit} "
                    f"in '{row.column}{row.row}' for {model_name} instance "
                    f'{str({k: v for k,v in row._asdict().items() if k != "Index"})}. '
                    f"Expected {row.reference_kcals_per_unit}/{row.reference_unit_of_measure} for {row.product}"
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
    # For Livelihood Activities we need to create instances of the subclass, as well as the base class
    # so create an additional list of instances for each subclass.
    livelihood_activities = defaultdict(list)
    for instance in validated_instances["LivelihoodActivity"]:
        # The subclass instances also need a pointer to the base class instance
        instance["livelihoodactivity_ptr"] = (
            instance["wealth_group"][:3] + instance["livelihood_strategy"][2:] + [instance["wealth_group"][3]]
        )
        livelihood_activities[instance["strategy_type"]].append(instance)

    # Concatenate the separate lists of instances for each model into a single list of records
    fixture = []
    metadata = defaultdict(int)
    for model_name, instances in {**validated_instances, **livelihood_activities}.items():
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
            # Start building the record for the  model instance.
            record = {
                "model": str(model._meta),  # returns, e.g; baseline.livelihoodzone
            }
            # If the model doesn't use a natural key, we need to specify the primary key separately
            if not hasattr(model, "natural_key"):
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
            metadata[f'num_{str(model._meta).split(".")[-1]}'] += 1

    metadata["total_instances"] = len(fixture)
    metadata["preview"] = MetadataValue.md(f"```json\n{json.dumps(fixture, indent=4)}\n```")
    return Output(
        fixture,
        metadata=metadata,
    )


@asset(partitions_def=bss_files_partitions_def)
def imported_baseline(
    context: AssetExecutionContext,
    consolidated_fixture,
) -> Output[None]:
    """
    Imported Django fixtures for a BSS, added to the Django database.
    """
    output_buffer = StringIO()

    # We need to use a .verbose_json file extension for Django to use the correct serializer.
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".verbose_json") as f:
        # Write the fixture to a temporary file so that Django can access it
        f.write(json.dumps(consolidated_fixture))
        f.seek(0)
        call_command(verbose_load_data.Command(), f.name, verbosity=2, format="verbose_json", stdout=output_buffer)

    # Create the metadata reporting the number of instances created for each model
    metadata = defaultdict(int)
    for instance in consolidated_fixture:
        metadata[f'num_{instance["model"].split(".")[-1]}'] += 1
    metadata["total_instances"] = len(consolidated_fixture)
    metadata["output"] = MetadataValue.md(f"```\n{output_buffer.getvalue()}\n```")

    return Output(
        None,
        metadata=metadata,
    )