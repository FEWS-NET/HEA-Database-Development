import django.db.models.deletion
from django.db import migrations, models


def forwards(apps, schema_editor):
    # Delete all logs, because join to ImportRun is non-nullable.
    ScanLog = apps.get_model("ingestion", "ScanLog")
    ScanLog.objects.all().delete()
    ImportLog = apps.get_model("ingestion", "ImportLog")
    ImportLog.objects.all().delete()


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    # TODO: Squash migrations so that the defaults and table truncation are not necessary.

    dependencies = [
        ("ingestion", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
        migrations.RemoveField(
            model_name="scanlog",
            name="livelihood_zone_baseline",
        ),
        migrations.RemoveField(
            model_name="spreadsheetlocation",
            name="livelihood_zone_baseline",
        ),
        migrations.AddField(
            model_name="spreadsheetlocation",
            name="import_run",
            field=models.ForeignKey(
                default=1, on_delete=django.db.models.deletion.DO_NOTHING, to="ingestion.importrun"
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="importlog",
            name="import_run",
            field=models.ForeignKey(
                default=1, on_delete=django.db.models.deletion.DO_NOTHING, to="ingestion.importrun"
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="scanlog",
            name="import_run",
            field=models.ForeignKey(
                default=1, on_delete=django.db.models.deletion.DO_NOTHING, to="ingestion.importrun"
            ),
            preserve_default=False,
        ),
    ]
