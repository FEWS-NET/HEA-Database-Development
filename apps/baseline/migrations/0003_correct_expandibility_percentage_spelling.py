from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("baseline", "0002_rename_fields_and_db_columns"),
    ]

    operations = [
        migrations.RenameField(
            model_name="expandabilityfactor",
            old_name="percentge_consumed",
            new_name="percentage_consumed",
        ),
        migrations.RenameField(
            model_name="expandabilityfactor",
            old_name="precentage_income",
            new_name="percentage_income",
        ),
    ]
