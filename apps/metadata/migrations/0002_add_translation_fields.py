from django.db import migrations, models

import common.fields


class Migration(migrations.Migration):

    dependencies = [
        ("metadata", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="hazardcategory",
            old_name="description",
            new_name="description_en",
        ),
        migrations.RenameField(
            model_name="hazardcategory",
            old_name="name",
            new_name="name_en",
        ),
        migrations.RenameField(
            model_name="livelihoodcategory",
            old_name="description",
            new_name="description_en",
        ),
        migrations.RenameField(
            model_name="livelihoodcategory",
            old_name="name",
            new_name="name_en",
        ),
        migrations.RenameField(
            model_name="market",
            old_name="description",
            new_name="description_en",
        ),
        migrations.RenameField(
            model_name="market",
            old_name="full_name",
            new_name="full_name_en",
        ),
        migrations.RenameField(
            model_name="market",
            old_name="name",
            new_name="name_en",
        ),
        migrations.RenameField(
            model_name="season",
            old_name="description",
            new_name="description_en",
        ),
        migrations.RenameField(
            model_name="season",
            old_name="name",
            new_name="name_en",
        ),
        migrations.RenameField(
            model_name="seasonalactivitytype",
            old_name="description",
            new_name="description_en",
        ),
        migrations.RenameField(
            model_name="seasonalactivitytype",
            old_name="name",
            new_name="name_en",
        ),
        migrations.RenameField(
            model_name="wealthcharacteristic",
            old_name="description",
            new_name="description_en",
        ),
        migrations.RenameField(
            model_name="wealthcharacteristic",
            old_name="name",
            new_name="name_en",
        ),
        migrations.RenameField(
            model_name="wealthgroupcategory",
            old_name="description",
            new_name="description_en",
        ),
        migrations.RenameField(
            model_name="wealthgroupcategory",
            old_name="name",
            new_name="name_en",
        ),
        migrations.AddField(
            model_name="hazardcategory",
            name="description_ar",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
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
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="hazardcategory",
            name="name_ar",
            field=common.fields.NameField(blank=True, max_length=60, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="hazardcategory",
            name="name_es",
            field=common.fields.NameField(blank=True, max_length=60, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="hazardcategory",
            name="name_fr",
            field=common.fields.NameField(blank=True, max_length=60, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="hazardcategory",
            name="name_pt",
            field=common.fields.NameField(blank=True, max_length=60, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="livelihoodcategory",
            name="description_ar",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
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
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="livelihoodcategory",
            name="name_ar",
            field=common.fields.NameField(blank=True, max_length=60, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="livelihoodcategory",
            name="name_es",
            field=common.fields.NameField(blank=True, max_length=60, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="livelihoodcategory",
            name="name_fr",
            field=common.fields.NameField(blank=True, max_length=60, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="livelihoodcategory",
            name="name_pt",
            field=common.fields.NameField(blank=True, max_length=60, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="market",
            name="description_ar",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
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
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="market",
            name="full_name_ar",
            field=common.fields.NameField(blank=True, max_length=200, verbose_name="full name"),
        ),
        migrations.AddField(
            model_name="market",
            name="full_name_es",
            field=common.fields.NameField(blank=True, max_length=200, verbose_name="full name"),
        ),
        migrations.AddField(
            model_name="market",
            name="full_name_fr",
            field=common.fields.NameField(blank=True, max_length=200, verbose_name="full name"),
        ),
        migrations.AddField(
            model_name="market",
            name="full_name_pt",
            field=common.fields.NameField(blank=True, max_length=200, verbose_name="full name"),
        ),
        migrations.AddField(
            model_name="market",
            name="name_ar",
            field=common.fields.NameField(blank=True, max_length=250, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="market",
            name="name_es",
            field=common.fields.NameField(blank=True, max_length=250, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="market",
            name="name_fr",
            field=common.fields.NameField(blank=True, max_length=250, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="market",
            name="name_pt",
            field=common.fields.NameField(blank=True, max_length=250, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="season",
            name="description_ar",
            field=models.TextField(blank=True, max_length=255, verbose_name="Description"),
        ),
        migrations.AddField(
            model_name="season",
            name="description_es",
            field=models.TextField(blank=True, max_length=255, verbose_name="Description"),
        ),
        migrations.AddField(
            model_name="season",
            name="description_fr",
            field=models.TextField(blank=True, max_length=255, verbose_name="Description"),
        ),
        migrations.AddField(
            model_name="season",
            name="description_pt",
            field=models.TextField(blank=True, max_length=255, verbose_name="Description"),
        ),
        migrations.AddField(
            model_name="season",
            name="name_ar",
            field=models.CharField(blank=True, max_length=50, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="season",
            name="name_es",
            field=models.CharField(blank=True, max_length=50, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="season",
            name="name_fr",
            field=models.CharField(blank=True, max_length=50, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="season",
            name="name_pt",
            field=models.CharField(blank=True, max_length=50, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="seasonalactivitytype",
            name="description_ar",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
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
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="seasonalactivitytype",
            name="name_ar",
            field=common.fields.NameField(blank=True, max_length=60, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="seasonalactivitytype",
            name="name_es",
            field=common.fields.NameField(blank=True, max_length=60, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="seasonalactivitytype",
            name="name_fr",
            field=common.fields.NameField(blank=True, max_length=60, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="seasonalactivitytype",
            name="name_pt",
            field=common.fields.NameField(blank=True, max_length=60, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="wealthcharacteristic",
            name="description_ar",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
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
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="wealthcharacteristic",
            name="name_ar",
            field=common.fields.NameField(blank=True, max_length=60, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="wealthcharacteristic",
            name="name_es",
            field=common.fields.NameField(blank=True, max_length=60, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="wealthcharacteristic",
            name="name_fr",
            field=common.fields.NameField(blank=True, max_length=60, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="wealthcharacteristic",
            name="name_pt",
            field=common.fields.NameField(blank=True, max_length=60, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="wealthgroupcategory",
            name="description_ar",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="wealthgroupcategory",
            name="description_es",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="wealthgroupcategory",
            name="description_fr",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="wealthgroupcategory",
            name="description_pt",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="wealthgroupcategory",
            name="name_ar",
            field=common.fields.NameField(blank=True, max_length=60, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="wealthgroupcategory",
            name="name_es",
            field=common.fields.NameField(blank=True, max_length=60, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="wealthgroupcategory",
            name="name_fr",
            field=common.fields.NameField(blank=True, max_length=60, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="wealthgroupcategory",
            name="name_pt",
            field=common.fields.NameField(blank=True, max_length=60, verbose_name="Name"),
        ),
    ]
