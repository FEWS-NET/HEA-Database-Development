from django.db import migrations, models

import common.fields


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0005_load_classified_product"),
    ]

    operations = [
        migrations.AddField(
            model_name="classifiedproduct",
            name="common_name_ar",
            field=common.fields.NameField(blank=True, max_length=60, null=True, verbose_name="common name"),
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="common_name_en",
            field=common.fields.NameField(blank=True, max_length=60, null=True, verbose_name="common name"),
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="common_name_es",
            field=common.fields.NameField(blank=True, max_length=60, null=True, verbose_name="common name"),
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="common_name_fr",
            field=common.fields.NameField(blank=True, max_length=60, null=True, verbose_name="common name"),
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="common_name_pt",
            field=common.fields.NameField(blank=True, max_length=60, null=True, verbose_name="common name"),
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="description_ar",
            field=models.CharField(max_length=800, null=True, verbose_name="description"),
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="description_en",
            field=models.CharField(max_length=800, null=True, verbose_name="description"),
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="description_es",
            field=models.CharField(max_length=800, null=True, verbose_name="description"),
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="description_fr",
            field=models.CharField(max_length=800, null=True, verbose_name="description"),
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="description_pt",
            field=models.CharField(max_length=800, null=True, verbose_name="description"),
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="scientific_name_ar",
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name="scientific name"),
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="scientific_name_en",
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name="scientific name"),
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="scientific_name_es",
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name="scientific name"),
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="scientific_name_fr",
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name="scientific name"),
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="scientific_name_pt",
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name="scientific name"),
        ),
        migrations.AddField(
            model_name="country",
            name="iso_en_name_ar",
            field=models.CharField(
                help_text=(
                    "The name of the Country approved by the ISO 3166 Maintenance Agency with accented "
                    "characters replaced by their ASCII equivalents"
                ),
                max_length=200,
                null=True,
                unique=True,
                verbose_name="ISO English ASCII name",
            ),
        ),
        migrations.AddField(
            model_name="country",
            name="iso_en_name_en",
            field=models.CharField(
                help_text=(
                    "The name of the Country approved by the ISO 3166 Maintenance Agency with "
                    "accented characters replaced by their ASCII equivalents"
                ),
                max_length=200,
                null=True,
                unique=True,
                verbose_name="ISO English ASCII name",
            ),
        ),
        migrations.AddField(
            model_name="country",
            name="iso_en_name_es",
            field=models.CharField(
                help_text=(
                    "The name of the Country approved by the ISO 3166 Maintenance Agency with "
                    "accented characters replaced by their ASCII equivalents"
                ),
                max_length=200,
                null=True,
                unique=True,
                verbose_name="ISO English ASCII name",
            ),
        ),
        migrations.AddField(
            model_name="country",
            name="iso_en_name_fr",
            field=models.CharField(
                help_text=(
                    "The name of the Country approved by the ISO 3166 Maintenance Agency with "
                    "accented characters replaced by their ASCII equivalents"
                ),
                max_length=200,
                null=True,
                unique=True,
                verbose_name="ISO English ASCII name",
            ),
        ),
        migrations.AddField(
            model_name="country",
            name="iso_en_name_pt",
            field=models.CharField(
                help_text=(
                    "The name of the Country approved by the ISO 3166 Maintenance Agency with "
                    "accented characters replaced by their ASCII equivalents"
                ),
                max_length=200,
                null=True,
                unique=True,
                verbose_name="ISO English ASCII name",
            ),
        ),
        migrations.AddField(
            model_name="country",
            name="iso_en_proper_ar",
            field=models.CharField(
                help_text=(
                    "The full formal name of the Country approved by the ISO 3166 Maintenance Agency "
                    "with accented characters replaced by their ASCII equivalents"
                ),
                max_length=200,
                null=True,
                verbose_name="ISO English ASCII full name",
            ),
        ),
        migrations.AddField(
            model_name="country",
            name="iso_en_proper_en",
            field=models.CharField(
                help_text=(
                    "The full formal name of the Country approved by the ISO 3166 Maintenance "
                    "Agency with accented characters replaced by their ASCII equivalents"
                ),
                max_length=200,
                null=True,
                verbose_name="ISO English ASCII full name",
            ),
        ),
        migrations.AddField(
            model_name="country",
            name="iso_en_proper_es",
            field=models.CharField(
                help_text=(
                    "The full formal name of the Country approved by the ISO 3166 Maintenance "
                    "Agency with accented characters replaced by their ASCII equivalents"
                ),
                max_length=200,
                null=True,
                verbose_name="ISO English ASCII full name",
            ),
        ),
        migrations.AddField(
            model_name="country",
            name="iso_en_proper_fr",
            field=models.CharField(
                help_text=(
                    "The full formal name of the Country approved by the ISO 3166 Maintenance "
                    "Agency with accented characters replaced by their ASCII equivalents"
                ),
                max_length=200,
                null=True,
                verbose_name="ISO English ASCII full name",
            ),
        ),
        migrations.AddField(
            model_name="country",
            name="iso_en_proper_pt",
            field=models.CharField(
                help_text=(
                    "The full formal name of the Country approved by the ISO 3166 Maintenance "
                    "Agency with accented characters replaced by their ASCII equivalents"
                ),
                max_length=200,
                null=True,
                verbose_name="ISO English ASCII full name",
            ),
        ),
        migrations.AddField(
            model_name="country",
            name="iso_en_ro_name_ar",
            field=models.CharField(
                help_text="The name of the Country approved by the ISO 3166 Maintenance Agency",
                max_length=200,
                null=True,
                unique=True,
                verbose_name="ISO English name",
            ),
        ),
        migrations.AddField(
            model_name="country",
            name="iso_en_ro_name_en",
            field=models.CharField(
                help_text="The name of the Country approved by the ISO 3166 Maintenance Agency",
                max_length=200,
                null=True,
                unique=True,
                verbose_name="ISO English name",
            ),
        ),
        migrations.AddField(
            model_name="country",
            name="iso_en_ro_name_es",
            field=models.CharField(
                help_text="The name of the Country approved by the ISO 3166 Maintenance Agency",
                max_length=200,
                null=True,
                unique=True,
                verbose_name="ISO English name",
            ),
        ),
        migrations.AddField(
            model_name="country",
            name="iso_en_ro_name_fr",
            field=models.CharField(
                help_text="The name of the Country approved by the ISO 3166 Maintenance Agency",
                max_length=200,
                null=True,
                unique=True,
                verbose_name="ISO English name",
            ),
        ),
        migrations.AddField(
            model_name="country",
            name="iso_en_ro_name_pt",
            field=models.CharField(
                help_text="The name of the Country approved by the ISO 3166 Maintenance Agency",
                max_length=200,
                null=True,
                unique=True,
                verbose_name="ISO English name",
            ),
        ),
        migrations.AddField(
            model_name="country",
            name="iso_en_ro_proper_ar",
            field=models.CharField(
                help_text="The full formal name of the Country approved by the ISO 3166 Maintenance Agency",
                max_length=200,
                null=True,
                verbose_name="ISO English full name",
            ),
        ),
        migrations.AddField(
            model_name="country",
            name="iso_en_ro_proper_en",
            field=models.CharField(
                help_text="The full formal name of the Country approved by the ISO 3166 Maintenance Agency",
                max_length=200,
                null=True,
                verbose_name="ISO English full name",
            ),
        ),
        migrations.AddField(
            model_name="country",
            name="iso_en_ro_proper_es",
            field=models.CharField(
                help_text="The full formal name of the Country approved by the ISO 3166 Maintenance Agency",
                max_length=200,
                null=True,
                verbose_name="ISO English full name",
            ),
        ),
        migrations.AddField(
            model_name="country",
            name="iso_en_ro_proper_fr",
            field=models.CharField(
                help_text="The full formal name of the Country approved by the ISO 3166 Maintenance Agency",
                max_length=200,
                null=True,
                verbose_name="ISO English full name",
            ),
        ),
        migrations.AddField(
            model_name="country",
            name="iso_en_ro_proper_pt",
            field=models.CharField(
                help_text="The full formal name of the Country approved by the ISO 3166 Maintenance Agency",
                max_length=200,
                null=True,
                verbose_name="ISO English full name",
            ),
        ),
        migrations.AddField(
            model_name="country",
            name="name_ar",
            field=common.fields.NameField(max_length=200, null=True, unique=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="country",
            name="name_en",
            field=common.fields.NameField(max_length=200, null=True, unique=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="country",
            name="name_es",
            field=common.fields.NameField(max_length=200, null=True, unique=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="country",
            name="name_fr",
            field=common.fields.NameField(max_length=200, null=True, unique=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="country",
            name="name_pt",
            field=common.fields.NameField(max_length=200, null=True, unique=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="currency",
            name="iso_en_name_ar",
            field=models.CharField(max_length=200, null=True, verbose_name="name"),
        ),
        migrations.AddField(
            model_name="currency",
            name="iso_en_name_en",
            field=models.CharField(max_length=200, null=True, verbose_name="name"),
        ),
        migrations.AddField(
            model_name="currency",
            name="iso_en_name_es",
            field=models.CharField(max_length=200, null=True, verbose_name="name"),
        ),
        migrations.AddField(
            model_name="currency",
            name="iso_en_name_fr",
            field=models.CharField(max_length=200, null=True, verbose_name="name"),
        ),
        migrations.AddField(
            model_name="currency",
            name="iso_en_name_pt",
            field=models.CharField(max_length=200, null=True, verbose_name="name"),
        ),
        migrations.AddField(
            model_name="unitofmeasure",
            name="description_ar",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
                null=True,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="unitofmeasure",
            name="description_en",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
                null=True,
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
                null=True,
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
                null=True,
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
                null=True,
                verbose_name="Description",
            ),
        ),
    ]
