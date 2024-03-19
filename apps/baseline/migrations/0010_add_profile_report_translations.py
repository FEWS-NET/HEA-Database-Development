from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("baseline", "0009_hunting_alter_livelihoodactivity_strategy_type_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="livelihoodzonebaseline",
            old_name="profile_report",
            new_name="profile_report_en",
        ),
        migrations.AddField(
            model_name="livelihoodzonebaseline",
            name="profile_report_ar",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="livelihoodzonebaseline/profile_report",
                verbose_name="Profile Report PDF file",
            ),
        ),
        migrations.AddField(
            model_name="livelihoodzonebaseline",
            name="profile_report_es",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="livelihoodzonebaseline/profile_report",
                verbose_name="Profile Report PDF file",
            ),
        ),
        migrations.AddField(
            model_name="livelihoodzonebaseline",
            name="profile_report_fr",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="livelihoodzonebaseline/profile_report",
                verbose_name="Profile Report PDF file",
            ),
        ),
        migrations.AddField(
            model_name="livelihoodzonebaseline",
            name="profile_report_pt",
            field=models.FileField(
                blank=True,
                null=True,
                upload_to="livelihoodzonebaseline/profile_report",
                verbose_name="Profile Report PDF file",
            ),
        ),
    ]
