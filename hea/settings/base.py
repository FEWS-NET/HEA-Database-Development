import os
import socket
import sys
from os.path import abspath, basename, dirname, join, normpath

import environ
import requests

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
        "ENGINE": "django.db.backends.postgresql",  # @TODO: Requires GDAL "django.contrib.gis.db.backends.postgis",
        "NAME": env("PGDATABASE"),
        "USER": env("PGUSER"),
        "PASSWORD": env("PGPASSWORD"),
        "HOST": env("PGHOST"),
        "PORT": env.int("PGPORT", 5432),
        "OPTIONS": {"sslmode": "prefer", "application_name": SITE_NAME.lower()},
        "SCHEMA": f"{SITE_NAME.lower()}_owner",
        "TEST": {
            "TEMPLATE": f"template_{SITE_NAME.lower()}",
            "SERIALIZE": False,
        },
    }
}
EXTERNAL_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
]
PROJECT_APPS = ["common", "metadata", "spatial", "baseline"]
INSTALLED_APPS = EXTERNAL_APPS + PROJECT_APPS

MIDDLEWARE = [
    "django.middleware.gzip.GZipMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    # "common.middleware.RequestLoggingMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "hea.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"


STATIC_HOST = env.str("DJANGO_STATIC_HOST", "")
STATIC_URL = STATIC_HOST + "/static/"
STATIC_ROOT = normpath(join(SITE_ROOT, "assets"))
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
