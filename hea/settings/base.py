import os
import socket
import sys
import warnings
from os.path import abspath, basename, dirname, join, normpath

import environ
import jsonlogging
import requests
from django.utils.translation import gettext_lazy as _

# Ignore irrelevant Openpyxl warnings
messages = [
    r"Unknown type for ContentType",
    r"Unknown type for _ip_UnifiedCompliancePolicyUIAction",
    r"Unknown type for Sign-off status",
    r"Unknown type for _ip_UnifiedCompliancePolicyProperties",
]
# And irrelevant Luigi errors, caused by using a local scheduler
messages += [
    r"The configuration contains the parameter 'no_configure_logging' with value 'True' that is not consumed by the task 'core'.",  # NOQA: E501
    r"The configuration contains the parameter 'pidfile' with value '/usr/src/app/run/luigi.pid' that is not consumed by the task 'scheduler'.",  # NOQA: E501
]
for message in messages:
    warnings.filterwarnings("ignore", message)

env = environ.Env(LOG_FORMATTER=(str, "standard"))

DJANGO_ROOT = dirname(dirname(abspath(__file__)))
SITE_ROOT = dirname(DJANGO_ROOT)
SITE_NAME = basename(DJANGO_ROOT)
sys.path.append(DJANGO_ROOT)
sys.path.append(normpath(join(SITE_ROOT, "apps")))
with open(os.path.join(SITE_ROOT, "VERSION.txt")) as v_file:
    APP_VERSION = v_file.readline().rstrip("\n")


SECRET_KEY = env("SECRET_KEY")

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = env.list(
    "DOMAIN",
    default=[
        env("PGDATABASE"),
        env("PGDATABASE") + ".localdomain",
        "localhost",
        "127.0.0.1",
        "host.docker.internal",
    ],
)
try:
    EC2_PRIVATE_IP = requests.get("http://169.254.169.254/2018-09-24/meta-data/local-ipv4", timeout=0.01).text
    if EC2_PRIVATE_IP:
        ALLOWED_HOSTS.append(EC2_PRIVATE_IP)
    # If using ECS with the awsvpc network type, the call will be to the trunked ENI address
    # rather than the address of the main network interface for the ECS host
    ECS_PRIVATE_IP = socket.gethostbyname(socket.gethostname())
    if ECS_PRIVATE_IP not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(ECS_PRIVATE_IP)
except requests.exceptions.RequestException:
    pass
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

POSTGIS_TEMPLATE = f"template_{SITE_NAME.lower()}"
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": env("PGDATABASE"),
        "USER": env("PGUSER"),
        "PASSWORD": env("PGPASSWORD"),
        "HOST": 'localhost',
        "PORT": env.int("PGPORT", 5432),
        "OPTIONS": {"sslmode": "prefer", "application_name": SITE_NAME.lower()},
        "SCHEMA": f"{SITE_NAME.lower()}_owner",
        "TEST": {
            "TEMPLATE": f"template_{SITE_NAME.lower()}",
            "SERIALIZE": False,
        },
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "OPTIONS": {
            "MAX_ENTRIES": 1000,
        },
    },
}

EXTERNAL_APPS = [
    "treebeard",
    "rest_framework",
    "django_filters",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "django.contrib.admindocs",
    "binary_database_files",
    "django_extensions",
    "ddtrace.contrib.django",
]
PROJECT_APPS = ["common", "metadata", "baseline"]
INSTALLED_APPS = EXTERNAL_APPS + PROJECT_APPS

MIDDLEWARE = [
    "django.middleware.gzip.GZipMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "common.middleware.language.LanguageMiddleware",
    "django.middleware.common.CommonMiddleware",
    # "common.middleware.RequestLoggingMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
        "common.renderers.HtmlTableRenderer",
        "rest_framework_xml.renderers.XMLRenderer",
        "common.renderers.FormattedCSVRenderer",
    ),
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
    ],
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "EXCEPTION_HANDLER": "apps.common.exception_handlers.drf_exception_handler",
    "STRICT_JSON": True,
}

ROOT_URLCONF = "hea.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            normpath(join(SITE_ROOT, "templates")),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "hea.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
LANGUAGES = (
    ("en", _("English")),
    ("fr", _("French")),
    ("es", _("Spanish")),
    ("pt", _("Portuguese")),
    ("ar", _("Arabic")),
)
LOCALE_PATHS = (os.path.join(SITE_ROOT, "locale"),)

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

# Media (including uploaded files)
MEDIA_ROOT = normpath(join(SITE_ROOT, "media"))
MEDIA_URL = "/media/"

# Staticfiles
STATIC_HOST = env.str("DJANGO_STATIC_HOST", "")
STATIC_URL = STATIC_HOST + "/static/"
STATIC_ROOT = normpath(join(SITE_ROOT, "assets"))
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

STATICFILES_DIRS = (normpath(join(SITE_ROOT, "static")),)

LOGGING = {
    "version": 1,
    # Don't disable existing loggers, because doing so
    # will stop the Gunicorn loggers from working
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"},
        "standard": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
        "simple": {"format": "%(levelname)s %(message)s"},
        "json": {
            "()": jsonlogging.LogstashFormatterV1,
            "tags": [
                "client=%s" % env("CLIENT"),
                "app=%s" % env("APP"),
                "env=%s" % env("ENV"),
                "app_version=%s" % APP_VERSION,
            ],
        },
    },
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
    },
    "handlers": {
        "logfile": {
            "level": "INFO",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": SITE_ROOT + "/log/django.log",
            "when": "midnight",
            "interval": 1,
            "backupCount": 7,
            "formatter": "standard",
        },
        "console": {
            "level": "INFO",
            "stream": sys.stdout,
            "class": "logging.StreamHandler",
            "formatter": env.str("LOG_FORMATTER", "standard"),
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "filters": ["require_debug_false"],
            "include_html": True,
        },
    },
    "loggers": {
        "ddtrace": {"handlers": ["logfile"], "level": "INFO"},
        "django.request": {"handlers": ["console", "logfile"], "level": "INFO", "propagate": False},
        "django.db.backends": {"handlers": ["console", "logfile"], "level": "INFO", "propagate": False},
        "django.security": {"handlers": ["console", "logfile"], "level": "ERROR", "propagate": False},
        "factory": {"handlers": ["console", "logfile"], "level": "INFO"},
        "faker": {"handlers": ["console", "logfile"], "level": "INFO"},
        "luigi": {"level": "INFO"},
        "luigi-interface": {"level": "INFO"},
        "urllib3": {"handlers": ["console", "logfile"], "level": "INFO", "propagate": False},
        "common.models": {"handlers": ["console", "logfile"], "level": "INFO", "propagate": False},
        "common.signals": {"handlers": ["console", "logfile"], "level": "INFO", "propagate": False},
    },
    # Keep root at DEBUG and use the `level` on the handler to control logging output,
    # so that additional handlers can be used to get additional detail, e.g. `common.resources.LoggingResourceMixin`
    "root": {"handlers": ["console", "logfile"], "level": "DEBUG"},
}

DEFAULT_FILE_STORAGE = "binary_database_files.storage.DatabaseStorage"
# Serve files from the database, in case they are not present on the file
# system, for example if the container has been replaced.
DATABASE_FILES_URL_METHOD = "URL_METHOD_2"


SERIALIZATION_MODULES = {
    "verbose_json": "common.pipelines.serializers.verbose_json",
}

# Don't report missing HSTS preload, because we don't run SSL in local or CI environments.
# See: https://docs.djangoproject.com/en/3.0/ref/settings/#std:setting-SILENCED_SYSTEM_CHECKS
SILENCED_SYSTEM_CHECKS = [
    # SECURE_HSTS_PRELOAD: https://docs.djangoproject.com/en/3.0/ref/settings/#secure-hsts-preload
    "security.W021",
]

# Ensure we can delete large numbers or records through the admin, to facilitate reloading.
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000
