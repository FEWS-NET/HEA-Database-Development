from django.test import TestCase

from baseline.models import (
    BaselineLivelihoodActivity,
    BaselineWealthGroup,
    ButterProduction,
    Community,
    CommunityCropProduction,
    CommunityLivestock,
    CommunityWealthGroup,
    CopingStrategy,
    CropProduction,
    Event,
    ExpandabilityFactor,
    Fishing,
    FoodPurchase,
    Hazard,
    Hunting,
    LivelihoodActivity,
    LivelihoodProductCategory,
    LivelihoodStrategy,
    LivelihoodZone,
    LivelihoodZoneBaseline,
    LivestockSale,
    MarketPrice,
    MeatProduction,
    MilkProduction,
    OtherCashIncome,
    OtherPurchase,
    PaymentInKind,
    ReliefGiftOther,
    ResponseLivelihoodActivity,
    SeasonalActivity,
    SeasonalActivityOccurrence,
    SeasonalProductionPerformance,
    SourceOrganization,
    WealthGroup,
    WealthGroupCharacteristicValue,
    WildFoodGathering,
)

from .factories import (
    BaselineLivelihoodActivityFactory,
    BaselineWealthGroupFactory,
    ButterProductionFactory,
    CommunityCropProductionFactory,
    CommunityFactory,
    CommunityLivestockFactory,
    CommunityWealthGroupFactory,
    CopingStrategyFactory,
    CropProductionFactory,
    EventFactory,
    ExpandabilityFactorFactory,
    FishingFactory,
    FoodPurchaseFactory,
    HazardFactory,
    HuntingFactory,
    LivelihoodActivityFactory,
    LivelihoodProductCategoryFactory,
    LivelihoodStrategyFactory,
    LivelihoodZoneBaselineFactory,
    LivelihoodZoneFactory,
    LivestockSaleFactory,
    MarketPriceFactory,
    MeatProductionFactory,
    MilkProductionFactory,
    OtherCashIncomeFactory,
    OtherPurchaseFactory,
    PaymentInKindFactory,
    ReliefGiftOtherFactory,
    ResponseLivelihoodActivityFactory,
    SeasonalActivityFactory,
    SeasonalActivityOccurrenceFactory,
    SeasonalProductionPerformanceFactory,
    SourceOrganizationFactory,
    WealthGroupCharacteristicValueFactory,
    WealthGroupFactory,
    WildFoodGatheringFactory,
)


class FactoryTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.num_records = 5

    def test_sourceorganization_factory(self):
        for _ in range(self.num_records):
            SourceOrganizationFactory()
        self.assertEqual(SourceOrganization.objects.count(), self.num_records)

    def test_livelihoodzone_factory(self):
        for _ in range(self.num_records):
            LivelihoodZoneFactory()
        self.assertEqual(LivelihoodZone.objects.count(), self.num_records)

    def test_livelihoodzonebaseline_factory(self):
        for _ in range(self.num_records):
            LivelihoodZoneBaselineFactory()
        self.assertEqual(LivelihoodZoneBaseline.objects.count(), self.num_records)

    def test_livelihoodproductcategory_factory(self):
        for _ in range(self.num_records):
            LivelihoodProductCategoryFactory()
        self.assertEqual(LivelihoodProductCategory.objects.count(), self.num_records)

    def test_community_factory(self):
        for _ in range(self.num_records):
            CommunityFactory()
        self.assertEqual(Community.objects.count(), self.num_records)

    def test_wealthgroup_factory(self):
        for _ in range(self.num_records):
            WealthGroupFactory()
        self.assertEqual(WealthGroup.objects.count(), self.num_records)

    def test_baselinewealthgroup_factory(self):
        for _ in range(self.num_records):
            BaselineWealthGroupFactory()
        self.assertEqual(BaselineWealthGroup.objects.count(), self.num_records)

    def test_communitywealthgroup_factory(self):
        for _ in range(self.num_records):
            CommunityWealthGroupFactory()
        self.assertEqual(CommunityWealthGroup.objects.count(), self.num_records)

    def test_wealthcharacteristicvalue_factory(self):
        for _ in range(self.num_records):
            WealthGroupCharacteristicValueFactory()
        self.assertEqual(WealthGroupCharacteristicValue.objects.count(), self.num_records)

    def test_livelihoodstrategy_factory(self):
        for _ in range(self.num_records):
            LivelihoodStrategyFactory()
        self.assertEqual(LivelihoodStrategy.objects.count(), self.num_records)

    def test_livelihoodactivity_factory(self):
        for _ in range(self.num_records):
            LivelihoodActivityFactory()
        self.assertEqual(LivelihoodActivity.objects.count(), self.num_records)

    def test_baselinelivelihoodactivity_factory(self):
        for _ in range(self.num_records):
            BaselineLivelihoodActivityFactory()
        self.assertEqual(BaselineLivelihoodActivity.objects.count(), self.num_records)

    def test_responselivelihoodactivity_factory(self):
        for _ in range(self.num_records):
            ResponseLivelihoodActivityFactory()
        self.assertEqual(ResponseLivelihoodActivity.objects.count(), self.num_records)

    def test_milkproduction_factory(self):
        for _ in range(self.num_records):
            MilkProductionFactory()
        self.assertEqual(MilkProduction.objects.count(), self.num_records)

    def test_butterproduction_factory(self):
        for _ in range(self.num_records):
            ButterProductionFactory()
        self.assertEqual(ButterProduction.objects.count(), self.num_records)

    def test_meatproduction_factory(self):
        for _ in range(self.num_records):
            MeatProductionFactory()
        self.assertEqual(MeatProduction.objects.count(), self.num_records)

    def test_livestocksale_factory(self):
        for _ in range(self.num_records):
            LivestockSaleFactory()
        self.assertEqual(LivestockSale.objects.count(), self.num_records)

    def test_cropproduction_factory(self):
        for _ in range(self.num_records):
            CropProductionFactory()
        self.assertEqual(CropProduction.objects.count(), self.num_records)

    def test_foodpurchase_factory(self):
        for _ in range(self.num_records):
            FoodPurchaseFactory()
        self.assertEqual(FoodPurchase.objects.count(), self.num_records)

    def test_paymentinkind_factory(self):
        for _ in range(self.num_records):
            PaymentInKindFactory()
        self.assertEqual(PaymentInKind.objects.count(), self.num_records)

    def test_reliefgiftother_factory(self):
        for _ in range(self.num_records):
            ReliefGiftOtherFactory()
        self.assertEqual(ReliefGiftOther.objects.count(), self.num_records)

    def test_hunting_factory(self):
        for _ in range(self.num_records):
            HuntingFactory()
        self.assertEqual(Hunting.objects.count(), self.num_records)

    def test_fishing_factory(self):
        for _ in range(self.num_records):
            FishingFactory()
        self.assertEqual(Fishing.objects.count(), self.num_records)

    def test_wildfoodgathering_factory(self):
        for _ in range(self.num_records):
            WildFoodGatheringFactory()
        self.assertEqual(WildFoodGathering.objects.count(), self.num_records)

    def test_othercashincome_factory(self):
        for _ in range(self.num_records):
            OtherCashIncomeFactory()
        self.assertEqual(OtherCashIncome.objects.count(), self.num_records)

    def test_otherpurchase_factory(self):
        for _ in range(self.num_records):
            OtherPurchaseFactory()
        self.assertEqual(OtherPurchase.objects.count(), self.num_records)

    def test_seasonalactivity_factory(self):
        for _ in range(self.num_records):
            SeasonalActivityFactory()
        self.assertEqual(SeasonalActivity.objects.count(), self.num_records)

    def test_seasonalactivityoccurrence_factory(self):
        for _ in range(self.num_records):
            SeasonalActivityOccurrenceFactory()
        self.assertEqual(SeasonalActivityOccurrence.objects.count(), self.num_records)

    def test_communitycropproduction_factory(self):
        for _ in range(self.num_records):
            CommunityCropProductionFactory()
        self.assertEqual(CommunityCropProduction.objects.count(), self.num_records)

    def test_wealthgroupattribute_factory(self):
        for _ in range(self.num_records):
            CommunityLivestockFactory()
        self.assertEqual(CommunityLivestock.objects.count(), self.num_records)

    def test_marketprice_factory(self):
        for _ in range(self.num_records):
            MarketPriceFactory()
        self.assertEqual(MarketPrice.objects.count(), self.num_records)

    def test_seasonalproductionperformance_factory(self):
        for _ in range(self.num_records):
            SeasonalProductionPerformanceFactory()
        self.assertEqual(SeasonalProductionPerformance.objects.count(), self.num_records)

    def test_hazard_factory(self):
        for _ in range(self.num_records):
            HazardFactory()
        self.assertEqual(Hazard.objects.count(), self.num_records)

    def test_event_factory(self):
        for _ in range(self.num_records):
            EventFactory()
        self.assertEqual(Event.objects.count(), self.num_records)

    def test_expandabilityfactor_factory(self):
        for _ in range(self.num_records):
            ExpandabilityFactorFactory()
        self.assertEqual(ExpandabilityFactor.objects.count(), self.num_records)

    def test_copingstrategy_factory(self):
        for _ in range(self.num_records):
            CopingStrategyFactory()
        self.assertEqual(CopingStrategy.objects.count(), self.num_records)

    def test_all_factories(self):
        for _ in range(2):
            SourceOrganizationFactory()
            LivelihoodZoneFactory()
            LivelihoodZoneBaselineFactory()
            LivelihoodProductCategoryFactory()
            CommunityFactory()
            WealthGroupFactory()
            BaselineWealthGroupFactory()
            CommunityWealthGroupFactory()
            WealthGroupCharacteristicValueFactory()
            LivelihoodStrategyFactory()
            LivelihoodActivityFactory()
            BaselineLivelihoodActivityFactory()
            ResponseLivelihoodActivityFactory()
            MilkProductionFactory()
            ButterProductionFactory()
            MeatProductionFactory()
            LivestockSaleFactory()
            CropProductionFactory()
            FoodPurchaseFactory()
            PaymentInKindFactory()
            ReliefGiftOtherFactory()
            HuntingFactory()
            FishingFactory()
            WildFoodGatheringFactory()
            OtherCashIncomeFactory()
            OtherPurchaseFactory()
            SeasonalActivityFactory()
            SeasonalActivityOccurrenceFactory()
            CommunityCropProductionFactory()
            CommunityLivestockFactory()
            MarketPriceFactory()
            SeasonalProductionPerformanceFactory()
            HazardFactory()
            EventFactory()
            ExpandabilityFactorFactory()
            CopingStrategyFactory()
