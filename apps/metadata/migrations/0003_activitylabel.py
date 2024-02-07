# Generated by Django 4.2.4 on 2024-02-01 23:35

import common.fields
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0008_load_classified_product"),
        ("metadata", "0002_add_translation_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="ActivityLabel",
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
                ("activity_label", common.fields.NameField(max_length=60, unique=True, verbose_name="Activity Label")),
                (
                    "is_start",
                    models.BooleanField(
                        default=False,
                        help_text="Indicates whether this Activity Label marks the start of a new Livelihood Strategy",
                        verbose_name="Is Start?",
                    ),
                ),
                (
                    "strategy_type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("MilkProduction", "Milk Production"),
                            ("ButterProduction", "Butter Production"),
                            ("MeatProduction", "Meat Production"),
                            ("LivestockSale", "Livestock Sale"),
                            ("CropProduction", "Crop Production"),
                            ("FoodPurchase", "Food Purchase"),
                            ("PaymentInKind", "Payment in Kind"),
                            ("ReliefGiftOther", "Relief, Gift or Other Food"),
                            ("Fishing", "Fishing"),
                            ("WildFoodGathering", "Wild Food Gathering"),
                            ("OtherCashIncome", "Other Cash Income"),
                            ("OtherPurchase", "Other Purchase"),
                        ],
                        help_text="The type of livelihood strategy, such as crop production, or wild food gathering.",
                        max_length=30,
                        verbose_name="Strategy Type",
                    ),
                ),
                ("season", models.CharField(blank=True, max_length=60, verbose_name="Season")),
                ("additional_identifier", models.CharField(blank=True, max_length=60, verbose_name="Season")),
                ("attribute", models.CharField(blank=True, max_length=60, verbose_name="Attribute")),
                (
                    "product",
                    models.ForeignKey(
                        blank=True,
                        db_column="product_code",
                        null=True,
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="activity_labels",
                        to="common.classifiedproduct",
                        verbose_name="Product",
                    ),
                ),
                (
                    "unit_of_measure",
                    models.ForeignKey(
                        blank=True,
                        db_column="unit_code",
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="activity_labels",
                        to="common.unitofmeasure",
                        verbose_name="Unit of Measure",
                    ),
                ),
            ],
            options={
                "verbose_name": "Activity Label",
                "verbose_name_plural": "Activity Labels",
            },
        ),
    ]
