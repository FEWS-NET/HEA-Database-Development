# Generated by Django 5.1.1 on 2024-11-22 21:21

from django.db import migrations, models

import common.models


class Migration(migrations.Migration):

    dependencies = [
        ("baseline", "0017_alter_livelihoodactivity_percentage_kcals"),
    ]

    operations = [
        migrations.AlterField(
            model_name="livelihoodactivity",
            name="price",
            field=models.FloatField(
                blank=True,
                help_text="Price per unit",
                null=True,
                validators=[common.models.validate_positive],
                verbose_name="Price",
            ),
        ),
        migrations.AlterField(
            model_name="othercashincome",
            name="payment_per_time",
            field=models.FloatField(
                blank=True,
                help_text="Amount of money received each time the labor is performed",
                null=True,
                validators=[common.models.validate_positive],
                verbose_name="Payment per time",
            ),
        ),
        migrations.AlterField(
            model_name="paymentinkind",
            name="payment_per_time",
            field=models.FloatField(
                blank=True,
                help_text="Amount of item received each time the labor is performed",
                null=True,
                validators=[common.models.validate_positive],
                verbose_name="Payment per time",
            ),
        ),
    ]