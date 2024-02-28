"""Settings and globals for the CI environment"""

import warnings

from .base import *  # NOQA
from .base import CACHES, LOGGING

# Raise errors in tests when we get naive datetimes
warnings.filterwarnings("error", r"DateTimeField .* received a naive datetime")


########## STATIC FILE CONFIGURATION
# Use normal StaticFileStorage so we don't have to run ./manage.py collectstatic first
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
########## End STATIC FILE CONFIGURATION

########## CACHE CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#caches
# Override the cache backend to avoid spurious test errors caused by database
# rollbacks that incorrectly leave data in the cache
for cache in CACHES:
    CACHES[cache] = {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}
########## END CACHE CONFIGURATION

########## LOGGING CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#logging
# Don't use JSON logging or stdout in test runs
LOGGING["handlers"]["console"]["formatter"] = "standard"
LOGGING["handlers"]["console"]["level"] = "WARNING"
########## END LOGGING CONFIGURATION
