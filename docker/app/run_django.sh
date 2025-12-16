#!/bin/bash

if [ x"$DJANGO_MIGRATE" != x"" ]; then
    # Wait up to 2 minutes for the database to be created, in case this is a brand-new installation
    for i in `seq 1 12`; do
        psql --no-align --tuples-only -c "SELECT current_user || '@' || current_database()" > /dev/null 2>&1 && break
        echo Waiting for database connection
        sleep 10
    done
    echo Running database migrations
    python manage.py migrate --noinput
fi

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

if [ x"$CREATE_SAMPLE_DATA" != x"" ]; then
    echo Start creation of sample data
    python manage.py create_sample_data &
fi

# Need to create and set permissions on the logs so that we can run as the django user and
# still have permission to write to the logs directory using docker-compose.override.yml
echo Setting up logs
touch log/access.log
touch log/django.log
touch log/django_sql.log
chown -R django:django log/*

echo Starting Gunicorn with DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}
if [ x"$LAUNCHER" != x"" ]; then
    echo using ${LAUNCHER}
fi
gosu django ${LAUNCHER} /usr/local/bin/gunicorn ${APP}.asgi:application \
    --name ${APP}${ENV} \
    --worker-class uvicorn.workers.UvicornWorker \
    --config $(dirname $(readlink -f "$0"))/gunicorn_config.py \
    $* 2>&1