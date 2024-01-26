# Generated by Django 4.2.2 on 2023-09-04 04:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0003_load_currencies"),
    ]

    operations = [
        migrations.AlterField(
            model_name="classifiedproduct",
            name="unit_of_measure",
            field=models.ForeignKey(
                db_column="unit_code",
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="common.unitofmeasure",
                verbose_name="Unit of Measure",
            ),
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="aliases",
            field=models.JSONField(
                blank=True, help_text="A list of alternate names for the product.", null=True, verbose_name="aliases"
            ),
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="hs2012",
            field=models.JSONField(
                blank=True,
                help_text="The 6-digit codes for the Product in the Harmonized Commodity Description and Coding System (HS), stored as XXXX.YY ",
                null=True,
                verbose_name="HS2012",
            ),
        ),
    ]
