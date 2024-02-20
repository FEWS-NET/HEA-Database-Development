"""
Load metadata from Google Sheets
"""

import os

import django
import luigi
import pandas as pd
from dagster import OpExecutionContext, job, op
from kiluigi.targets.google_drive import GoogleDriveTarget

from ..utils import class_from_name

# set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hea.settings.production")

# Configure Django with our custom settings before importing any Django classes
django.setup()

from common.lookups import ClassifiedProductLookup  # NOQA: E402
from common.models import ClassifiedProduct  # NOQA: E402


@op
def load_all_metadata(context: OpExecutionContext):
    """
    Load all metadata from the Reference Data Google Sheet into the Django models.
    """
    # @TODO replace KiLuigi's GoogleDriveTarget with fsspec.open and gdrivefs to remove the dependency on Luigi.
    # creds = json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    # with fsspec.open(
    #    "gdrive:///0AOJ0gJ8sjnO7Uk9PVA/Database Design/Reference Data",
    #    token="service_account",
    #    access="read_only",
    #    creds=creds,
    # ) as f:
    target = GoogleDriveTarget(
        "14ygcIlYa0ZZpNIQJpmsGHrNIOYXKzihGf6JyLIG3GbY",
        format=luigi.format.Nop,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    with target.open() as f:
        with pd.ExcelFile(f) as reference_data:
            model = None
            sheet_name = None
            sheet_names = reference_data.sheet_names[1:]
            # Iterate over the sheets in the ReferenceData workbook, in reverse order (because the Label sheets that
            # need Subject Matter Expert input are at beginning, and depend on the sheets at the end).
            for sheet_name in reversed(sheet_names):
                # Check whether the ReferenceData worksheet matches a Django model.
                model = None
                for app in ["common", "metadata", "baseline"]:
                    try:
                        model = class_from_name(f"{app}.models.{sheet_name}")
                        break
                    except AttributeError:
                        continue
                if model:
                    valid_field_names = [field.name for field in model._meta.concrete_fields]
                    # Also include values that point directly to the primary key of related objects
                    valid_field_names += [
                        field.get_attname()
                        for field in model._meta.concrete_fields
                        if field.get_attname() not in valid_field_names
                    ]
                    # If we found a model, then update the model from the contents of the Referemce Data worksheet
                    df = pd.read_excel(f, sheet_name).fillna("")
                    if "status" in df:
                        df = df[df["status"] == "Complete"]
                    if "aliases" in df:
                        df["aliases"] = df["aliases"].apply(lambda x: sorted(x.split("~")) if x else None)
                    if "cpcv2" in df:
                        df["cpcv2"] = df["cpcv2"].apply(lambda x: sorted(x.split("~")) if x else None)
                    if "hs2012" in df:
                        df["hs2012"] = df["hs2012"].apply(lambda x: sorted(x.split("~")) if x else None)
                    if "kcals_per_unit" in df:
                        df["kcals_per_unit"] = df["kcals_per_unit"].replace("", None)
                    if "is_start" in df:
                        df["is_start"] = df["is_start"].replace("", False)
                    if "product_name" in df:
                        df = ClassifiedProductLookup().do_lookup(df, "product_name", "product_id")
                    if "country_id" in df:
                        df["country_id"] = df["country_id"].replace(pd.NA, None)
                    if "product_id" in df:
                        df["product_id"] = df["product_id"].replace(pd.NA, None)
                    if "unit_of_measure_id" in df:
                        df["unit_of_measure_id"] = df["unit_of_measure_id"].replace("", None)
                    if "currency_id" in df:
                        df["currency_id"] = df["currency_id"].replace("", None)
                    if "wealth_characteristic_id" in df:
                        df["wealth_characteristic_id"] = df["wealth_characteristic_id"].replace("", None)
                    if "ordering" in df:
                        df["ordering"] = df["ordering"].replace("", None)

                    if sheet_name == "ClassifiedProduct":
                        for record in df.to_dict(orient="records"):
                            cpc = record.pop("cpc")
                            try:
                                instance = model.objects.get(pk=cpc)
                                for k, v in record.items():
                                    if k in valid_field_names:
                                        current = getattr(instance, k)
                                        if isinstance(current, list):
                                            current = sorted(current)
                                        if v != current:
                                            if cpc[-2] != "H" and k not in [
                                                "aliases",
                                                "common_name_en",
                                                "common_name_es",
                                                "common_name_fr",
                                                "common_name_pt",
                                                "common_name_ar",
                                            ]:
                                                if v and current:
                                                    raise RuntimeError(
                                                        "Attempted to update field %s for non-HEA product %s from %s to %s"  # NOQA: E501
                                                        % (k, cpc, current, v)
                                                    )
                                                else:
                                                    continue
                                            setattr(instance, k, v)
                                instance.save()
                                context.log.info(f"Updated {sheet_name} {str(instance)}")
                            except ClassifiedProduct.DoesNotExist:
                                if cpc[1:].isnumeric():
                                    raise ValueError("Missing real CPC code %s" % cpc)
                                parent_instance = model.objects.get(pk=cpc[:-2])
                                record = {k: v for k, v in record.items() if k in valid_field_names}
                                record["cpc"] = cpc
                                instance = parent_instance.add_child(**record)
                                context.log.info(
                                    f"Created {sheet_name} {str(instance)} as a child of {str(parent_instance)}"
                                )
                    else:
                        if sheet_name == "SourceOrganization":
                            id_fields = "name"
                        elif sheet_name == "Season":
                            id_fields = "name_en"
                        elif sheet_name == "UnitOfMeasure":
                            id_fields = "abbreviation"
                        elif sheet_name == "ActivityLabel":
                            id_fields = "activity_label"
                        elif sheet_name == "WealthCharacteristicLabel":
                            id_fields = "wealth_characteristic_label"
                        else:
                            id_fields = "code"
                        for record in df.to_dict(orient="records"):
                            if isinstance(id_fields, str):
                                id_fields = [id_fields]

                            id_values = [record.pop(k) for k in id_fields]
                            keys = dict(zip(id_fields, id_values))
                            record = {k: v for k, v in record.items() if k in valid_field_names}
                            try:
                                instance, created = model.objects.update_or_create(**{"defaults": record, **keys})
                            except Exception as e:
                                raise RuntimeError(
                                    "Failed to create or update %s %s with %s" % (sheet_name, keys, record)
                                ) from e
                            context.log.info(f'{"Created" if created else "Updated"} {sheet_name} {str(instance)}')


@job
def update_metadata():
    load_all_metadata()
