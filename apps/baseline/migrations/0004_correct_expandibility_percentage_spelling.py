from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("baseline", "0003_add_community_full_name_and_code"),
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
