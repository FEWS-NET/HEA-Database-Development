# Generated by Django 5.0.2 on 2024-04-25 09:28

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("baseline", "0014_livelihoodzonebaseline_currency"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="livelihoodzonebaselinecorrection",
            options={
                "verbose_name": "Livelihood Zone Baseline Correction",
                "verbose_name_plural": "Livelihood Zone Baseline Corrections",
            },
        ),
        migrations.AlterField(
            model_name="community",
            name="interview_number",
            field=models.CharField(
                blank=True,
                help_text="The interview number or interview code assigned to the Community",
                max_length=30,
                null=True,
                verbose_name="Interview Number",
            ),
        ),
        migrations.AlterField(
            model_name="livelihoodzonebaselinecorrection",
            name="cell_range",
            field=models.CharField(max_length=20, verbose_name="Cell range"),
        ),
        migrations.AlterField(
            model_name="livelihoodzonebaselinecorrection",
            name="previous_value",
            field=models.JSONField(verbose_name="Previous value before correction"),
        ),
        migrations.AlterField(
            model_name="livelihoodzonebaselinecorrection",
            name="value",
            field=models.JSONField(verbose_name="Corrected value"),
        ),
        migrations.AlterField(
            model_name="livelihoodzonebaselinecorrection",
            name="worksheet_name",
            field=models.CharField(
                choices=[
                    ("WB", "WB"),
                    ("Data", "Data"),
                    ("Data2", "Data2"),
                    ("Data3", "Data3"),
                    ("Timeline", "Timeline"),
                ],
                max_length=20,
                verbose_name="Worksheet name",
            ),
        ),
        migrations.AddConstraint(
            model_name="livelihoodzonebaselinecorrection",
            constraint=models.UniqueConstraint(
                fields=("livelihood_zone_baseline", "worksheet_name", "cell_range"),
                name="livelihood_zone_baseline_corrections_uniq",
            ),
        ),
    ]
