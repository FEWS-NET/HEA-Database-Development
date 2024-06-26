# Generated by Django 5.0.2 on 2024-03-06 13:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("baseline", "0008_livelihoodactivity_extra"),
    ]

    operations = [
        migrations.CreateModel(
            name="Hunting",
            fields=[],
            options={
                "verbose_name": "Hunting",
                "verbose_name_plural": "Hunting",
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
