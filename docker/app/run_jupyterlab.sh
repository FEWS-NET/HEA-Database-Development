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

JUPYTER_NO_CONFIG=1 \
XDG_DATA_HOME="/usr/src/app/notebooks" \
PYTHONPATH="/usr/src/app:/usr/src/app/apps:$PYTHONPATH" \
JUPYTER_RUNTIME_DIR="/usr/src/app" \
    gosu django jupyter lab \
        --notebook-dir=/usr/src/app/notebooks \
        --preferred-dir /usr/src/app/notebooks \
        --port=8888 \
        --no-browser

# JUPYTER_NO_CONFIG: Prevents per-user notebook configuration scripts from running.
# No config seems safest way to avoid devs stepping on each others' toes sharing the container?

# PYTHONPATH JUPYTER_RUNTIME_DIR: So Python imports match our Django code

# XDG_DATA_HOME: Prevents JupyterLab looking for django OS home directory /home/django - tmp better?
# Seems to create a .local subdirectory which Jupyter will hide, haven't seen what else.

# Other environment variables:
# JUPYTER_CONFIG_DIR: Override config file location.
# JUPYTER_DATA_DIR: Override the default data directory (used for non-transient,
# non-configuration files, eg, kernelspecs, nbextensions, or voila templates):

# >>> jupyter --paths
# config:
#     /root/.jupyter
#     /root/.local/etc/jupyter
#     /usr/local/etc/jupyter
#     /etc/jupyter
# data:
#     /root/.local/share/jupyter
#     /usr/local/share/jupyter
#     /usr/share/jupyter
# runtime:
#     /root/.local/share/jupyter/runtime
#

# JupyterLab doubles our package count to 142, a public increase in surface area.
# I am wondering if your original idea of a dedicated container is wiser.
# FROM dev as jupyter
# RUN pip install --quiet --no-cache-dir -r /usr/src/app/requirements/jupyterlab.txt
# COPY . /usr/src/app

