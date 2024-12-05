import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
from django.db import migrations, models

import common.fields


class Migration(migrations.Migration):
    dependencies = [
        ("baseline", "0016_alter_livelihoodstrategy_additional_identifier_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="KeyParameter",
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
                    "strategy_type",
                    models.CharField(
                        choices=[
                            ("MilkProduction", "Milk Production"),
                            ("ButterProduction", "Butter Production"),
                            ("MeatProduction", "Meat Production"),
                            ("LivestockSale", "Livestock Sale"),
                            ("CropProduction", "Crop Production"),
                            ("FoodPurchase", "Food Purchase"),
                            ("PaymentInKind", "Payment in Kind"),
                            ("ReliefGiftOther", "Relief, Gift or Other Food"),
                            ("Hunting", "Hunting"),
                            ("Fishing", "Fishing"),
                            ("WildFoodGathering", "Wild Food Gathering"),
                            ("OtherCashIncome", "Other Cash Income"),
                            ("OtherPurchase", "Other Purchase"),
                        ],
                        db_index=True,
                        help_text="The type of livelihood strategy, such as crop production, or wild food gathering.",
                        max_length=30,
                        verbose_name="Strategy Type",
                    ),
                ),
                (
                    "key_parameter_type",
                    models.CharField(
                        choices=[("price", "Price"), ("quantity", "Quantity")],
                        help_text="The type of key parameter, such as quantity or price.",
                        max_length=30,
                        verbose_name="Key Parameter Type",
                    ),
                ),
                ("name_en", common.fields.NameField(max_length=200, verbose_name="Name")),
                ("name_fr", common.fields.NameField(blank=True, max_length=200, verbose_name="Name")),
                ("name_es", common.fields.NameField(blank=True, max_length=200, verbose_name="Name")),
                ("name_pt", common.fields.NameField(blank=True, max_length=200, verbose_name="Name")),
                ("name_ar", common.fields.NameField(blank=True, max_length=200, verbose_name="Name")),
                (
                    "description_en",
                    common.fields.DescriptionField(
                        blank=True,
                        help_text="Any extra information or detail that is relevant to the object.",
                        max_length=2000,
                        verbose_name="Description",
                    ),
                ),
                (
                    "description_fr",
                    common.fields.DescriptionField(
                        blank=True,
                        help_text="Any extra information or detail that is relevant to the object.",
                        max_length=2000,
                        verbose_name="Description",
                    ),
                ),
                (
                    "description_es",
                    common.fields.DescriptionField(
                        blank=True,
                        help_text="Any extra information or detail that is relevant to the object.",
                        max_length=2000,
                        verbose_name="Description",
                    ),
                ),
                (
                    "description_pt",
                    common.fields.DescriptionField(
                        blank=True,
                        help_text="Any extra information or detail that is relevant to the object.",
                        max_length=2000,
                        verbose_name="Description",
                    ),
                ),
                (
                    "description_ar",
                    common.fields.DescriptionField(
                        blank=True,
                        help_text="Any extra information or detail that is relevant to the object.",
                        max_length=2000,
                        verbose_name="Description",
                    ),
                ),
                (
                    "livelihood_zone_baseline",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="baseline.livelihoodzonebaseline",
                        verbose_name="Livelihood Zone Baseline",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
