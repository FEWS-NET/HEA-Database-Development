from pathlib import Path

from django.conf import settings
from django.db import migrations, models

from common.utils import LoadModelFromDict


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0001_initial"),
    ]

    operations = [
        LoadModelFromDict(model="Country", data=Path(__file__).with_suffix(".txt")),
    ]
