# Full Import of the BSSs

This document describes how to do a full reload of the Baseline Storage Sheets (BSSs) into the HEA Warehouse using the
Dagster pipelines.

The reload runs as a sequence of stages. Each stage depends on the data that the previous stage put into the Django
database. The stages also use different partition definitions:

| Partition definition | Partition key example          | Created by                                         |
| -------------------- | ------------------------------ | -------------------------------------------------- |
| None                 |                                | Not partitioned                                    |
| `bss_files`          | `Malawi~MW01~2018-03-31`       | The `bss_metadata` asset, from the BSS Metadata sheet |
| `bss_instances`      | `Malawi~MW01~2018-03-31`       | The `bss_instance_sensor`, from the `LivelihoodZoneBaseline` table |

Run each stage to completion and check its output before starting the next one. A failure in an early stage usually
causes many confusing failures in later stages, so it is quicker to fix it first.

## Summary

| Stage | Job                               | Partitions      | Purpose                                                 |
| ----- | --------------------------------- | --------------- | ------------------------------------------------------- |
| 1     | `update_external_assets`          | `bss_files`     | Read the BSS Metadata sheet and create the `bss_files` partitions |
| 2     | `upload_baselines`                | `bss_files`     | Create a `LivelihoodZoneBaseline` for each BSS, with the original file attached |
| 3     | `update_metadata`                 | None            | Load the Corrections worksheet from the BSS Metadata sheet |
| 3     | `load_all_geographies`            | None            | Optional: load the zone geographies and populations from FDW |
| 4     | `import_communities_from_fixture` | `bss_instances` | Crate the `corrected_files` and load the Communities into the database |
| 5     | `update_metadata`                 | None            | Load the Community Aliases from the BSS Metadata sheet  |
| 6     | `extract_dataframes`              | `bss_instances` | Extract the data from each corrected BSS into DataFrames |
| 6     | `summarize_dataframes`            | None            | Optional: create the label summaries across all BSSs    |
| 6     | `create_consolidated_fixture`     | `bss_instances` | Build and validate a fixture for each BSS               |
| 6     | `import_baseline_from_fixture`    | `bss_instances` | Load each consolidated fixture into the database        |

## Prerequisites

- Run the database migrations: `./manage.py migrate`.
- Set the environment variables that the pipelines use, as listed in `env.example`. These include
  `BSS_METADATA_WORKBOOK`, `BSS_FILES_FOLDER`, `GOOGLE_APPLICATION_CREDENTIALS` and `DAGSTER_ASSET_BASE_PATH`.
- Make sure that a Django user exists for every author named in the Corrections worksheet. Stage 3 uses these users
  as the authors of the corrections.
- In the Dagster UI, open Deployment > Concurrency (`/deployment/concurrency`) and set a limit for the
  `django_loaddata` pool, for example 1. The import assets run in this pool, which stops concurrent `loaddata` runs
  from causing duplicate primary key errors.
- Turn on the `bss_instance_sensor`, which is needed after stage 2.

To run a partitioned job for every partition, open the job in the Dagster UI, click Materialize all, and launch a
backfill for all the partitions. If some partitions fail, fix the cause and then launch a new backfill for just the
failed partitions.

## Stage 1: Metadata

1. Run `update_external_assets` to materialize `bss_metadata` and `completed_bss_metadata`. `bss_metadata` creates a
   `bss_files` partition for every BSS in the Metadata worksheet whose file exists.

   On a new Dagster instance there are no `bss_files` partitions yet. If the launchpad requires a partition, then
   select `bss_metadata` and `completed_bss_metadata` on the Assets page and materialize them from there instead.

   Check: the `num_baselines` metadata on `bss_metadata`, and the `num_incomplete` and `incomplete` metadata on
   `completed_bss_metadata`. Stage 2 fails for any BSS with incomplete metadata, so complete the BSS Metadata
   worksheet first and then rerun this step.

## Stage 2: Baselines

1. Run `upload_baselines` for all `bss_files` partitions. For each BSS it materializes:
   - `original_files`: the BSS read from `BSS_FILES_FOLDER`.
   - `baseline_instances`: the `LivelihoodZone` and `LivelihoodZoneBaseline` records from the BSS Metadata.
   - `uploaded_baselines`: loads those records and attaches the original BSS to the `LivelihoodZoneBaseline`.

   Check: every partition succeeds. Also review the `missing_worksheets` and `worksheet_errors` metadata on
   `original_files`, which show BSSs that will probably fail in later stages.

2. Optional: run `load_all_geographies` to add the geography and population estimate to each Baseline.

3. Wait for the `bss_instance_sensor` to create a `bss_instances` partition for each `LivelihoodZoneBaseline`. The
   sensor runs every 10 minutes.

   Check: the number of `bss_instances` partitions matches the number of `bss_files` partitions.

## Stage 3: Corrections

Run `update_metadata`, which includes `load_all_corrections`. It loads the `Corrections` worksheet from the
BSS Metadata sheet into `LivelihoodZoneBaselineCorrection`.

Corrections are matched to Baselines that are already in the database. Any correction for a Baseline that does not
exist is ignored, so this job must run after stage 2.

Check: the run succeeds. The logs list every correction that was created, updated or deleted.

## Stage 4: Communities

1. Run `import_communities_from_fixture` for all `bss_instances` partitions. For each BSS it materializes:
   - `corrected_files`: the original BSS with the corrections applied.
   - `community_instances`: the Communities from the header rows of the `WB` worksheet.
   - `imported_communities`: loads the Communities into the database.

   Check: every partition succeeds.

## Stage 5: Community Aliases

Run `update_metadata`, which includes `update_community_aliases`. It loads the `Community Aliases` worksheet from the
BSS Metadata sheet and saves the aliases in the matching Communities. Stage 6 uses the aliases to match the Community
names in the other worksheets, which are sometimes spelled differently from the names in the `WB` worksheet header.

Check: the run succeeds. The logs list every Community whose aliases were updated.

## Stage 6: Consolidated fixture

1. Run `extract_dataframes` for all `bss_instances` partitions. It extracts the data from each `corrected_files` BSS
   into DataFrames, one for each section of the BSS.

   Check: every partition succeeds.

   Optional: run `summarize_dataframes` to create the label summaries across all BSSs, which help to manage the label
   metadata. These assets call Google Translate, which makes them slow.

2. Run `create_consolidated_fixture` for all `bss_instances` partitions. It creates the model instances for each
   section of the BSS, validates them, and combines them into a single `consolidated_fixture`.

   Check: every partition succeeds. The common errors are:
   - `contains unmatched Community full_name values`. A Community name in the worksheet does not match a Community
     or any of its aliases. Add the alias to the Community Aliases worksheet, rerun stage 5, and then rerun this job
     for the failed partitions.
   - Unrecognized labels. Update the label in the Reference Data sheet, rerun `update_reference_data`, and then rerun
     this job for the failed partitions.
   - Validation errors from the `*_valid_instances` assets, which describe the invalid records.

3. Run `import_baseline_from_fixture` for all `bss_instances` partitions. This materializes `imported_baseline`,
   which loads each `consolidated_fixture` into the database.

   The consolidated fixture is authoritative for the Baselines that it contains records for. In the same transaction as
   the load, `imported_baseline` deletes any Wealth Groups, Wealth Group Characteristic Values, Livelihood Strategies,
   Livelihood Activities, Key Parameters, Seasonal Activities and other Baseline data for those Baselines that are not
   in the fixture. Records that are in the fixture are updated in place, so their primary keys don't change. The
   Baseline, its Corrections and its Communities (including the Community Aliases) are retained, because they are
   loaded by earlier stages. The `num_deleted_<model>` metadata on the materialization reports the number of records
   deleted. Similarly, `imported_seasonal_activities` deletes Seasonal Activities and Seasonal Activity Occurrences that
   are not in its fixture.

   Check: every partition succeeds. The "BSS import" Pipeline Status page (`/<lang>/viz/pipeline-status/`) shows the
   status of every asset from `corrected_files` to `imported_baseline` for each partition. It also reports the root
   failure for each failed partition, so it is useful for checking stages 4 and 6.

## Rerunning part of the import

When source data changes, rerun the stage that uses that data and every later stage, for the affected partitions
only:

| Changed data                       | Rerun from                                                      |
| ---------------------------------- | --------------------------------------------------------------- |
| Reference Data sheet               | Stage 1 `update_reference_data`, then stage 6 `create_consolidated_fixture` |
| BSS Metadata worksheet or BSS file | Stage 1 `update_external_assets`                                 |
| Corrections worksheet              | Stage 3                                                          |
| Community Aliases worksheet        | Stage 5, then stage 6 `create_consolidated_fixture`              |
