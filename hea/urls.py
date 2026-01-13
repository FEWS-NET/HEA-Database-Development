import os

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.decorators.cache import cache_page
from django.views.decorators.http import etag
from django.views.i18n import JavaScriptCatalog
from rest_framework import routers

from baseline.viewsets import (
    BaselineLivelihoodActivityViewSet,
    BaselineWealthGroupCharacteristicValueViewSet,
    BaselineWealthGroupViewSet,
    ButterProductionViewSet,
    CommunityCropProductionViewSet,
    CommunityLivestockViewSet,
    CommunityViewSet,
    CommunityWealthGroupCharacteristicValueViewSet,
    CommunityWealthGroupViewSet,
    CopingStrategyViewSet,
    CropProductionViewSet,
    EventViewSet,
    ExpandabilityFactorViewSet,
    FishingViewSet,
    FoodPurchaseViewSet,
    HazardViewSet,
    HuntingViewSet,
    LivelihoodActivitySummaryViewSet,
    LivelihoodActivityViewSet,
    LivelihoodProductCategoryViewSet,
    LivelihoodStrategyViewSet,
    LivelihoodZoneBaselineFacetedSearchView,
    LivelihoodZoneBaselineViewSet,
    LivelihoodZoneViewSet,
    LivestockSaleViewSet,
    MarketPriceViewSet,
    MeatProductionViewSet,
    MilkProductionViewSet,
    OtherCashIncomeViewSet,
    OtherPurchaseViewSet,
    PaymentInKindViewSet,
    ReliefGiftOtherViewSet,
    ResponseLivelihoodActivityViewSet,
    SeasonalActivityOccurrenceViewSet,
    SeasonalActivityViewSet,
    SeasonalProductionPerformanceViewSet,
    SourceOrganizationViewSet,
    WealthGroupCharacteristicValueViewSet,
    WealthGroupViewSet,
    WildFoodGatheringViewSet,
)
from common.views import AssetDownloadView, BaselineExplorerProxyView, DagsterProxyView
from common.viewsets import (
    ClassifiedProductViewSet,
    CountryViewSet,
    CurrencyViewSet,
    UnitOfMeasureViewSet,
    UserProfileViewSet,
    UserViewSet,
)
from metadata.viewsets import (
    HazardCategoryViewSet,
    LivelihoodCategoryViewSet,
    SeasonalActivityTypeViewSet,
    SeasonViewSet,
    WealthCharacteristicViewSet,
    WealthGroupCategoryViewSet,
)

router = routers.DefaultRouter()

# Common
router.register(r"country", CountryViewSet)
router.register(r"currency", CurrencyViewSet)
router.register(r"unitofmeasure", UnitOfMeasureViewSet)
router.register(r"classifiedproduct", ClassifiedProductViewSet)
router.register(r"user", UserViewSet)
router.register(r"userprofile", UserProfileViewSet)

# Metadata
router.register(r"livelihoodcategory", LivelihoodCategoryViewSet)
router.register(r"wealthcharacteristic", WealthCharacteristicViewSet)
router.register(r"wealthgroupcategory", WealthGroupCategoryViewSet)
router.register(r"seasonalactivitytype", SeasonalActivityTypeViewSet)
router.register(r"hazardcategory", HazardCategoryViewSet)
router.register(r"season", SeasonViewSet)

# Baseline
router.register(r"sourceorganization", SourceOrganizationViewSet)
router.register(r"livelihoodzone", LivelihoodZoneViewSet)
router.register(r"livelihoodzonebaseline", LivelihoodZoneBaselineViewSet)
router.register(r"livelihoodactivitysummary", LivelihoodActivitySummaryViewSet, "livelihoodactivitysummary")
router.register(r"livelihoodproductcategory", LivelihoodProductCategoryViewSet)
router.register(r"community", CommunityViewSet)
router.register(r"wealthgroup", WealthGroupViewSet)
router.register(r"baselinewealthgroup", BaselineWealthGroupViewSet)
router.register(r"communitywealthgroup", CommunityWealthGroupViewSet)
router.register(r"wealthgroupcharacteristicvalue", WealthGroupCharacteristicValueViewSet)
router.register(
    r"baselinewealthgroupcharacteristicvalue",
    BaselineWealthGroupCharacteristicValueViewSet,
    "baselinewealthgroupcharacteristicvalue",
)
router.register(
    r"communitywealthgroupcharacteristicvalue",
    CommunityWealthGroupCharacteristicValueViewSet,
    "communitywealthgroupcharacteristicvalue",
)
router.register(r"livelihoodstrategy", LivelihoodStrategyViewSet)
router.register(r"livelihoodactivity", LivelihoodActivityViewSet)
router.register(r"baselinelivelihoodactivity", BaselineLivelihoodActivityViewSet)
router.register(r"responselivelihoodactivity", ResponseLivelihoodActivityViewSet)
router.register(r"milkproduction", MilkProductionViewSet)
router.register(r"butterproduction", ButterProductionViewSet)
router.register(r"meatproduction", MeatProductionViewSet)
router.register(r"livestocksale", LivestockSaleViewSet)
router.register(r"cropproduction", CropProductionViewSet)
router.register(r"foodpurchase", FoodPurchaseViewSet)
router.register(r"paymentinkind", PaymentInKindViewSet)
router.register(r"relief", ReliefGiftOtherViewSet)
router.register(r"fishing", FishingViewSet)
router.register(r"hunting", HuntingViewSet)
router.register(r"wildfoodgathering", WildFoodGatheringViewSet)
router.register(r"othercashincome", OtherCashIncomeViewSet)
router.register(r"otherpurchase", OtherPurchaseViewSet)
router.register(r"seasonalactivity", SeasonalActivityViewSet)
router.register(r"seasonalactivityoccurrence", SeasonalActivityOccurrenceViewSet)
router.register(r"communitycropproduction", CommunityCropProductionViewSet)
router.register(r"communitylivestock", CommunityLivestockViewSet)
router.register(r"marketprice", MarketPriceViewSet)
router.register(r"seasonalproductionperformance", SeasonalProductionPerformanceViewSet)
router.register(r"hazard", HazardViewSet)
router.register(r"event", EventViewSet)
router.register(r"expandabilityfactor", ExpandabilityFactorViewSet)
router.register(r"copingstrategy", CopingStrategyViewSet)

urlpatterns = [
    ########## LOCALE INDEPENDENT PATHS go here. ##########
    # Database Files
    path("", include("binary_database_files.urls")),
    # API
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    # Provides il8n/set_language to change Django language:
    path("i18n/", include("django.conf.urls.i18n")),
]
urlpatterns += [
    path(
        "api/livelihoodzonebaselinefacetedsearch/",
        LivelihoodZoneBaselineFacetedSearchView.as_view(),
        name="livelihood-zone-baseline-faceted-search",
    ),
    re_path(os.environ.get("DAGSTER_WEBSERVER_PREFIX", "pipelines") + r"/(?P<path>.*)", DagsterProxyView.as_view()),
    path("assetdownload/<str:asset_name>/", AssetDownloadView.as_view(), name="asset_download"),
    path(
        "assetdownload/<str:asset_name>/<str:partition_name>/",
        AssetDownloadView.as_view(),
        name="asset_download_partitioned",
    ),
    # Baseline Explorer React GUI using Django rev proxy to serve a cloudfront distro
    path("baseline-explorer/<path:path>", BaselineExplorerProxyView.as_view(), name="baseline_explorer"),
    # The URL pattern below does not capture any path parameter from the URL. But django-revproxy views
    # require a path argument. We manually pass a default: {"path": ""}.
    path("baseline-explorer/", BaselineExplorerProxyView.as_view(), {"path": ""}, name="baseline_explorer"),
]


# Django's solution for translating JavaScript apps
# Provides gettext translation functionality for Javascript clients (and ngettext, pgettext, iterpolate, etc.)
# See: https://docs.djangoproject.com/en/4.2/topics/i18n/translation/#using-the-javascript-translation-catalog
javascript_catalog_view = JavaScriptCatalog.as_view()
if not settings.DEBUG:
    # In production, wrap the catalog view in conditional get and cache_page decorators
    # cache_page needs to be the outer decorator because it sets the cache-control header,
    # which is required on the 304 response from the etag decorator.
    javascript_catalog_view = cache_page(
        60 * 60 * 24 * 30, cache="default", key_prefix=f"jsi18n-{settings.APP_VERSION}"
    )(etag(lambda request, *args, **kwargs: settings.APP_VERSION)(javascript_catalog_view))

urlpatterns += i18n_patterns(
    ########## LOCALE DEPENDENT PATHS go here. ##########
    path(
        "jsi18n/",
        javascript_catalog_view,
        name="javascript-catalog",
    ),
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", admin.site.urls),
)
