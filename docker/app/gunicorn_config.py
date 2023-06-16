import os
import sys

import environ
import jsonlogging

env = environ.Env(
    # set casting, default value
    DD_TRACE_ENABLED=(bool, False),
    GUNICORN_PORT=(int, 8000),
    LOG_FORMATTER=(str, "standard"),
)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    with open(os.path.join(BASE_DIR, "VERSION.txt")) as v_file:
        APP_VERSION = v_file.readline().rstrip("\n")
except IOError:
    APP_VERSION = "develop"
# Allow external access on the standard Django port
bind = f"0.0.0.0:{env('GUNICORN_PORT')}"
# Allow unlimited length requests
# This is an DDOS attack vector, but the risk is small and Data Explorer
# can create very long requests when passing individual dataseries ids
limit_request_line = 0
# Set the access_log_format and handlers according to whether we are logging to DataDog
access_handlers = ["logfile", "access_log"]
if env("DD_TRACE_ENABLED"):
    access_handlers += ["console"]
    statsd_host = env("DD_DOGSTATSD_URL").split("//")[
        1
    ]  # Gunicorn doesn't recognize the udp:// scheme
# Set the access_log_format according to whether we are using a log processor like FluentD or DataDog
if env("LOG_FORMATTER") == "json":
    access_log_format = '{ "time_local":"%(t)s", "remote_addr":"%(h)s", "request":"%(U)s", "query":"%(q)s", "request_method":"%(m)s", "status":%(s)s, "body_bytes_sent":%(B)d, "request_time":%(D)d, "http_user_agent":"%(a)s", "http_referrer":"%(f)s", "x_forwarded_for": "%({X-Forwarded-For}i)s"}'  # NOQA
else:
    access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
        },
        "standard": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s"
        },
        "simple": {"format": "%(levelname)s %(message)s"},
        "message_only": {"format": "%(message)s"},
        "json": {
            "()": jsonlogging.LogstashFormatterV1,
            "tags": [
                f"client={env('CLIENT')}",
                f"app={env('APP')}",
                f"env={env('ENV')}",
                f"app_version={APP_VERSION}",
            ],
        },
    },
    "handlers": {
        "logfile": {
            "level": "DEBUG",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": BASE_DIR + "/log/django.log",
            "when": "midnight",
            "interval": 1,
            "backupCount": 7,
            "formatter": "standard",
        },
        "console": {
            "level": "DEBUG",
            "stream": sys.stdout,
            "class": "logging.StreamHandler",
            "formatter": env("LOG_FORMATTER"),
        },
        "access_log": {
            "level": "DEBUG",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": BASE_DIR + "/log/access.log",
            "when": "midnight",
            "interval": 1,
            "backupCount": 7,
            "formatter": "message_only",
        },
    },
    "loggers": {
        "gunicorn.error": {
            "handlers": ["console", "logfile"],
            "level": "DEBUG",
            "propagate": False,
        },
        "gunicorn.access": {
            "handlers": access_handlers,
            "level": "DEBUG",
            "propagate": False,
        },
        "environ": {"level": "INFO", "propagate": False},
        "fiona": {"level": "INFO", "propagate": False},
        "rasterio": {"level": "INFO", "propagate": False},
        "shapely": {"level": "INFO", "propagate": False},
    },
    "root": {"handlers": ["console", "logfile"], "level": "DEBUG"},
}
