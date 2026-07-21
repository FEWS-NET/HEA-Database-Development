from .base import *  # NOQA
from .base import INSTALLED_APPS, MIDDLEWARE

DEBUG = True

INSTALLED_APPS = INSTALLED_APPS + ("debug_toolbar",)

MIDDLEWARE = MIDDLEWARE + ("debug_toolbar.middleware.DebugToolbarMiddleware",)

INTERNAL_IPS = ("127.0.0.1", "::1")

DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
}
