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
            # Check whether the ReferenceData worksheet matches a Django model.
            for sheet_name in reference_data.sheet_names[1:]:
                model = None
                for app in ["common", "metadata", "baseline"]:
                    try:
                        model = class_from_name(f"{app}.models.{sheet_name}")
                        break
                    except AttributeError:
                        continue
                if model:
                    field_names = [f.name for f in model._meta.get_fields()]
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
                    if "product_id" in df:
                        df["product_id"] = df["product_id"].replace(pd.NA, None)
                        if "product" in field_names and "product_id" not in field_names:
                            field_names.append("product_id")
                    if "unit_of_measure_id" in df:
                        df["unit_of_measure_id"] = df["unit_of_measure_id"].replace("", None)
                        if "unit_of_measure" in field_names and "unit_of_measure_id" not in field_names:
                            field_names.append("unit_of_measure_id")
                    if "ordering" in df:
                        df["ordering"] = df["ordering"].replace("", None)

                    if sheet_name == "ClassifiedProduct":
                        for record in df.to_dict(orient="records"):
                            cpc = record.pop("cpc")
                            try:
                                instance = model.objects.get(pk=cpc)
                                for k, v in record.items():
                                    if k in field_names and v:
                                        expected = getattr(instance, k)
                                        if isinstance(expected, list):
                                            expected = sorted(expected)
                                        if v != expected:
                                            if cpc[-2] != "H" and k not in [
                                                "aliases",
                                                "common_name_en",
                                                "common_name_es",
                                                "common_name_fr",
                                                "common_name_pt",
                                                "common_name_ar",
                                            ]:
                                                raise RuntimeError(
                                                    "Attempted to update field %s for non-HEA product %s from %s to %s"
                                                    % (k, cpc, getattr(instance, k), v)
                                                )
                                            setattr(instance, k, v)
                                instance.save()
                                context.log.info(f"Updated {sheet_name} {str(instance)}")
                            except ClassifiedProduct.DoesNotExist:
                                if cpc[1:].isnumeric():
                                    raise ValueError("Missing real CPC code %s" % cpc)
                                parent_instance = model.objects.get(pk=cpc[:-2])
                                record = {k: v for k, v in record.items() if k in field_names}
                                record["cpc"] = cpc
                                instance = parent_instance.add_child(**record)
                                context.log.info(
                                    f"Created {sheet_name} {str(instance)} as a child of {str(parent_instance)}"
                                )
                    else:
                        if sheet_name == "SourceOrganization":
                            id_field = "name"
                        elif sheet_name == "ActivityLabel":
                            id_field = "activity_label"
                        elif sheet_name == "WealthCharacteristicLabel":
                            id_field = "wealth_characteristic_label"
                        else:
                            id_field = "code"
                        for record in df.to_dict(orient="records"):
                            id_value = record.pop(id_field)
                            record = {k: v for k, v in record.items() if k in field_names}
                            instance, created = model.objects.update_or_create(
                                **{"defaults": record, id_field: id_value}
                            )
                            context.log.info(f'{"Created" if created else "Updated"} {sheet_name} {str(instance)}')


@job
def update_metadata():
    load_all_metadata()
