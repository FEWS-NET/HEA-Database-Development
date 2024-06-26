# Generated by Django 4.2.7 on 2024-02-09 21:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("metadata", "0002_add_translation_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="season",
            name="aliases",
            field=models.JSONField(
                blank=True, help_text="A list of alternate names for the Season.", null=True, verbose_name="aliases"
            ),
        ),
        migrations.AlterField(
            model_name="season",
            name="name_ar",
            field=models.CharField(blank=True, max_length=100, verbose_name="Name"),
        ),
        migrations.AlterField(
            model_name="season",
            name="name_en",
            field=models.CharField(max_length=100, unique=True, verbose_name="Name"),
        ),
        migrations.AlterField(
            model_name="season",
            name="name_es",
            field=models.CharField(blank=True, max_length=100, verbose_name="Name"),
        ),
        migrations.AlterField(
            model_name="season",
            name="name_fr",
            field=models.CharField(blank=True, max_length=100, verbose_name="Name"),
        ),
        migrations.AlterField(
            model_name="season",
            name="name_pt",
            field=models.CharField(blank=True, max_length=100, verbose_name="Name"),
        ),
    ]
