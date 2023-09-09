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
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="common.unitofmeasure",
                verbose_name="Unit of Measure",
            ),
        ),
    ]
