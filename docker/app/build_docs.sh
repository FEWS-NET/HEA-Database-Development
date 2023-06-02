#!/bin/bash
set -e

# Re-render Warehouse schema diagram

# Prepare database
./manage.py migrate --noinput

# grep removes any lines starting with { or [
# This is because sometimes manage.py emits warnings "{ ... Failed to send traces to Datadog Agent ... }" on stdout
# DOT output is indented so not affected.
./manage.py graph_models  --settings=fdw.settings.build_docs   --verbosity=0  --theme django2018   \
    --include-models   DocumentType,DataSourceOrganization,DataSourceDocument,DataUsagePolicy,DataSourceDocumentSchedule,DataSeries,DataSet,DataCollection,DataCollectionPeriod,BaseDataPoint,DataPoint,IndicatorGroup,Indicator,GeographicUnit \
      spatial warehouse | grep -Ev '^({|\[)' > tmp_class_diagram.dot && \

  dot tmp_class_diagram.dot -Tpng -oclass_diagram.png && \

      # Only overwrite repo copy if previous command successful. "/bin/mv" as some shells alias `mv` to `mv -i`.
      /bin/mv -f class_diagram.png docs/src/images/class_diagram.png && \

        rm tmp_class_diagram.dot


# Re-generate OpenAPI yaml

# Sphinx will copy anything in _extra to the root of the built docs
# Django serves this at /docs/openapi/
./manage.py spectacular --settings=fdw.settings.build_docs --file openapi.yml && \

  /bin/mv -f openapi.yml docs/_extra/openapi.yml


# Make the HTML docs (see Makefile for description of CLI options)

cd docs
make html -e SPHINXOPTS="-j 1 -a -E -c ."
make -e SPHINXOPTS="-j 1 -a -E -c . -D language='fr'" -e BUILDDIR="_build/fr" html
make -e SPHINXOPTS="-j 1 -a -E -c . -D language='es'" -e BUILDDIR="_build/es" html

# Create the PDF if latexmk is available
if hash latexmk 2>/dev/null; then
    # -Q doesn't work on latexpdf
    make latexpdf

    # Copy build pdf docs to the html folder so they can be downloaded from hosted documentation
    cp _build/latex/*.pdf _build/html/
fi


cd ..
