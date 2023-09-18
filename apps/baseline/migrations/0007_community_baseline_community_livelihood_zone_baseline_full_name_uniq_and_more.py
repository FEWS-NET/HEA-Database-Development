# Generated by Django 4.2.4 on 2023-08-30 22:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("baseline", "0006_remove_community_interviewers_and_more"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="community",
            constraint=models.UniqueConstraint(
                fields=("livelihood_zone_baseline", "full_name"),
                name="baseline_community_livelihood_zone_baseline_full_name_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="livelihoodzonebaseline",
            constraint=models.UniqueConstraint(
                fields=("livelihood_zone", "reference_year_end_date"),
                name="baseline_livelihoodzonebaseline_livelihood_zone_reference_year_end_date_uniq",
            ),
        ),
        migrations.AddConstraint(
            model_name="wealthgroup",
            constraint=models.UniqueConstraint(
                fields=("livelihood_zone_baseline", "wealth_category", "community"),
                name="baseline_wealthgroup_livelihood_zone_baseline_wealth_category_community_uniq",
            ),
        ),
        migrations.AlterField(
            model_name="livelihoodzonebaseline",
            name="valid_from_date",
            field=models.DateField(
                blank=True,
                help_text="The first day of the month that this baseline is valid from",
                null=True,
                verbose_name="Valid From Date",
            ),
        ),
        migrations.AlterField(
            model_name="livelihoodzonebaseline",
            name="valid_to_date",
            field=models.DateField(
                blank=True,
                help_text="The last day of the month that this baseline is valid until",
                null=True,
                verbose_name="Valid To Date",
            ),
        ),
    ]