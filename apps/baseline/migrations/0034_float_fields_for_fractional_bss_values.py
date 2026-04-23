from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("baseline", "0033_add_annual_kcals_cost_function"),
    ]

    operations = [
        migrations.AlterField(
            model_name="foodpurchase",
            name="months_per_year",
            field=models.FloatField(
                blank=True,
                help_text="Number of months in a year that the product is purchased",
                null=True,
                verbose_name="Months per year",
            ),
        ),
        migrations.AlterField(
            model_name="foodpurchase",
            name="times_per_year",
            field=models.FloatField(
                blank=True,
                help_text="Number of times in a year that the purchase is made",
                null=True,
                verbose_name="Times per year",
            ),
        ),
        migrations.AlterField(
            model_name="othercashincome",
            name="people_per_household",
            field=models.FloatField(
                blank=True,
                help_text="Number of household members who perform the labor",
                null=True,
                verbose_name="People per household",
            ),
        ),
        migrations.AlterField(
            model_name="otherpurchase",
            name="months_per_year",
            field=models.FloatField(
                blank=True,
                help_text="Number of months in a year that the product is purchased",
                null=True,
                verbose_name="Months per year",
            ),
        ),
        migrations.AlterField(
            model_name="otherpurchase",
            name="times_per_year",
            field=models.FloatField(
                blank=True,
                help_text="Number of times in a year that the product is purchased",
                null=True,
                verbose_name="Times per year",
            ),
        ),
    ]
