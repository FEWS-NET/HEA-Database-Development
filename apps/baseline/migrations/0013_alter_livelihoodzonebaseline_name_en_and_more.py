# Generated by Django 5.0.4 on 2024-04-16 15:11

from django.db import migrations, models

import common.fields


class Migration(migrations.Migration):

    dependencies = [
        ("baseline", "0012_livelihoodzonebaselinecorrection"),
        ("metadata", "0005_activitylabel_notes_wealthcharacteristiclabel_notes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="livelihoodzonebaseline",
            name="name_en",
            field=common.fields.NameField(max_length=200, verbose_name="Name"),
        ),
        migrations.AddConstraint(
            model_name="livelihoodzonebaseline",
            constraint=models.UniqueConstraint(
                fields=("name_en", "reference_year_end_date"),
                name="baseline_livelihoodzonebaseline_name_en_reference_year_end_date_uniq",
            ),
        ),
    ]