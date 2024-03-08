from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("baseline", "0010_add_profile_report_translations"),
    ]

    operations = [
        migrations.AddField(
            model_name="livelihoodzonebaseline",
            name="bss_language",
            field=models.CharField(
                blank=True,
                choices=[
                    ("en", "English"),
                    ("fr", "French"),
                    ("es", "Spanish"),
                    ("pt", "Portuguese"),
                    ("ar", "Arabic"),
                ],
                max_length=10,
                null=True,
                verbose_name="BSS Language",
            ),
        ),
    ]
