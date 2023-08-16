# Generated by Django 4.2.4 on 2023-08-15 12:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("metadata", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="hazardcategory",
            name="ordering",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="The order to display the items in when sorting by this field, if not obvious.",
                null=True,
                verbose_name="Ordering",
            ),
        ),
        migrations.AddField(
            model_name="livelihoodcategory",
            name="ordering",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="The order to display the items in when sorting by this field, if not obvious.",
                null=True,
                verbose_name="Ordering",
            ),
        ),
        migrations.AddField(
            model_name="market",
            name="ordering",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="The order to display the items in when sorting by this field, if not obvious.",
                null=True,
                verbose_name="Ordering",
            ),
        ),
        migrations.AddField(
            model_name="seasonalactivitytype",
            name="ordering",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="The order to display the items in when sorting by this field, if not obvious.",
                null=True,
                verbose_name="Ordering",
            ),
        ),
        migrations.AddField(
            model_name="wealthcategory",
            name="ordering",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="The order to display the items in when sorting by this field, if not obvious.",
                null=True,
                verbose_name="Ordering",
            ),
        ),
        migrations.AddField(
            model_name="wealthcharacteristic",
            name="ordering",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="The order to display the items in when sorting by this field, if not obvious.",
                null=True,
                verbose_name="Ordering",
            ),
        ),
    ]