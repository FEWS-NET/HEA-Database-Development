from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import path

urlpatterns = i18n_patterns(
    ########## LOCALE DEPENDENT PATHS go here. ##########
    path("admin/", admin.site.urls),
)
