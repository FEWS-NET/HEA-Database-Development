from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from baseline.views import ModelDocStringsAPI

router = routers.DefaultRouter()
# router.register(r"livelihoodcategories", LivelihoodCategoryViewSet)

urlpatterns = [
    ########## LOCALE INDEPENDENT PATHS go here. ##########
    path("api/", include(router.urls)),
    path("api/model_doc_strings/<str:model_name>", ModelDocStringsAPI.as_view()),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
] + i18n_patterns(
    ########## LOCALE DEPENDENT PATHS go here. ##########
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", admin.site.urls),
)
