from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("baseline", "0038_other_livestock_production"),
    ]

    operations = [
        migrations.AlterField(
            model_name="othercashincome",
            name="times_per_year",
            field=models.FloatField(
                blank=True,
                help_text="Number of times in a year that the income is received",
                null=True,
                verbose_name="Times per year",
            ),
        ),
    ]
