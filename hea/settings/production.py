from urllib.parse import urlparse

import sentry_sdk

from .base import *  # NOQA
from .base import env

# In production we run behind a load balancer that acts as an https end point
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_REDIRECT_EXEMPT = ["^heartbeat/$"]
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True


# Sentry Configuration
# See: https://docs.sentry.io/platforms/python/guides/django/
def before_send(event, hint):
    """Don't log django.DisallowedHost errors in Sentry."""
    if "log_record" in hint:
        if hint["log_record"].name == "django.security.DisallowedHost":
            return None
    return event


def filter_transactions(event, hint):
    url_string = event["request"]["url"]
    parsed_url = urlparse(url_string)

    if parsed_url.path == "/heartbeat":
        return None

    return event


if env.str("SENTRY_DSN", ""):
    sentry_sdk.init(
        dsn=env.str("SENTRY_DSN", ""),
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
        send_default_pii=True,
        before_send=before_send,
        before_send_transaction=filter_transactions,
    )
