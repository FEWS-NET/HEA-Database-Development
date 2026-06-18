from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("baseline", "0039_othercashincome_times_per_year_float"),
    ]

    operations = [
        migrations.AlterField(
            model_name="paymentinkind",
            name="months_per_year",
            field=models.FloatField(
                blank=True,
                null=True,
                verbose_name="Months per year",
                help_text="Number of months in a year that the labor is performed",
            ),
        ),
        migrations.AlterField(
            model_name="paymentinkind",
            name="times_per_year",
            field=models.FloatField(
                blank=True,
                null=True,
                verbose_name="Times per year",
                help_text="Number of times in a year that the labor is performed",
            ),
        ),
        migrations.AlterField(
            model_name="reliefgiftother",
            name="months_per_year",
            field=models.FloatField(
                blank=True,
                null=True,
                verbose_name="Months per year",
                help_text="Number of months in a year that the item is received",
            ),
        ),
        migrations.AlterField(
            model_name="reliefgiftother",
            name="times_per_year",
            field=models.FloatField(
                blank=True,
                null=True,
                verbose_name="Times per year",
                help_text="Number of times in a year that the item is received",
            ),
        ),
        migrations.AlterField(
            model_name="othercashincome",
            name="months_per_year",
            field=models.FloatField(
                blank=True,
                null=True,
                verbose_name="Months per year",
                help_text="Number of months in a year that the labor is performed",
            ),
        ),
    ]
