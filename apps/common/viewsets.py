from django.apps import apps
from django.contrib.auth.models import User
from django.db.models import Exists, OuterRef, Q
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotAcceptable
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission, IsAuthenticated

from common.filters import CaseInsensitiveModelMultipleChoiceFilter

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

    has_wealthgroups = filters.BooleanFilter(method="filter_has_wealthgroups")

    def filter_has_wealthgroups(self, queryset, name, value):
        if value is None:
            return queryset
        WealthGroup = apps.get_model("baseline", "WealthGroup")
        wealth_group_exists = WealthGroup.objects.filter(
            livelihood_zone_baseline__livelihood_zone__country=OuterRef("pk")
        )
        if value:
            return queryset.filter(Exists(wealth_group_exists))
        else:
            return queryset.exclude(Exists(wealth_group_exists))


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
    has_wealthgroups = filters.BooleanFilter(method="filter_has_wealthgroups")
    country = CaseInsensitiveModelMultipleChoiceFilter(queryset=Country.objects.all(), method="filter_by_country")

    def filter_has_wealthgroups(self, queryset, name, value):
        if value is None:
            return queryset

        WealthGroup = apps.get_model("baseline", "WealthGroup")

        # Get baseline IDs that have wealth groups
        baselines_with_wg = WealthGroup.objects.values_list("livelihood_zone_baseline_id", flat=True).distinct()

        if value:
            # Return products with strategies in those baselines
            return queryset.filter(livelihood_strategies__livelihood_zone_baseline_id__in=baselines_with_wg).distinct()
        else:
            return queryset

    def filter_by_country(self, queryset, name, value):
        if not value:
            return queryset

        country_queries = Q()
        for country in value:
            country_queries |= Q(
                livelihood_strategies__livelihood_zone_baseline__livelihood_zone__country__iso3166a2__iexact=country.iso3166a2
            )

        return queryset.filter(country_queries).distinct()

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
