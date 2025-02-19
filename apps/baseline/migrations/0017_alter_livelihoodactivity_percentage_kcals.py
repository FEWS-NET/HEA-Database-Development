# Generated by Django 5.1.1 on 2024-11-22 03:51

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("baseline", "0016_alter_livelihoodstrategy_additional_identifier_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="livelihoodactivity",
            name="percentage_kcals",
            field=models.FloatField(
                blank=True,
                help_text="Percentage of annual household kcal requirement provided by this livelihood strategy",
                null=True,
                validators=[django.core.validators.MinValueValidator(0)],
                verbose_name="Percentage of required kcals",
            ),
        ),
    ]
