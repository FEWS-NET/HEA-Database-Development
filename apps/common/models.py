"""
Foundational metadata models used for many applications.
"""

import datetime
import inspect
import logging
import operator
from functools import reduce

from django.core import validators
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models import CASCADE, Q
from django.utils.encoding import force_str
from django.utils.formats import date_format
from django.utils.timezone import now
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeFramedModel, TimeStampedModel
from treebeard.mp_tree import MP_Node, MP_NodeQuerySet

from .fields import (  # noqa: F401
    CodeField,
    DescriptionField,
    NameField,
    PrecisionField,
    add_translatable_field_to_model,
)

logger = logging.getLogger(__name__)


class ShowQueryVariablesMixin(object):
    """
    Mixin for models.Manager classes that shows the query arguments when a get() query fails
    """

    def get_display_args(self, args_list, args_dict):
        """
        Prepare the query arguments to be displayed in an error message - we
        can't just rely on the unicode conversion for model instances because
        we might end up in an infinite recursion - see https://code.djangoproject.com/ticket/20278
        """
        display_dict = {}
        for index, value in enumerate(args_list):
            if isinstance(value, Q):
                # Represent models as their primary key, rather than their
                # unicode representation
                display_dict["arg%d" % index] = {
                    "connector": value.connector,
                    "children": self.get_display_args(value.children, {}),
                }
            else:
                display_dict["arg%d" % index] = value
        for key, value in args_dict.items():
            if isinstance(value, models.Model):
                # Represent models as their primary key, rather than their
                # unicode representation
                display_dict[key] = value.pk
            else:
                display_dict[key] = value
        return display_dict

    def get(self, *args, **kwargs):
        """
        Provide query parameters in the error message when the get() fails
        """
        try:
            return super().get_queryset().get(*args, **kwargs)
        except self.model.DoesNotExist:
            raise self.model.DoesNotExist(
                "%s matching query does not exist. "
                "Lookup parameters were %s" % (self.model._meta.object_name, self.get_display_args(args, kwargs))
            )
        except self.model.MultipleObjectsReturned as e:
            raise self.model.MultipleObjectsReturned(
                str(e) + " Lookup parameters were %s" % (self.get_display_args(args, kwargs))
            )


class SearchQueryMixin:
    """
    Mixin for models.Manager and query.QuerySet classes that implements a
    generic search filter.
    """

    def search(self, search_term=None, **kwargs):
        """
        Filter based on a search term
        """
        search_filter = self.get_search_filter(search_term, **kwargs)
        queryset = self.filter(search_filter)
        queryset = self.sort_search_results(queryset, search_filter)
        return queryset

    def get_search_filter(self, search_term=None, **kwargs):
        """
        Construct the search criteria. Should be overridden in subclasses.
        """
        raise NotImplementedError

    def sort_search_results(self, queryset, search_filter):
        """
        Provides a hook for sorting the results, so that the best match is
        picked, rather than a random one, during imports. Passes queryset
        so that it can be annotated, eg, with a CASE statement.
        See GeographicUnitManager for an example, and issue HELP-793.
        """
        return queryset


class IdentifierQueryMixin(object):
    """
    Mixin for models.Manager classes that automatically select related models required for identifier fields
    """

    def get_related_models(self, model, prefix="", related_models=None):
        if related_models is None:
            related_models = set()

        for fields in model.ExtraMeta.identifier:
            current_model = model
            fields = fields.split("__")
            last_idx = len(fields)

            if prefix:
                accumulated = [prefix]
            else:
                accumulated = []

            if last_idx > 0:
                last_idx -= 1

            for idx, field in enumerate(fields):
                field = current_model._meta.get_field(field)
                accumulated.append(field.name)
                if field.remote_field:
                    related_model = "__".join(accumulated)
                    related_models.add(related_model)
                    self.get_related_models(field.remote_field.model, related_model, related_models)

                    if idx < last_idx:
                        current_model = field.remote_field.model

        return related_models

    def get_queryset(self):
        qs = super().get_queryset()
        related_models = self.get_related_models(self.model)
        if related_models:
            qs = qs.select_related(*related_models)
        return qs


class IdentifierManager(IdentifierQueryMixin, ShowQueryVariablesMixin, models.Manager):
    """
    Automatically select related models required for identifier fields
    """

    use_for_related_fields = True


# @TODO https://fewsnet.atlassian.net/browse/HEA-26
# We will use Django Model Translation, and fall back to using this class if
# necessary.
class TranslatableModel(models.Model):
    """
    Abstract base class that makes a model translatable, assuming that it
    contains a `name` field.
    """

    es_name = NameField(
        blank=True,
        verbose_name=_("Spanish name"),
        help_text=_("Spanish name if different from the English name"),
    )
    fr_name = NameField(
        blank=True,
        verbose_name=_("French name"),
        help_text=_("French name if different from the English name"),
    )
    pt_name = NameField(
        blank=True,
        verbose_name=_("Portuguese name"),
        help_text=_("Portuguese name if different from the English name"),
    )
    ar_name = NameField(
        blank=True,
        verbose_name=_("Arabic name"),
        help_text=_("Arabic name if different from the English name"),
    )

    def local_name(self):
        """
        Return the translated display name for the model instance.
        """
        language = get_language()
        if language == "es" and self.es_name:
            return self.es_name
        elif language == "fr" and self.fr_name:
            return self.fr_name
        elif language == "pt" and self.pt_name:
            return self.pt_name
        elif language == "ar" and self.ar_name:
            return self.ar_name
        else:
            return _(self.name)

    local_name.short_description = _("local name")

    class Meta:
        abstract = True


# @TODO Should this be in Metadata
class Model(TimeStampedModel):
    """
    An abstract base class model that provides:
    * created and modified timestamps
    * named identifier attributes
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Order by identifier if no other ordering is specified
        if self._meta.ordering == []:
            self._meta.ordering = self.ExtraMeta.identifier

    objects = IdentifierManager()

    class Meta:
        abstract = True

    class ExtraMeta:
        identifier = []

    def __str__(self):
        if self.ExtraMeta.identifier:
            components = []
            for field in self.ExtraMeta.identifier:
                try:
                    component = force_str(getattr(self, field))
                except ObjectDoesNotExist:
                    component = ""
                components.append(component)
            return ": ".join([component for component in components if component])
        elif hasattr(self, "natural_key"):
            return ": ".join([component for component in self.natural_key()])
        else:
            return super().__str__()

    def __repr__(self):
        return "<%s: %s (%s)>" % (self.__class__.__name__, self, self.pk)


class NonOverlappingTimeFramedQuerySet(models.QuerySet):
    """
    Provide a current() method for NonOverlappingTimeFramedModel

    """

    def current(self, as_of_date=None):
        """
        Extends timeframed to return a single record (normally called from a
        parent model on a set of children

        """
        try:
            return self.filter_current(as_of_date).get()
        except self.model.DoesNotExist:
            return None
        except self.model.MultipleObjectsReturned:
            raise self.model.MultipleObjectsReturned(
                "There is more than one current %s for %s"
                % (self.model._meta.verbose_name, as_of_date.isoformat() if as_of_date else "now")
            )

    def filter_current(self, as_of_date=None):
        """
        Return a queryset filtered to the records that are current/active as of the date specified.
        """
        start = self.model.get_start_field()
        end = self.model.get_end_field()
        if not as_of_date:
            # need to test specifically for DateTimeField because it inherits from DateField
            as_of_date = (
                now() if isinstance(self.model._meta.get_field(end), models.DateTimeField) else datetime.date.today()
            )
        # Criteria: A current record is one whose start date is in the past OR null
        # AND whose end date is in the future OR null
        current_queryset = self.filter(
            (Q(**{"%s__lte" % start: as_of_date}) | Q(**{"%s__isnull" % start: True}))
            & (Q(**{"%s__gte" % end: as_of_date}) | Q(**{"%s__isnull" % end: True}))
        )
        return current_queryset

    def current_all(self, as_of_date=None):
        """
        Return all the records that are current/active as of the date specified.
        """
        return self.filter_current(as_of_date).all()


class NonOverlappingTimeFramedManager(models.Manager.from_queryset(NonOverlappingTimeFramedQuerySet)):
    """
    Provide a current() method for NonOverlappingTimeFramedModel

    """

    use_for_related_fields = True


class NonOverlappingMixin(models.Model):
    """
    A mixin that provides additional validation that a timeframe or date range
    is non-overlapping. Only a single pair of start and end field is supported.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Order by end date within the non-overlapping fields if no other ordering is specified
        if self._meta.ordering == []:
            self._meta.ordering = self.ExtraMeta.non_overlapping + [
                self.get_end_field(),
                self.get_start_field(),
            ]
        if not hasattr(self.ExtraMeta, "identifier"):
            self.ExtraMeta.identifer = self.ExtraMeta.non_overlapping + [self.get_start_field()]

    @classmethod
    def get_start_field(cls):
        return getattr(cls.ExtraMeta, "start_field", "start")

    @classmethod
    def get_end_field(cls):
        return getattr(cls.ExtraMeta, "end_field", "end")

    def get_start(self):
        """
        Get the value of the start of the period, using reduce to traverse models
        """
        return reduce(getattr, [self] + self.get_start_field().split("__"))

    def get_end(self):
        """
        Get the value of the end of the period, using reduce to traverse models
        """
        return reduce(getattr, [self] + self.get_end_field().split("__"))

    def expire(self):
        setattr(
            self,
            self.get_end_field(),
            now()
            if isinstance(self._meta.get_field(self.get_end_field()), models.DateTimeField)
            else datetime.date.today(),
        )
        self.save()

    def clean(self):
        """
        Validate that the End is greater than Start. Also, validate that this
        range doesn't overlap any existing range.
        """
        start = self.get_start()
        end = self.get_end()
        if start and end and end < start:
            raise ValidationError(_("The End of the period must be on or after the Start"))

        parent_models = [
            base_class for base_class in inspect.getmro(self.__class__) if issubclass(base_class, NonOverlappingMixin)
        ]

        non_overlapping_fields = set()
        for parent_model in parent_models:
            for fieldname in parent_model.ExtraMeta.non_overlapping:
                # m2m fields are not supported.
                assert not isinstance(self._meta.get_field(fieldname), models.ManyToManyField)
                # For a foreign key we want to check the id attribute rather
                # than the object since it's always guaranteed to exist.
                # In contrast, if you tried to access an unassigned foreign key
                # object you would get a model.DoesNotExist exception.
                if isinstance(self._meta.get_field(fieldname), models.ForeignKey):
                    fieldname += "_id"
                non_overlapping_fields.add(fieldname)

        evaluation_queryset = self._meta.model.objects.all()
        if not non_overlapping_fields:
            evaluation_queryset = evaluation_queryset.none()

        if not start:
            if isinstance(self._meta.get_field(self.get_start_field()), models.DateTimeField):
                start = datetime.datetime.min
            else:
                start = datetime.date.min
        if not end:
            if isinstance(self._meta.get_field(self.get_end_field()), models.DateTimeField):
                end = datetime.datetime.max
            else:
                end = datetime.date.max

        # We can exclude all the non-matching rows and see what's left
        # We don't have an overlap if the other range is entirely before
        # this range, or if this range is entirely before the other range
        condition = {fieldname: getattr(self, fieldname) for fieldname in non_overlapping_fields}
        evaluation_queryset = evaluation_queryset.filter(**condition)

        condition = {self.get_end_field() + "__lt": start}
        evaluation_queryset = evaluation_queryset.exclude(**condition)

        condition = {self.get_start_field() + "__gt": end}
        evaluation_queryset = evaluation_queryset.exclude(**condition)

        if self.pk:
            # The record is also in the queryset, so exclude it.
            evaluation_queryset = evaluation_queryset.exclude(pk=self.pk)

        if evaluation_queryset.count():
            raise ValidationError(
                _(
                    "%(class)s %(pk)s (%(instance)s) has the same %(non_overlapping_fields)s and has a period that overlaps %(start)s to %(end)s"  # NOQA: E501
                ),
                code="overlapping_timeframe",
                params={
                    "class": self._meta.verbose_name.title(),
                    "pk": evaluation_queryset[0].pk,
                    "instance": str(evaluation_queryset[0]),
                    "non_overlapping_fields": "{} and {}".format(
                        ", ".join(list(non_overlapping_fields)[:-1]),
                        list(non_overlapping_fields)[-1],
                    )
                    if len(non_overlapping_fields) > 1
                    else list(non_overlapping_fields)[0],
                    "start": start,
                    "end": end,
                },
            )

        super().clean()

    def save(self, *args, **kwargs):
        """
        Ensure that custom validation is applied
        """
        self.full_clean(
            exclude=[field.name for field in self._meta.fields if isinstance(field, models.ForeignKey)],
            validate_unique=False,
        )
        super().save(*args, **kwargs)

    objects = NonOverlappingTimeFramedManager()

    class Meta:
        abstract = True

    class ExtraMeta:
        non_overlapping = (
            []
        )  # This must be set on concrete models to a list of fields within which periods cannot overlap
        start_field = "start"
        end_field = "end"


class NonOverlappingTimeFramedModel(NonOverlappingMixin, TimeFramedModel):
    """
    An abstract base class model that provides ``start``
    and ``end`` fields to record a timeframe.

    Provides additional validation that the timeframe is non-overlapping
    """

    class Meta:
        abstract = True

    def date_label(self):
        """
        Get a label that describes the validity period of the version
        """
        if not self.start and not self.end:
            date_text = _("Open Ended")
        elif self.start and not self.end:
            date_text = _("From %(start)s") % {
                "start": date_format(self.start, format="SHORT_DATE_FORMAT", use_l10n=True)
            }
        elif self.end and not self.start:
            date_text = _("Until %(end)s") % {"end": date_format(self.end, format="SHORT_DATE_FORMAT", use_l10n=True)}
        else:
            date_text = _("%(start)s - %(end)s") % {
                "start": date_format(self.start, format="SHORT_DATE_FORMAT", use_l10n=True),
                "end": date_format(self.end, format="SHORT_DATE_FORMAT", use_l10n=True),
            }
        return date_text


class NonOverlappingDateFramedModel(NonOverlappingMixin, models.Model):
    """
    An abstract base class model that provides ``start``
    and ``end`` fields to record a date range.

    Provides additional validation that the date range is non-overlapping
    """

    start = models.DateField(verbose_name=_("start"), null=True, blank=True)
    end = models.DateField(verbose_name=_("end"), null=True, blank=True)

    class Meta:
        abstract = True

    def date_label(self):
        """
        Get a label that describes the validity period of the version
        """
        if not self.start and not self.end:
            date_text = _("Open Ended")
        elif self.start and not self.end:
            date_text = _("From %(start)s") % {
                "start": date_format(self.start, format="SHORT_DATE_FORMAT", use_l10n=True)
            }
        elif self.end and not self.start:
            date_text = _("Until %(end)s") % {"end": date_format(self.end, format="SHORT_DATE_FORMAT", use_l10n=True)}
        else:
            date_text = _("%(start)s - %(end)s") % {
                "start": date_format(self.start, format="SHORT_DATE_FORMAT", use_l10n=True),
                "end": date_format(self.end, format="SHORT_DATE_FORMAT", use_l10n=True),
            }
        return date_text


class Country(models.Model):
    """
    A Country (or dependent territory or special area of geographical interest) included in ISO 3166.
    """

    iso3166a2 = models.CharField(max_length=2, primary_key=True, verbose_name="ISO 3166-1 Alpha-2")
    # name = NameField(max_length=200, unique=True)
    iso3166a3 = models.CharField(max_length=3, unique=True, verbose_name="ISO 3166-1 Alpha-3")
    iso3166n3 = models.IntegerField(
        unique=True,
        blank=True,
        null=True,
        validators=[validators.MinValueValidator(1), validators.MaxValueValidator(999)],
        verbose_name="ISO 3166-1 Numeric",
    )
    iso_en_name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="ISO English ASCII name",
        help_text=_(
            "The name of the Country approved by the ISO 3166 Maintenance Agency with accented characters replaced by their ASCII equivalents"  # NOQA: E501
        ),
    )
    iso_en_proper = models.CharField(
        max_length=200,
        verbose_name="ISO English ASCII full name",
        help_text=_(
            "The full formal name of the Country approved by the ISO 3166 Maintenance Agency with accented characters replaced by their ASCII equivalents"  # NOQA: E501
        ),
    )
    iso_en_ro_name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="ISO English name",
        help_text=_("The name of the Country approved by the ISO 3166 Maintenance Agency"),
    )
    iso_en_ro_proper = models.CharField(
        max_length=200,
        verbose_name="ISO English full name",
        help_text=_("The full formal name of the Country approved by the ISO 3166 Maintenance Agency"),
    )
    iso_fr_name = models.CharField(
        max_length=200,
        verbose_name=_("ISO French name"),
        help_text=_("The name in French of the Country approved by the ISO 3166 Maintenance Agency"),
    )
    iso_fr_proper = models.CharField(
        max_length=200,
        verbose_name=_("ISO French full name"),
        help_text=_("The full formal name in French of the Country approved by the ISO 3166 Maintenance Agency"),
    )
    iso_es_name = models.CharField(
        max_length=200,
        verbose_name=_("ISO Spanish name"),
        help_text=_("The name in Spanish of the Country approved by the ISO 3166 Maintenance Agency"),
    )

    def __str__(self):
        return self.iso_en_ro_name if self.iso_en_ro_name else ""

    class Meta:
        verbose_name = _("Country")
        verbose_name_plural = _("Countries")


add_translatable_field_to_model(Country, "name", NameField(max_length=200, unique=True))


# @TODO Should this be in Metadata and if so, should it be a Unit of Measure
# Roger: probably not because it has additional attributes (iso4217n3) and/or
# because money isn't necessarily an item in the same way as maize or school fees
# are, if we aren't using a Transfer-based model.
class Currency(models.Model):
    """
    A monetary unit in common use and included in ISO 4217.
    """

    iso4217a3 = models.CharField(max_length=20, primary_key=True, verbose_name="ISO 4217 Alpha-3")
    iso4217n3 = models.IntegerField(unique=True, verbose_name="ISO 4217 Numeric", blank=True, null=True)
    iso_en_name = models.CharField(max_length=200, verbose_name=_("name"))

    class Meta:
        verbose_name = _("Currency")
        verbose_name_plural = _("Currencies")

    def __str__(self):
        return self.iso4217a3

    class ExtraMeta:
        identifier = ["iso4217a3"]


class ClassifiedProductQuerySet(SearchQueryMixin, MP_NodeQuerySet):
    """
    Extends MP_NodeQuerySet with custom search method
    """

    def get_search_filter(self, search_term):
        # The product should be either a name, or a string code,
        # but could (incorrectly) be an int or a float from a poorly
        # formatted Excel file
        # It could also be a combined code and description
        if isinstance(search_term, float):
            search_term = int(search_term)
        if isinstance(search_term, int):
            search_term = str(search_term)
        parts = []
        for part in search_term.split(" - "):
            parts.append(
                Q(cpcv2__iexact=part)
                | Q(description__iexact=part)
                | Q(common_name__iexact=part)
                | Q(scientific_name__iexact=part)
                | Q(per_country_aliases__aliases__contains=[part.lower()])
                | Q(aliases__contains=[part.lower()])
                | Q(hs2012__contains=[part])
            )
        return reduce(operator.and_, parts)

    def search(self, search_term=None, **kwargs):
        """
        Filter based on a search term.

        Need to apply distinct to the filter results because country-level aliases may introduce duplicates.
        """
        return super().search(search_term, **kwargs).distinct()


class UnitOfMeasureQuerySet(SearchQueryMixin, models.QuerySet):
    """
    Extends QuerySet with custom search method
    """

    def get_search_filter(self, search_term):
        return (
            Q(abbreviation__iexact=search_term)
            | Q(description__iexact=search_term)
            | Q(aliases__contains=[search_term.lower()])
        )


class UnitOfMeasure(Model):
    """
    A Unit of Measure, such as kilogram, litre or metre.
    """

    # Unit Of Measure Types
    WEIGHT = "Weight"
    VOLUME = "Volume"
    ITEM = "Item"
    AREA = "Area"
    YIELD = "Yield"
    PERCENTAGE = "Percentage"
    LENGTH = "Length"
    UNIT_TYPE_CHOICES = (
        (WEIGHT, _("Weight")),
        (VOLUME, _("Volume")),
        (ITEM, _("Item")),
        (AREA, _("Area")),
        (YIELD, _("Yield")),
        (PERCENTAGE, _("Percentage")),
        (LENGTH, _("Length")),
    )
    abbreviation = models.CharField(max_length=12, primary_key=True, verbose_name=_("abbreviation"))
    unit_type = models.CharField(max_length=10, choices=UNIT_TYPE_CHOICES, verbose_name=_("unit type"))
    description = DescriptionField()
    aliases = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_("aliases"),
        help_text=_("A list of alternate names for the product."),
    )

    objects = IdentifierManager.from_queryset(UnitOfMeasureQuerySet)()

    def calculate_fields(self):
        # Ensure that aliases are lowercase and don't contain duplicates
        if self.aliases:
            self.aliases = list(sorted(set([alias.strip().lower() for alias in self.aliases if alias.strip()])))

    def save(self, *args, **kwargs):
        self.calculate_fields()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Unit of Measure")
        verbose_name_plural = _("Units of Measure")

    class ExtraMeta:
        identifier = ["description"]


class UnitOfMeasureConversionManager(models.Manager):
    def get_conversion_factor(self, from_unit, to_unit):
        """
        Return the conversion factor from "from_unit" to "to_unit".

        This method caches the query result to improve performance

        * If the units are the same then return 1
        * Otherwise, try to find a direct conversion factor between the two units.
        * If there is no direct conversion factor then try to find an inverse
          conversion factor by reversing the from and to units and returning
          the inverse of that conversion factor
        * If there is no inverse conversion factor either, then attempt to
          compute a conversion facor by using the common intermediate unit for
          that dimension of measure e.g. kilogram for WEIGHT, litre for VOLUME,
          Individual Item for ITEM.
        """
        # Use string comparison because each Unit could be a string or a UnitOfMeasure instance
        from_unit_pk = from_unit.pk if isinstance(from_unit, UnitOfMeasure) else from_unit
        to_unit_pk = to_unit.pk if isinstance(to_unit, UnitOfMeasure) else to_unit
        if (
            not from_unit_pk
            or not to_unit_pk
            or not isinstance(from_unit, (UnitOfMeasure, str))
            or not isinstance(to_unit, (UnitOfMeasure, str))
        ):
            raise self.model.DoesNotExist("UnitOfMeasureConversions must have a From Unit and a To Unit")
        if from_unit_pk == to_unit_pk:
            return 1
        key = "~".join(
            ["convert_unit", from_unit_pk.replace(" ", "_"), to_unit_pk.replace(" ", "_")]
        )  # Cache keys can't contain spaces
        conversion_factor = cache.get(key)
        if not conversion_factor:
            try:
                # Try a direct conversion factor
                conversion = self.get(from_unit=from_unit, to_unit=to_unit)
                conversion_factor = conversion.conversion_factor
            except self.model.DoesNotExist:
                try:
                    # Try an inverse conversion factor
                    conversion = self.get(from_unit=to_unit, to_unit=from_unit)
                    conversion_factor = 1 / conversion.conversion_factor
                except self.model.DoesNotExist:
                    # We need the actual units now, not a string pk, so we can check the unit_type
                    if not isinstance(from_unit, UnitOfMeasure):
                        from_unit = UnitOfMeasure.objects.get(pk=from_unit)
                    if not isinstance(to_unit, UnitOfMeasure):
                        to_unit = UnitOfMeasure.objects.get(pk=to_unit)
                    # Still no match, try to compute a conversion factor
                    # through a common intermediate unit
                    inter_unit = None
                    if from_unit.unit_type == to_unit.unit_type == UnitOfMeasure.WEIGHT:
                        # Use Kilogram as intermediate
                        inter_unit = UnitOfMeasure.objects.get(abbreviation="kg")
                    elif from_unit.unit_type == to_unit.unit_type == UnitOfMeasure.VOLUME:
                        # Use Litre as intermediate
                        inter_unit = UnitOfMeasure.objects.get(abbreviation="L")
                    elif from_unit.unit_type == to_unit.unit_type == UnitOfMeasure.ITEM:
                        # Use Individual Item as intermediate
                        inter_unit = UnitOfMeasure.objects.get(abbreviation="ea")
                    if (
                        inter_unit and from_unit != inter_unit and to_unit != inter_unit
                    ):  # necessary to avoid infinite recursion
                        try:
                            conversion_factor = self.get_conversion_factor(
                                from_unit, inter_unit
                            ) * self.get_conversion_factor(inter_unit, to_unit)
                        except self.model.DoesNotExist:
                            # Save as a result rather than raise the error so that the result can be cached
                            conversion_factor = self.model.DoesNotExist
                    else:
                        # Save as a result rather than raise the error so that the result can be cached
                        conversion_factor = self.model.DoesNotExist
            timeout = (60 * 60) if conversion_factor == self.model.DoesNotExist else (24 * 60 * 60)
            cache.set(key, conversion_factor, timeout)
        if conversion_factor == self.model.DoesNotExist:
            # If there is no conversion factor then raise the error
            raise self.model.DoesNotExist(
                "There is no valid direct, inverse or intermediate conversion factor for converting from %s to %s"
                % (from_unit, to_unit)
            )
        return conversion_factor


class UnitOfMeasureConversion(Model):
    """
    A conversion from one :class:`common.models.UnitOfMeasure` to another, such as from kilogram to
    pound, or from metre to foot.

    """

    from_unit = models.ForeignKey(
        UnitOfMeasure,
        verbose_name=_("from unit"),
        db_column="from_unit_code",
        related_name="from_conversions",
        on_delete=CASCADE,
    )
    to_unit = models.ForeignKey(
        UnitOfMeasure,
        verbose_name=_("to unit"),
        db_column="to_unit_code",
        related_name="to_conversions",
        on_delete=CASCADE,
    )
    conversion_factor = models.DecimalField(max_digits=38, decimal_places=12, verbose_name=_("conversion factor"))

    objects = UnitOfMeasureConversionManager()

    class Meta:
        verbose_name = _("Unit of Measure Conversion")
        verbose_name_plural = _("Unit of Measure Conversions")
        constraints = [
            models.UniqueConstraint(
                fields=["from_unit", "to_unit"], name="common_unitofmeasureconv_from_unit_code_to_unit_code_uniq"
            )
        ]

    class ExtraMeta:
        identifier = ["from_unit", "to_unit"]

    def clean(self):
        """
        Conversions have to be of the same unit type.

        Conversion across unit types, e.g. Litres to Kilograms are possible,
        but are dependent on the product being converted, which is not
        supported at the moment.
        """
        super().clean()
        if self.from_unit_id and self.to_unit_id:
            from_unit = self.from_unit
            to_unit = self.to_unit
            if from_unit.unit_type != to_unit.unit_type:
                raise ValidationError(
                    _(
                        f"From unit and to unit must have the same unit type, expected unit is of type {from_unit.unit_type}"  # NOQA: E501
                    )
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class ClassifiedProduct(MP_Node, Model):
    """
    A product such as a commodity or service classified using UN CPC v2 codes.

    See http://unstats.un.org/unsd/cr/registry/cpc-2.asp for more information

    """

    cpcv2 = models.CharField(
        max_length=8,
        primary_key=True,
        verbose_name="CPC V2",
        help_text="classification structure of products based on the UN’s Central Product Classification rules,"
        " prefixed with R, L, P or S, a letter indicating whether the Product is Raw agricultural output,"
        " Live animals, a Processed product or a Service.",
    )
    description = models.CharField(max_length=800, verbose_name=_("description"))
    common_name = NameField(blank=True, verbose_name=_("common name"))
    aliases = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_("aliases"),
        help_text=_("A list of alternate names for the product."),
    )
    # Note that we store and look up HS2012 values as xxxx.yy, e.g. Durum Wheat is 1001.19 rather than 100119,
    # because it avoids confusion between the CPCv2 and HS2012 codes.
    hs2012 = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_("HS2012"),
        help_text=_(
            "The 6-digit codes for the Product in the Harmonized Commodity Description and Coding System (HS), "
            "stored as XXXX.YY "
        ),
    )
    scientific_name = models.CharField(max_length=100, verbose_name="scientific name", blank=True, null=True)

    unit_of_measure = models.ForeignKey(
        UnitOfMeasure, db_column="unit_code", null=True, on_delete=models.PROTECT, verbose_name=_("Unit of Measure")
    )
    kcals_per_unit = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_("Kcals per Unit"))

    objects = IdentifierManager.from_queryset(ClassifiedProductQuerySet)()

    def display_name(self):
        """
        Return the English display name for the Classified Product.
        """
        if self.common_name:
            return self.common_name
        elif len(self.description) < 60:
            return self.description
        else:
            return self.description[:60] + "..."

    display_name.short_description = _("name")

    def __str__(self):
        return "%s / %s" % (self.cpcv2, self.display_name())

    def calculate_fields(self):
        """
        Ensure that aliases & hs2012 are lowercase and don't contain duplicates
        """
        if self.aliases:
            self.aliases = list(set([alias.lower() for alias in self.aliases if alias]))
        if self.hs2012:
            self.hs2012 = list(set([code.lower() for code in self.hs2012 if code]))

    def save(self, *args, **kwargs):
        self.calculate_fields()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        ordering = ()  # Required for correct ordering of Treebeard subclasses

    class ExtraMeta:
        identifier = ["cpcv2", "description"]


class CountryClassifiedProductAliases(Model):
    """
    Country-specific aliases for a :class:`.ClassifiedProduct`
    """

    country = models.ForeignKey(Country, db_column="country_code", verbose_name=_("country"), on_delete=CASCADE)
    product = models.ForeignKey(
        ClassifiedProduct,
        db_column="product_code",
        verbose_name=_("Product"),
        related_name="per_country_aliases",
        on_delete=CASCADE,
    )
    # @TODO Do we use this approach for compatibility with FDW and reuse of Lookups
    # or do we use the Tranlsation approach with a separate table (and what will that do for country-specific aliases)
    # or do we use a variation of FDW only with JSONField to maintain database independence.
    # aliases = ArrayField(models.CharField(max_length=60), verbose_name=_("aliases"))

    class Meta:
        verbose_name = _("Country Classified Product Alias")
        verbose_name_plural = _("Country Classified Product Aliases")
        constraints = [
            models.UniqueConstraint(
                fields=["country", "product"], name="common_countryclassified_country_code_product_code_uniq"
            )
        ]
