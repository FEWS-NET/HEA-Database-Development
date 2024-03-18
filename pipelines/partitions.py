from dagster import DynamicPartitionsDefinition

# List of files in the BSS root folder
bss_files_partitions_def = DynamicPartitionsDefinition(name="bss_files")

# List of instances in the LivelihoodBaseline model
bss_instances_partitions_def = DynamicPartitionsDefinition(name="bss_instances")
