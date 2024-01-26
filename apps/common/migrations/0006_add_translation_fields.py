from django.db import migrations, models

import common.fields


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0005_unitofmeasure_aliases_and_rename_cpc"),
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
        migrations.RenameField(
            model_name="unitofmeasure",
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
            field=models.CharField(blank=True, max_length=800, verbose_name="description"),
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="description_es",
            field=models.CharField(blank=True, max_length=800, verbose_name="description"),
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="description_fr",
            field=models.CharField(blank=True, max_length=800, verbose_name="description"),
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="description_pt",
            field=models.CharField(blank=True, max_length=800, verbose_name="description"),
        ),
        migrations.AddField(
            model_name="unitofmeasure",
            name="description_ar",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="unitofmeasure",
            name="description_es",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="unitofmeasure",
            name="description_fr",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="unitofmeasure",
            name="description_pt",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
                verbose_name="Description",
            ),
        ),
    ]
