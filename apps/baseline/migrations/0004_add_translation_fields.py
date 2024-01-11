from django.db import migrations

import common.fields


class Migration(migrations.Migration):

    dependencies = [
        ("baseline", "0003_alter_communitylivestock_options"),
    ]

    operations = [
        migrations.RenameField(
            model_name="livelihoodzone",
            old_name="description",
            new_name="description_en",
        ),
        migrations.RenameField(
            model_name="livelihoodzone",
            old_name="name",
            new_name="name_en",
        ),
        migrations.RenameField(
            model_name="livelihoodzonebaseline",
            old_name="description",
            new_name="description_en",
        ),
        migrations.RenameField(
            model_name="livelihoodzonebaseline",
            old_name="name",
            new_name="name_en",
        ),
        migrations.AddField(
            model_name="livelihoodzone",
            name="description_ar",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="livelihoodzone",
            name="description_es",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="livelihoodzone",
            name="description_fr",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="livelihoodzone",
            name="description_pt",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="livelihoodzone",
            name="name_ar",
            field=common.fields.NameField(blank=True, max_length=200, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="livelihoodzone",
            name="name_es",
            field=common.fields.NameField(blank=True, max_length=200, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="livelihoodzone",
            name="name_fr",
            field=common.fields.NameField(blank=True, max_length=200, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="livelihoodzone",
            name="name_pt",
            field=common.fields.NameField(blank=True, max_length=200, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="livelihoodzonebaseline",
            name="description_ar",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="livelihoodzonebaseline",
            name="description_es",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="livelihoodzonebaseline",
            name="description_fr",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="livelihoodzonebaseline",
            name="description_pt",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=2000,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="livelihoodzonebaseline",
            name="name_ar",
            field=common.fields.NameField(blank=True, max_length=200, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="livelihoodzonebaseline",
            name="name_es",
            field=common.fields.NameField(blank=True, max_length=200, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="livelihoodzonebaseline",
            name="name_fr",
            field=common.fields.NameField(blank=True, max_length=200, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="livelihoodzonebaseline",
            name="name_pt",
            field=common.fields.NameField(blank=True, max_length=200, verbose_name="Name"),
        ),
    ]
