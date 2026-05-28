from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("baseline", "0037_livelihoodactivity_sort_key_wealthgroup_idx"),
    ]

    operations = [
        migrations.CreateModel(
            name="OtherLivestockProduction",
            fields=[],
            options={
                "verbose_name": "Other Livestock Production",
                "verbose_name_plural": "Other Livestock Production",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("baseline.livelihoodactivity",),
        ),
        migrations.AlterField(
            model_name="livelihoodactivity",
            name="strategy_type",
            field=models.CharField(
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
                db_index=True,
                help_text="The type of livelihood strategy, such as crop production, or wild food gathering.",
                max_length=30,
                verbose_name="Strategy Type",
            ),
        ),
        migrations.AlterField(
            model_name="livelihoodstrategy",
            name="strategy_type",
            field=models.CharField(
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
                db_index=True,
                help_text="The type of livelihood strategy, such as crop production, or wild food gathering.",
                max_length=30,
                verbose_name="Strategy Type",
            ),
        ),
    ]
