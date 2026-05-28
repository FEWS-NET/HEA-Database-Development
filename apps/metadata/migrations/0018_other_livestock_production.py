from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("metadata", "0017_seasonalactivitytype_has_product_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="activitylabel",
            name="strategy_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("MilkProduction", "Milk Production"),
                    ("ButterProduction", "Butter Production"),
                    ("MeatProduction", "Meat Production"),
                    ("LivestockSale", "Livestock Sale"),
                    ("OtherLivestockProduction", "Other Livestock Production"),
                    ("CropProduction", "Crop Production"),
                    ("FoodPurchase", "Food Purchase"),
                    ("PaymentInKind", "Payment in Kind"),
                    ("ReliefGiftOther", "Relief, Gift or Other Food"),
                    ("Hunting", "Hunting"),
                    ("Fishing", "Fishing"),
                    ("WildFoodGathering", "Wild Food Gathering"),
                    ("OtherCashIncome", "Other Cash Income"),
                    ("OtherPurchase", "Other Purchase"),
                    ("LivestockProduction", "Livestock Production"),
                ],
                help_text="The type of livelihood strategy, such as crop production, or wild food gathering.",
                max_length=30,
                verbose_name="Strategy Type",
            ),
        ),
        migrations.AlterField(
            model_name="season",
            name="purpose",
            field=models.CharField(
                blank=True,
                choices=[
                    ("MilkProduction", "Milk Production"),
                    ("ButterProduction", "Butter Production"),
                    ("MeatProduction", "Meat Production"),
                    ("LivestockSale", "Livestock Sale"),
                    ("OtherLivestockProduction", "Other Livestock Production"),
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
                help_text="The Livelihood Strategy Type that this Season is relevant for.",
                max_length=30,
                null=True,
                verbose_name="Purpose",
            ),
        ),
    ]
