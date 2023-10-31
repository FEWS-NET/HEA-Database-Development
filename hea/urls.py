from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from baseline.viewsets import (
    AnnualProductionPerformanceViewSet,
    BaselineLivelihoodActivityViewSet,
    BaselineWealthGroupViewSet,
    ButterProductionViewSet,
    CommunityCropProductionViewSet,
    CommunityLivestockViewSet,
    CommunityViewSet,
    CommunityWealthGroupViewSet,
    CopingStrategyViewSet,
    CropProductionViewSet,
    EventViewSet,
    ExpandabilityFactorViewSet,
    FishingViewSet,
    FoodPurchaseViewSet,
    HazardViewSet,
    LivelihoodActivityViewSet,
    LivelihoodProductCategoryViewSet,
    LivelihoodStrategyViewSet,
    LivelihoodZoneBaselineViewSet,
    LivelihoodZoneViewSet,
    LivestockSalesViewSet,
    MarketPriceViewSet,
    MeatProductionViewSet,
    MilkProductionViewSet,
    OtherCashIncomeViewSet,
    OtherPurchasesViewSet,
    PaymentInKindViewSet,
    ReliefGiftsOtherViewSet,
    ResponseLivelihoodActivityViewSet,
    SeasonalActivityOccurrenceViewSet,
    SeasonalActivityViewSet,
    SourceOrganizationViewSet,
    WealthGroupCharacteristicValueViewSet,
    WealthGroupViewSet,
    WildFoodGatheringViewSet,
)
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

# Common
router.register(r"country", CountryViewSet)
router.register(r"currency", CurrencyViewSet)
router.register(r"unitofmeasure", UnitOfMeasureViewSet)
router.register(r"classifiedproduct", ClassifiedProductViewSet)

# Metadata
router.register(r"livelihoodcategory", LivelihoodCategoryViewSet)
router.register(r"wealthcharacteristic", WealthCharacteristicViewSet)
router.register(r"wealthcategory", WealthCategoryViewSet)
router.register(r"seasonalactivitytype", SeasonalActivityTypeViewSet)
router.register(r"hazardcategory", HazardCategoryViewSet)
router.register(r"season", SeasonViewSet)

# Baseline
router.register(r"sourceorganization", SourceOrganizationViewSet)
router.register(r"livelihoodzone", LivelihoodZoneViewSet)
router.register(r"livelihoodzonebaseline", LivelihoodZoneBaselineViewSet)
router.register(r"livelihoodproductcategory", LivelihoodProductCategoryViewSet)
router.register(r"community", CommunityViewSet)
router.register(r"wealthgroup", WealthGroupViewSet)
router.register(r"baselinewealthgroup", BaselineWealthGroupViewSet)
router.register(r"communitywealthgroup", CommunityWealthGroupViewSet)
router.register(r"wealthgroupcharacteristicvalue", WealthGroupCharacteristicValueViewSet)
router.register(r"livelihoodstrategy", LivelihoodStrategyViewSet)
router.register(r"livelihoodactivity", LivelihoodActivityViewSet)
router.register(r"baselinelivelihoodactivity", BaselineLivelihoodActivityViewSet)
router.register(r"responselivelihoodactivity", ResponseLivelihoodActivityViewSet)
router.register(r"milkproduction", MilkProductionViewSet)
router.register(r"butterproduction", ButterProductionViewSet)
router.register(r"meatproduction", MeatProductionViewSet)
router.register(r"livestocksale", LivestockSalesViewSet)
router.register(r"cropproduction", CropProductionViewSet)
router.register(r"foodpurchase", FoodPurchaseViewSet)
router.register(r"paymentsinkind", PaymentInKindViewSet)
router.register(r"reliefgiftsandotherfood", ReliefGiftsOtherViewSet)
router.register(r"fishing", FishingViewSet)
router.register(r"wildfoodgathering", WildFoodGatheringViewSet)
router.register(r"othercashincome", OtherCashIncomeViewSet)
router.register(r"otherpurchase", OtherPurchasesViewSet)
router.register(r"seasonalactivity", SeasonalActivityViewSet)
router.register(r"seasonalactivityoccurrence", SeasonalActivityOccurrenceViewSet)
router.register(r"communitycropproduction", CommunityCropProductionViewSet)
router.register(r"communitylivestock", CommunityLivestockViewSet)
router.register(r"marketprice", MarketPriceViewSet)
router.register(r"annualproductionperformance", AnnualProductionPerformanceViewSet)
router.register(r"hazard", HazardViewSet)
router.register(r"event", EventViewSet)
router.register(r"expandabilityfactor", ExpandabilityFactorViewSet)
router.register(r"copingstrategy", CopingStrategyViewSet)

urlpatterns = [
    ########## LOCALE INDEPENDENT PATHS go here. ##########
    # Database Files
    path("", include("binary_database_files.urls")),
    # API
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
] + i18n_patterns(
    ########## LOCALE DEPENDENT PATHS go here. ##########
    path("api/", include(router.urls)),
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", admin.site.urls),
)
