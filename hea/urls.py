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
from baseline.viewsets import (
    AnnualProductionPerformanceViewSet,
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
    SeasonalActivityOccurrenceViewSet,
    SeasonalActivityViewSet,
    SourceOrganizationViewSet,
    WealthGroupCharacteristicValueViewSet,
    WealthGroupViewSet,
    WildFoodGatheringViewSet,
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
router.register(r"sourceorganizations", SourceOrganizationViewSet)
router.register(r"livelihoodzones", LivelihoodZoneViewSet)
router.register(r"livelihoodzonebaselines", LivelihoodZoneBaselineViewSet)
router.register(r"livelihoodproductcategories", LivelihoodProductCategoryViewSet)
router.register(r"communities", CommunityViewSet)
router.register(r"wealthgroups", WealthGroupViewSet)
router.register(r"baselinewealthgroups", BaselineWealthGroupViewSet)
router.register(r"communitywealthgroups", CommunityWealthGroupViewSet)
router.register(r"wealthcharacteristicvalues", WealthGroupCharacteristicValueViewSet)
router.register(r"livelihoodstrategies", LivelihoodStrategyViewSet)
router.register(r"livelihoodactivities", LivelihoodActivityViewSet)
router.register(r"milkproduction", MilkProductionViewSet)
router.register(r"butterproduction", ButterProductionViewSet)
router.register(r"meatproduction", MeatProductionViewSet)
router.register(r"livestocksales", LivestockSalesViewSet)
router.register(r"cropproduction", CropProductionViewSet)
router.register(r"foodpurchases", FoodPurchaseViewSet)
router.register(r"paymentsinkind", PaymentInKindViewSet)
router.register(r"relief,giftsandotherfood", ReliefGiftsOtherViewSet)
router.register(r"fishing", FishingViewSet)
router.register(r"wildfoodgathering", WildFoodGatheringViewSet)
router.register(r"othercashincome", OtherCashIncomeViewSet)
router.register(r"otherpurchases", OtherPurchasesViewSet)
router.register(r"seasonalactivities", SeasonalActivityViewSet)
router.register(r"seasonalactivityoccurrences", SeasonalActivityOccurrenceViewSet)
router.register(r"communitycropproductions", CommunityCropProductionViewSet)
router.register(r"wealthgroupattributes", CommunityLivestockViewSet)
router.register(r"marketprices", MarketPriceViewSet)
router.register(r"annualproductionperformance", AnnualProductionPerformanceViewSet)
router.register(r"hazards", HazardViewSet)
router.register(r"events", EventViewSet)
router.register(r"expandabilityfactor", ExpandabilityFactorViewSet)
router.register(r"copingstrategies", CopingStrategyViewSet)

urlpatterns = [
    ########## LOCALE INDEPENDENT PATHS go here. ##########
    # Database Files
    path("", include("binary_database_files.urls")),
    # API
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
] + i18n_patterns(
    ########## LOCALE DEPENDENT PATHS go here. ##########
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", admin.site.urls),
)
