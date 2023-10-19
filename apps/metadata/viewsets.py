from django_filters import rest_framework as filters
from rest_framework import viewsets

from common.models import Country
from metadata.models import (
    HazardCategory,
    LivelihoodCategory,
    ReferenceData,
    Season,
    SeasonalActivityType,
    WealthCharacteristic,
    WealthGroupCategory,
)
from metadata.serializers import (
    HazardCategorySerializer,
    LivelihoodCategorySerializer,
    ReferenceDataSerializer,
    SeasonalActivityTypeSerializer,
    SeasonSerializer,
    WealthCharacteristicSerializer,
    WealthGroupCategorySerializer,
)


class ReferenceDataFilterSet(filters.FilterSet):
    """ """

    name = filters.CharFilter(
        field_name="name",
        lookup_expr="icontains",
        label="Name",
    )
    description = filters.CharFilter(
        field_name="description",
        lookup_expr="icontains",
        label="Description",
    )

    class Meta:
        model = ReferenceData
        fields = ["name", "description"]


class ReferenceDataViewSet(viewsets.ModelViewSet):
    """ """

    serializer_class = ReferenceDataSerializer
    filterset_class = ReferenceDataFilterSet
    search_fields = ["code", "name", "description", "aliases"]


class LivelihoodCategoryViewSet(ReferenceDataViewSet):
    """ """

    queryset = LivelihoodCategory.objects.all()
    serializer_class = LivelihoodCategorySerializer


class WealthGroupCategoryViewSet(ReferenceDataViewSet):
    """ """

    queryset = WealthGroupCategory.objects.all()
    serializer_class = WealthGroupCategorySerializer


class WealthCharacteristicFilterSet(ReferenceDataFilterSet):
    """ """

    variable_type = filters.ChoiceFilter(
        choices=WealthCharacteristic.VariableType.choices,
    )

    class Meta:
        model = ReferenceData
        fields = ["name", "description", "variable_type"]


class WealthCharacteristicViewSet(ReferenceDataViewSet):
    """ """

    queryset = WealthCharacteristic.objects.all()
    serializer_class = WealthCharacteristicSerializer
    filterset_class = WealthCharacteristicFilterSet
    search_fields = ["code", "name", "description", "variable_type", "aliases"]


class SeasonalActivityTypeFilterSet(ReferenceDataFilterSet):
    """ """

    activity_category = filters.ChoiceFilter(
        choices=SeasonalActivityType.SeasonalActivityCategory.choices,
    )

    class Meta:
        model = ReferenceData
        fields = [
            "name",
            "description",
            "activity_category",
        ]


class SeasonalActivityTypeViewSet(ReferenceDataViewSet):
    """ """

    queryset = SeasonalActivityType.objects.all()
    serializer_class = SeasonalActivityTypeSerializer
    filterset_class = SeasonalActivityTypeFilterSet
    search_fields = ["code", "name", "description", "activity_category", "aliases"]


class HazardCategoryViewSet(ReferenceDataViewSet):
    """ """

    queryset = HazardCategory.objects.all()
    serializer_class = HazardCategorySerializer


class SeasonFilterSet(filters.FilterSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["country"].extra["choices"] = [
            (c.pk, c.iso_en_name) for c in Country.objects.all().order_by("iso_en_name")
        ]

    country = filters.MultipleChoiceFilter(
        field_name="country",
        choices=[],
        label="Country ISO 3166-1 alpha-2 Code",
        distinct=False,
    )
    season_type = filters.ChoiceFilter(
        choices=Season.SeasonType.choices,
    )
    name = filters.CharFilter(
        field_name="name",
        lookup_expr="icontains",
        label="Name",
    )
    description = filters.CharFilter(
        field_name="description",
        lookup_expr="icontains",
        label="Description",
    )

    class Meta:
        model = Season
        fields = ("name", "description", "season_type")


class SeasonViewSet(viewsets.ModelViewSet):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer
    filterset_class = SeasonFilterSet
    search_fields = ["name", "description", "season_type"]
