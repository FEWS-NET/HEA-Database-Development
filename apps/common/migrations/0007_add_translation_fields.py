# TODO: Delete this and recreate with the full set of fields

from django.db import migrations, models

import common.fields


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0006_unitofmeasure_aliases"),
    ]

    operations = [
        migrations.RenameField(
            model_name="classifiedproduct",
            old_name="common_name",
            new_name="common_name_en",
        ),
        migrations.RenameField(
            model_name="classifiedproduct",
            old_name="description",
            new_name="description_en",
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="common_name_ar",
            field=common.fields.NameField(blank=True, max_length=60, verbose_name="common name"),
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="common_name_es",
            field=common.fields.NameField(blank=True, max_length=60, verbose_name="common name"),
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="common_name_fr",
            field=common.fields.NameField(blank=True, max_length=60, verbose_name="common name"),
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="common_name_pt",
            field=common.fields.NameField(blank=True, max_length=60, verbose_name="common name"),
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="description_ar",
            field=models.CharField(default="", max_length=800, verbose_name="description"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="description_es",
            field=models.CharField(default="", max_length=800, verbose_name="description"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="description_fr",
            field=models.CharField(default="", max_length=800, verbose_name="description"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="description_pt",
            field=models.CharField(default="", max_length=800, verbose_name="description"),
            preserve_default=False,
        ),
    ]
