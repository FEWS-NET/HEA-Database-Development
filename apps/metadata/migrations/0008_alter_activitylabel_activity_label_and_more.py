# Generated by Django 5.0.2 on 2024-05-20 18:43

from django.db import migrations, models

import common.fields


class Migration(migrations.Migration):

    dependencies = [
        ("metadata", "0007_activitylabel_status_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="activitylabel",
            name="activity_label",
            field=common.fields.NameField(max_length=200, verbose_name="Activity Label"),
        ),
        migrations.AlterField(
            model_name="activitylabel",
            name="additional_identifier",
            field=models.CharField(blank=True, max_length=200, verbose_name="Season"),
        ),
        migrations.AlterField(
            model_name="wealthcharacteristiclabel",
            name="wealth_characteristic_label",
            field=common.fields.NameField(max_length=200, unique=True, verbose_name="Wealth Characteristic Label"),
        ),
    ]
