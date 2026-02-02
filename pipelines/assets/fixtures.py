import datetime
import json
import os
import tempfile
from collections import defaultdict
from io import StringIO

import django
import pandas as pd
from dagster import AssetExecutionContext, MetadataValue, Output, asset
from django.core.exceptions import ObjectDoesNotExist, ValidationError
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

from baseline.models import LivelihoodActivity, LivelihoodZoneBaseline  # NOQA: E402
from common.management.commands import verbose_load_data  # NOQA: E402
from common.models import ClassifiedProduct  # NOQA: E402
from metadata.models import LivelihoodStrategyType  # NOQA: E402


def validate_instances(
    context: AssetExecutionContext, config: BSSMetadataConfig, instances: dict[str, list[dict]], partition_key: str
) -> Output[dict[str, list[dict]]]:
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
                instance["wealth_group"][:3]  # livelihood_zone, reference_year_end_date, wealth_group_category
                + instance["livelihood_strategy"][2:]  # strategy_type, season, product_id, additional_identifier
                + [instance["wealth_group"][3]]  # full_name
            )
            subclass_livelihood_activities[instance["strategy_type"]].append(subclass_instance)

        instances = {**instances, **subclass_livelihood_activities}

    valid_instances = {model_name: [] for model_name in instances}
    valid_keys = {model_name: {} for model_name in instances}
    errors = []
    current_timestamp = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    for model_name, model_instances in instances.items():

        # Ignore models where we don't have any instances to validate.
        if not model_instances:
            continue

        model = class_from_name(f"baseline.models.{model_name}")
        # Build a list of expected field names
        valid_field_names = [field.name for field in model._meta.concrete_fields]
        # Also include values that point directly to the primary key of related objects
        valid_field_names += [
            field.get_attname()
            for field in model._meta.concrete_fields
            if field.get_attname() not in valid_field_names
        ]

        # Iterate over the instances, validating each one in turn
        for i, instance in enumerate(model_instances):
            model_errors = []
            # Add created and modified timestamps if they are missing
            for field in ["created", "modified"]:
                if field in valid_field_names and field not in instance:
                    instance[field] = current_timestamp

            # Add the natural key so we can validate foreign keys in child models.
            if model_name == "LivelihoodZone":
                instance["natural_key"] = instance["code"]
            elif model_name == "LivelihoodZoneBaseline":
                instance["natural_key"] = [instance["livelihood_zone_id"], instance["reference_year_end_date"]]
            elif model_name == "Community":
                instance["natural_key"] = instance["livelihood_zone_baseline"] + [instance["full_name"]]
            elif model_name == "WealthGroup":
                instance["natural_key"] = instance["livelihood_zone_baseline"] + [
                    instance["wealth_group_category"],
                    instance["full_name"],
                ]
            elif model_name == "LivelihoodStrategy":
                instance["natural_key"] = instance["livelihood_zone_baseline"] + [
                    instance["strategy_type"],
                    # instance['season'] is a natural key itself, so it is stored as a list even though it only
                    # has a single component - the season name - so take the first element of the list.
                    # Natural key components must be "" rather than None
                    instance["season"][0] if instance["season"] else "",
                    instance["product_id"] or "",  # Natural key components must be "" rather than None
                    instance["additional_identifier"],
                ]
            elif model_name in ["LivelihoodActivity"] + [x for x in LivelihoodStrategyType]:
                instance["natural_key"] = (
                    instance["wealth_group"][:3]  # livelihood_zone, reference_year_end_date, wealth_group_category
                    + instance["livelihood_strategy"][2:]  # strategy_type, season, product_id, additional_identifier
                    + [instance["wealth_group"][3]]  # full_name
                )
            elif model_name == "WealthGroupCharacteristicValue":
                instance["natural_key"] = instance["wealth_group"][
                    :3  # livelihood_zone, reference_year_end_date, wealth_group_category
                ] + [
                    instance["wealth_characteristic_id"],
                    instance["reference_type"],
                    instance["product_id"] or "",  # Natural key components must be "" rather than None
                    instance["wealth_group"][3],  # full_name
                ]
            # The natural key is a list of strings, or possibly numbers, so validate that here to avoid confusing
            # error messages later.
            if "natural_key" not in instance:
                raise RuntimeError(f"Missing natural_key for {model_name} {i} from {str(instance)}")
            if not isinstance(instance["natural_key"], list):
                raise RuntimeError(
                    f"Invalid natural_key {instance['natural_key']} for {model_name} {i} from {str(instance)}"
                )
            for component in instance["natural_key"]:
                if not isinstance(component, (str, int)):
                    raise RuntimeError(
                        f"Invalid component '{component}' in natural_key {instance['natural_key']} for {model_name} {i} from {str(instance)}"
                    )

            # Create a string reference to the record for error messages
            record_reference = f"{model_name} {i} from "
            if "bss_sheet" in instance:
                record_reference += f"'{instance['bss_sheet']}'!"
            if "bss_column" in instance and "bss_row" in instance:
                record_reference += f"{instance['bss_column']}{instance['bss_row']}: "
            elif "bss_column" in instance:
                record_reference += f"{instance['bss_column']}:{instance['bss_column']}: "
            elif "bss_row" in instance:
                record_reference += f"{instance['bss_row']}:{instance['bss_row']}: "
            record_reference += f"{str({k: v for k,v in instance.items()})}"

            # Apply field-level checks
            for field in model._meta.concrete_fields:
                column = field.name if field.name in instance else field.get_attname()

                # Ensure that mandatory fields have values
                if not field.blank:
                    if column not in instance:
                        error = f"Missing mandatory field {field.name} for {record_reference}"
                        model_errors.append(error)
                    elif not instance[column] and not instance[column] == 0:
                        error = f"Missing value for mandatory field {column} for {record_reference}"
                        model_errors.append(error)
                # Ensure the instances contain valid parent references for foreign keys
                if isinstance(field, models.ForeignKey):
                    if column not in instance:
                        error = f"Missing mandatory foreign key {column} for {record_reference}"
                        model_errors.append(error)
                    else:
                        # Validate foreign key values
                        if field.related_model.__name__ not in valid_keys:
                            # If related model is part of the fixture, then it should have already been validated
                            if field.related_model.__name__ in instances:
                                raise RuntimeError(
                                    "Related model %s not validated yet but needed for %s"
                                    % (field.related_model.__name__, model_name)
                                )
                            else:
                                # The model is not in the fixture, and hasn't been checked already, so use the primary and
                                # natural keys for already saved instances. Save the keys as a dict mapping to the
                                # instance, so that we can resolve natural keys later when validating model.clean()
                                remote_keys = {
                                    related_instance.pk: related_instance
                                    for related_instance in field.related_model.objects.all()
                                }
                                if hasattr(field.related_model, "natural_key"):
                                    for related_instance in field.related_model.objects.all():
                                        remote_keys[related_instance.natural_key()] = related_instance
                                valid_keys[field.related_model.__name__] = remote_keys

                        if not field.null and not instance[column]:
                            error = f"Missing mandatory foreign key {column} for {record_reference}"
                            model_errors.append(error)
                        elif instance[column]:
                            # Check the non-null foreign key values are in the remote keys
                            # Convert natural keys from lists to tuples for lookup (because lists can't be dict keys)
                            value = tuple(instance[column]) if isinstance(instance[column], list) else instance[column]
                            if value not in valid_keys[field.related_model.__name__]:
                                error = f"Unrecognized '{column}' foreign key {value} for {record_reference}."
                                model_errors.append(error)

            # Check that the kcals/kg matches the values in the ClassifiedProduct model, if it's present in the BSS
            if model_name == "LivelihoodActivity" and "product__kcals_per_unit" in instance:
                product = ClassifiedProduct.objects.get(pk=instance["product_id"])
                if instance["product__kcals_per_unit"] != product.kcals_per_unit:
                    error = (
                        f"Non-standard value {instance['product__kcals_per_unit']}; "
                        f"expected {product.kcals_per_unit}/{product.unit_of_measure} for {product}\n"
                        f"for {record_reference}."
                    )
                    model_errors.append(error)

            # Attempt to run the model's `clean()` to validate model-level logic where possible.
            model_instance = model()
            try:
                for field in model._meta.concrete_fields:
                    column = field.name if field.name in instance else field.get_attname()
                    if column in instance:
                        value = instance[column]
                        # Replace empty strings with None for optional fields
                        if field.null and not value:
                            value = None
                        # Handle foreign key fields, resolving natural keys to model instances
                        if isinstance(field, models.ForeignKey):
                            if isinstance(value, list):
                                value = tuple(value)
                            value = valid_keys[field.related_model.__name__].get(value)
                        else:
                            # Use the Django model to validate the fields, so we can apply already defined model
                            # validations and return informative error messages.
                            try:
                                field.clean(value, model_instance)
                            except Exception as e:
                                error = (
                                    f'Invalid {field.name} value {value}:  "{", ".join(e.error_list[0].messages)}"\n'
                                    f"for {record_reference}."
                                )
                                model_errors.append(error)
                        setattr(model_instance, column, value)
                # We don't need to validate LivelihoodActivity, because we will validate the subclass instances anyway.
                if model != LivelihoodActivity:
                    try:
                        model_instance.clean()
                    except Exception as e:
                        # Ignore missing related object errors since the related object may be
                        # loaded by the same fixture. We check class name to handle a possible
                        # custom RelatedObjectNotFound exception defined elsewhere.
                        if isinstance(e, ObjectDoesNotExist) or e.__class__.__name__ == "RelatedObjectNotFound":
                            pass
                        elif isinstance(e, ValidationError):
                            # Record validation error messages in a similar format to field.clean handling
                            msgs = []
                            if hasattr(e, "message_dict"):
                                for k, v in e.message_dict.items():
                                    msgs.extend(v if isinstance(v, list) else [v])
                            else:
                                msgs = e.messages if hasattr(e, "messages") else [str(e)]
                            for msg in msgs:
                                error = f"{msg}\nfor {record_reference}."
                                model_errors.append(error)
                        else:
                            # Record unexpected errors from clean() so the author can investigate
                            model_errors.append(f"Error during clean(): {e}\nfor {record_reference}.")
            except Exception as e:
                model_errors.append(f"Error creating {model_name} instance: {e}\nfor {record_reference}.")
                # Ignore errors creating the instance for clean()
                pass

            if model_errors:
                errors += model_errors
            else:
                # Instance is valid, so add it to the list of valid instances
                valid_instances[model_name].append(instance)
                valid_keys[model_name][tuple(instance["natural_key"])] = model_instance

    metadata = {}
    for model_name in instances.keys():
        metadata[f"valid_{model_name}"] = f"{len(valid_instances[model_name])}/{len(instances[model_name])}"
    metadata["total_valid_instances"] = (
        f"{sum(len(value) for value in valid_instances.values())}/{sum(len(value) for value in instances.values())}"
    )
    metadata["preview"] = MetadataValue.md(
        f"```json\n{json.dumps(valid_instances, indent=4, ensure_ascii=False)}\n```"
    )

    if errors:
        if config.strict:
            raise RuntimeError("Missing or inconsistent metadata in BSS %s:\n%s" % (partition_key, "\n".join(errors)))
        else:
            context.log.warning(
                "Ignoring missing or inconsistent metadata in BSS %s:\n%s" % (partition_key, "\n".join(errors))
            )
            metadata["errors"] = MetadataValue.md(f'```text\n{"\n".join(errors)}\n```')
            # Move the preview metadata item to the end of the dict
            metadata["preview"] = metadata.pop("preview")

    return Output(valid_instances, metadata=metadata)


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
    metadata["preview"] = MetadataValue.md(f"```json\n{json.dumps(fixture, indent=4, ensure_ascii=False)}\n```")
    return Output(fixture, metadata=metadata)


def import_fixture(fixture: list[dict]) -> Output[None]:
    """
    Import a Django fixture and return a metadata dictionary.
    """
    output_buffer = StringIO()

    # We need to use a .verbose_json file extension for Django to use the correct serializer.
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".verbose_json") as f:
        # Write the fixture to a temporary file so that Django can access it
        f.write(json.dumps(fixture, indent=4, ensure_ascii=False))
        f.seek(0)
        call_command(verbose_load_data.Command(), f.name, verbosity=2, format="verbose_json", stdout=output_buffer)

    # Create the metadata reporting the number of instances created for each model
    metadata = defaultdict(int)
    for instance in fixture:
        metadata[f'num_{instance["model"].split(".")[-1]}'] += 1
    metadata["total_instances"] = len(fixture)
    metadata["preview"] = MetadataValue.md(f"```json\n{json.dumps(fixture, indent=4, ensure_ascii=False)}\n```")
    metadata["output"] = MetadataValue.md(f"```\n{output_buffer.getvalue()}\n```")
    # No downstream assets, so we only need to return the metadata
    return Output(
        None,
        metadata=metadata,
    )


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
    }

    # Add the wild foods and other cash income instances, if they are present
    for model_name, instances in {**other_cash_income_valid_instances, **wild_foods_valid_instances}.items():
        if instances and model_name != "WealthGroup":
            if model_name not in consolidated_instances:
                consolidated_instances[model_name] = []
            consolidated_instances[model_name] += instances

    return get_fixture_from_instances(consolidated_instances)


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
    output = get_fixture_from_instances(baseline_instances)
    fixture = output.value
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
        metadata=metadata.metadata,
    )


@asset(partitions_def=bss_instances_partitions_def)
def imported_communities(
    context: AssetExecutionContext,
    community_instances,
) -> Output[None]:
    """
    Communities from a BSS, imported to the Django database using a fixture.
    """
    output = get_fixture_from_instances(community_instances)
    return import_fixture(output.value)


@asset(partitions_def=bss_instances_partitions_def)
def imported_baseline(
    context: AssetExecutionContext,
    consolidated_fixture,
) -> Output[None]:
    """
    Imported Django fixture for a BSS, added to the Django database.
    """
    return import_fixture(consolidated_fixture)
