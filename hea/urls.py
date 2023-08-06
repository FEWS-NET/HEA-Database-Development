from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from common.viewsets import (
    ClassifiedProductViewSet,
    CountryViewSet,
    CurrencyViewSet,
    UnitOfMeasureViewSet,
)
from metadata.viewsets import (
    HazardCategoryViewSet,
    LivelihoodCategoryViewSet,
    SeasonalActivityTypeViewSet,
    SeasonViewSet,
    WealthCategoryViewSet,
    WealthCharacteristicViewSet,
)

router = routers.DefaultRouter()

router.register(r"country", CountryViewSet)
router.register(r"currency", CurrencyViewSet)
router.register(r"unitofmeasure", UnitOfMeasureViewSet)
router.register(r"classifiedproduct", ClassifiedProductViewSet)

router.register(r"livelihoodcategory", LivelihoodCategoryViewSet)
router.register(r"wealthcharacteristic", WealthCharacteristicViewSet)
router.register(r"wealthcategory", WealthCategoryViewSet)
router.register(r"seasonalactivitytype", SeasonalActivityTypeViewSet)
router.register(r"hazardcategory", HazardCategoryViewSet)
router.register(r"season", SeasonViewSet)


urlpatterns = [
    ########## LOCALE INDEPENDENT PATHS go here. ##########
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
] + i18n_patterns(
    ########## LOCALE DEPENDENT PATHS go here. ##########
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", admin.site.urls),
)
