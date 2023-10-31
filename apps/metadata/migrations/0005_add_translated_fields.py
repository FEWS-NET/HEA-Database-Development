from django.db import migrations, models

import common.fields


class Migration(migrations.Migration):

    dependencies = [
        ("metadata", "0004_alter_wealthcharacteristic_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="hazardcategory",
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
            model_name="hazardcategory",
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
            model_name="hazardcategory",
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
            model_name="hazardcategory",
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
            model_name="hazardcategory",
            name="description_pt",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
                null=True,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="hazardcategory",
            name="name_ar",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="hazardcategory",
            name="name_en",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="hazardcategory",
            name="name_es",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="hazardcategory",
            name="name_fr",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="hazardcategory",
            name="name_pt",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="livelihoodcategory",
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
            model_name="livelihoodcategory",
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
            model_name="livelihoodcategory",
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
            model_name="livelihoodcategory",
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
            model_name="livelihoodcategory",
            name="description_pt",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
                null=True,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="livelihoodcategory",
            name="name_ar",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="livelihoodcategory",
            name="name_en",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="livelihoodcategory",
            name="name_es",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="livelihoodcategory",
            name="name_fr",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="livelihoodcategory",
            name="name_pt",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="market",
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
            model_name="market",
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
            model_name="market",
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
            model_name="market",
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
            model_name="market",
            name="description_pt",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
                null=True,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="market",
            name="name_ar",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="market",
            name="name_en",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="market",
            name="name_es",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="market",
            name="name_fr",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="market",
            name="name_pt",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="season",
            name="description_ar",
            field=models.TextField(max_length=255, null=True, verbose_name="Description"),
        ),
        migrations.AddField(
            model_name="season",
            name="description_en",
            field=models.TextField(max_length=255, null=True, verbose_name="Description"),
        ),
        migrations.AddField(
            model_name="season",
            name="description_es",
            field=models.TextField(max_length=255, null=True, verbose_name="Description"),
        ),
        migrations.AddField(
            model_name="season",
            name="description_fr",
            field=models.TextField(max_length=255, null=True, verbose_name="Description"),
        ),
        migrations.AddField(
            model_name="season",
            name="description_pt",
            field=models.TextField(max_length=255, null=True, verbose_name="Description"),
        ),
        migrations.AddField(
            model_name="season",
            name="name_ar",
            field=models.CharField(max_length=50, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="season",
            name="name_en",
            field=models.CharField(max_length=50, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="season",
            name="name_es",
            field=models.CharField(max_length=50, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="season",
            name="name_fr",
            field=models.CharField(max_length=50, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="season",
            name="name_pt",
            field=models.CharField(max_length=50, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="seasonalactivitytype",
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
            model_name="seasonalactivitytype",
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
            model_name="seasonalactivitytype",
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
            model_name="seasonalactivitytype",
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
            model_name="seasonalactivitytype",
            name="description_pt",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
                null=True,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="seasonalactivitytype",
            name="name_ar",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="seasonalactivitytype",
            name="name_en",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="seasonalactivitytype",
            name="name_es",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="seasonalactivitytype",
            name="name_fr",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="seasonalactivitytype",
            name="name_pt",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="wealthcategory",
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
            model_name="wealthcategory",
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
            model_name="wealthcategory",
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
            model_name="wealthcategory",
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
            model_name="wealthcategory",
            name="description_pt",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
                null=True,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="wealthcategory",
            name="name_ar",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="wealthcategory",
            name="name_en",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="wealthcategory",
            name="name_es",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="wealthcategory",
            name="name_fr",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="wealthcategory",
            name="name_pt",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="wealthcharacteristic",
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
            model_name="wealthcharacteristic",
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
            model_name="wealthcharacteristic",
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
            model_name="wealthcharacteristic",
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
            model_name="wealthcharacteristic",
            name="description_pt",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
                null=True,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="wealthcharacteristic",
            name="name_ar",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="wealthcharacteristic",
            name="name_en",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="wealthcharacteristic",
            name="name_es",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="wealthcharacteristic",
            name="name_fr",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="wealthcharacteristic",
            name="name_pt",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
    ]
