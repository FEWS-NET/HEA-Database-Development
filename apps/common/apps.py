from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "common"
    verbose_name = _("common")

    def ready(self):
        """Patch urllib3 connection pool size on startup"""
        from urllib3 import HTTPConnectionPool

        original_init = HTTPConnectionPool.__init__

        def patched_init(self, *args, **kwargs):
            # Force larger pool size
            kwargs["maxsize"] = kwargs.get("maxsize", 50)
            if kwargs["maxsize"] < 50:
                kwargs["maxsize"] = 50

            original_init(self, *args, **kwargs)

        # Apply patch
        HTTPConnectionPool.__init__ = patched_init

        print("urllib3 connection pool patched: maxsize=50")
