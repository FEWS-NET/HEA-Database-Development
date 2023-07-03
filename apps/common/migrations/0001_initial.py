# Generated by Django 4.2.2 on 2023-07-03 23:07

import common.fields
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ClassifiedProduct",
            fields=[
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="modified"
                    ),
                ),
                ("path", models.CharField(max_length=255, unique=True)),
                ("depth", models.PositiveIntegerField()),
                ("numchild", models.PositiveIntegerField(default=0)),
                (
                    "cpcv2",
                    models.CharField(
                        help_text="classification structure of products based on the UN’s Central Product Classification rules, prefixed with R, L, P or S, a letter indicating whether the Product is Raw agricultural output, Live animals, a Processed product or a Service.",
                        max_length=8,
                        primary_key=True,
                        serialize=False,
                        verbose_name="CPC V2",
                    ),
                ),
                ("description", models.CharField(max_length=800, verbose_name="description")),
                ("common_name", common.fields.NameField(blank=True, max_length=60, verbose_name="common name")),
                (
                    "scientific_name",
                    models.CharField(blank=True, max_length=100, null=True, verbose_name="scientific name"),
                ),
            ],
            options={
                "verbose_name": "Product",
                "verbose_name_plural": "Products",
                "ordering": (),
            },
        ),
        migrations.CreateModel(
            name="Country",
            fields=[
                (
                    "iso3166a2",
                    models.CharField(
                        max_length=2, primary_key=True, serialize=False, verbose_name="ISO 3166-1 Alpha-2"
                    ),
                ),
                ("name", common.fields.NameField(max_length=200, unique=True, verbose_name="Name")),
                ("iso3166a3", models.CharField(max_length=3, unique=True, verbose_name="ISO 3166-1 Alpha-3")),
                (
                    "iso3166n3",
                    models.IntegerField(
                        blank=True,
                        null=True,
                        unique=True,
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(999),
                        ],
                        verbose_name="ISO 3166-1 Numeric",
                    ),
                ),
                (
                    "iso_en_name",
                    models.CharField(
                        help_text="The name of the Country approved by the ISO 3166 Maintenance Agency with accented characters replaced by their ASCII equivalents",
                        max_length=200,
                        unique=True,
                        verbose_name="ISO English ASCII name",
                    ),
                ),
                (
                    "iso_en_proper",
                    models.CharField(
                        help_text="The full formal name of the Country approved by the ISO 3166 Maintenance Agency with accented characters replaced by their ASCII equivalents",
                        max_length=200,
                        verbose_name="ISO English ASCII full name",
                    ),
                ),
                (
                    "iso_en_ro_name",
                    models.CharField(
                        help_text="The name of the Country approved by the ISO 3166 Maintenance Agency",
                        max_length=200,
                        unique=True,
                        verbose_name="ISO English name",
                    ),
                ),
                (
                    "iso_en_ro_proper",
                    models.CharField(
                        help_text="The full formal name of the Country approved by the ISO 3166 Maintenance Agency",
                        max_length=200,
                        verbose_name="ISO English full name",
                    ),
                ),
                (
                    "iso_fr_name",
                    models.CharField(
                        help_text="The name in French of the Country approved by the ISO 3166 Maintenance Agency",
                        max_length=200,
                        verbose_name="ISO French name",
                    ),
                ),
                (
                    "iso_fr_proper",
                    models.CharField(
                        help_text="The full formal name in French of the Country approved by the ISO 3166 Maintenance Agency",
                        max_length=200,
                        verbose_name="ISO French full name",
                    ),
                ),
                (
                    "iso_es_name",
                    models.CharField(
                        help_text="The name in Spanish of the Country approved by the ISO 3166 Maintenance Agency",
                        max_length=200,
                        verbose_name="ISO Spanish name",
                    ),
                ),
            ],
            options={
                "verbose_name": "Country",
                "verbose_name_plural": "Countries",
            },
        ),
        migrations.CreateModel(
            name="Currency",
            fields=[
                (
                    "iso4217a3",
                    models.CharField(
                        max_length=20, primary_key=True, serialize=False, verbose_name="ISO 4217 Alpha-3"
                    ),
                ),
                (
                    "iso4217n3",
                    models.IntegerField(blank=True, null=True, unique=True, verbose_name="ISO 4217 Numeric"),
                ),
                ("iso_en_name", models.CharField(max_length=200, verbose_name="name")),
            ],
            options={
                "verbose_name": "Currency",
                "verbose_name_plural": "Currencies",
            },
        ),
        migrations.CreateModel(
            name="UnitOfMeasure",
            fields=[
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="modified"
                    ),
                ),
                (
                    "abbreviation",
                    models.CharField(max_length=12, primary_key=True, serialize=False, verbose_name="abbreviation"),
                ),
                (
                    "unit_type",
                    models.CharField(
                        choices=[
                            ("Weight", "Weight"),
                            ("Volume", "Volume"),
                            ("Item", "Item"),
                            ("Area", "Area"),
                            ("Yield", "Yield"),
                            ("Percentage", "Percentage"),
                            ("Length", "Length"),
                        ],
                        max_length=10,
                        verbose_name="unit type",
                    ),
                ),
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
                "verbose_name": "Unit of Measure",
                "verbose_name_plural": "Units of Measure",
            },
        ),
        migrations.CreateModel(
            name="UnitOfMeasureConversion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="modified"
                    ),
                ),
                (
                    "conversion_factor",
                    models.DecimalField(decimal_places=12, max_digits=38, verbose_name="conversion factor"),
                ),
                (
                    "from_unit",
                    models.ForeignKey(
                        db_column="from_unit_code",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="from_conversions",
                        to="common.unitofmeasure",
                        verbose_name="from unit",
                    ),
                ),
                (
                    "to_unit",
                    models.ForeignKey(
                        db_column="to_unit_code",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="to_conversions",
                        to="common.unitofmeasure",
                        verbose_name="to unit",
                    ),
                ),
            ],
            options={
                "verbose_name": "Unit of Measure Conversion",
                "verbose_name_plural": "Unit of Measure Conversions",
            },
        ),
        migrations.CreateModel(
            name="CountryClassifiedProductAliases",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="modified"
                    ),
                ),
                (
                    "country",
                    models.ForeignKey(
                        db_column="country_code",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="common.country",
                        verbose_name="country",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        db_column="product_code",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="per_country_aliases",
                        to="common.classifiedproduct",
                        verbose_name="product",
                    ),
                ),
            ],
            options={
                "verbose_name": "Country Classified Product Alias",
                "verbose_name_plural": "Country Classified Product Aliases",
            },
        ),
        migrations.AddConstraint(
            model_name="unitofmeasureconversion",
            constraint=models.UniqueConstraint(
                fields=("from_unit", "to_unit"), name="common_unitofmeasureconv_from_unit_code_to_unit_code_uniq"
            ),
        ),
        migrations.AddConstraint(
            model_name="countryclassifiedproductaliases",
            constraint=models.UniqueConstraint(
                fields=("country", "product"), name="common_countryclassified_country_code_product_code_uniq"
            ),
        ),
    ]
