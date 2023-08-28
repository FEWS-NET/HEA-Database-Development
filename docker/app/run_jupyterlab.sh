#!/bin/bash

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
chown -R django:django log/*

# @TODO Move the pip install of Jupyter here, and remove it from requirements/base.txt, to reduce the number of
# Python packages installed in the base image.
# pip install jupyterlab==4.0.5

echo Starting JupyterLab
IPYTHONDIR=/usr/src/app/jupyter/ipython \
JUPYTER_CONFIG_DIR=/usr/src/app/jupyter/lab/user-settings \
JUPYTER_DATA_DIR=/usr/src/app/jupyter/jupyter/data \
JUPYTER_RUNTIME_DIR=/usr/src/app/run/jupyter/ \
gosu django jupyter lab --notebook-dir=/usr/src/app/notebooks --ip=0.0.0.0 --port=8888 --no-browser
