from pathlib import Path

from django.conf import settings
from django.db import migrations, models

from common.utils import LoadModelFromDict


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0002_load_countries"),
    ]

    operations = [
        LoadModelFromDict(model="Currency", data=Path(__file__).with_suffix(".txt")),
    ]
