import abc
import logging
from typing import Iterable

from django.conf import settings
from django.db import models
from django.utils import translation
from django.utils.encoding import force_str

from ingestion.models import ChoiceAlias, FieldNameAlias

logger = logging.getLogger(__name__)


def get_fully_qualified_field_name(field_def):
    return f"{field_def.model._meta.app_label}.{field_def.model.__name__}.{field_def.name}"


class Mapper(abc.ABC):
    def __init__(self, field_def):
        self.field_def = field_def
        # self.cache is a dict {alias: mapped_value}. It is cached per import.
        self.cache = {}
        self.populate_lookup_cache()

    def map(self, bss_value_extractors, source_value):
        # See if the current cell matches any of the regexes in this field's BssValueExtractors
        sought_value = self.prepare_value(source_value)
        if not bss_value_extractors:
            for alias, value in self.cache.items():
                if sought_value == self.prepare_value(alias):
                    return None, "", alias, value  # a regex empty string is equivalent to no mapping
        for bss_value_extractor in bss_value_extractors:
            for alias, value in self.cache.items():
                matching_re = bss_value_extractor.match(sought_value, self.prepare_value(alias))
                if matching_re:
                    logger.info(
                        f"Successfully matched source value {source_value} "
                        f"regex {matching_re} extractor {bss_value_extractor}."
                    )
                    return bss_value_extractor, matching_re, alias, value
        return None

    def add_alias_to_cache(self, parsed_value, mapped_value, add_variants=False):
        lookup_value = self.prepare_value(parsed_value)
        if lookup_value in self.cache:
            logger.error(
                f"Duplicate lookup value. {get_fully_qualified_field_name(self.field_def)} "
                f"source value {lookup_value}."
            )
        self.cache[lookup_value] = mapped_value
        if add_variants and isinstance(parsed_value, str):
            for variant in (self.camel_case_to_spaced, self.snake_case_to_spaced):
                space_separated = self.prepare_value(variant(parsed_value))
                if space_separated and space_separated not in self.cache and space_separated != lookup_value:
                    self.add_alias_to_cache(space_separated, mapped_value)

    def all_aliases(self):
        return (f"{alias}=>{mapped}" for alias, mapped in self.cache.items())

    @staticmethod
    def camel_case_to_spaced(code):
        # If we have a code in camel case, eg, "MeatProduction", treat "meat production" as an alias.

        # if it is a string of mixed case and no spaces
        if " " not in code and any(x.isupper() for x in code) and any(x.islower() for x in code):
            return "".join(" " + c.lower() if c.isupper() else c for c in code).lstrip()

    @staticmethod
    def snake_case_to_spaced(code):
        # If we have a code in camel case, eg, "meat_production", treat "meat production" as an alias.
        # Returns None if the string does not look like snake case or does not produce an alternative alias.
        if " " not in code and "_" in code:
            return code.replace("_", " ")

    @staticmethod
    def prepare_value(parsed_value):
        translated = force_str(parsed_value, strings_only=True)
        return Mapper.prepare_string(translated) if isinstance(translated, str) else parsed_value

    @staticmethod
    def prepare_string(parsed_value):
        return parsed_value.strip().rstrip(":").lower()

    def populate_lookup_cache(self):
        pass


class ForeignKeyMapper(Mapper):
    """
    Use self.mapper_factory(field_def) so that aliases are cached for the import.

    Override populate_lookup_cache if fields other than aliases, name (all languages) and code should also be mapped.

    Nb. All model instances are garbage collected and just their key is stored in the cache.
    """

    def populate_lookup_cache(self):
        queryset = self.field_def.related_model.objects.all()
        for instance in queryset:
            if isinstance(getattr(instance, "aliases", None), Iterable):
                for alias in instance.aliases:
                    self.add_alias_to_cache(alias, instance.pk)
            if isinstance(getattr(instance, "code", None), str) and instance.code:
                self.add_alias_to_cache(instance.code, instance.pk, add_variants=True)
            # name_en, name_fr, etc.
            for language_code, language_name in settings.LANGUAGES:
                lookup = getattr(instance, f"name_{language_code}", None)
                if isinstance(lookup, str) and lookup.strip():
                    self.add_alias_to_cache(instance.code, instance.pk)


class ChoiceMapper(Mapper):
    """Use self.mapper_factory(field_def) so that aliases are cached for the import."""

    def populate_lookup_cache(self):
        for language_code, language_name in settings.LANGUAGES:
            translation.activate(language_code)
            for value, label in self.field_def.choices:
                if label.strip():  # if translation returns nothing, don't use it
                    self.add_alias_to_cache(label, value)
                if self.prepare_value(label) != self.prepare_value(value):  # recognize choice code
                    self.add_alias_to_cache(value, value, add_variants=True)
        translation.activate(settings.LANGUAGE_CODE)

        queryset = ChoiceAlias.objects.filter(
            app_label=self.field_def.model._meta.app_label,
            model=self.field_def.model.__name__,
            field=self.field_def.name,
        )
        for instance in queryset:
            self.add_alias_to_cache(instance.alias, instance.code)


class FieldNameMapper(Mapper):
    """
    Use self.mapper_factory(field_def, find_field=True) so that aliases are cached for the import.
    Used when searching for field name aliases,
    eg, looking for a milking_animals label for baseline.MilkProduction in Data column A.
    """

    def populate_lookup_cache(self):
        queryset = FieldNameAlias.objects.filter(
            app_label=self.field_def.model._meta.app_label,
            model=self.field_def.model.__name__,
            field=self.field_def.name,
        )
        for instance in queryset:
            self.add_alias_to_cache(instance.alias, ".".join((instance.app_label, instance.model, instance.field)))


class SimpleValueMapper(Mapper):
    def map(self, bss_value_extractors, source_value):
        return None, None, source_value, source_value


class MapperFactory:
    """
    Permits caching of lookups for duration of import, rather than instantiating on each importer or passing them.
    """

    def __init__(self):
        self.cache = {}

    def __call__(self, field_def, find_field=False):
        key = (get_fully_qualified_field_name(field_def), find_field)
        if key not in self.cache:
            if find_field:
                # FieldNameMapper is used for searching for field name aliases,
                # eg, looking for a milking_animals label for baseline.MilkProduction in Data column A.
                self.cache[key] = FieldNameMapper(field_def)
            elif isinstance(field_def, models.ForeignKey):
                self.cache[key] = ForeignKeyMapper(field_def)
            elif isinstance(getattr(field_def, "choices", None), Iterable):
                self.cache[key] = ChoiceMapper(field_def)
            else:
                self.cache[key] = SimpleValueMapper(field_def)
        return self.cache[key]
