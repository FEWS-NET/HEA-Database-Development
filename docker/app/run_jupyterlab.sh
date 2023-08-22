#!/bin/bash

echo Compiling translations
python manage.py compilemessages

# Wait up to 30 minutes for outstanding migrations to finish running on another container, checking every 30 seconds
#for i in `seq 1 60`; do
#    ./manage.py migrate --plan | grep "No planned migration operations." && break
#    echo Waiting for outstanding database migrations
#    sleep 30
#done

# Need to create and set permissions on the logs so that we can run as the django user and
# still have permission to write to the logs directory using docker-compose.override.yml
echo Setting up logs
touch log/django.log
chown -R django:django log/*

echo Starting JupyterLab in the /notebooks directory
cd /usr/src/app/notebooks
gosu django jupyter lab --notebook-dir=/usr/src/app/notebooks --preferred-dir=/usr/src/app/notebooks --port=8888 --no-browser
