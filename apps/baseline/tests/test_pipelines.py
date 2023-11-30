from django.test import TestCase
from kiluigi.utils import submit_task

from baseline.pipelines.ingestion import ImportBaseline
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
        ClassifiedProductFactory(cpcv2="L02151", description="Chickens", aliases=["chicken", "hen", "hens"]),
        ClassifiedProductFactory(
            cpcv2="L02111AP", description="Cattle, oxen, unspecified", common_name="Oxen", aliases=["ox"]
        )
        UnitOfMeasureFactory(abbreviation="acre", unit_type=UnitOfMeasure.AREA, aliases=["acres"], conversion=None)
        LivelihoodCategoryFactory(
            code="agropastoral",
            name="Agropastoral",
        )
        WealthGroupCategoryFactory(code="VP", name="Very Poor", aliases=["vp", "tp"])
        WealthGroupCategoryFactory(code="P", name="Poor", aliases=["p"])
        WealthGroupCategoryFactory(code="M", name="Medium", aliases=["m"])
        WealthGroupCategoryFactory(code="B/O", name="Better Off", aliases=["b/o", "r", "a"])
        WealthCharacteristicFactory(
            code="percentage of households", name="Wealth breakdown (% of households)", aliases=["wealth breakdown"]
        )
        WealthCharacteristicFactory(
            code="household size", name="Average Household Size", aliases=["HH size", "HH size (taille)"]
        )
        WealthCharacteristicFactory(
            code="area owned",
            name="Land area owned",
            has_unit_of_measure=True,
            aliases=["area owned (<unit_of_measure>)", "land area owned (<unit_of_measure>)"],
        )
        WealthCharacteristicFactory(
            code="area cultivated",
            name="Land area cultivated",
            has_unit_of_measure=True,
            aliases=["area cultivated (<unit_of_measure>)", "land area cultivated (<unit_of_measure>)"],
        )
        WealthCharacteristicFactory(
            code="area cultivated - rainfed",
            name="Land area cultivated - rainfed crops",
            has_unit_of_measure=True,
            aliases=[
                "area cultivated - rainfed (<unit_of_measure>)",
                "land area cultivated - rainfed crops (<unit_of_measure>)",
            ],
        )
        WealthCharacteristicFactory(
            code="area cultivated - irrigated",
            name="Land area cultivated - irrigated crops",
            has_unit_of_measure=True,
            aliases=[
                "area cultivated - irrigated (<unit_of_measure>)",
                "land area cultivated - irrigated crops (<unit_of_measure>)",
            ],
        )
        WealthCharacteristicFactory(
            code="adult females",
            name="adult females",
            variable_type="float",
            has_product=True,
        )
        WealthCharacteristicFactory(
            code="bicycles",
            name="Bicycles",
            aliases=["Bicycle"],
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="fruit tree",
            name="Fruit Tree",
            aliases=["fruit trees", "other (fruit tree)"],
        )
        WealthCharacteristicFactory(
            code="grocery / shop / kiosk",
            name="Grocery, Shop or Kiosk",
            aliases=["Kiosk", "Grocery/ kiosk", "Other (grocery/shop)"],
        )
        WealthCharacteristicFactory(
            code="land rented",
            name="Land rented in/out (+/-)",
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="main cash crops",
            name="Main cash crops",
            variable_type="str",
        )
        WealthCharacteristicFactory(
            code="main food crops",
            name="Main food crops",
            variable_type="str",
        )
        WealthCharacteristicFactory(
            code="main source of cash income 1st",
            name="Main source of cash income 1st",
            variable_type="str",
        )
        WealthCharacteristicFactory(
            code="main source of cash income 2nd",
            name="Main source of cash income 2nd",
            variable_type="str",
        )
        WealthCharacteristicFactory(
            code="main source of cash income 3rd",
            name="Main source of cash income 3rd",
            variable_type="str",
        )
        WealthCharacteristicFactory(
            code="mobile phones",
            name="Mobile phones",
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="months of consumption from crops",
            name="Months of consumption from crops in RY",
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="number at start of year",
            name="no. at start of reference year",
            variable_type="float",
            has_product=True,
            aliases=["<product>: total owned at start of year"],
        )
        WealthCharacteristicFactory(
            code="number at end of year",
            name="no. at end of reference year",
            variable_type="float",
            has_product=True,
        )
        WealthCharacteristicFactory(
            code="number born during year",
            name="no. born during year",
            aliases=["no.born during year"],
            variable_type="float",
            has_product=True,
        )
        WealthCharacteristicFactory(
            code="number bought",
            name="no. bought",
            variable_type="float",
            has_product=True,
        )
        WealthCharacteristicFactory(
            code="number died",
            name="no. died",
            variable_type="float",
            has_product=True,
        )
        WealthCharacteristicFactory(
            code="number of children at school",
            name="Number of children at school (WGs only)",
            aliases=["number of children at school (wgs only)"],
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="number of men in interview",
            name="No. of men in interview (participants)",
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="number of people actually working",
            name="No. of people actually working",
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="number of people capable of working",
            name="No. of people capable of working",
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="number of wives per husband",
            name="Number of wives per husband",
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="number of women in interview",
            name="No. of women in interview (participants)",
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="number owned",
            name="number owned",
            variable_type="float",
            has_product=True,
            aliases=["<product> number owned", "cattle: <product> number owned"],
        )
        WealthCharacteristicFactory(
            code="number slaughtered",
            name="no. slaughtered",
            variable_type="float",
            has_product=True,
        )
        WealthCharacteristicFactory(
            code="number sold",
            name="no. sold",
            variable_type="float",
            has_product=True,
        )
        WealthCharacteristicFactory(
            code="other",
            name="Other (unspecified)",
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="relief and assistance recipients",
            name="Relief and assistance recipients (yes/no)",
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="schooling levels commonly attained",
            name="Schooling levels commonly attained",
            variable_type="float",
        )
        WealthCharacteristicFactory(
            code="total owned at start of year",
            name="total owned at start of year",
            variable_type="float",
            has_product=True,
        )
        SourceOrganizationFactory(name="FEWS NET")

    def test_import_baseline(self):
        # Capture logging and direct writes to stdout (because loaddata writes
        # to stdout directly), so that unit test output is still clean.
        with conditional_logging():

            task = ImportBaseline(
                bss_path="apps/baseline/tests/bss.xlsx", metadata_path="apps/baseline/tests/metadata.xlsx"
            )
            submit_task(task, force=True, cascade=True, local_scheduler=True)

            result = task.output().open().read()
            self.assertRegex(result, r"Installed (\d+) object\(s\) from 1 fixture\(s\)")
