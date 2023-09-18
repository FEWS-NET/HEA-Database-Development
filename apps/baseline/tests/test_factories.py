from django.test import TestCase

from .factories import (
    AnnualProductionPerformanceFactory,
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
    LivelihoodActivityFactory,
    LivelihoodProductCategoryFactory,
    LivelihoodStrategyFactory,
    LivelihoodZoneBaselineFactory,
    LivelihoodZoneFactory,
    LivestockSalesFactory,
    MarketPriceFactory,
    MeatProductionFactory,
    MilkProductionFactory,
    OtherCashIncomeFactory,
    OtherPurchasesFactory,
    PaymentInKindFactory,
    ReliefGiftsOtherFactory,
    ResponseLivelihoodActivityFactory,
    SeasonalActivityFactory,
    SeasonalActivityOccurrenceFactory,
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

    def test_livelihoodzone_factory(self):
        for _ in range(self.num_records):
            LivelihoodZoneFactory()

    def test_livelihoodzonebaseline_factory(self):
        for _ in range(self.num_records):
            LivelihoodZoneBaselineFactory()

    def test_livelihoodproductcategory_factory(self):
        for _ in range(self.num_records):
            LivelihoodProductCategoryFactory()

    def test_community_factory(self):
        for _ in range(self.num_records):
            CommunityFactory()

    def test_wealthgroup_factory(self):
        for _ in range(self.num_records):
            WealthGroupFactory()

    def test_baselinewealthgroup_factory(self):
        for _ in range(self.num_records):
            BaselineWealthGroupFactory()

    def test_communitywealthgroup_factory(self):
        for _ in range(self.num_records):
            CommunityWealthGroupFactory()

    def test_wealthcharacteristicvalue_factory(self):
        for _ in range(self.num_records):
            WealthGroupCharacteristicValueFactory()

    def test_livelihoodstrategy_factory(self):
        for _ in range(self.num_records):
            LivelihoodStrategyFactory()

    def test_livelihoodactivity_factory(self):
        for _ in range(self.num_records):
            LivelihoodActivityFactory()

    def test_baselinelivelihoodactivity_factory(self):
        for _ in range(self.num_records):
            BaselineLivelihoodActivityFactory()

    def test_responselivelihoodactivity_factory(self):
        for _ in range(self.num_records):
            ResponseLivelihoodActivityFactory()

    def test_milkproduction_factory(self):
        for _ in range(self.num_records):
            MilkProductionFactory()

    def test_butterproduction_factory(self):
        for _ in range(self.num_records):
            ButterProductionFactory()

    def test_meatproduction_factory(self):
        for _ in range(self.num_records):
            MeatProductionFactory()

    def test_livestocksales_factory(self):
        for _ in range(self.num_records):
            LivestockSalesFactory()

    def test_cropproduction_factory(self):
        for _ in range(self.num_records):
            CropProductionFactory()

    def test_foodpurchase_factory(self):
        for _ in range(self.num_records):
            FoodPurchaseFactory()

    def test_paymentinkind_factory(self):
        for _ in range(self.num_records):
            PaymentInKindFactory()

    def test_reliefgiftsandotherfood_factory(self):
        for _ in range(self.num_records):
            ReliefGiftsOtherFactory()

    def test_fishing_factory(self):
        for _ in range(self.num_records):
            FishingFactory()

    def test_wildfoodgathering_factory(self):
        for _ in range(self.num_records):
            WildFoodGatheringFactory()

    def test_othercashincome_factory(self):
        for _ in range(self.num_records):
            OtherCashIncomeFactory()

    def test_otherpurchases_factory(self):
        for _ in range(self.num_records):
            OtherPurchasesFactory()

    def test_seasonalactivity_factory(self):
        for _ in range(self.num_records):
            SeasonalActivityFactory()

    def test_seasonalactivityoccurrence_factory(self):
        for _ in range(self.num_records):
            SeasonalActivityOccurrenceFactory()

    def test_communitycropproduction_factory(self):
        for _ in range(self.num_records):
            CommunityCropProductionFactory()

    def test_wealthgroupattribute_factory(self):
        for _ in range(self.num_records):
            CommunityLivestockFactory()

    def test_marketprice_factory(self):
        for _ in range(self.num_records):
            MarketPriceFactory()

    def test_annualproductionperformance_factory(self):
        for _ in range(self.num_records):
            AnnualProductionPerformanceFactory()

    def test_hazard_factory(self):
        for _ in range(self.num_records):
            HazardFactory()

    def test_event_factory(self):
        for _ in range(self.num_records):
            EventFactory()

    def test_expandabilityfactor_factory(self):
        for _ in range(self.num_records):
            ExpandabilityFactorFactory()

    def test_copingstrategy_factory(self):
        for _ in range(self.num_records):
            CopingStrategyFactory()

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
            LivestockSalesFactory()
            CropProductionFactory()
            FoodPurchaseFactory()
            PaymentInKindFactory()
            ReliefGiftsOtherFactory()
            FishingFactory()
            WildFoodGatheringFactory()
            OtherCashIncomeFactory()
            OtherPurchasesFactory()
            SeasonalActivityFactory()
            SeasonalActivityOccurrenceFactory()
            CommunityCropProductionFactory()
            CommunityLivestockFactory()
            MarketPriceFactory()
            AnnualProductionPerformanceFactory()
            HazardFactory()
            EventFactory()
            ExpandabilityFactorFactory()
            CopingStrategyFactory()
