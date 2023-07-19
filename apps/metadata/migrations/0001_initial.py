# Generated by Django 4.2.2 on 2023-07-17 06:56

import django.db.models.deletion
from django.db import migrations, models

import common.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("common", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Dimension",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("path", models.CharField(max_length=255, unique=True)),
                ("depth", models.PositiveIntegerField()),
                ("numchild", models.PositiveIntegerField(default=0)),
                (
                    "es_name",
                    common.fields.NameField(
                        blank=True,
                        help_text="Spanish name if different from the English name",
                        max_length=60,
                        verbose_name="Spanish name",
                    ),
                ),
                (
                    "fr_name",
                    common.fields.NameField(
                        blank=True,
                        help_text="French name if different from the English name",
                        max_length=60,
                        verbose_name="French name",
                    ),
                ),
                (
                    "pt_name",
                    common.fields.NameField(
                        blank=True,
                        help_text="Portuguese name if different from the English name",
                        max_length=60,
                        verbose_name="Portuguese name",
                    ),
                ),
                (
                    "ar_name",
                    common.fields.NameField(
                        blank=True,
                        help_text="Arabic name if different from the English name",
                        max_length=60,
                        verbose_name="Arabic name",
                    ),
                ),
                ("code", common.fields.CodeField(max_length=60, verbose_name="Code")),
                (
                    "description",
                    common.fields.DescriptionField(
                        blank=True,
                        help_text="Any extra information or detail that is relevant to the object.",
                        max_length=2000,
                        verbose_name="Description",
                    ),
                ),
                ("default", models.BooleanField(default=False, help_text="The default value in a given sub-list.")),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="DimensionType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "es_name",
                    common.fields.NameField(
                        blank=True,
                        help_text="Spanish name if different from the English name",
                        max_length=60,
                        verbose_name="Spanish name",
                    ),
                ),
                (
                    "fr_name",
                    common.fields.NameField(
                        blank=True,
                        help_text="French name if different from the English name",
                        max_length=60,
                        verbose_name="French name",
                    ),
                ),
                (
                    "pt_name",
                    common.fields.NameField(
                        blank=True,
                        help_text="Portuguese name if different from the English name",
                        max_length=60,
                        verbose_name="Portuguese name",
                    ),
                ),
                (
                    "ar_name",
                    common.fields.NameField(
                        blank=True,
                        help_text="Arabic name if different from the English name",
                        max_length=60,
                        verbose_name="Arabic name",
                    ),
                ),
                ("code", common.fields.CodeField(max_length=60, verbose_name="Code")),
                (
                    "description",
                    common.fields.DescriptionField(
                        blank=True,
                        help_text="Any extra information or detail that is relevant to the object.",
                        max_length=2000,
                        verbose_name="Description",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="CropType",
            fields=[
                (
                    "dimension_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="metadata.dimension",
                    ),
                ),
            ],
            options={
                "verbose_name": "Crop Type",
                "verbose_name_plural": "Crop Types",
            },
            bases=("metadata.dimension",),
        ),
        migrations.CreateModel(
            name="HazardCategory",
            fields=[
                (
                    "dimension_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="metadata.dimension",
                    ),
                ),
            ],
            options={
                "verbose_name": "Hazard Category",
                "verbose_name_plural": "Hazard Categories",
            },
            bases=("metadata.dimension",),
        ),
        migrations.CreateModel(
            name="LivelihoodCategory",
            fields=[
                (
                    "dimension_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="metadata.dimension",
                    ),
                ),
            ],
            options={
                "verbose_name": "Livelihood Category",
                "verbose_name_plural": "Livelihood Category",
            },
            bases=("metadata.dimension",),
        ),
        migrations.CreateModel(
            name="LivestockType",
            fields=[
                (
                    "dimension_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="metadata.dimension",
                    ),
                ),
            ],
            options={
                "verbose_name": "Livestock Type",
                "verbose_name_plural": "Livestock Types",
            },
            bases=("metadata.dimension",),
        ),
        migrations.CreateModel(
            name="SeasonalActivityType",
            fields=[
                (
                    "dimension_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="metadata.dimension",
                    ),
                ),
                ("name", common.fields.NameField(max_length=60, verbose_name="Name")),
                (
                    "activity_category",
                    models.CharField(
                        choices=[
                            ("crop", "Crops"),
                            ("livestock", "Livestock"),
                            ("gardening", "Gardening"),
                            ("fishing", "Fishing"),
                        ],
                        max_length=20,
                        verbose_name="Activity Category",
                    ),
                ),
            ],
            options={
                "verbose_name": "Seasonal Activity Type",
                "verbose_name_plural": "Seasonal Activity Types",
            },
            bases=("metadata.dimension",),
        ),
        migrations.CreateModel(
            name="SourceSystem",
            fields=[
                (
                    "dimension_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="metadata.dimension",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("metadata.dimension",),
        ),
        migrations.CreateModel(
            name="TranslationType",
            fields=[
                (
                    "dimension_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="metadata.dimension",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("metadata.dimension",),
        ),
        migrations.CreateModel(
            name="WealthCategory",
            fields=[
                (
                    "dimension_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="metadata.dimension",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("metadata.dimension",),
        ),
        migrations.CreateModel(
            name="WealthCharacteristic",
            fields=[
                (
                    "dimension_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="metadata.dimension",
                    ),
                ),
                (
                    "variable_type",
                    models.CharField(
                        choices=[("float", "Numeric"), ("str", "String"), ("bool", "Boolean")],
                        default="str",
                        help_text="Whether the field is numeric, character, boolean, etc.",
                        verbose_name="Variable Type",
                    ),
                ),
            ],
            options={
                "verbose_name": "Wealth Group Characteristic",
                "verbose_name_plural": "Wealth Group Characteristics",
            },
            bases=("metadata.dimension",),
        ),
        migrations.CreateModel(
            name="Translation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.CharField()),
                (
                    "from_dimension",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="translations_from",
                        to="metadata.dimension",
                    ),
                ),
                (
                    "translation_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="translations_of_type",
                        to="metadata.dimension",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Season",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, verbose_name="Name")),
                ("description", models.TextField(max_length=255, verbose_name="Description")),
                (
                    "start_month",
                    models.IntegerField(
                        choices=[
                            (1, "January"),
                            (2, "February"),
                            (3, "March"),
                            (4, "April"),
                            (5, "May"),
                            (6, "June"),
                            (7, "July"),
                            (8, "August"),
                            (9, "September"),
                            (10, "October"),
                            (11, "November"),
                            (12, "December"),
                        ],
                        help_text="The typical first month of the Season",
                        verbose_name="Start Month",
                    ),
                ),
                (
                    "end_month",
                    models.IntegerField(
                        choices=[
                            (1, "January"),
                            (2, "February"),
                            (3, "March"),
                            (4, "April"),
                            (5, "May"),
                            (6, "June"),
                            (7, "July"),
                            (8, "August"),
                            (9, "September"),
                            (10, "October"),
                            (11, "November"),
                            (12, "December"),
                        ],
                        help_text="The typical end month of the Season",
                        verbose_name="End Month",
                    ),
                ),
                (
                    "alignment",
                    models.CharField(
                        choices=[("Start", "Start"), ("End", "End")],
                        default="End",
                        max_length=5,
                        verbose_name="Year alignment",
                    ),
                ),
                (
                    "order",
                    models.IntegerField(
                        help_text="The order of the Season with the Season Year", verbose_name="Order"
                    ),
                ),
                (
                    "rain_fall_record",
                    models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Rainfall record"),
                ),
                (
                    "country",
                    models.ForeignKey(
                        db_column="country_code",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="common.country",
                        verbose_name="Country",
                    ),
                ),
            ],
            options={
                "verbose_name": "Season",
                "verbose_name_plural": "Seasons",
            },
        ),
        migrations.AddField(
            model_name="dimension",
            name="dimension_type",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="metadata.dimensiontype"),
        ),
        migrations.CreateModel(
            name="Item",
            fields=[
                (
                    "dimension_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="metadata.dimension",
                    ),
                ),
                (
                    "kcals_per_unit",
                    models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Kcals per kg"),
                ),
                (
                    "input_unit_of_measure",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="common.unitofmeasure",
                        verbose_name="Input Unit of Measure",
                    ),
                ),
            ],
            options={
                "verbose_name": "Item",
                "verbose_name_plural": "Items",
            },
            bases=("metadata.dimension",),
        ),
        migrations.CreateModel(
            name="Alias",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("synonym", common.fields.NameField(max_length=60, verbose_name="Name")),
                ("dimension", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="metadata.dimension")),
                (
                    "source",
                    models.ForeignKey(
                        blank=True,
                        help_text="Optional filter for aliases specific to a source.",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="sources",
                        to="metadata.sourcesystem",
                        verbose_name="Source",
                    ),
                ),
            ],
        ),
    ]
