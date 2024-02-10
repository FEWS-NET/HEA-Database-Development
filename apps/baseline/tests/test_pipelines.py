from unittest import skip

import pandas as pd
from django.test import TestCase
from kiluigi.utils import submit_task

from baseline.pipelines.ingestion import ImportBaseline, NormalizeData
from baseline.tests.factories import SourceOrganizationFactory
from common.models import UnitOfMeasure
from common.tests.factories import (
    ClassifiedProductFactory,
    CountryFactory,
    UnitOfMeasureFactory,
)
from common.utils import conditional_logging
from metadata.tests.factories import (
    LivelihoodCategoryFactory,
    WealthCharacteristicFactory,
    WealthGroupCategoryFactory,
)


class IngestionPipelineTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        CountryFactory(iso3166a2="MW", iso3166a3="MWI", iso3166n3=454, iso_en_ro_name="Malawi")
        ClassifiedProductFactory(cpc="L02151", description="Chickens", aliases=["chicken", "hen", "hens"]),
        ClassifiedProductFactory(
            cpc="L02111HA", description_en="Cattle, oxen, unspecified", common_name_en="Oxen", aliases=["ox"]
        )
        UnitOfMeasureFactory(abbreviation="acre", unit_type=UnitOfMeasure.AREA, aliases=["acres"], conversion=None)
        LivelihoodCategoryFactory(
            code="agropastoral",
            name_en="Agropastoral",
        )
        WealthGroupCategoryFactory(code="VP", name_en="Very Poor", aliases=["vp", "tp"])
        WealthGroupCategoryFactory(code="P", name_en="Poor", aliases=["p"])
        WealthGroupCategoryFactory(code="M", name_en="Medium", aliases=["m"])
        WealthGroupCategoryFactory(code="B/O", name_en="Better Off", aliases=["b/o", "r", "a"])
        WealthCharacteristicFactory(
            code="percentage of households", name_en="Wealth breakdown (% of households)", aliases=["wealth breakdown"]
        )
        WealthCharacteristicFactory(
            code="household size", name_en="Average Household Size", aliases=["HH size", "HH size (taille)"]
        )
        WealthCharacteristicFactory(
            code="area owned",
            name_en="Land area owned",
            has_unit_of_measure=True,
            aliases=["area owned (<unit_of_measure>)", "land area owned (<unit_of_measure>)"],
        )
        WealthCharacteristicFactory(
            code="area cultivated",
            name_en="Land area cultivated",
            has_unit_of_measure=True,
            aliases=["area cultivated (<unit_of_measure>)", "land area cultivated (<unit_of_measure>)"],
        )
        WealthCharacteristicFactory(
            code="area cultivated - rainfed",
            name_en="Land area cultivated - rainfed crops",
            has_unit_of_measure=True,
            aliases=[
                "area cultivated - rainfed (<unit_of_measure>)",
                "land area cultivated - rainfed crops (<unit_of_measure>)",
            ],
        )
        WealthCharacteristicFactory(
            code="area cultivated - irrigated",
            name_en="Land area cultivated - irrigated crops",
            has_unit_of_measure=True,
            aliases=[
                "area cultivated - irrigated (<unit_of_measure>)",
                "land area cultivated - irrigated crops (<unit_of_measure>)",
            ],
        )
        WealthCharacteristicFactory(
            code="adult females",
            name_en="adult females",
            variable_type="float",
            has_product=True,
        )
        WealthCharacteristicFactory(
            code="bicycles",
            name_en="Bicycles",
            aliases=["Bicycle"],
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="fruit tree",
            name_en="Fruit Tree",
            aliases=["fruit trees", "other (fruit tree)"],
        )
        WealthCharacteristicFactory(
            code="grocery / shop / kiosk",
            name_en="Grocery, Shop or Kiosk",
            aliases=["Kiosk", "Grocery/ kiosk", "Other (grocery/shop)"],
        )
        WealthCharacteristicFactory(
            code="land rented",
            name_en="Land rented in/out (+/-)",
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="main cash crops",
            name_en="Main cash crops",
            variable_type="str",
        )
        WealthCharacteristicFactory(
            code="main food crops",
            name_en="Main food crops",
            variable_type="str",
        )
        WealthCharacteristicFactory(
            code="main source of cash income 1st",
            name_en="Main source of cash income 1st",
            variable_type="str",
        )
        WealthCharacteristicFactory(
            code="main source of cash income 2nd",
            name_en="Main source of cash income 2nd",
            variable_type="str",
        )
        WealthCharacteristicFactory(
            code="main source of cash income 3rd",
            name_en="Main source of cash income 3rd",
            variable_type="str",
        )
        WealthCharacteristicFactory(
            code="mobile phones",
            name_en="Mobile phones",
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="months of consumption from crops",
            name_en="Months of consumption from crops in RY",
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="number at start of year",
            name_en="no. at start of reference year",
            variable_type="float",
            has_product=True,
            aliases=["<product>: total owned at start of year"],
        )
        WealthCharacteristicFactory(
            code="number at end of year",
            name_en="no. at end of reference year",
            variable_type="float",
            has_product=True,
        )
        WealthCharacteristicFactory(
            code="number born during year",
            name_en="no. born during year",
            aliases=["no.born during year"],
            variable_type="float",
            has_product=True,
        )
        WealthCharacteristicFactory(
            code="number bought",
            name_en="no. bought",
            variable_type="float",
            has_product=True,
        )
        WealthCharacteristicFactory(
            code="number died",
            name_en="no. died",
            variable_type="float",
            has_product=True,
        )
        WealthCharacteristicFactory(
            code="number of children at school",
            name_en="Number of children at school (WGs only)",
            aliases=["number of children at school (wgs only)"],
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="number of men in interview",
            name_en="No. of men in interview (participants)",
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="number of people actually working",
            name_en="No. of people actually working",
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="number of people capable of working",
            name_en="No. of people capable of working",
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="number of wives per husband",
            name_en="Number of wives per husband",
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="number of women in interview",
            name_en="No. of women in interview (participants)",
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="number owned",
            name_en="number owned",
            variable_type="float",
            has_product=True,
            aliases=["<product> number owned", "cattle: <product> number owned"],
        )
        WealthCharacteristicFactory(
            code="number slaughtered",
            name_en="no. slaughtered",
            variable_type="float",
            has_product=True,
        )
        WealthCharacteristicFactory(
            code="number sold",
            name_en="no. sold",
            variable_type="float",
            has_product=True,
        )
        WealthCharacteristicFactory(
            code="other",
            name_en="Other (unspecified)",
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="relief and assistance recipients",
            name_en="Relief and assistance recipients (yes/no)",
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="schooling levels commonly attained",
            name_en="Schooling levels commonly attained",
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="total owned at start of year",
            name_en="total owned at start of year",
            variable_type="float",
            has_product=True,
        )
        SourceOrganizationFactory(name="FEWS NET")

    def test_import_baseline(self):
        # Capture logging and direct writes to stdout (because loaddata writes
        # to stdout directly), so that unit test output is still clean.
        with conditional_logging(capacity=2000):
            task = ImportBaseline(
                bss_path="apps/baseline/tests/bss.xlsx", metadata_path="apps/baseline/tests/metadata.xlsx"
            )
            submit_task(task, force=True, cascade=True, local_scheduler=True)

            result = task.output().open().read()
            self.assertRegex(result, r"Installed (\d+) object\(s\) from 1 fixture\(s\)")

    # Skip this test because it currently doesn't work for all strings. For example, 'Pig sales - local: no. sold'
    # needs to match L02140HA: Swine / pigs, local quality, but we haven't set up "Pig sales - local" as an alias for
    # L02140HA. There are other similar examples where the metadata is not set up properly and it isn't clear that this
    # approach will ultimately be successful.  For example, should we match the string "Gifts: type" even though this
    # indicates a blank entry in the Livelihood Strategy list - and actual entry would have corrected "type" with the
    # actual gift.
    @skip("Currently not working")
    def test_livelihood_strategy_map(self):
        test_string_dict = {
            "MilkProduction": ["season 1: lactation period (days)", "season 1: no. milking animals"],
            "ButterProduction": ["ghee/butter production (kg)", "milk+ghee/butter kcals (%) - 2nd season"],
            "MeatProduction": ["Cow meat: no. animals slaughtered"],
            "LivestockSale": [
                "Pig sales - local: no. sold",
                "Other (Eggs): quantity",
                "Other Eggs: quantity",
                "Other (Eggs) quantity",
                "Other Eggs quantity",
                "Other: quantity",
                "Eggs: quantity",
                "Eggs quantity",
                "Other (Eggs): quantity",
                "Other: quantity",
                "Vente de moutons - locale: nb  venduss",
                "Vente de poules: nb  venduses",
            ],
            "CropProduction": [
                "Green cons - rainfed: no of months",
                "Green cons - irrigated: no of months",
                "Green maize sold: quantity",
                "Maize rainfed: kg produced",
                "Groundnuts (dry): no. local meas",
                "Other crop: Ground beans",
                "Other crop: type",
                "Cotton: kg sold",
                "Other cash crop: type",
            ],
            "FoodPurchase": [
                "Maize grain: name of meas.",
                "Cassava dried: name of meas.",
                "Sugar purchase: kg",
                "Meat purchase: quantity (kg)",
                "Dried fish purchase: quantity (kg)",
            ],
            "ReliefGiftOther": [
                "School feeding (cooked): no. children",
                "Relief - grain: quantity (kg)",
                "Other food: school feeding take-home ration",
                "Other food: type",
                "School feeding (cooked): no. children",
                "Relief - pulses: quantity (kg)",
                "Gifts: type",
                "Safety Nets: no. people per HH",
            ],
            "OtherCashIncome": [
                "Construction cash income (brick making, fencing )",
                "Self-employment (firewood sales, pett trade/ trade)",
                "Remittances: no. times per year",
            ],
            # Some rows in column A are duplicated for both the PaymentInKind
            # and OtherCashIncome strategy types, and so in those cases
            # get_activity_attributes doesn't return a strategy_type, and
            # instead we rely on the strategy_type detected from the section
            # header in column A, e.g. "PAYMENT IN KIND"
            None: [
                "Labour: pre-harvest",
                "Labour: type",
            ],
        }

        for strategy_type, test_strings in test_string_dict.items():
            for test_string in test_strings:
                with self.subTest(test_string=test_string):
                    attributes = NormalizeData.get_activity_attributes(test_string)
                    self.assertIsInstance(attributes, dict, "Test string was not matched")
                    self.assertFalse(all([pd.isna(attribute) for attribute in attributes]))
                    self.assertEqual(
                        attributes["strategy_type"],
                        strategy_type,
                        f'Incorrect strategy type {attributes["strategy_type"]} from pattern {attributes["pattern"]}',
                    )
