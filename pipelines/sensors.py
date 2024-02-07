from pathlib import Path

from dagster import AssetSelection, RunRequest, SensorResult, sensor

from .assets.baseline import (
    bss_files_metadata,
    bss_files_partitions_def,
    corrected_files,
)


@sensor(asset_selection=AssetSelection.keys(bss_files_metadata.key, corrected_files.key))
def bss_file_sensor(context):
    instance = context.instance
    filenames = {
        "/".join(f.with_suffix("").parts[-2:])
        for f in Path("/home/roger/Temp/Baseline Storage Sheets (BSS)").glob("*/*")
        if f.is_file() and f.suffix in [".xls", ".xlsx"]
    }

    partitions = bss_files_partitions_def.get_partition_keys(dynamic_partitions_store=instance)

    for partition in partitions:
        if partition not in filenames:
            instance.delete_dynamic_partition(bss_files_partitions_def.name, partition)

    new_files = [
        f for f in filenames if not context.instance.has_dynamic_partition(bss_files_partitions_def.name, str(f))
    ]

    return SensorResult(
        run_requests=[RunRequest(partition_key=filename) for filename in new_files],
        dynamic_partitions_requests=[bss_files_partitions_def.build_add_request(new_files)],
    )
