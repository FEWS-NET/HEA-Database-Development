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

router = routers.DefaultRouter()

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
router.register(r"baselinelivelihoodactivities", BaselineLivelihoodActivityViewSet)
router.register(r"responselivelihoodactivities", ResponseLivelihoodActivityViewSet)
router.register(r"milkproduction", MilkProductionViewSet)
router.register(r"butterproduction", ButterProductionViewSet)
router.register(r"meatproduction", MeatProductionViewSet)
router.register(r"livestocksales", LivestockSalesViewSet)
router.register(r"cropproduction", CropProductionViewSet)
router.register(r"foodpurchases", FoodPurchaseViewSet)
router.register(r"paymentsinkind", PaymentInKindViewSet)
router.register(r"reliefgiftsandotherfood", ReliefGiftsOtherViewSet)
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
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
] + i18n_patterns(
    ########## LOCALE DEPENDENT PATHS go here. ##########
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", admin.site.urls),
)
