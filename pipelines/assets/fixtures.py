import datetime
import json
import os
import tempfile
from collections import defaultdict
from io import StringIO

import django
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


def get_fixture_from_instances(instance_dict: dict[str, list[dict]]) -> list[dict]:
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
    return metadata, fixture


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def consolidated_instances(
    wealth_characteristic_instances,
    livelihood_activity_instances,
    other_cash_income_instances,
    wild_foods_instances,
) -> Output[dict]:
    """
    Consolidated record instances from a BSS, ready to be validated.
    """
    # Build a dict of all the models, and their instances, that are to be loaded
    consolidated_instances = {
        # Put the wealth_characteristic_fixture first, because it loads the
        # WealthGroup instances, which are needed as a foreign key from LivelihoodActivity, etc.
        **wealth_characteristic_instances,
        **livelihood_activity_instances,
    }
    # Add the wild foods and other cash income instances, if they are present
    for model_name, instances in {**other_cash_income_instances, **wild_foods_instances}.items():
        if instances:
            consolidated_instances[model_name] += instances

    # For Livelihood Activities we need to create instances of the subclass, as well as the base class
    # so create an additional list of instances for each subclass.
    subclass_livelihood_activities = defaultdict(list)
    for instance in consolidated_instances["LivelihoodActivity"]:
        # The subclass instances also need a pointer to the base class instance
        instance["livelihoodactivity_ptr"] = (
            instance["wealth_group"][:3] + instance["livelihood_strategy"][2:] + [instance["wealth_group"][3]]
        )
        subclass_livelihood_activities[instance["strategy_type"]].append(instance)

    consolidated_instances = {**consolidated_instances, **subclass_livelihood_activities}

    metadata = {f"num_{key.lower()}": len(value) for key, value in consolidated_instances.items()}
    metadata["total_instances"] = sum(len(value) for value in consolidated_instances.values())
    metadata["preview"] = MetadataValue.md(f"```json\n{json.dumps(consolidated_instances, indent=4)}\n```")
    return Output(
        consolidated_instances,
        metadata=metadata,
    )


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def validated_instances(
    context: AssetExecutionContext,
    consolidated_instances,
) -> Output[dict]:
    """
    Validated record instances from a BSS, ready to be loaded via a Django fixture.
    """
    partition_key = context.asset_partition_key_for_output()
    # Create a dict of all the models, and a dataframe of their instances
    validate_instances(consolidated_instances, partition_key)

    metadata = {f"num_{key.lower()}": len(value) for key, value in consolidated_instances.items()}
    metadata["total_instances"] = sum(len(value) for value in consolidated_instances.values())
    metadata["preview"] = MetadataValue.md(f"```json\n{json.dumps(consolidated_instances, indent=4)}\n```")
    return Output(
        consolidated_instances,
        metadata=metadata,
    )


def validate_instances(consolidated_instances, partition_key):
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
        elif model_name == "SeasonalActivity":
            df["key"] = df[
                ["livelihood_zone_baseline", "seasonal_activity_type", "product", "additional_identifier"]
            ].apply(
                lambda x: (
                    x.iloc[0]
                    + [x.iloc[1], x.iloc[2] if pd.notna(x.iloc[2]) else "", x.iloc[3] if pd.notna(x.iloc[3]) else ""]
                ),
                axis="columns",
            )
        elif model_name == "SeasonalActivityOccurrence":
            df["key"] = df[["livelihood_zone_baseline", "seasonal_activity", "community", "start", "end"]].apply(
                lambda x: (x.iloc[0] + x.iloc[1] + [x.iloc[2][-1] if x.iloc[2] else ""] + [x.iloc[3], x.iloc[4]]),
                axis="columns",
            )
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
        raise RuntimeError("Missing or inconsistent metadata in BSS %s:\n%s" % (partition_key, errors))


@asset(partitions_def=bss_instances_partitions_def, io_manager_key="json_io_manager")
def consolidated_fixtures(
    context: AssetExecutionContext,
    config: BSSMetadataConfig,
    validated_instances,
) -> Output[list[dict]]:
    """
    Consolidated Django fixture for a BSS, including Livelihood Activities and Wealth Group Characteristic Values.
    """
    metadata, fixture = get_fixture_from_instances(validated_instances)
    metadata["preview"] = MetadataValue.md(f"```json\n{json.dumps(fixture, indent=4)}\n```")
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
    metadata, fixture = get_fixture_from_instances(baseline_instances)
    output_buffer = StringIO()

    # We need to use a .verbose_json file extension for Django to use the correct serializer.
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".verbose_json") as f:
        # Write the fixture to a temporary file so that Django can access it
        f.write(json.dumps(fixture))
        f.seek(0)
        call_command(verbose_load_data.Command(), f.name, verbosity=2, format="verbose_json", stdout=output_buffer)

    # Add the output to the metadata
    metadata["output"] = MetadataValue.md(f"```\n{output_buffer.getvalue()}\n```")

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
    metadata, fixture = get_fixture_from_instances(community_instances)
    output_buffer = StringIO()

    # We need to use a .verbose_json file extension for Django to use the correct serializer.
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".verbose_json") as f:
        # Write the fixture to a temporary file so that Django can access it
        f.write(json.dumps(fixture))
        f.seek(0)
        call_command(verbose_load_data.Command(), f.name, verbosity=2, format="verbose_json", stdout=output_buffer)

    # Add the output to the metadata
    metadata["preview"] = MetadataValue.md(f"```json\n{json.dumps(fixture, indent=4)}\n```")
    metadata["output"] = MetadataValue.md(f"```\n{output_buffer.getvalue()}\n```")

    return Output(
        None,
        metadata=metadata,
    )


@asset(partitions_def=bss_instances_partitions_def)
def imported_baselines(
    context: AssetExecutionContext,
    consolidated_fixtures,
) -> Output[None]:
    """
    Imported Django fixtures for a BSS, added to the Django database.
    """
    output_buffer = StringIO()

    # We need to use a .verbose_json file extension for Django to use the correct serializer.
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".verbose_json") as f:
        # Write the fixture to a temporary file so that Django can access it
        f.write(json.dumps(consolidated_fixtures))
        f.seek(0)
        call_command(verbose_load_data.Command(), f.name, verbosity=2, format="verbose_json", stdout=output_buffer)

    # Create the metadata reporting the number of instances created for each model
    metadata = defaultdict(int)
    for instance in consolidated_fixtures:
        metadata[f'num_{instance["model"].split(".")[-1]}'] += 1
    metadata["total_instances"] = len(consolidated_fixtures)
    metadata["output"] = MetadataValue.md(f"```\n{output_buffer.getvalue()}\n```")

    return Output(
        None,
        metadata=metadata,
    )
