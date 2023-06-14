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
