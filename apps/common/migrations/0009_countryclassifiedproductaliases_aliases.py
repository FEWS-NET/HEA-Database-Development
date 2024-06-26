# Generated by Django 5.0.4 on 2024-04-15 22:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0008_load_classified_product"),
    ]

    operations = [
        migrations.AddField(
            model_name="countryclassifiedproductaliases",
            name="aliases",
            field=models.JSONField(
                default=[], help_text="A list of alternate names for the product.", verbose_name="aliases"
            ),
            preserve_default=False,
        ),
    ]
