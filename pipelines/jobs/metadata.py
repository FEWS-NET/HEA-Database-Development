"""
Load metadata from Google Sheets
"""

import datetime
import json
import os
from io import BytesIO

import django
import numpy as np
import pandas as pd
import requests
from dagster import OpExecutionContext, job, op
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon, Polygon
from django.db import models, transaction
from gdrivefs.core import GoogleDriveFile
from upath import UPath

from ..configs import ReferenceDataConfig
from ..utils import class_from_name

# set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hea.settings.production")

# Configure Django with our custom settings before importing any Django classes
django.setup()

from baseline.lookups import CommunityLookup  # NOQA: E402
from baseline.models import (  # NOQA: E402
    Community,
    LivelihoodZoneBaseline,
    LivelihoodZoneBaselineCorrection,
)
from common.lookups import ClassifiedProductLookup, UserLookup  # NOQA: E402
from metadata.models import ActivityLabel  # NOQA: E402


def load_metadata_for_model(context: OpExecutionContext, sheet_name: str, model: models.Model, df: pd.DataFrame):
    """
    Load the metadata from a single worksheet, passed as a DataFrame, into a Django model.
    """
    model_name = model.__name__
    valid_field_names = [field.name for field in model._meta.concrete_fields]
    # Also include values that point directly to the primary key of related objects
    valid_field_names += [
        field.get_attname() for field in model._meta.concrete_fields if field.get_attname() not in valid_field_names
    ]
    if "aliases" in df:
        df["aliases"] = df["aliases"].apply(lambda x: sorted(x.lower().split("~")) if x else None)
    if "cpcv2" in df:
        df["cpcv2"] = df["cpcv2"].apply(lambda x: sorted(x.split("~")) if x else None)
    if "hs2012" in df:
        df["hs2012"] = df["hs2012"].apply(lambda x: sorted(x.split("~")) if x else None)
    if "kcals_per_unit" in df:
        df["kcals_per_unit"] = df["kcals_per_unit"].replace("", None)
    if "is_start" in df:
        df["is_start"] = df["is_start"].replace("", False)
    if "product_name" in df:
        df = ClassifiedProductLookup(require_match=False).do_lookup(df, "product_name", "product_id")
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
    if "activity_type" in df:
        df["activity_type"] = df["activity_type"].replace("", ActivityLabel.LivelihoodActivityType.LIVELIHOOD_ACTIVITY)

    if model_name == "ClassifiedProduct":
        existing_instances = {instance.pk: instance for instance in model.objects.filter(pk__in=df["cpc"])}
        for record in df.to_dict(orient="records"):
            cpc = record.pop("cpc")
            if cpc in existing_instances:
                instance = existing_instances[cpc]
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
            else:
                if cpc[1:].isnumeric():
                    raise ValueError("Missing real CPC code %s" % cpc)
                parent_instance = model.objects.get(pk=cpc[:-2])
                record = {k: v for k, v in record.items() if k in valid_field_names}
                record["cpc"] = cpc
                instance = parent_instance.add_child(**record)
                context.log.info(f"Created {model_name} {str(instance)} as a child of {str(parent_instance)}")
        num_instances = model.objects.bulk_update(
            existing_instances.values(),
            fields=record.keys(),
        )
        context.log.info(f"Updated {num_instances} {sheet_name} instances")

    else:
        if model_name == "SourceOrganization":
            id_fields = "name"
        elif model_name == "Season":
            id_fields = "name_en"
        elif model_name == "UnitOfMeasure":
            id_fields = "abbreviation"
        elif model_name == "ActivityLabel":
            id_fields = ["activity_label", "activity_type"]
        elif model_name == "WealthCharacteristicLabel":
            id_fields = "wealth_characteristic_label"
        else:
            id_fields = "code"
        # Add primary keys if they are not already in the id_fields,
        # so that we can save individual instances if required
        if isinstance(id_fields, str):
            id_fields = [id_fields]
        if model._meta.pk.name not in id_fields:
            keys_df = pd.DataFrame.from_records(
                model.objects.all().values(model._meta.pk.name, *id_fields)
            )  # NOQA: E501
            df = df.merge(
                keys_df,
                how="left",
                on=id_fields,
            )
            df[model._meta.pk.name] = df[model._meta.pk.name].replace(np.nan, None)
        # Turn the dataframe into a set of unsaved model instances
        instances = []
        for record in df.to_dict(orient="records"):
            record = {k: v for k, v in record.items() if k in valid_field_names}
            instances.append(model(**record))
        try:
            instances = model.objects.bulk_create(
                instances,
                update_conflicts=True,
                update_fields=[k for k in valid_field_names if k not in id_fields and k != model._meta.pk.name],
                unique_fields=id_fields,
            )
            context.log.info(f"Created or updated {len(instances)} {sheet_name} instances")
        except Exception:
            # Bulk create failed, so try creating/updating the instances one at a time to see which one failed
            for i, instance in enumerate(instances):
                try:
                    instance.save()
                except Exception as e:
                    key = [getattr(instance, id_field) for id_field in id_fields]
                    instance = {
                        k: v for k, v in instance.__dict__.items() if k not in ["_state", "created", "modified"]
                    }
                    raise RuntimeError(
                        f"Failed to create/update {model_name} instance {i} {key} from:\n{json.dumps(instance, indent=4, ensure_ascii=False)}"
                    ) from e


@op
def load_all_metadata(context: OpExecutionContext, config: ReferenceDataConfig):
    """
    Load all metadata (or a subset passed in sheet_names) from the Reference Data Google Sheet into the Django models.
    """
    storage_options = {"token": "service_account", "access": "read_only", "root_file_id": "0AOJ0gJ8sjnO7Uk9PVA"}
    storage_options["creds"] = json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    p = UPath("gdrive://Database Design/Reference Data", **storage_options)
    with p.fs.open(p.path, mode="rb", cache_type="bytes") as f:
        # Google Sheets have to exported rather than read directly
        if isinstance(f, GoogleDriveFile) and (f.details["mimeType"] == "application/vnd.google-apps.spreadsheet"):
            f = BytesIO(p.fs.export(p.path, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))

        with pd.ExcelFile(f) as reference_data:
            # Get the required sheet names from the config, or load all sheets that match a Django model
            sheet_names = config.sheet_names or reference_data.sheet_names[1:]
            # Make sure that the sheet names are in the same order as they are in the worksbook
            sheet_names = [sheet_name for sheet_name in reference_data.sheet_names[1:] if sheet_name in sheet_names]
            # Iterate over the sheets in the ReferenceData workbook, in reverse order (because the Label sheets that
            # need Subject Matter Expert input are at beginning, and depend on the sheets at the end).
            for sheet_name in reversed(sheet_names):
                if sheet_name in ["ActivityLabel", "OtherCashIncomeLabel", "WildFoodsLabel", "SummaryLabel"]:
                    model = ActivityLabel
                else:
                    # Check whether the ReferenceData worksheet matches a Django model.
                    model = None
                    for app in ["common", "metadata", "baseline"]:
                        try:
                            model = class_from_name(f"{app}.models.{sheet_name}")
                            break
                        except AttributeError:
                            continue
                if model:
                    # If we found a model, then update the model from the contents of the Reference Data worksheet
                    df = pd.read_excel(f, sheet_name).fillna("")
                    try:
                        load_metadata_for_model(context, sheet_name, model, df)
                    except Exception as e:
                        raise RuntimeError("Failed to create/update %s" % sheet_name) from e


@op
def load_all_corrections(context: OpExecutionContext):
    """
    Load all Corrections from the BSS Metadata Google Sheet into the Django models.
    """
    storage_options = {"token": "service_account", "access": "read_only", "root_file_id": "0AOJ0gJ8sjnO7Uk9PVA"}
    storage_options["creds"] = json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    p = UPath("gdrive://Database Design/BSS Metadata", **storage_options)
    with p.fs.open(p.path, mode="rb", cache_type="bytes") as f:
        # Google Sheets have to be exported rather than read directly
        if isinstance(f, GoogleDriveFile) and (f.details["mimeType"] == "application/vnd.google-apps.spreadsheet"):
            f = BytesIO(p.fs.export(p.path, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))

        df = pd.read_excel(f, sheet_name="Corrections", engine="openpyxl")

        # Use a 1-based index to match the Excel Row Number
        df.index += 1

        # Add the author_id as a foreign key to the User model
        df = UserLookup().do_lookup(df, "author", "author_id")

        # Add the livelihood_zone_baseline_id as a foreign key to the LivelihoodZoneBaseline model
        livelihood_zone_baseline_df = pd.DataFrame.from_records(
            LivelihoodZoneBaseline.objects.all().values("id", "livelihood_zone_id", "reference_year_end_date")
        )
        livelihood_zone_baseline_df["livelihood_zone_baseline"] = (
            livelihood_zone_baseline_df["livelihood_zone_id"].astype(str)
            + "~"
            + livelihood_zone_baseline_df["reference_year_end_date"].map(lambda x: x.isoformat())
        )
        livelihood_zone_baseline_df["livelihood_zone_baseline_id"] = livelihood_zone_baseline_df["id"]
        df = df.merge(
            livelihood_zone_baseline_df[["livelihood_zone_baseline", "livelihood_zone_baseline_id"]],
            how="inner",
            on="livelihood_zone_baseline",
        )
        df["created"] = df["modified"] = datetime.datetime.now(tz=datetime.timezone.utc)
        df = df.fillna("")

        # Check the the corrections dataframe doesn't contain any duplicates
        duplicates_df = df[df.duplicated(subset=["livelihood_zone_baseline", "worksheet_name", "cell_range"])][
            ["livelihood_zone_baseline", "worksheet_name", "cell_range"]
        ]
        if not duplicates_df.empty:
            raise ValueError(f"Found duplicate corrections:\n{duplicates_df.to_markdown()}")

        with transaction.atomic():

            df = df.set_index(["livelihood_zone_baseline_id", "worksheet_name", "cell_range"], drop=False)

            # Get the current set of corrections from the database, so we can see what has changed
            existing_instances = LivelihoodZoneBaselineCorrection.objects.filter(
                livelihood_zone_baseline_id__in=df["livelihood_zone_baseline_id"].unique()
            ).select_related("livelihood_zone_baseline")
            existing_df = pd.DataFrame.from_records(
                existing_instances.values(),
                columns=[
                    "livelihood_zone_baseline_id",
                    "worksheet_name",
                    "cell_range",
                    "previous_value",
                    "value",
                    "author_id",
                    "comment",
                ],
            )
            existing_df = existing_df.set_index(
                ["livelihood_zone_baseline_id", "worksheet_name", "cell_range"], drop=False
            )

            # Ignore unchanged corrections
            unchanged_corrections = df[
                df.set_index(
                    [
                        "livelihood_zone_baseline_id",
                        "worksheet_name",
                        "cell_range",
                        "previous_value",
                        "value",
                        "author_id",
                        "comment",
                    ]
                ).index.isin(
                    existing_df.set_index(
                        [
                            "livelihood_zone_baseline_id",
                            "worksheet_name",
                            "cell_range",
                            "previous_value",
                            "value",
                            "author_id",
                            "comment",
                        ]
                    ).index
                )
            ]
            df = df[~df.index.isin(unchanged_corrections.index)]

            # Build the corrections as a list of unsaved LivelihoodZoneBaselineCorrection instances
            corrections = [
                LivelihoodZoneBaselineCorrection(
                    **{
                        k: v
                        for k, v in correction.items()
                        if k
                        in [
                            "livelihood_zone_baseline_id",
                            "worksheet_name",
                            "cell_range",
                            "previous_value",
                            "value",
                            "correction_date",
                            "author_id",
                            "comment",
                            "created",
                            "modified",
                        ]
                    }
                )
                for correction in df.to_dict(orient="records")
            ]
            # Save the corrections to the database using a bulk_create, updating any existing corrections
            instances = LivelihoodZoneBaselineCorrection.objects.bulk_create(
                corrections,
                update_conflicts=True,
                update_fields=["previous_value", "value", "correction_date", "author_id", "comment", "modified"],
                unique_fields=["livelihood_zone_baseline_id", "worksheet_name", "cell_range"],
            )

            # Report on the corrections that were created or updated
            for instance in instances:
                key = (instance.livelihood_zone_baseline_id, instance.worksheet_name, instance.cell_range)
                record = df.loc[key]
                if key not in existing_df.index:
                    context.log.info(
                        f"Created correction for {record['livelihood_zone_baseline']} {record['worksheet_name']}!{record['cell_range']}"
                    )
                else:
                    context.log.info(
                        f"Updated correction for {record['livelihood_zone_baseline']} {record['worksheet_name']}!{record['cell_range']}"
                    )

            # Delete any LivelihoodZoneBaselineCorrection instances that are for Baselines that are in the Corrections
            # worksheet but that don't match a correction entry in the worksheet.
            for instance in existing_instances:
                key = (instance.livelihood_zone_baseline_id, instance.worksheet_name, instance.cell_range)
                if key not in df.index and key not in unchanged_corrections.index:
                    context.log.info(f"Deleted correction {str(instance)}")
                    instance.delete()

            context.log.info(f"Skipped {len(unchanged_corrections)} unchanged corrections")


@op
def load_all_community_aliases(context: OpExecutionContext):
    """
    Load all Community Aliases from the BSS Metadata Google Sheet into the Django models.
    """
    storage_options = {"token": "service_account", "access": "read_only", "root_file_id": "0AOJ0gJ8sjnO7Uk9PVA"}
    storage_options["creds"] = json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    p = UPath("gdrive://Database Design/BSS Metadata", **storage_options)
    with p.fs.open(p.path, mode="rb", cache_type="bytes") as f:
        # Google Sheets have to be exported rather than read directly
        if isinstance(f, GoogleDriveFile) and (f.details["mimeType"] == "application/vnd.google-apps.spreadsheet"):
            f = BytesIO(p.fs.export(p.path, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))

        df = pd.read_excel(f, sheet_name="Community Aliases", engine="openpyxl")

        # Use a 1-based index to match the Excel Row Number
        df.index += 1

        # Add two new columnds to df, livelihood_zone_id and reference_year_end_date, by splitting the livelihood_zone_baseline on the ~
        df[["livelihood_zone_id", "reference_year_end_date"]] = df["livelihood_zone_baseline"].str.split(
            "~", expand=True
        )
        df["full_name"] = df["full_name"].str.strip()
        df["reference_year_end_date"] = pd.to_datetime(df["reference_year_end_date"])

        # Add the livelihood_zone_baseline_id as a foreign key to the LivelihoodZoneBaseline model
        livelihood_zone_baseline_df = pd.DataFrame.from_records(
            LivelihoodZoneBaseline.objects.all().values("id", "livelihood_zone_id", "reference_year_end_date")
        )
        livelihood_zone_baseline_df["livelihood_zone_baseline_id"] = livelihood_zone_baseline_df["id"]
        livelihood_zone_baseline_df["reference_year_end_date"] = pd.to_datetime(
            livelihood_zone_baseline_df["reference_year_end_date"]
        )
        df = df.merge(
            livelihood_zone_baseline_df[
                ["livelihood_zone_id", "reference_year_end_date", "livelihood_zone_baseline_id"]
            ],
            how="inner",
            on=["livelihood_zone_id", "reference_year_end_date"],
        )

        # Add the community id
        df["livelihood_zone_baseline_key"] = df["livelihood_zone_baseline"]
        df["livelihood_zone_baseline"] = df["livelihood_zone_baseline_id"]
        df = CommunityLookup().do_lookup(df, "full_name", "id")

        df["aliases"] = df["aliases"].apply(lambda x: tuple(sorted(x.lower().split("~"))) if x else None)
        df["modified"] = datetime.datetime.now(tz=datetime.timezone.utc)
        df = df.dropna()

        # Check the the corrections dataframe doesn't contain any duplicates
        duplicates_df = df[df.duplicated(subset=["livelihood_zone_baseline", "full_name"])][
            ["livelihood_zone_baseline_key", "full_name"]
        ]
        if not duplicates_df.empty:
            raise ValueError(f"Found duplicate aliases:\n{duplicates_df.to_markdown()}")

        with transaction.atomic():

            df = df.set_index(["livelihood_zone_baseline_id", "full_name"], drop=False)

            # Get the current set of aliases from the database, so we can see what has changed
            existing_instances = Community.objects.filter(
                livelihood_zone_baseline_id__in=df["livelihood_zone_baseline_id"].unique()
            ).select_related("livelihood_zone_baseline")
            existing_df = pd.DataFrame.from_records(
                existing_instances.values(),
                columns=[
                    "livelihood_zone_baseline_id",
                    "full_name",
                    "aliases",
                ],
            )
            existing_df["aliases"] = existing_df["aliases"].apply(lambda x: tuple(x) if x else None)
            existing_df = existing_df.set_index(["livelihood_zone_baseline_id", "full_name"], drop=False)

            # Ignore unchanged aliases
            unchanged_aliases = df[
                df.set_index(
                    [
                        "livelihood_zone_baseline_id",
                        "full_name",
                        "aliases",
                    ]
                ).index.isin(
                    existing_df.set_index(
                        [
                            "livelihood_zone_baseline_id",
                            "full_name",
                            "aliases",
                        ]
                    ).index
                )
            ]
            df = df[~df.index.isin(unchanged_aliases.index)]

            # Build the update as a list of unsaved Community instances
            communities = [
                Community(
                    **{
                        k: v
                        for k, v in community.items()
                        if k
                        in [
                            "id",
                            "livelihood_zone_baseline_id",
                            "full_name",
                            "aliases",
                            "modified",
                        ]
                    }
                )
                for community in df.to_dict(orient="records")
            ]
            # Save the communities to the database using a bulk_update
            Community.objects.bulk_update(
                communities,
                fields=["aliases", "modified"],
            )

            # Report on the aliases that were updated
            for record in df.itertuples():
                context.log.info(
                    f"Updated aliases for Community {record.livelihood_zone_baseline_key} {record.full_name}"
                )

            context.log.info(f"Skipped {len(unchanged_aliases)} Communities with unchanged aliases")


@op
def load_all_fewsnet_geographies(context: OpExecutionContext):
    """
    Load all Livelihood Zone Baseline geographies from the FEWS NET Data Warehouse via the API.
    """
    baseline_countries = (
        LivelihoodZoneBaseline.objects.all()
        .values_list("livelihood_zone__country__iso3166a2", flat=True)
        .order_by("livelihood_zone__country__iso3166a2")
        .distinct()
    )
    all_geometries = {}
    for iso3166a2 in baseline_countries:
        response = requests.get(
            f"https://fdw.fews.net/api/feature/?format=geojson&unit_type=livelihood_zone&ordering=fnid&country_code={iso3166a2}"
        )
        response.raise_for_status()
        srid = int(response.json()["crs"]["properties"]["name"].split(":")[-1])
        for feature in response.json()["features"]:
            # Also save the geometry for the Livelihood Zone Baseline
            all_geometries[
                (
                    feature["properties"]["attributes"]["EFF_YEAR"],
                    feature["properties"]["attributes"]["LZCODE"],
                )
            ] = feature

        for livelihood_zone_baseline in LivelihoodZoneBaseline.objects.filter(
            livelihood_zone__country_id=iso3166a2
        ).order_by(
            "livelihood_zone__country__iso3166a2",
            "reference_year_end_date",
            "livelihood_zone__code",
        ):
            for feature in all_geometries.values():
                start_date = (
                    datetime.date.fromisoformat(feature["properties"]["start_date"])
                    if feature["properties"]["start_date"]
                    else datetime.date.min
                )
                end_date = (
                    datetime.date.fromisoformat(feature["properties"]["end_date"])
                    if feature["properties"]["end_date"]
                    else datetime.date.max
                )
                if (
                    feature["properties"]["attributes"]["LZCODE"] == livelihood_zone_baseline.livelihood_zone.code
                ) and (start_date <= livelihood_zone_baseline.valid_from_date <= end_date):
                    geometry = GEOSGeometry(json.dumps(feature["geometry"]), srid=srid)
                    if isinstance(geometry, Polygon):
                        geometry = MultiPolygon(geometry)
                    livelihood_zone_baseline.geography = geometry
                    livelihood_zone_baseline.save()
                    context.log.info(f"Updated geometry for {livelihood_zone_baseline}")
                    continue
            context.log.warning(f"Failed to find FEWS NET geometry for {livelihood_zone_baseline}")


@job
def update_metadata():
    load_all_metadata()
    load_all_corrections()
    load_all_community_aliases()


@job
def load_all_geographies():
    load_all_fewsnet_geographies()
