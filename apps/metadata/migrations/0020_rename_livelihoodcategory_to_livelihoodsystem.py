from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("metadata", "0019_other_livestock_production"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="LivelihoodCategory",
            new_name="LivelihoodSystem",
        ),
        migrations.AlterModelTable(
            name="livelihoodsystem",
            table="metadata_livelihoodsystem",
        ),
    ]
