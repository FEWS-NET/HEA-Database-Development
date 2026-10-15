# Household Economic Analysis (HEA)

The HEA Warehouse manages HEA Baseline data.

## Producing the Entity-Relationship Diagrams

You can generate the entity-relationship diagrams for the application,
using commands like:

```
./manage.py graph_models \
--dot \
--settings=hea.settings.base \
--verbosity=0 \
--theme erd \
--verbose-names \
--disable-sort-fields \
--hide-relations-from-fields \
--disable-abstract-fields \
--output ./erd.puml \
baseline
```

This produces a .puml file that can be rendered using a PlantUML
server, either within your IDE or using a service like http://www.plantuml.com/.

## Pipeline Status

The Pipeline Status pages (`/<lang>/viz/pipeline-status/`, linked from the Pipelines section of the
admin sidebar) show the Dagster status of every asset in each monitored pipeline, for every partition.
They require the `common.access_dagster_ui` permission.

A pipeline is monitored by adding `pipeline_status` metadata to its terminal asset, e.g.:

```python
@asset(
    partitions_def=bss_instances_partitions_def,
    metadata={"pipeline_status": {"label": "BSS import", "group_label": "Country", "group_separator": "~"}},
)
def imported_baseline(...):
```

The pipeline is the terminal asset plus all its upstream assets that share the same partitions
definition, so for `imported_baseline` it runs from `corrected_files`. All the keys are optional:
`label` defaults to the asset key, and if `group_separator` is set then the partitions can be filtered
by the part of the partition key before the first separator, e.g. the country. Both dynamic and time
window partitions are supported.

Dagster marks every asset downstream of a failed step as failed too, so the page reports the
*root failures* for each partition: the failed assets that do not have a failed parent. Click a
partition in the heatmap, or in the Failing partitions table, to see an asset graph for that
partition with links to the corresponding assets and runs in the Dagster UI. The asset graph requires
the Graphviz `dot` executable, which is installed in the application Docker image.

The status for all partitions is cached for 60 seconds. The status logic is in `pipelines/status.py` and
the views are in the `viz` app.

## Debugging inside Docker Containers

The `LAUNCHER` environment sets a wrapper program around the Python process
(`gunicorn`, `dagster-daemon`, `dagster-webserver`). This can be used to
enable a debugger inside Docker Containers:

1. Set `LAUNCHER="python3 -m debugpy --listen 0.0.0.0:5678"` in `.env`
2. Create Launch Configurations in Visual Studio Code like:

```json
			{
				"name": "Python: Attach to app (Docker Container)",
				"type": "debugpy",
				"request": "attach",
				"connect": {
					"host": "localhost",
					"port": 5678
				},
				"pathMappings": [
					{
						"localRoot": "${workspaceFolder:hea}",
						"remoteRoot": "/usr/src/app"
					}
				],
				"django": true,
				"justMyCode": false
			},
			{
				"name": "Python: Attach to dagster-daemon (Docker Container)",
				"type": "debugpy",
				"request": "attach",
				"connect": {
					"host": "localhost",
					"port": 5680
				},
				"pathMappings": [
					{
						"localRoot": "${workspaceFolder:hea}",
						"remoteRoot": "/usr/src/app"
					}
				],
				"django": true,
				"justMyCode": false
			}
```

3. Start the Docker containers as normal, and then use the Run and Debug
pane in Visual Studio code to launch the configuration that attaches to
the desired server.