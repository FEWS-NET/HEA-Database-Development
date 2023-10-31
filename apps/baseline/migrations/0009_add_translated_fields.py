from django.db import migrations, models

import common.fields


class Migration(migrations.Migration):

    dependencies = [
        ("baseline", "0008_nullable_wealthgroup_average_household_size_and_percentage_of_households"),
    ]

    operations = [
        migrations.AddField(
            model_name="annualproductionperformance",
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
            model_name="annualproductionperformance",
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
            model_name="annualproductionperformance",
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
            model_name="annualproductionperformance",
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
            model_name="annualproductionperformance",
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
            model_name="community",
            name="full_name_ar",
            field=common.fields.NameField(
                help_text="The full name the Community, including the parent administrative units.",
                max_length=200,
                null=True,
                verbose_name="Full Name",
            ),
        ),
        migrations.AddField(
            model_name="community",
            name="full_name_en",
            field=common.fields.NameField(
                help_text="The full name the Community, including the parent administrative units.",
                max_length=200,
                null=True,
                verbose_name="Full Name",
            ),
        ),
        migrations.AddField(
            model_name="community",
            name="full_name_es",
            field=common.fields.NameField(
                help_text="The full name the Community, including the parent administrative units.",
                max_length=200,
                null=True,
                verbose_name="Full Name",
            ),
        ),
        migrations.AddField(
            model_name="community",
            name="full_name_fr",
            field=common.fields.NameField(
                help_text="The full name the Community, including the parent administrative units.",
                max_length=200,
                null=True,
                verbose_name="Full Name",
            ),
        ),
        migrations.AddField(
            model_name="community",
            name="full_name_pt",
            field=common.fields.NameField(
                help_text="The full name the Community, including the parent administrative units.",
                max_length=200,
                null=True,
                verbose_name="Full Name",
            ),
        ),
        migrations.AddField(
            model_name="community",
            name="name_ar",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="community",
            name="name_en",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="community",
            name="name_es",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="community",
            name="name_fr",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="community",
            name="name_pt",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="event",
            name="description_ar",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=255,
                null=True,
                verbose_name="Description of Event(s) and/or Response(s)",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="description_en",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=255,
                null=True,
                verbose_name="Description of Event(s) and/or Response(s)",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="description_es",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=255,
                null=True,
                verbose_name="Description of Event(s) and/or Response(s)",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="description_fr",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=255,
                null=True,
                verbose_name="Description of Event(s) and/or Response(s)",
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="description_pt",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=255,
                null=True,
                verbose_name="Description of Event(s) and/or Response(s)",
            ),
        ),
        migrations.AddField(
            model_name="hazard",
            name="description_ar",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=255,
                null=True,
                verbose_name="Description of Event(s) and/or Response(s)",
            ),
        ),
        migrations.AddField(
            model_name="hazard",
            name="description_en",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=255,
                null=True,
                verbose_name="Description of Event(s) and/or Response(s)",
            ),
        ),
        migrations.AddField(
            model_name="hazard",
            name="description_es",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=255,
                null=True,
                verbose_name="Description of Event(s) and/or Response(s)",
            ),
        ),
        migrations.AddField(
            model_name="hazard",
            name="description_fr",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=255,
                null=True,
                verbose_name="Description of Event(s) and/or Response(s)",
            ),
        ),
        migrations.AddField(
            model_name="hazard",
            name="description_pt",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=255,
                null=True,
                verbose_name="Description of Event(s) and/or Response(s)",
            ),
        ),
        migrations.AddField(
            model_name="livelihoodzone",
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
            model_name="livelihoodzone",
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
            model_name="livelihoodzone",
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
            model_name="livelihoodzone",
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
            model_name="livelihoodzone",
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
            model_name="livelihoodzone",
            name="name_ar",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="livelihoodzone",
            name="name_en",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="livelihoodzone",
            name="name_es",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="livelihoodzone",
            name="name_fr",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="livelihoodzone",
            name="name_pt",
            field=common.fields.NameField(max_length=60, null=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="livelihoodzonebaseline",
            name="population_source_ar",
            field=models.CharField(
                blank=True,
                help_text="The data source for the Population Estimate, e.g. National Bureau of Statistics",
                max_length=120,
                null=True,
                verbose_name="Population Source",
            ),
        ),
        migrations.AddField(
            model_name="livelihoodzonebaseline",
            name="population_source_en",
            field=models.CharField(
                blank=True,
                help_text="The data source for the Population Estimate, e.g. National Bureau of Statistics",
                max_length=120,
                null=True,
                verbose_name="Population Source",
            ),
        ),
        migrations.AddField(
            model_name="livelihoodzonebaseline",
            name="population_source_es",
            field=models.CharField(
                blank=True,
                help_text="The data source for the Population Estimate, e.g. National Bureau of Statistics",
                max_length=120,
                null=True,
                verbose_name="Population Source",
            ),
        ),
        migrations.AddField(
            model_name="livelihoodzonebaseline",
            name="population_source_fr",
            field=models.CharField(
                blank=True,
                help_text="The data source for the Population Estimate, e.g. National Bureau of Statistics",
                max_length=120,
                null=True,
                verbose_name="Population Source",
            ),
        ),
        migrations.AddField(
            model_name="livelihoodzonebaseline",
            name="population_source_pt",
            field=models.CharField(
                blank=True,
                help_text="The data source for the Population Estimate, e.g. National Bureau of Statistics",
                max_length=120,
                null=True,
                verbose_name="Population Source",
            ),
        ),
        migrations.AddField(
            model_name="marketprice",
            name="description_ar",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=100,
                null=True,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="marketprice",
            name="description_en",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=100,
                null=True,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="marketprice",
            name="description_es",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=100,
                null=True,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="marketprice",
            name="description_fr",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=100,
                null=True,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="marketprice",
            name="description_pt",
            field=common.fields.DescriptionField(
                blank=True,
                help_text="Any extra information or detail that is relevant to the object.",
                max_length=100,
                null=True,
                verbose_name="Description",
            ),
        ),
        migrations.AddField(
            model_name="sourceorganization",
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
            model_name="sourceorganization",
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
            model_name="sourceorganization",
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
            model_name="sourceorganization",
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
            model_name="sourceorganization",
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
            model_name="sourceorganization",
            name="full_name_ar",
            field=common.fields.NameField(max_length=300, null=True, unique=True, verbose_name="full name"),
        ),
        migrations.AddField(
            model_name="sourceorganization",
            name="full_name_en",
            field=common.fields.NameField(max_length=300, null=True, unique=True, verbose_name="full name"),
        ),
        migrations.AddField(
            model_name="sourceorganization",
            name="full_name_es",
            field=common.fields.NameField(max_length=300, null=True, unique=True, verbose_name="full name"),
        ),
        migrations.AddField(
            model_name="sourceorganization",
            name="full_name_fr",
            field=common.fields.NameField(max_length=300, null=True, unique=True, verbose_name="full name"),
        ),
        migrations.AddField(
            model_name="sourceorganization",
            name="full_name_pt",
            field=common.fields.NameField(max_length=300, null=True, unique=True, verbose_name="full name"),
        ),
        migrations.AddField(
            model_name="sourceorganization",
            name="name_ar",
            field=common.fields.NameField(max_length=200, null=True, unique=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="sourceorganization",
            name="name_en",
            field=common.fields.NameField(max_length=200, null=True, unique=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="sourceorganization",
            name="name_es",
            field=common.fields.NameField(max_length=200, null=True, unique=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="sourceorganization",
            name="name_fr",
            field=common.fields.NameField(max_length=200, null=True, unique=True, verbose_name="Name"),
        ),
        migrations.AddField(
            model_name="sourceorganization",
            name="name_pt",
            field=common.fields.NameField(max_length=200, null=True, unique=True, verbose_name="Name"),
        ),
    ]
