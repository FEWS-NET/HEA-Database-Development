import os.path

from django.db import migrations

from common.utils import LoadModelFromDict


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0002_load_countries"),
    ]

    operations = [
        LoadModelFromDict(model="Currency", data=os.path.splitext(os.path.abspath(__file__))[0] + ".txt"),
    ]
