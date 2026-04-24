"""
Filter that enhance Django Filters, generally used for the REST API
"""

import logging

from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.core.validators import EMPTY_VALUES
from django.db.models import F, Func, Q
from django.forms import TextInput
from django.forms.fields import ChoiceField, DateField, Field, MultipleChoiceField
from django.forms.models import ModelMultipleChoiceField
from django.utils.datastructures import MultiValueDict
from django.utils.encoding import force_str
from django_filters import ModelMultipleChoiceFilter, MultipleChoiceFilter
from django_filters.filters import BooleanFilter, CharFilter, ChoiceFilter, DateFilter
from rest_framework.filters import OrderingFilter

from .utils import DEFAULT_DATES

logger = logging.getLogger(__name__)


class CaseInsensitiveChoiceField(ChoiceField):
    """
    Extend django.forms.fields.ChoiceField to do a case-insensitive match for the valid value
    """

    def to_python(self, value):
        "Returns a Unicode object matching the case of one the valid values"
        if value:
            for k, v in self.choices:
                if isinstance(v, (list, tuple)):
                    # This is an optgroup, so look inside the group for options
                    for k2, dummy in v:
                        if value.lower() == k2.lower or force_str(value).lower() == force_str(k2).lower():
                            value = k2
                else:
                    if value.lower() == k.lower() or force_str(value).lower() == force_str(k).lower():
                        value = k
        return super().to_python(value)


class CaseInsensitiveMultipleChoiceField(MultipleChoiceField):
    """
    Extend django.forms.fields.MultipleChoiceField to do a case-insensitive match for the valid value
    """

    def to_python(self, value):
        "Returns a Unicode object matching the case of one the valid values"
        if value and isinstance(value, (list, tuple)):
            corrected_value = []
            for item in value:
                if item:
                    for k, v in self.choices:
                        if isinstance(v, (list, tuple)):
                            # This is an optgroup, so look inside the group for options
                            for k2, dummy in v:
                                if item.lower() == k2.lower or force_str(item).lower() == force_str(k2).lower():
                                    item = k2
                        else:
                            if item.lower() == k.lower() or force_str(item).lower() == force_str(k).lower():
                                item = k
                    corrected_value.append(item)
            value = corrected_value
        return super().to_python(value)


class RelatedOrderingFilter(OrderingFilter):
    """
    Extends OrderingFilter to support ordering by fields in related models
    using the Django ORM __ notation
    """

    def is_valid_field(self, model, field):
        """
        Return true if the field exists within the model (or in the related
        model specified using the Django ORM __ notation)
        """
        components = field.split("__", 1)
        try:
            field = model._meta.get_field(components[0])
            if field.remote_field and len(components) == 2:
                return self.is_valid_field(field.remote_field.model, components[1])
            return True
        except FieldDoesNotExist:
            return False

    def remove_invalid_fields(self, queryset, fields, view, request):
        """
        Remove any ordering fields that are not present in the model
        """
        return [term for term in fields if self.is_valid_field(queryset.model, term.lstrip("-"))]


class CharMultiple(TextInput):
    allow_multiple_selected = True

    def value_from_datadict(self, data, files, name):
        if isinstance(data, MultiValueDict):
            return data.getlist(name)
        return data.get(name, None)


class MultipleCharField(Field):
    widget = CharMultiple


class MultiFieldFilter(CharFilter):
    """
    This filter preforms an OR query on the defined fields from a
    single entered value.

    The following will work similar to the default UserAdmin search::

        class UserFilterSet(FilterSet):
            search = MultiFieldFilter(['username', ('first_name', 'icontains'),
                                       'last_name', 'email'], lookup_expr='iexact')
            class Meta:
                model = User
                fields = ['search']
    """

    field_class = MultipleCharField

    def __init__(self, fields, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields = fields

    def filter(self, qs, value):
        """
        Return a new queryset applying the specified lookup_expr to all the fields
        """
        if not self.fields or not value:
            return qs

        q = Q()
        if not isinstance(value, (tuple, list)):
            value = [
                value,
            ]
        for v in set(value):
            for field in self.fields:
                if isinstance(field, tuple):
                    q |= Q(**{field[0] + "__" + field[1]: v})
                else:
                    q |= Q(**{field + "__" + self.lookup_expr: v})
        qs = qs.filter(q)
        return qs.distinct() if self.distinct else qs


class CaseInsensitiveChoiceFilter(ChoiceFilter):
    """
    Extensions of ChoiceFilter which does a case-insensitive match against the valid choices
    """

    field_class = CaseInsensitiveChoiceField


class CaseInsensitiveMultipleChoiceFilter(MultipleChoiceFilter):
    """
    Extensions of ChoiceFilter which does a case-insensitive match against the valid choices
    """

    field_class = CaseInsensitiveMultipleChoiceField


class UpperCaseFilter(CharFilter):
    """
    Accepts multiple values and converts them to uppercase before applying the
    specified lookup_expr.
    """

    field_class = MultipleCharField

    def __init__(self, field, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lookup_field = field

    def filter(self, qs, value):
        if not value:
            return qs

        q = Q()
        if not isinstance(value, (tuple, list)):
            value = [
                value,
            ]
        for v in set(value):
            q |= Q(**{self.lookup_field + "__" + self.lookup_expr: v.upper()})
        qs = qs.filter(q)
        return qs.distinct() if self.distinct else qs


class CaseInsensitiveModelMultipleChoiceField(ModelMultipleChoiceField):
    def _check_values(self, value):
        # convert the param queryset to lower
        value = [v.lower() for v in value if v]
        key = self.to_field_name or "pk"
        try:
            value = frozenset(value)
        except TypeError:
            # list of lists isn't hashable, for example
            raise ValidationError(
                self.error_messages["list"],
                code="list",
            )
        for pk in value:
            try:
                self.queryset.filter(**{key: pk})
            except (ValueError, TypeError):
                raise ValidationError(
                    self.error_messages["invalid_pk_value"],
                    code="invalid_pk_value",
                    params={"pk": pk},
                )
        # for a conversion of the filter to lower case in the DB left side fitler
        qs = self.queryset.annotate(pk_lower=Func(F(key), function="Lower")).filter(**{"pk_lower__in": value})
        pks = set(force_str(getattr(o, key)).lower() for o in qs)
        for val in value:
            if force_str(val) not in pks:
                raise ValidationError(
                    self.error_messages["invalid_choice"],
                    code="invalid_choice",
                    params={"value": val},
                )
        return qs


class CaseInsensitiveModelMultipleChoiceFilter(ModelMultipleChoiceFilter):
    field_class = CaseInsensitiveModelMultipleChoiceField


class EmptyStringFilter(BooleanFilter):
    def filter(self, qs, value):
        super().filter(qs, value)
        if value in EMPTY_VALUES:
            return qs
        exclude = self.exclude ^ (value is False)
        method = qs.exclude if exclude else qs.filter

        return method(**{self.field_name: ""})


class DefaultingDateField(DateField):
    """
    A date field that accepts defaults like "last_month", "today"
    """

    def to_python(self, value):
        if value in DEFAULT_DATES:
            value = DEFAULT_DATES[value]()
        return super().to_python(value)


class DefaultingDateFilter(DateFilter):
    """
    A date filter that accepts defaults like "today"
    """

    field_class = DefaultingDateField

    def filter(self, qs, value):
        if value:
            if self.lookup_expr in ["lte", "gte"]:
                # period_date filter for start and end date with either gte or lte expression will fall here.
                query = Q()
                query = Q(**{self.field_name + "__" + self.lookup_expr: value})
                return qs.filter(query)
            else:
                return qs.current_all(value)
        return qs
