from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("metadata", "0019_other_livestock_production"),
        ("baseline", "0042_rename_main_livelihood_category"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="LivelihoodCategory",
            new_name="LivelihoodSystem",
        ),
        migrations.AlterModelOptions(
            name="livelihoodsystem",
            options={"verbose_name": "Livelihood System", "verbose_name_plural": "Livelihood Systems"},
        ),
        migrations.AlterField(
            model_name="livelihoodsystem",
            name="color",
            field=models.CharField(
                default="#FFFFFF",
                help_text="Color hex value code for the Livelihood System.",
                max_length=7,
                verbose_name="Color",
            ),
        ),
        migrations.AlterModelTable(
            name="livelihoodsystem",
            table="metadata_livelihoodsystem",
        ),
    ]
