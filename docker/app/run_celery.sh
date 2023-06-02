#!/bin/bash

# Collect static files to allow Celery Tasks to build outputs requiring them
if [ ! -f assets/staticfiles.json ]; then
    echo Collecting static files
    python manage.py collectstatic --noinput
fi

echo Compiling translations
python manage.py compilemessages

# Wait up to 30 minutes for outstanding migrations to finish running on another container, checking every 30 seconds
for i in `seq 1 60`; do
    ./manage.py migrate --plan | grep "No planned migration operations." && break
    echo Waiting for outstanding database migrations
    sleep 30
done

# Need to create and set permissions on the logs so that we can run as the django user and
# still have permission to write to the logs directory using docker-compose.override.yml
echo Setting up logs
touch log/django.log
touch log/django_sql.log
chown -R django:django log/*

params=()
if [ "${POOL}" == "threads" ]; then
    # If $POOL == threads, pass to the worker call and set concurrency to two, to permit Luigi to spawn
    # additional worker Processes (prefork raises "daemonic processes are not allowed to have children"), and prevent
    # long-running pipelines blocking the queue.
    params+=(--pool="${POOL}")
    params+=(--concurrency=2)
else
    # Default pool is prefork, using multiprocessing. Allow only one process per container and add containers to scale.
    # Containers are very lightweight, so there is no real resource consumption difference between running 4 Processes
    # within a single Worker vs 4 Workers with a single Process each.
    params+=(--concurrency=1)
fi

# Note that we need `--loglevel=DEBUG` in order to ensure that DEBUG level messages
# can reach custom handlers, for example in common.resources.LoggingResourceMixin
# Use the AWS EC2 meta-data if it exists and fall back to the default route
echo Starting Celery with DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE} and ddtrace to ${DD_TRACE_AGENT_URL}
gosu django ddtrace-run celery --app=${APP} worker --hostname=${PGDATABASE}_${QUEUE}@%n --queues=${QUEUES:-$QUEUE} -Ofair "${params[@]}" --loglevel=DEBUG --events
