# Generated by Django 4.2.4 on 2023-10-17 05:53

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0004_alter_classifiedproduct"),
    ]

    operations = [
        migrations.RenameField(
            model_name="classifiedproduct",
            old_name="cpcv2",
            new_name="cpc",
        ),
        migrations.AlterField(
            model_name="classifiedproduct",
            name="cpc",
            field=models.CharField(
                help_text="classification structure of products based on version 2.1 of the UN’s Central Product Classification rules, prefixed with R, L, P or S, a letter indicating whether the Product is Raw agricultural output, Live animals, a Processed product or a Service.",
                max_length=8,
                primary_key=True,
                serialize=False,
                verbose_name="CPC v2.1",
            ),
        ),
        migrations.AddField(
            model_name="classifiedproduct",
            name="cpcv2",
            field=models.JSONField(
                blank=True,
                null=True,
                help_text="classification structure of products based on version 2 of the UN’s Central Product Classification rules, prefixed with R, L, P or S, a letter indicating whether the Product is Raw agricultural output, Live animals, a Processed product or a Service.",
                verbose_name="CPC v2",
            ),
        ),
        migrations.AddField(
            model_name="unitofmeasure",
            name="aliases",
            field=models.JSONField(
                blank=True, help_text="A list of alternate names for the product.", null=True, verbose_name="aliases"
            ),
        ),
    ]
