import django.utils.timezone
import model_utils.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("baseline", "0006_livelihoodzone_alternate_code"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="BssValueExtractor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="modified"
                    ),
                ),
                ("app_label", models.CharField()),
                ("model", models.CharField()),
                ("field", models.CharField()),
                (
                    "find_field",
                    models.BooleanField(
                        default=False,
                        help_text="True if the scan was looking for a field name alias, eg, 'Quantity Produced' for LivelihoodActivity.quantity_produced, as opposed to a value to be stored in that field.",
                    ),
                ),
                (
                    "regex",
                    models.CharField(
                        blank=True,
                        help_text='Put the text ALIAS in the regex where the alias should be injected. All occurrences will be replaced. To match any chars, `(`, maybe spaces, alias, maybe spaces, `)`, any chars, use: ".+\\(\\s*ALIAS\\s*\\).*". It will return None and not log anything if no value is extracted. It will concatenate multiple matches if found and log a warning.If no regex is needed, then no BssValueExtractor is needed, and the full cell contents will be matched.(Identical behaviour to regex being an empty string.)',
                    ),
                ),
            ],
            options={
                "verbose_name": "BSS Value Extractor",
                "verbose_name_plural": "BSS Value Extractors",
            },
        ),
        migrations.CreateModel(
            name="ChoiceAlias",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="modified"
                    ),
                ),
                ("app_label", models.CharField()),
                ("model", models.CharField()),
                ("field", models.CharField()),
                ("code", models.CharField()),
                ("alias", models.CharField(blank=True)),
            ],
            options={
                "verbose_name": "Choice Alias",
                "verbose_name_plural": "Choice Aliases",
            },
        ),
        migrations.CreateModel(
            name="FieldNameAlias",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="modified"
                    ),
                ),
                ("app_label", models.CharField()),
                ("model", models.CharField()),
                ("field", models.CharField()),
                ("alias", models.CharField(blank=True)),
            ],
            options={
                "verbose_name": "Field Name Alias",
                "verbose_name_plural": "Field Name Aliases",
            },
        ),
        migrations.CreateModel(
            name="SpreadsheetLocation",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="modified"
                    ),
                ),
                ("app_label", models.CharField()),
                ("model", models.CharField()),
                ("field", models.CharField()),
                (
                    "find_field",
                    models.BooleanField(
                        default=False,
                        help_text="True if the scan was looking for a field name alias, eg, 'Quantity Produced' for LivelihoodActivity.quantity_produced, as opposed to a value to be stored in that field.",
                    ),
                ),
                ("sheet_name", models.CharField()),
                ("column", models.PositiveIntegerField()),
                ("row", models.PositiveIntegerField()),
                ("regex", models.CharField(blank=True)),
                (
                    "alias",
                    models.CharField(
                        blank=True, help_text="Alias that successfully matched the source value.", null=True
                    ),
                ),
                ("source_value", models.CharField(blank=True)),
                ("matching_re", models.CharField(blank=True)),
                (
                    "mapped_value",
                    models.JSONField(
                        blank=True,
                        help_text="A string, integer, decimal, choice key, string id or integer id.",
                        null=True,
                    ),
                ),
                ("instance_number", models.PositiveIntegerField(blank=True, null=True)),
                ("object_id", models.CharField(blank=True, null=True)),
                (
                    "bss_value_extractor",
                    models.ForeignKey(
                        blank=True,
                        help_text="The extractor used to parse the cell value. Null if no extractor was used and the whole value was used.",
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="ingestion.bssvalueextractor",
                    ),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="contenttypes.contenttype",
                    ),
                ),
                (
                    "livelihood_zone_baseline",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING, to="baseline.livelihoodzonebaseline"
                    ),
                ),
            ],
            options={
                "verbose_name": "Spreadsheet Location",
                "verbose_name_plural": "Spreadsheet Locations",
            },
        ),
        migrations.CreateModel(
            name="ScanLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="modified"
                    ),
                ),
                ("sheet_name", models.CharField()),
                ("column", models.PositiveIntegerField()),
                ("row", models.PositiveIntegerField()),
                ("app_label", models.CharField()),
                ("model", models.CharField()),
                ("field", models.CharField()),
                (
                    "find_field",
                    models.BooleanField(
                        default=False,
                        help_text="True if the scan was looking for a field name alias, eg, 'Quantity Produced' for LivelihoodActivity.quantity_produced, as opposed to a value to be stored in that field.",
                    ),
                ),
                ("source_value", models.CharField(blank=True)),
                (
                    "alias",
                    models.CharField(
                        blank=True, help_text="Alias that successfully matched the source value.", null=True
                    ),
                ),
                (
                    "regex",
                    models.CharField(
                        blank=True,
                        help_text="The Regex that successfully matched the source value. Duplicated here in case regex is updated on BssVlueExtractor.",
                        null=True,
                    ),
                ),
                (
                    "matching_re",
                    models.CharField(
                        blank=True,
                        help_text="The regex with the alias injected that successfully matched the source value.",
                        null=True,
                    ),
                ),
                (
                    "mapped_value",
                    models.JSONField(
                        blank=True,
                        help_text="The value, such as choice value, foreign key or plain value, that the source value matched. A string, integer, decimal, choice key, string id or integer id.",
                        null=True,
                    ),
                ),
                (
                    "bss_value_extractor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="ingestion.bssvalueextractor",
                    ),
                ),
                (
                    "livelihood_zone_baseline",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING, to="baseline.livelihoodzonebaseline"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ImportRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="modified"
                    ),
                ),
                (
                    "livelihood_zone_baseline",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.DO_NOTHING, to="baseline.livelihoodzonebaseline"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ImportLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="created"
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name="modified"
                    ),
                ),
                (
                    "log_level",
                    models.IntegerField(
                        choices=[
                            (0, "Not Set"),
                            (10, "Debug"),
                            (20, "Info"),
                            (30, "Warn"),
                            (40, "Error"),
                            (50, "Critical"),
                        ],
                        default=0,
                        verbose_name="Log Level",
                    ),
                ),
                ("message", models.TextField()),
                ("instance", models.JSONField(blank=True, null=True)),
                ("sheet_name", models.CharField(blank=True, null=True)),
                ("column", models.PositiveIntegerField(blank=True, null=True)),
                ("row", models.PositiveIntegerField(blank=True, null=True)),
                ("app_label", models.CharField(blank=True, null=True)),
                ("model", models.CharField(blank=True, null=True)),
                ("field", models.CharField(blank=True, null=True)),
                ("source_value", models.CharField(blank=True, null=True)),
                ("matching_re", models.CharField(blank=True, null=True)),
                (
                    "mapped_value",
                    models.JSONField(
                        blank=True,
                        help_text="The value, such as choice value, foreign key or plain value, that the source value matched. A string, integer, decimal, choice key, string id or integer id.",
                        null=True,
                    ),
                ),
                ("regex", models.CharField(blank=True, null=True)),
                ("aliases", models.JSONField(blank=True, null=True)),
                ("successful_mappings", models.JSONField(blank=True, null=True)),
                ("failed_mappings", models.JSONField(blank=True, null=True)),
                (
                    "bss_value_extractor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="ingestion.bssvalueextractor",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
