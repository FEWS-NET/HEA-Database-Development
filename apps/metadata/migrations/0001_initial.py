# Generated by Django 4.2.2 on 2023-06-16 09:04

import django.db.models.deletion
from django.db import migrations, models

import common.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DimensionType",
            fields=[
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
                (
                    "code",
                    common.fields.CodeField(max_length=60, primary_key=True, serialize=False, verbose_name="code"),
                ),
                ("name", common.fields.NameField(max_length=60, verbose_name="name")),
                (
                    "description",
                    common.fields.DescriptionField(
                        blank=True,
                        help_text="Any extra information or detail that is relevant to the object.",
                        max_length=2000,
                        verbose_name="description",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="UnitOfMeasure",
            fields=[
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
                (
                    "code",
                    common.fields.CodeField(max_length=60, primary_key=True, serialize=False, verbose_name="code"),
                ),
                ("name", common.fields.NameField(max_length=60, verbose_name="name")),
                (
                    "description",
                    common.fields.DescriptionField(
                        blank=True,
                        help_text="Any extra information or detail that is relevant to the object.",
                        max_length=2000,
                        verbose_name="description",
                    ),
                ),
                (
                    "dimension_type",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="metadata.dimensiontype"),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Currency",
            fields=[
                (
                    "unitofmeasure_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="metadata.unitofmeasure",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=("metadata.unitofmeasure",),
        ),
        migrations.CreateModel(
            name="WealthGroupAttributeType",
            fields=[
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
                (
                    "code",
                    common.fields.CodeField(max_length=60, primary_key=True, serialize=False, verbose_name="code"),
                ),
                ("name", common.fields.NameField(max_length=60, verbose_name="name")),
                (
                    "description",
                    common.fields.DescriptionField(
                        blank=True,
                        help_text="Any extra information or detail that is relevant to the object.",
                        max_length=2000,
                        verbose_name="description",
                    ),
                ),
                (
                    "dimension_type",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="metadata.dimensiontype"),
                ),
            ],
            options={
                "verbose_name": "Wealth Group Attribute Type",
                "verbose_name_plural": "Wealth Group Attribute Types",
            },
        ),
        migrations.CreateModel(
            name="WealthCategory",
            fields=[
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
                (
                    "code",
                    common.fields.CodeField(max_length=60, primary_key=True, serialize=False, verbose_name="code"),
                ),
                ("name", common.fields.NameField(max_length=60, verbose_name="name")),
                (
                    "description",
                    common.fields.DescriptionField(
                        blank=True,
                        help_text="Any extra information or detail that is relevant to the object.",
                        max_length=2000,
                        verbose_name="description",
                    ),
                ),
                (
                    "dimension_type",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="metadata.dimensiontype"),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="SeasonalActivityCategory",
            fields=[
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
                (
                    "code",
                    common.fields.CodeField(max_length=60, primary_key=True, serialize=False, verbose_name="code"),
                ),
                ("name", common.fields.NameField(max_length=60, verbose_name="name")),
                (
                    "description",
                    common.fields.DescriptionField(
                        blank=True,
                        help_text="Any extra information or detail that is relevant to the object.",
                        max_length=2000,
                        verbose_name="description",
                    ),
                ),
                (
                    "dimension_type",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="metadata.dimensiontype"),
                ),
            ],
            options={
                "verbose_name": "Seasonal Activity Category",
                "verbose_name_plural": "Seasonal Activity Categories",
            },
        ),
        migrations.CreateModel(
            name="LivestockType",
            fields=[
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
                (
                    "code",
                    common.fields.CodeField(max_length=60, primary_key=True, serialize=False, verbose_name="code"),
                ),
                ("name", common.fields.NameField(max_length=60, verbose_name="name")),
                (
                    "description",
                    common.fields.DescriptionField(
                        blank=True,
                        help_text="Any extra information or detail that is relevant to the object.",
                        max_length=2000,
                        verbose_name="description",
                    ),
                ),
                (
                    "dimension_type",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="metadata.dimensiontype"),
                ),
            ],
            options={
                "verbose_name": "Livestock Type",
                "verbose_name_plural": "Livestock Types",
            },
        ),
        migrations.CreateModel(
            name="LivelihoodCategory",
            fields=[
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
                (
                    "code",
                    common.fields.CodeField(max_length=60, primary_key=True, serialize=False, verbose_name="code"),
                ),
                ("name", common.fields.NameField(max_length=60, verbose_name="name")),
                (
                    "description",
                    common.fields.DescriptionField(
                        blank=True,
                        help_text="Any extra information or detail that is relevant to the object.",
                        max_length=2000,
                        verbose_name="description",
                    ),
                ),
                (
                    "dimension_type",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="metadata.dimensiontype"),
                ),
            ],
            options={
                "verbose_name": "Livelihood Category",
                "verbose_name_plural": "Livelihood Category",
            },
        ),
        migrations.CreateModel(
            name="Item",
            fields=[
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
                (
                    "code",
                    common.fields.CodeField(max_length=60, primary_key=True, serialize=False, verbose_name="code"),
                ),
                ("name", common.fields.NameField(max_length=60, verbose_name="name")),
                (
                    "description",
                    common.fields.DescriptionField(
                        blank=True,
                        help_text="Any extra information or detail that is relevant to the object.",
                        max_length=2000,
                        verbose_name="description",
                    ),
                ),
                (
                    "dimension_type",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="metadata.dimensiontype"),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="IncomeSource",
            fields=[
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
                (
                    "code",
                    common.fields.CodeField(max_length=60, primary_key=True, serialize=False, verbose_name="code"),
                ),
                ("name", common.fields.NameField(max_length=60, verbose_name="name")),
                (
                    "description",
                    common.fields.DescriptionField(
                        blank=True,
                        help_text="Any extra information or detail that is relevant to the object.",
                        max_length=2000,
                        verbose_name="description",
                    ),
                ),
                (
                    "dimension_type",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="metadata.dimensiontype"),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="HazardCateogy",
            fields=[
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
                (
                    "code",
                    common.fields.CodeField(max_length=60, primary_key=True, serialize=False, verbose_name="code"),
                ),
                ("name", common.fields.NameField(max_length=60, verbose_name="name")),
                (
                    "description",
                    common.fields.DescriptionField(
                        blank=True,
                        help_text="Any extra information or detail that is relevant to the object.",
                        max_length=2000,
                        verbose_name="description",
                    ),
                ),
                (
                    "dimension_type",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="metadata.dimensiontype"),
                ),
            ],
            options={
                "verbose_name": "Hazard Category",
                "verbose_name_plural": "Hazard Categories",
            },
        ),
        migrations.CreateModel(
            name="FoodSource",
            fields=[
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
                (
                    "code",
                    common.fields.CodeField(max_length=60, primary_key=True, serialize=False, verbose_name="code"),
                ),
                ("name", common.fields.NameField(max_length=60, verbose_name="name")),
                (
                    "description",
                    common.fields.DescriptionField(
                        blank=True,
                        help_text="Any extra information or detail that is relevant to the object.",
                        max_length=2000,
                        verbose_name="description",
                    ),
                ),
                (
                    "dimension_type",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="metadata.dimensiontype"),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ExpenditureCategory",
            fields=[
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
                (
                    "code",
                    common.fields.CodeField(max_length=60, primary_key=True, serialize=False, verbose_name="code"),
                ),
                ("name", common.fields.NameField(max_length=60, verbose_name="name")),
                (
                    "description",
                    common.fields.DescriptionField(
                        blank=True,
                        help_text="Any extra information or detail that is relevant to the object.",
                        max_length=2000,
                        verbose_name="description",
                    ),
                ),
                (
                    "dimension_type",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="metadata.dimensiontype"),
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
                (
                    "code",
                    common.fields.CodeField(max_length=60, primary_key=True, serialize=False, verbose_name="code"),
                ),
                ("name", common.fields.NameField(max_length=60, verbose_name="name")),
                (
                    "description",
                    common.fields.DescriptionField(
                        blank=True,
                        help_text="Any extra information or detail that is relevant to the object.",
                        max_length=2000,
                        verbose_name="description",
                    ),
                ),
                (
                    "dimension_type",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="metadata.dimensiontype"),
                ),
            ],
            options={
                "verbose_name": "Crop Type",
                "verbose_name_plural": "Crop Types",
            },
        ),
    ]
