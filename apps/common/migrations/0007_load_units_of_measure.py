import os.path
from collections import namedtuple

from django.db import migrations, models

from common.utils import LoadModelFromDict

Unit = namedtuple("UnitOfMeasure", ["abbreviation", "description_en", "unit_type", "aliases"])
UNITS = [
    Unit("kg", "kilogram", "Weight", ["kilogram", "kilogramme", "kilo", "1 kg", "1kg"]),
    Unit("lb", "pound", "Weight", ["pound", "pound (lb.)"]),
    Unit("L", "litre", "Volume", ["l", "litre", "liter", "1 litre", "1 liter"]),
    Unit("gal", "US Liquid Gallon", "Volume", ["gallon", "1 gallon"]),
    Unit("ea", "individual item", "Item", ["each", "individual", "head"]),
    Unit("t", "tonne", "Weight", ["mt"]),
    Unit("m2", "square metre", "Area", ["square meter"]),
    Unit("ha", "hectare", "Area", ""),
    Unit("acre", "acre", "Area", ["acres"]),
    Unit("cda", "cuerda", "Area", ["cuerdas"]),
    Unit("km2", "square kilometre", "Area", ["square kilometer"]),
    Unit("hg", "hectogram", "Weight", ""),
    Unit("kg/ha", "kilograms per hectare", "Yield", ""),
    Unit("hg/ha", "hectograms per hectare", "Yield", ""),
    Unit("MT/ha", "tonnes per hectare", "Yield", ""),
]

Conv = namedtuple("UnitOfMeasureConversion", ["from_unit", "to_unit", "conversion_factor"])
CONVS = [
    Conv("lb", "kg", 0.45359237),
    Conv("t", "kg", 1000),
    Conv("gal", "L", 3.785411784),
    Conv("ha", "m2", 10000),
    Conv("acre", "m2", 4046.8564224),
    # 16 cuerdas = 1 ha, see GT06_4jun20 'WB'!A19.
    # This is 10000/16 = 625 m2/cda
    # According to https://en.wikipedia.org/wiki/Cuerda:
    #   One cuerda of 30 x 30 varas = 628.87 square meters
    Conv("cda", "m2", 628.87),
    Conv("km2", "m2", 1000000),
    Conv("hg", "kg", 0.1),
    Conv("hg/ha", "kg/ha", 0.1),
    Conv("MT/ha", "kg/ha", 1000),
]


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("common", "0006_add_translation_fields"),
    ]

    operations = [
        LoadModelFromDict(model="UnitOfMeasure", data=UNITS),
        LoadModelFromDict(model="UnitOfMeasureConversion", data=CONVS),
    ]
