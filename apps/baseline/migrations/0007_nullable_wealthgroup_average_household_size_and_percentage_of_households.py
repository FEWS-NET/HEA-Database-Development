# Generated by Django 4.2.4 on 2023-09-12 02:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("baseline", "0006_remove_community_interviewers_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="wealthgroup",
            name="average_household_size",
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Average household size"),
        ),
        migrations.AlterField(
            model_name="wealthgroup",
            name="percentage_of_households",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="Percentage of households in the Community or Livelihood Zone that are in this Wealth Group",
                null=True,
                verbose_name="Percentage of households",
            ),
        ),
    ]
