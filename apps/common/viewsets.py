from inspect import isclass

from django.contrib.auth.models import User
from django.db.models import ExpressionWrapper, F, FloatField, Q
from django.db.models.functions import Coalesce, NullIf
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotAcceptable
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import GenericViewSet

from .enums import AggregationScope
from .fields import translation_fields
from .filters import MultiFieldFilter
from .models import ClassifiedProduct, Country, Currency, UnitOfMeasure, UserProfile
from .serializers import (
    ClassifiedProductSerializer,
    CountrySerializer,
    CurrencySerializer,
    CurrentUserSerializer,
    UnitOfMeasureSerializer,
    UserProfileSerializer,
    UserSerializer,
)


class ApiOnlyPagination(PageNumberPagination):
    page_size = None
    api_page_size = 50
    page_size_query_param = "page_size"

    def get_page_size(self, request):
        # Don't return everything if we are using the browsable API
        if request.accepted_renderer.format == "api" and self.page_size_query_param not in request.query_params:
            return self.api_page_size
        # If geojson is requested we don't want to support pagination
        if request.accepted_renderer.format == "geojson" and self.page_size_query_param in request.query_params:
            raise NotAcceptable("Pagination is not supported for GeoJSON format.")

        return super().get_page_size(request)


class BaseModelViewSet(viewsets.ModelViewSet):
    """
    A base viewsets for all viewsets to set the pagination for api requests
    """

    pagination_class = ApiOnlyPagination


class CountryFilterSet(filters.FilterSet):
    """
    FilterSet for the Country model.

    This FilterSet is used to apply filtering on the Country model based on various filter fields.

    Attributes:
        country_code: A MultipleChoiceFilter for filtering by the ISO 3166-1 alpha-2 country code.
                      Choices will be dynamically populated based on the Country model data.

        country: A MultiFieldFilter for filtering by various fields related to country names.
                 The filter uses a case-insensitive exact lookup expression.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the CountryFilterSet.

        Populates the 'choices' attribute of the 'country_code' filter dynamically
        based on the Country model data.

        Args:
            *args: Positional arguments to pass to the superclass.
            **kwargs: Keyword arguments to pass to the superclass.
        """
        super().__init__(*args, **kwargs)
        self.filters["country_code"].extra["choices"] = [
            (c.pk, c.iso_en_name) for c in Country.objects.all().order_by("iso_en_name")
        ]

    country_code = filters.MultipleChoiceFilter(
        field_name="iso3166a2",
        choices=[],
        label="Country ISO 3166-1 alpha-2 Code",
        distinct=False,
    )

    country = MultiFieldFilter(
        [
            "iso3166a2",
            "iso_en_ro_name",
            "iso_en_name",
            "iso_en_ro_proper",
            "iso_en_proper",
            "iso_fr_name",
            "iso_fr_proper",
            "iso_es_name",
        ],
        lookup_expr="iexact",
        label="Country",
    )


class CountryViewSet(BaseModelViewSet):
    """
    ViewSet for the Country model.

    This ViewSet provides CRUD operations for the Country model.
    The queryset is set to retrieve all Country objects.
    The serializer used is CountrySerializer.
    The filtering is performed using CountryFilterSet.
    The 'search_fields' attribute defines the fields that can be searched in the view.
    """

    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    filterset_class = CountryFilterSet

    search_fields = [
        "iso3166a2",
        "name",
        "iso_en_name",
        "iso_en_proper",
        "iso_en_ro_name",
        "iso_en_ro_proper",
        "iso_fr_name",
        "iso_fr_proper",
        "iso_es_name",
    ]


class CurrencyFilterSet(filters.FilterSet):
    """
    FilterSet for the Currency model.

    This FilterSet is used to apply filtering on the Currency model based on various filter fields.

    Attributes:
        currency_code: A MultipleChoiceFilter for filtering by the ISO 4217 Alpha-3 currency code.
                       Choices will be dynamically populated based on the Currency model data.

        currency: A MultiFieldFilter for filtering by various fields related to currency data.
                  The filter uses a case-insensitive exact lookup expression.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the CurrencyFilterSet.

        Populates the 'choices' attribute of the 'currency_code' filter dynamically
        based on the Currency model data.

        Args:
            *args: Positional arguments to pass to the superclass.
            **kwargs: Keyword arguments to pass to the superclass.
        """
        super().__init__(*args, **kwargs)
        self.filters["currency_code"].extra["choices"] = [
            (c.pk, c.iso_en_name) for c in Currency.objects.all().order_by("iso_en_name")
        ]

    currency_code = filters.MultipleChoiceFilter(
        field_name="iso4217a3",
        label="ISO 4217 Alpha-3",
        choices=[],
        distinct=False,
    )

    currency = MultiFieldFilter(
        ["iso4217a3", "iso4217n3", "iso_en_name"],
        lookup_expr="iexact",
        label="Currency",
    )


class CurrencyViewSet(BaseModelViewSet):
    """
    ViewSet for the Currency model.

    This ViewSet provides CRUD operations for the Currency model.
    The queryset is set to retrieve all Currency objects.
    The serializer used is CurrencySerializer.
    The filtering is performed using CurrencyFilterSet.
    The 'search_fields' attribute defines the fields that can be searched in the view.
    """

    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    filterset_class = CurrencyFilterSet
    search_fields = ["iso4217a3", "iso4217n3", "iso_en_name"]


class UnitOfMeasureFilterSet(filters.FilterSet):
    """
    FilterSet for the UnitOfMeasure model.

    This FilterSet is used to apply filtering on the UnitOfMeasure model based on various filter fields.

    Attributes:
        unit_type: A ChoiceFilter for filtering by the unit type.
                   Choices are based on the available UNIT_TYPE_CHOICES from the UnitOfMeasure model.
    """

    unit_type = filters.ChoiceFilter(choices=UnitOfMeasure.UNIT_TYPE_CHOICES)

    class Meta:
        """
        Metadata options for the UnitOfMeasureFilterSet.

        Specifies the model and fields to be used for filtering.

        Attributes:
            model: The model to be filtered (UnitOfMeasure).
            fields: The fields in the model to be used for filtering.
        """

        model = UnitOfMeasure
        fields = (
            "abbreviation",
            *translation_fields("description"),
            "unit_type",
        )


class UnitOfMeasureViewSet(BaseModelViewSet):
    """
    ViewSet for the UnitOfMeasure model.

    This ViewSet provides CRUD operations for the UnitOfMeasure model.
    The queryset is set to retrieve all UnitOfMeasure objects.
    The serializer used is UnitOfMeasureSerializer.
    The filtering is performed using UnitOfMeasureFilterSet.
    The 'search_fields' attribute defines the fields that can be searched in the view.
    """

    queryset = UnitOfMeasure.objects.all()
    serializer_class = UnitOfMeasureSerializer
    filterset_class = UnitOfMeasureFilterSet
    search_fields = (
        "abbreviation",
        *translation_fields("description"),
        "unit_type",
    )


class ClassifiedProductFilterSet(filters.FilterSet):
    """
    FilterSet for the ClassifiedProduct model.

    This FilterSet is used to apply filtering on the ClassifiedProduct model based on various filter fields.

    Attributes:
        cpc: A CharFilter for filtering by the CPC value (case-insensitive contains lookup).
        description_en: A CharFilter for filtering by the description (case-insensitive contains lookup).
        common_name_en: A CharFilter for filtering by the common name (case-insensitive contains lookup).
        unit_of_measure: A ModelChoiceFilter for filtering by the associated UnitOfMeasure object.
                         The filter will display choices based on the available UnitOfMeasure objects.
    """

    cpc = filters.CharFilter(lookup_expr="icontains", label="CPC v2.1")
    description_en = filters.CharFilter(
        lookup_expr="icontains", label=format_lazy("{} ({})", _("Description"), _("English"))
    )
    description_fr = filters.CharFilter(
        lookup_expr="icontains", label=format_lazy("{} ({})", _("Description"), _("French"))
    )
    description_es = filters.CharFilter(
        lookup_expr="icontains", label=format_lazy("{} ({})", _("Description"), _("Spanish"))
    )
    description_ar = filters.CharFilter(
        lookup_expr="icontains", label=format_lazy("{} ({})", _("Description"), _("Arabic"))
    )
    description_pt = filters.CharFilter(
        lookup_expr="icontains", label=format_lazy("{} ({})", _("Description"), _("Portuguese"))
    )
    common_name_en = filters.CharFilter(
        lookup_expr="icontains", label=format_lazy("{} ({})", _("Common Name"), _("English"))
    )
    common_name_fr = filters.CharFilter(
        lookup_expr="icontains", label=format_lazy("{} ({})", _("Common Name"), _("French"))
    )
    common_name_es = filters.CharFilter(
        lookup_expr="icontains", label=format_lazy("{} ({})", _("Common Name"), _("Spanish"))
    )
    common_name_ar = filters.CharFilter(
        lookup_expr="icontains", label=format_lazy("{} ({})", _("Common Name"), _("Arabic"))
    )
    common_name_pt = filters.CharFilter(
        lookup_expr="icontains", label=format_lazy("{} ({})", _("Common Name"), _("Portuguese"))
    )
    unit_of_measure = filters.ModelChoiceFilter(queryset=UnitOfMeasure.objects.all(), field_name="unit_of_measure")

    class Meta:
        """
        Metadata options for the ClassifiedProductFilterSet.

        Specifies the model and fields to be used for filtering.

        Attributes:
            model: The model to be filtered (ClassifiedProduct).
            fields: The fields in the model to be used for filtering.
        """

        model = ClassifiedProduct
        fields = (
            "cpc",
            *translation_fields("description"),
            *translation_fields("common_name"),
            "scientific_name",
            "unit_of_measure",
            "kcals_per_unit",
        )


class ClassifiedProductViewSet(BaseModelViewSet):
    """
    ViewSet for the ClassifiedProduct model.

    This ViewSet provides CRUD operations for the ClassifiedProduct model.
    The queryset is set to retrieve all ClassifiedProduct objects.
    The serializer used is ClassifiedProductSerializer.
    The filtering is performed using ClassifiedProductFilterSet.
    The 'search_fields' attribute defines the fields that can be searched in the view.
    """

    queryset = ClassifiedProduct.objects.all()
    serializer_class = ClassifiedProductSerializer
    filterset_class = ClassifiedProductFilterSet
    search_fields = (
        "cpc",
        *translation_fields("description"),
        *translation_fields("common_name"),
    )


class CurrentUserOnly(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        elif view.kwargs == {"pk": "current"}:
            # Even anonymous users can see their current user record
            return True
        elif request.query_params.get("pk") == "current":
            # List views seem to use query_params rather than kwargs
            return True
        return False


class UserViewSet(BaseModelViewSet):
    """
    Allows users to be viewed or edited.
    """

    queryset = User.objects.all()
    permission_classes = [CurrentUserOnly]
    serializer_class = UserSerializer
    search_fields = ["username", "first_name", "last_name"]

    def get_object(self):
        pk = self.kwargs.get("pk")

        if pk == "current":
            self.serializer_class = CurrentUserSerializer
            return self.request.user if self.request.user.id else User.get_anonymous()

        return super().get_object()

    @action(detail=True, methods=["get"])
    def current(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class UserProfileViewSet(BaseModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [CurrentUserOnly, IsAuthenticated]

    def get_object(self):
        pk = self.kwargs.get("pk")
        if pk == "current":
            return self.request.user.userprofile if self.request.user.id else None
        return super().get_object()

    def get_queryset(self):
        queryset = super().get_queryset()
        pk = self.request.query_params.get("pk") or self.kwargs.get("pk")

        if pk == "current":
            return queryset.filter(user=self.request.user.id)
        elif pk:
            # Superusers can access profiles without using pk=current.
            return queryset.filter(user=pk)
        else:
            return queryset


class AggregatingViewSet(GenericViewSet):
    """
    A viewset parent class that adds aggregation functionality to a viewset.

    Supports the following URL parameters:

     * fields: Some or all of the model fields listed in the serializer Meta.fields property, comma delimited.
        This field list controls the fields returned, and the level of aggregation / drill-down.

     * slice_by_[field]: Produces aggregates of a slice of the data within each row. The serializer defines some
        common slice_by properties for easy use, eg, slice_by_product=R0 slices by product__cpc__istartswith.

     * slice_by_[field]__[Django lookup type]: Slices can be calculated on any model field, but the user
        must specify a Django ORM lookup type that is suitable for the field type. This allows expert users to define
        custom slices that the developer hasn't pre-configured on serializer.slice_fields.

     * min_ and/or max_[field]: Removes any rows where the value is outside the specified min/max/range.
        The specific nature of these range parameters are configured on the serializer.

     * filters and ordering parameters provided by the FilterSet

    To use, inherit from this class, and ensure the linked serializer inherits from AggregatingSerializer and includes
    the Meta.model, Meta.fields, aggregates, slice_fields properties, and the field_to_database_path method if
    necessary. Field class attributes are not necessary.

    The results will include all valid fields specified in the fields parameter, plus values aggregated to the model,
    row and slice levels, plus the percentage the slice represents of the row and model.

    The FilterSet filters are applied to all calculations, including at the model-level.

    The fields parameter determines the drill-down of each row from the base model. For example if a child model field
    is included, then rows will be disaggregated to show figures broken down by that child model field. Any fields not
    included are aggregated together. The FilterSet filters are applied to the rows too.

    The slice_by parameter defines a slice of data within each row. The FilterSet filters are applied to the slice
    totals too.

    Calculated field examples:
      * expenditure_avg_row  # this is the average expenditure for all database records within the row.
      * kcals_consumed_sum_slice  # this is the sum of kcals consumed for a slice within each row.
      * kcals_consumed_sum_slice_percentage_of_row  # this is the percentage the slice represents of the row total.

    Filters can be applied on any of these calculated fields, by passing a parameter that prefixes min_ or max_ to
    the field name, eg, min_kcals_consumed_sum=1000 or max_kcals_consumed_sum_slice_percentage_of_row=99.

    All configuration is set in the AggregatingSerializer sub-class. The AggregatingViewSet sub-class need only
    implement, for example:

        queryset = LivelihoodZoneBaseline.objects.all()
        serializer_class = LivelihoodZoneBaselineReportSerializer  # must be a sub-class of AggregatingSerializer.
        filterset_class = LivelihoodZoneBaselineFilterSet  # a standard FilterSet, supports filter and order options.
    """

    pagination_class = ApiOnlyPagination

    def list(self, request, *args, **kwargs):
        """
        Aggregates the values specified in the serializer.aggregates property, grouping and aggregating by any
        fields not requested by the user.
        """

        # These filters are applied to global, row and slice totals.
        queryset = super().get_queryset()
        queryset = self.filter_queryset(queryset)

        # Get the field list to group/disaggregate the results by:
        # TODO: Should get_fields be on the viewset? This is prematurely instantiating it before we've a queryset.
        group_by_fields = self.get_serializer().get_fields().keys()

        # Convert user-friendly field name (eg, livelihood_strategy_pk) into db field path (livelihood_strategies__pk).
        group_by_field_paths = [self.serializer_class.field_to_database_path(field) for field in group_by_fields]

        # Get them from the query. The ORM converts this qs.values() call into a SQL `GROUP BY *field_paths` clause.
        queryset = queryset.values(*group_by_field_paths)

        # Add the row aggregations, eg, total consumption filtered by wealth group and row but not prd/strtgy slice:
        row_aggregates = self.get_aggregates(AggregationScope.ROW)
        queryset = queryset.annotate(**row_aggregates)

        # Add the slice aggregates, eg, slice_sum_kcals_consumed for product/strategy slice:
        slice_aggregates = self.get_aggregates(AggregationScope.SLICE)
        if slice_aggregates:
            queryset = queryset.annotate(**slice_aggregates)

            # Add the calculations on aggregates, eg,
            #   kcals_consumed_sum_slice_percentage_of_row = slice_sum_kcals_consumed * 100 / sum_kcals_consumed
            percentage_expressions = self.get_percentage_expressions()
            queryset = queryset.annotate(**percentage_expressions)

            # Add the filters on aggregates, eg, kcals_consumed_percent > 50%
            queryset = queryset.filter(self.get_filters_by_calculated_fields())

        # If no ordering has been specified by the FilterSet, order by value descending:
        if not self.request.query_params.get(api_settings.ORDERING_PARAM):
            if slice_aggregates:
                # If a slice has been specified, order by slice_percentage_of_row desc
                order_by_value_desc = [
                    f"-{self.serializer_class.get_aggregate_field_name(field_name, aggregate, AggregationScope.SLICE, AggregationScope.ROW,)}"  # NOQA: E501
                    for field_name, aggregate in self.serializer_class.aggregates.items()
                ]
            else:
                # If no slice specified, order by row value desc
                order_by_value_desc = [
                    f"-{self.serializer_class.get_aggregate_field_name(field_name, aggregate, AggregationScope.ROW,)}"
                    for field_name, aggregate in self.serializer_class.aggregates.items()
                ]
            queryset = queryset.order_by(*order_by_value_desc)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_aggregates(self, scope):
        """
        Produces aggregate expressions for scopes row or slice.
        """
        assert isinstance(scope, AggregationScope)

        if scope == AggregationScope.SLICE:
            slice_filters = self.get_slice_filters()
            # Add slice and slice_percentage_of columns only if the user has specified a slice.
            if not slice_filters:
                return {}

        aggregates = {}
        for field_name, aggregate in self.serializer_class.aggregates.items():
            aggregate_field_name = self.serializer_class.get_aggregate_field_name(field_name, aggregate, scope)

            if isclass(aggregate):
                field_path = self.serializer_class.field_to_database_path(field_name)
                aggregate_args = {"default": 0, "output_field": FloatField()}
                if scope == AggregationScope.SLICE:
                    aggregate_args["filter"] = slice_filters
                scoped_aggregate = aggregate(field_path, **aggregate_args)

            else:
                scoped_aggregate = aggregate.copy()
                scoped_aggregate.default = 0
                if scope == AggregationScope.SLICE:
                    scoped_aggregate.filter = slice_filters

            aggregates[aggregate_field_name] = scoped_aggregate
        return aggregates

    def get_slice_filters(self):
        """
        Filters to slice the aggregations, to obtain, eg, the kcals for the selected products/strategy types.
        This is then divided by the total for the LZB and row for the slice percentages.
        """
        slice_filters = Q()
        for slice_field, slice_expr in self.serializer_class.slice_fields.items():
            slice_filter = Q()
            for item in self.request.query_params.getlist(f"slice_by_{slice_field}"):
                slice_filter |= Q(**{slice_expr: item})
            # Slice must match any of the products AND any of the strategy types (if selected)
            slice_filters &= slice_filter

        # Also support slices on any field, but user must specify ORM lookup type in URL parameter name, and prefix
        # the parameter with 'slice_by_', for example, ?slice_by_product_cpc__startswith=botswana
        # An error is returned if the user uses an inappropriate lookup type for a field. Note that string lookup
        # types cannot be used on Foreign Key fields, even if they are string codes - field_to_database_path must
        # reach the corresponding primary key, eg, livelihood_strategies__product__cpc not
        # livelihood_strategies__product.
        for field_name in set(self.serializer_class.Meta.fields) - self.get_serializer().get_fields().keys():
            # fmt: off
            # Copied from https://docs.djangoproject.com/en/5.1/ref/models/querysets/#field-lookups
            lookup_types = ("exact", "iexact", "contains", "icontains", "in", "gt", "gte", "lt", "lte", "startswith", "istartswith", "endswith", "iendswith", "range", "date", "year", "iso_year", "month", "day", "week", "week_day", "iso_week_day", "quarter", "time", "hour", "minute", "second", "isnull", "regex", "iregex", )  # NOQA: E501
            # fmt: on
            for lookup_type in lookup_types:
                slice_filter = Q()
                field_path = self.serializer_class.field_to_database_path(field_name)
                slice_expr = f"{field_path}__{lookup_type}"
                for item in self.request.query_params.getlist(f"slice_by_{field_name}__{lookup_type}"):
                    slice_filter |= Q(**{slice_expr: item})
                # Slice must match ANY of the products AND any of the strategy types AND any of the custom slices
                slice_filters &= slice_filter

        return slice_filters

    def get_percentage_expressions(self):
        """
        Aggregate slice percentages.
        Nb. Cannot calculate in Python as need db-wide filtering and ordering on them.
        Could add row percentage of model, eg, lzb.
        """
        # TODO: Add complex kcal income calculations from LIAS
        percentage_expressions = {}
        for field_name, aggregate in self.serializer_class.aggregates.items():
            # Eg, kcals_consumed_sum_slice
            slice_field_name = self.serializer_class.get_aggregate_field_name(
                field_name,
                aggregate,
                AggregationScope.SLICE,
            )
            slice_total = F(slice_field_name)

            # The denominator, eg, kcals_consumed_sum_row or kcals_consumed_sum_row:
            denominator_field_name = self.serializer_class.get_aggregate_field_name(
                field_name,
                aggregate,
                AggregationScope.ROW,
            )
            total = F(denominator_field_name)

            # Multiply slice by 100 for percentage, divide by denominator. NullIf protects against divide by zero.
            expr = ExpressionWrapper(
                ExpressionWrapper(slice_total * 100.0, output_field=FloatField())
                / NullIf(total, 0.0, output_field=FloatField()),
                output_field=FloatField(),
            )

            # Zero if no there are no value records retrieved for the slice.
            expr = Coalesce(expr, 0.0, output_field=FloatField())

            # Output field, eg, kcals_consumed_slice_percentage_of_row or kcals_consumed_slice_percentage_of_row:
            pct_field_name = self.serializer_class.get_aggregate_field_name(
                field_name,
                aggregate,
                AggregationScope.SLICE,
                AggregationScope.ROW,
            )
            percentage_expressions[pct_field_name] = ExpressionWrapper(expr, output_field=FloatField())
        return percentage_expressions

    def get_filters_by_calculated_fields(self):
        """
        Add min/max range filters. Filters are available for any aggregate or percentage field, by prefixing
        min_ or max_ to the aggregate field name.
        eg, .filter(
            kcals_consumed_sum_slice_percentage_of_row__gte=
                params.get("min_kcals_consumed_sum_slice_percentage_of_row"),
            kcals_consumed_sum_slice__gte=
                params.get("min_kcals_consumed_sum_slice"),
        )
        """
        filters_on_aggregates = Q()
        for field_name, aggregate in self.serializer_class.aggregates.items():
            for url_param_prefix, orm_expr in (("min", "gte"), ("max", "lte")):
                for agg_field_name in (
                    self.serializer_class.get_aggregate_field_name(
                        field_name,
                        aggregate,
                        AggregationScope.ROW,
                    ),
                    self.serializer_class.get_aggregate_field_name(
                        field_name,
                        aggregate,
                        AggregationScope.SLICE,
                        AggregationScope.ROW,
                    ),
                ):
                    url_param_name = f"{url_param_prefix}_{agg_field_name}"
                    limit = self.request.query_params.get(url_param_name)
                    if limit is not None:
                        filters_on_aggregates &= Q(**{f"{agg_field_name}__{orm_expr}": float(limit)})
        return filters_on_aggregates
