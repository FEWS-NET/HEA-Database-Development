import datetime
import json
import os
import tempfile
from collections import defaultdict
from io import StringIO

import django
import numpy as np
import pandas as pd
from dagster import AssetExecutionContext, MetadataValue, Output, asset
from django.core.files import File
from django.core.management import call_command
from django.db import models

from ..configs import BSSMetadataConfig
from ..partitions import bss_files_partitions_def, bss_instances_partitions_def
from ..utils import class_from_name

# set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hea.settings.production")

# Configure Django with our custom settings before importing any Django classes
django.setup()

from baseline.models import LivelihoodZoneBaseline  # NOQA: E402
from common.lookups import ClassifiedProductLookup  # NOQA: E402
from common.management.commands import verbose_load_data  # NOQA: E402


def validate_instances(
    context: AssetExecutionContext, instances: dict[str, list[dict]], partition_key: str
) -> tuple[dict[str, list[dict]], dict]:
    """
    Validate the instances for a set of related models, prior to loading them as a fixture.

    Validating the instances before attempting the load allows us to provide
    more informative error messages than the ones provided by Django's `loaddata`.
    """

    # For Livelihood Activities we need to create and validate instances of the subclass, as well as the base class
    # so create an additional list of instances for each subclass.
    if "LivelihoodActivity" in instances:
        subclass_livelihood_activities = defaultdict(list)
        for instance in instances["LivelihoodActivity"]:
            subclass_instance = instance.copy()
            # The subclass instances also need a pointer to the base class instance
            subclass_instance["livelihoodactivity_ptr"] = (
                instance["wealth_group"][:3] + instance["livelihood_strategy"][2:] + [instance["wealth_group"][3]]
            )
            subclass_livelihood_activities[instance["strategy_type"]].append(subclass_instance)

        instances = {**instances, **subclass_livelihood_activities}

    # Create a dict to contain a dataframe of the instances for each model
    dfs = {}
    errors = []
    for model_name, model_instances in instances.items():
        # Ignore models where we don't have any instances to validate.
        if model_instances:
            model = class_from_name(f"baseline.models.{model_name}")
            # Build a list of expected field names
            valid_field_names = [field.name for field in model._meta.concrete_fields]
            # Also include values that point directly to the primary key of related objects
            valid_field_names += [
                field.get_attname()
                for field in model._meta.concrete_fields
                if field.get_attname() not in valid_field_names
            ]

            # Apply some model-level defaults. We do this by iterating over the instances rather than using the dataframe
            # because we want to return the instances without any other changes that might be made by the dataframe as a
            # result of dtype conversion or NaNs.
            current_timestamp = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
            for instance in model_instances:
                for field in ["created", "modified"]:
                    if field in valid_field_names and field not in instance:
                        instance[field] = current_timestamp

            df = pd.DataFrame.from_records(model_instances)

            # Add the natural key for the instances to the dataframe,
            # so we can validate foreign keys in child models.
            if model_name == "LivelihoodZone":
                df["key"] = df["code"]
            elif model_name == "LivelihoodZoneBaseline":
                df["key"] = df[["livelihood_zone_id", "reference_year_end_date"]].apply(
                    lambda x: [x.iloc[0], x.iloc[1]], axis="columns"
                )
            elif model_name == "Community":
                df["key"] = df[["livelihood_zone_baseline", "full_name"]].apply(
                    lambda x: x.iloc[0] + [x.iloc[1]], axis="columns"
                )
            elif model_name == "WealthGroup":
                df["key"] = df[["livelihood_zone_baseline", "wealth_group_category", "community"]].apply(
                    lambda x: x.iloc[0] + [x.iloc[1], x.iloc[2][-1] if x.iloc[2] else ""], axis="columns"
                )
            elif model_name == "LivelihoodStrategy":
                df["key"] = df[
                    ["livelihood_zone_baseline", "strategy_type", "season", "product_id", "additional_identifier"]
                ].apply(
                    lambda x: x.iloc[0]
                    + [x.iloc[1], x.iloc[2][0] if x.iloc[2] else "", x.iloc[3] if x.iloc[3] else "", x.iloc[4]],
                    axis="columns",
                )
            elif model_name == "LivelihoodActivity":
                df["key"] = df[["livelihood_zone_baseline", "wealth_group", "livelihood_strategy"]].apply(
                    lambda x: [
                        x.iloc[0][0],
                        x.iloc[0][1],
                        x.iloc[1][2],
                        x.iloc[2][2],
                        x.iloc[2][3],
                        x.iloc[2][4],
                        x.iloc[2][5],
                        x.iloc[1][3],
                    ],
                    axis="columns",
                )

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
                        for record in df[df[column].isnull()].itertuples():
                            error = (
                                f"Missing value for mandatory field {column} for {model_name} in record "
                                f"{record.Index} from cell '{record.bss_sheet}'!{record.bss_column}{record.bss_row}"
                                f'{str({k: v for k,v in record._asdict().items() if k != "Index"})}'
                            )
                            errors.append(error)
                # Ensure the instances contain valid parent references for foreign keys
                if isinstance(field, models.ForeignKey):
                    if column not in df:
                        error = f"Missing mandatory foreign key {column} for {model_name}"
                        errors.append(error)
                        continue
                    if not field.null:
                        for record in df[df[column].isnull()].itertuples():
                            error = (
                                f"Missing mandatory foreign key {column} for {model_name} in record "
                                f"{record.Index} from cell '{record.bss_sheet}'!{record.bss_column}{record.bss_row}"
                                f'{str({k: v for k,v in record._asdict().items() if k != "Index"})}'
                            )
                            errors.append(error)
                    # Validate foreign key values
                    if field.related_model.__name__ in dfs:
                        # The model is part of the fixture, so use the saved key from the dataframe
                        remote_keys = dfs[field.related_model.__name__][1]["key"]
                    else:
                        # The model is not in the fixture, so use the primary and natural keys for already saved instances
                        remote_keys = [instance.pk for instance in field.related_model.objects.all()]
                        if "natural_key" in dir(field.related_model):
                            remote_keys += [
                                list(instance.natural_key()) for instance in field.related_model.objects.all()
                            ]
                    # Check the non-null foreign key values are in the remote keys
                    for record in df[
                        df[column].replace("", pd.NA).notna() & ~df[column].isin(remote_keys)
                    ].itertuples():
                        error = (
                            f"Unrecognized '{column}' foreign key {getattr(record, column)} "
                            f"for {model_name} in record "
                            f"{record.Index} from cell '{record.bss_sheet}'!{record.bss_column}{record.bss_row}"
                            f'{str({k: v for k,v in record._asdict().items() if k != "Index"})}'
                        )
                        errors.append(error)

            # Use the Django model to validate the fields, so we can apply already defined model validations and
            # return informative error messages.
            fields = [
                field
                for field in model._meta.concrete_fields
                if not isinstance(field, models.ForeignKey) and field.name in df
            ]
            instance = model()
            for record in df.replace(np.nan, None).itertuples():
                for field in fields:
                    value = getattr(record, field.name)
                    if not value and field.null:
                        # Replace empty strings with None for optional fields
                        value = None
                    try:
                        field.clean(value, instance)
                    except Exception as e:
                        error = (
                            f'Invalid {field.name} value {value}:  "{", ".join(e.error_list[0].messages)}"\nRecord '
                            f"{record.Index} from cell '{record.bss_sheet}'!{record.bss_column}{record.bss_row} "
                            f"for {model_name} in record "
                            f'{str({k: v for k,v in record._asdict().items() if k != "Index"})}.'
                        )
                        errors.append(error)

            # Check that the kcals/kg matches the values in the ClassifiedProduct model, if it's present in the BSS
            if model_name == "LivelihoodActivity" and "product__kcals_per_unit" in df:
                df["product"] = df["livelihood_strategy"].apply(lambda x: x[4])
                df = ClassifiedProductLookup().get_instances(df, "product", "product")
                df["reference_kcals_per_unit"] = df["product"].apply(lambda x: x.kcals_per_unit)
                df["reference_unit_of_measure"] = df["product"].apply(lambda x: x.unit_of_measure)
                for record in df[df["product__kcals_per_unit"] != df["reference_kcals_per_unit"]].itertuples():
                    error = (
                        f"Non-standard value {record.product__kcals_per_unit} in '{record.column}' "
                        f"for {model_name} in record "
                        f'{str({k: v for k,v in record._asdict().items() if k != "Index"})}. '
                        f"Expected {record.reference_kcals_per_unit}/{record.reference_unit_of_measure} for {record.product}"
                    )
                    errors.append(error)

    if errors:
        raise RuntimeError("Missing or inconsistent metadata in BSS %s:\n%s" % (partition_key, "\n".join(errors)))

    metadata = {f"num_{key.lower()}": len(value) for key, value in instances.items()}
    metadata["total_instances"] = sum(len(value) for value in instances.values())
    metadata["preview"] = MetadataValue.md(f"```json\n{json.dumps(instances, indent=4)}\n```")
    return instances, metadata


def get_fixture_from_instances(instance_dict: dict[str, list[dict]]) -> tuple[list[dict], dict]:
    """
    Convert a dict containing a list of instances for each model into a Django fixture.
    """

    # Concatenate the separate lists of instances for each model into a single list of records
    fixture = []
    metadata = defaultdict(int)
    for model_name, instances in instance_dict.items():
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
    return fixture, metadata


def import_fixture(fixture: list[dict]) -> dict:
    """
    Import a Django fixture and return a metadata dictionary.
    """
    output_buffer = StringIO()

    # We need to use a .verbose_json file extension for Django to use the correct serializer.
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".verbose_json") as f:
        # Write the fixture to a temporary file so that Django can access it
        f.write(json.dumps(fixture))
        f.seek(0)
        call_command(verbose_load_data.Command(), f.name, verbosity=2, format="verbose_json", stdout=output_buffer)

    # Create the metadata reporting the number of instances created for each model
    metadata = defaultdict(int)
    for instance in fixture:
        metadata[f'num_{instance["model"].split(".")[-1]}'] += 1
    metadata["total_instances"] = len(fixture)
    metadata["preview"] = MetadataValue.md(f"```json\n{json.dumps(fixture, indent=4)}\n```")
    metadata["output"] = MetadataValue.md(f"```\n{output_buffer.getvalue()}\n```")
    return metadata


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def consolidated_fixture(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    wealth_characteristic_valid_instances,
    livelihood_activity_valid_instances,
    other_cash_income_valid_instances,
    wild_foods_valid_instances,
) -> Output[list[dict]]:
    """
    Consolidated Django fixture for a BSS, including Livelihood Activities and Wealth Group Characteristic Values.
    """
    # Combine the Wealth Charactertistic fixture with the records from the
    # Livelihood Activities fixtures, ignoring the duplicate Wealth Group
    # records.
    consolidated_instances = {
        # Put the wealth_characteristic_fixture first, because it loads the
        # WealthGroup instances, which are needed as a foreign key from LivelihoodActivity, etc.
        **wealth_characteristic_valid_instances,
        **{
            model_name: instances
            for model_name, instances in livelihood_activity_valid_instances.items()
            if model_name != "WealthGroup"
        },
        **wild_foods_valid_instances,
    }
    
    # Add the wild foods and other cash income instances, if they are present
    for model_name, instances in {**other_cash_income_valid_instances, **wild_foods_valid_instances}.items():
        if instances and model_name != "WealthGroup":
            consolidated_instances[model_name] += instances

    fixture, metadata = get_fixture_from_instances(consolidated_instances)

    return Output(
        fixture,
        metadata=metadata,
    )


@asset(partitions_def=bss_files_partitions_def)
def uploaded_baselines(
    context: AssetExecutionContext,
    baseline_instances,
    original_files,
) -> Output[None]:
    """
    Baselines from external BSS metadata, uploaded to the Django database using a fixture.

    This asset creates an empty Baseline with access to the original file.
    Downstream assets apply corrections to the original file and then process
    the contents to create Communities, Wealth Groups, Livelihood Strategies, etc.
    """
    fixture, metadata = get_fixture_from_instances(baseline_instances)
    metadata = import_fixture(fixture)

    # Add the file objects `bss` and `profile_report` FileFields to the model instances
    instance = baseline_instances["LivelihoodZoneBaseline"][0]
    livelihood_zone_baseline = LivelihoodZoneBaseline.objects.get_by_natural_key(
        instance["livelihood_zone_id"], instance["reference_year_end_date"]
    )
    livelihood_zone_baseline.bss = File(original_files, name=instance["bss"])
    livelihood_zone_baseline.save()

    return Output(
        None,
        metadata=metadata,
    )


@asset(partitions_def=bss_instances_partitions_def)
def imported_communities(
    context: AssetExecutionContext,
    community_instances,
) -> Output[None]:
    """
    Communities from a BSS, imported to the Django database using a fixture.
    """
    fixture, metadata = get_fixture_from_instances(community_instances)
    metadata = import_fixture(fixture)

    return Output(
        None,
        metadata=metadata,
    )


@asset(partitions_def=bss_instances_partitions_def)
def imported_baseline(
    context: AssetExecutionContext,
    consolidated_fixture,
) -> Output[None]:
    """
    Imported Django fixture for a BSS, added to the Django database.
    """
    metadata = import_fixture(consolidated_fixture)

    return Output(
        None,
        metadata=metadata,
    )
