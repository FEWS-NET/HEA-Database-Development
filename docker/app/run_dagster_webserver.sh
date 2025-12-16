#!/bin/bash

# Wait up to 30 minutes for outstanding migrations to finish running on another container, checking every 30 seconds
for i in $(seq 1 60); do
    ./manage.py migrate --plan | grep "No planned migration operations." && break
    echo Waiting for outstanding database migrations
    sleep 30
done

# Need to create and set permissions on the logs so that we can run as the django user and
# still have permission to write to the logs directory using docker-compose.override.yml
echo Setting up logs
touch log/django.log
chown -R django:django log/*

echo Starting Dagster Webserver
if [ x"$LAUNCHER" != x"" ]; then
    echo using ${LAUNCHER}
fi
gosu django ${LAUNCHER} /usr/local/bin/dagster-webserver -h 0.0.0.0 -p 3000 -m pipelines --path-prefix /${DAGSTER_WEBSERVER_PREFIX} $*