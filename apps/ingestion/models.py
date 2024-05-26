import logging
import re

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import Model

logger = logging.getLogger(__name__)


class BssValueExtractor(Model):
    app_label = models.CharField()
    model = models.CharField()
    field = models.CharField()
    find_field = models.BooleanField(
        default=False,
        help_text=_(
            "True if the scan was looking for a field name alias, eg, 'Quantity Produced' for "
            "LivelihoodActivity.quantity_produced, as opposed to a value to be stored in that field."
        ),
    )
    regex = models.CharField(
        blank=True,
        help_text=_(
            "Put the text ALIAS in the regex where the alias should be injected. "
            "For regexes with multiple slots for multipart aliases, put the text ALIAS in the regex multiple times, "
            "and use || in the alias to separate the alias parts. The number of parts must match. "
            'To match any chars, `(`, maybe spaces, alias, maybe spaces, `)`, any chars, use: ".+\(\s*ALIAS\s*\).*". '
            "It will not match if no value is extracted. "
            "If no regex is needed, then no BssValueExtractor is needed, and the full cell contents will be matched."
            "(Identical behaviour to regex being an empty string.)"
        ),
    )

    # "Question mark cardinality suffix makes group non-greedy, for example the 3rd and final characters in the below example. "  # NOQA: E501
    # 're.findall(".*?([a-c]+).*?", "fsgdabcbafd") returns ["abcba"]'
    # "BssValueExtractor.parse will log a warning if more than one substring is extracted and return only the first. "  # NOQA: E501

    class Meta:
        verbose_name = _("BSS Value Extractor")
        verbose_name_plural = _("BSS Value Extractors")

    def match(self, source_value, sought_alias):
        num_alias_slots = self.regex.count("ALIAS")
        if num_alias_slots == 1:
            escaped_alias = re.escape(sought_alias)
            injected_re = self.regex.replace("ALIAS", escaped_alias)
        else:
            # regex expects a multipart alias - check if alias is suitable, split on || substring
            aliases = sought_alias.split("||")
            if num_alias_slots == len(aliases):
                injected_re = self.regex
                for alias in aliases:
                    escaped_alias = re.escape(alias)
                    injected_re = injected_re.replace("ALIAS", escaped_alias, 1)
            else:
                # regex expects a multipart alias, but alias has wrong number of parts, so this is not a match
                return None

        candidates = re.findall(injected_re, source_value)
        if not candidates:
            # Most times this will be scanning an irrelevant cell looking for a match.
            # logger.info(
            #     f"No value parsed for {self.app_label}.{self.model}.{self.field} for source value {source_value}."
            # )
            return None
        return injected_re


class ImportRun(Model):
    livelihood_zone_baseline = models.ForeignKey("baseline.LivelihoodZoneBaseline", on_delete=models.DO_NOTHING)


class SpreadsheetLocation(Model):
    bss_value_extractor = models.ForeignKey(
        BssValueExtractor,
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        help_text=_(
            "The extractor used to parse the cell value. Null if no extractor was used and the whole value was used."
        ),
    )
    app_label = models.CharField()
    model = models.CharField()
    field = models.CharField()
    find_field = models.BooleanField(
        default=False,
        help_text=_(
            "True if the scan was looking for a field name alias, eg, 'Quantity Produced' for "
            "LivelihoodActivity.quantity_produced, as opposed to a value to be stored in that field."
        ),
    )
    import_run = models.ForeignKey(ImportRun, on_delete=models.DO_NOTHING)
    sheet_name = models.CharField()
    column = models.PositiveIntegerField()
    row = models.PositiveIntegerField()
    regex = models.CharField(blank=True)  # duplicate here on creation, in case regex is updated on BssValueExtractor
    alias = models.CharField(
        null=True,
        blank=True,
        help_text=_("Alias that successfully matched the source value."),
    )

    source_value = models.CharField(blank=True)  # empty string may ingest as zero
    matching_re = models.CharField(blank=True)  # TODO: regex is without alias injected, matching_re is with?
    mapped_value = models.JSONField(
        null=True, blank=True, help_text=_("A string, integer, decimal, choice key, string id or integer id.")
    )

    # The below are all only populated after the destination instance has been saved:
    instance_number = models.PositiveIntegerField(null=True, blank=True)

    # The below three are all set with just: destination_instance=any_django_instance
    # It stores the instance that this spreadsheet value ends up being saved on
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.CharField(null=True, blank=True)  # permits ints or char keys
    destination_instance = GenericForeignKey("content_type", "object_id")

    class Meta:
        verbose_name = _("Spreadsheet Location")
        verbose_name_plural = _("Spreadsheet Locations")

    def __str__(self):
        return " ".join(
            f"{prop}:{getattr(self, prop)}"
            for prop in (
                "sheet_name",
                "column",
                "row",
                "source_value",
                "mapped_value",
            )
            if getattr(self, prop, None)
        )


class ChoiceAlias(Model):
    app_label = models.CharField()
    model = models.CharField()
    field = models.CharField()
    code = models.CharField()
    alias = models.CharField(blank=True)

    class Meta:
        verbose_name = _("Choice Alias")
        verbose_name_plural = _("Choice Aliases")


class FieldNameAlias(Model):
    app_label = models.CharField()
    model = models.CharField()
    field = models.CharField()
    alias = models.CharField(blank=True)

    class Meta:
        verbose_name = _("Field Name Alias")
        verbose_name_plural = _("Field Name Aliases")


class LogLevel(models.IntegerChoices):
    NOTSET = 0, _("Not Set")
    DEBUG = 10, _("Debug")
    INFO = 20, _("Info")
    WARN = 30, _("Warn")
    ERROR = 40, _("Error")
    CRITICAL = 50, _("Critical")


class ImportLog(Model):
    """
    Enables us to, for example, extract all logs for a specific cell with a problem value,
    or all logs for a specific field, and see the state at the time of logging.
    """

    import_run = models.ForeignKey(ImportRun, on_delete=models.DO_NOTHING)
    log_level = models.IntegerField(verbose_name=_("Log Level"), choices=LogLevel.choices, default=LogLevel.NOTSET)
    message = models.TextField()
    instance = models.JSONField(null=True, blank=True)
    sheet_name = models.CharField(null=True, blank=True)
    column = models.PositiveIntegerField(null=True, blank=True)
    row = models.PositiveIntegerField(null=True, blank=True)
    app_label = models.CharField(null=True, blank=True)
    model = models.CharField(null=True, blank=True)
    field = models.CharField(null=True, blank=True)
    source_value = models.CharField(null=True, blank=True)
    matching_re = models.CharField(null=True, blank=True)
    mapped_value = models.JSONField(
        null=True,
        blank=True,
        help_text=_(
            "The value, such as choice value, foreign key or plain value, that the source value matched. "
            "A string, integer, decimal, choice key, string id or integer id."
        ),
    )
    bss_value_extractor = models.ForeignKey(BssValueExtractor, on_delete=models.DO_NOTHING, null=True, blank=True)
    regex = models.CharField(null=True, blank=True)
    aliases = models.JSONField(null=True, blank=True)
    successful_mappings = models.JSONField(null=True, blank=True)  # will need to monitor space used
    failed_mappings = models.JSONField(null=True, blank=True)  # will need to monitor space used


class ScanLog(Model):
    """
    Tracks every attempt to load each value from each cell.
    Successful scans have the resulting alias, regex, injected regex and mapped value.
    """

    import_run = models.ForeignKey(ImportRun, on_delete=models.DO_NOTHING)
    sheet_name = models.CharField()
    column = models.PositiveIntegerField()
    row = models.PositiveIntegerField()
    app_label = models.CharField()
    model = models.CharField()
    field = models.CharField()
    find_field = models.BooleanField(
        default=False,
        help_text=_(
            "True if the scan was looking for a field name alias, eg, 'Quantity Produced' for "
            "LivelihoodActivity.quantity_produced, as opposed to a value to be stored in that field."
        ),
    )
    source_value = models.CharField(blank=True)

    # Only populated for successful scans - alias used, regex with alias injected, original regex and mapped value:
    bss_value_extractor = models.ForeignKey(BssValueExtractor, on_delete=models.DO_NOTHING, null=True, blank=True)
    alias = models.CharField(
        null=True,
        blank=True,
        help_text=_("Alias that successfully matched the source value."),
    )
    regex = models.CharField(
        null=True,
        blank=True,
        help_text=_(
            "The Regex that successfully matched the source value. "
            "Duplicated here in case regex is updated on BssVlueExtractor."
        ),
    )
    matching_re = models.CharField(
        null=True,
        blank=True,
        help_text=_("The regex with the alias injected that successfully matched the source value."),
    )
    mapped_value = models.JSONField(
        null=True,
        blank=True,
        help_text=_(
            "The value, such as choice value, foreign key or plain value, that the source value matched. "
            "A string, integer, decimal, choice key, string id or integer id."
        ),
    )
