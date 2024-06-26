# Generated by Django 4.2.7 on 2024-02-10 02:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0008_load_classified_product"),
        ("baseline", "0006_livelihoodzone_alternate_code"),
    ]

    operations = [
        migrations.AlterField(
            model_name="wealthgroupcharacteristicvalue",
            name="product",
            field=models.ForeignKey(
                blank=True,
                db_column="product_code",
                help_text="Product, e.g. Cattle",
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="wealth_group_characteristic_values",
                to="common.classifiedproduct",
                verbose_name="Product",
            ),
        ),
        migrations.AlterField(
            model_name="wealthgroupcharacteristicvalue",
            name="unit_of_measure",
            field=models.ForeignKey(
                blank=True,
                db_column="unit_code",
                null=True,
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="wealth_group_characteristic_values",
                to="common.unitofmeasure",
                verbose_name="Unit of Measure",
            ),
        ),
        migrations.AlterField(
            model_name="wealthgroupcharacteristicvalue",
            name="wealth_group",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="baseline.wealthgroup", verbose_name="Wealth Group"
            ),
        ),
        migrations.AlterField(
            model_name="livelihoodstrategy",
            name="unit_of_measure",
            field=models.ForeignKey(
                blank=True,
                db_column="unit_code",
                help_text="Unit used to measure production from this Livelihood Strategy",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="common.unitofmeasure",
                verbose_name="Unit of Measure",
            ),
        ),
        migrations.AlterField(
            model_name="livelihoodactivity",
            name="livelihood_strategy",
            field=models.ForeignKey(
                help_text="Livelihood Strategy",
                on_delete=django.db.models.deletion.CASCADE,
                to="baseline.livelihoodstrategy",
            ),
        ),
        migrations.AlterField(
            model_name="livelihoodactivity",
            name="wealth_group",
            field=models.ForeignKey(
                help_text="Wealth Group", on_delete=django.db.models.deletion.CASCADE, to="baseline.wealthgroup"
            ),
        ),
    ]
