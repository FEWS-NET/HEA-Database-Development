import os.path

from django.conf import settings
from django.db import migrations, models

from common.utils import LoadModelFromDict


def forwards(apps, schema_editor):
    # To avoid running migrations in tests
    if "test" not in settings.DATABASES["default"]["NAME"]:
        LoadModelFromDict(model="Country", data=os.path.splitext(os.path.abspath(__file__))[0] + ".txt"),


def backwards(apps, schema_editor):
    Country = apps.get_model("common", "Country")
    Country.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
