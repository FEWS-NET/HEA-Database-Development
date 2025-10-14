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