#!/bin/bash

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
chown -R django:django log/*

# Use the AWS EC2 meta-data if it exists and fall back to the default route
echo Starting Celery Beat with DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE} and ddtrace to ${DD_TRACE_AGENT_URL}
[ -f /usr/src/app/run/beat.pid ] && rm /usr/src/app/run/beat.pid
gosu django ddtrace-run celery --app=${APP} beat --loglevel=INFO --pidfile=/usr/src/app/run/beat.pid $*
