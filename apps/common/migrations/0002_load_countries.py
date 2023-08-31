import os.path

from django.conf import settings
from django.db import migrations, models

from common.utils import ConditionalLoadModelFromDict


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0001_initial"),
    ]

    operations = [
        ConditionalLoadModelFromDict(
            model="Country",
            data=os.path.splitext(os.path.abspath(__file__))[0] + ".txt",
            skip="test" in settings.DATABASES["default"]["NAME"],
        ),
    ]
