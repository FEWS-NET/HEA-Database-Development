# Generated by Django 4.2.7 on 2023-12-03 16:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("baseline", "0002_seasonalproductionperformance_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="communitylivestock",
            options={"verbose_name": "Community Livestock", "verbose_name_plural": "Community livestock"},
        ),
    ]