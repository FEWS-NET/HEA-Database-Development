from django_filters import rest_framework as filters
from rest_framework import viewsets

from .filters import MultiFieldFilter
from .models import ClassifiedProduct, Country, Currency, UnitOfMeasure
from .serializers import (
    ClassifiedProductSerializer,
    CountrySerializer,
    CurrencySerializer,
    UnitOfMeasureSerializer,
)


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


class CountryViewSet(viewsets.ModelViewSet):
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


class CurrencyViewSet(viewsets.ModelViewSet):
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
        fields = ["abbreviation", "description", "unit_type"]


class UnitOfMeasureViewSet(viewsets.ModelViewSet):
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
    search_fields = ["abbreviation", "description", "unit_type"]


class ClassifiedProductFilterSet(filters.FilterSet):
    """
    FilterSet for the ClassifiedProduct model.

    This FilterSet is used to apply filtering on the ClassifiedProduct model based on various filter fields.

    Attributes:
        cpcv2: A CharFilter for filtering by the CPCV2 value (case-insensitive contains lookup).
        description: A CharFilter for filtering by the description (case-insensitive contains lookup).
        common_name: A CharFilter for filtering by the common name (case-insensitive contains lookup).
        unit_of_measure: A ModelChoiceFilter for filtering by the associated UnitOfMeasure object.
                         The filter will display choices based on the available UnitOfMeasure objects.
    """

    cpcv2 = filters.CharFilter(lookup_expr="icontains", label="CPCV2")
    description = filters.CharFilter(lookup_expr="icontains", label="Description")
    common_name = filters.CharFilter(lookup_expr="icontains", label="Common Name")
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
        fields = ["cpcv2", "description", "common_name", "scientific_name", "unit_of_measure", "kcals_per_unit"]


class ClassifiedProductViewSet(viewsets.ModelViewSet):
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
    search_fields = ["cpcv2", "description", "common_name"]
