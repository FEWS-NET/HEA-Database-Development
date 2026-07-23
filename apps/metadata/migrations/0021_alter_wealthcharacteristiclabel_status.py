from django.db import migrations, models


def forwards(apps, schema_editor):
    WealthCharacteristicLabel = apps.get_model("metadata", "WealthCharacteristicLabel")
    WealthCharacteristicLabel.objects.filter(
        status__isnull=True,
        wealth_characteristic__isnull=True,
    ).update(status="Ignore")


def backwards(apps, schema_editor):
    WealthCharacteristicLabel = apps.get_model("metadata", "WealthCharacteristicLabel")
    WealthCharacteristicLabel.objects.filter(status="Ignore").update(status=None)


class Migration(migrations.Migration):

    dependencies = [
        ("metadata", "0020_rename_livelihoodcategory_to_livelihoodsystem"),
    ]

    operations = [
        migrations.AlterField(
            model_name="wealthcharacteristiclabel",
            name="status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("Complete", "Complete"),
                    ("Discussion", "Under Discussion"),
                    ("Correct BSS", "Correct the BSS"),
                    ("Ignore", "Ignore this label and associated data in the row"),
                ],
                max_length=20,
                verbose_name="Status",
            ),
        ),
        migrations.RunPython(forwards, backwards),
    ]
