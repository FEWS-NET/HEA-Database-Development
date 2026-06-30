from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("baseline", "0040_float_fields_months_per_year_times_per_year"),
    ]

    operations = [
        migrations.RenameField(
            model_name="livelihoodzonebaseline",
            old_name="main_livelihood_category",
            new_name="primary_livelihood_system",
        ),
        migrations.AlterField(
            model_name="livelihoodzonebaseline",
            name="primary_livelihood_system",
            field=models.ForeignKey(
                db_column="livelihood_system_code",
                on_delete=models.RESTRICT,
                to="metadata.livelihoodcategory",
                verbose_name="Livelihood Zone Type",
            ),
        ),
    ]
