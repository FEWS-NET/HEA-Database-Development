from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as filters

from common.fields import translation_fields
from common.models import Country
from common.viewsets import BaseModelViewSet
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
    name_en = filters.CharFilter(lookup_expr="icontains", label=format_lazy("{} ({})", _("Name"), _("English")))
    name_fr = filters.CharFilter(lookup_expr="icontains", label=format_lazy("{} ({})", _("Name"), _("French")))
    name_es = filters.CharFilter(lookup_expr="icontains", label=format_lazy("{} ({})", _("Name"), _("Spanish")))
    name_ar = filters.CharFilter(lookup_expr="icontains", label=format_lazy("{} ({})", _("Name"), _("Arabic")))
    name_pt = filters.CharFilter(lookup_expr="icontains", label=format_lazy("{} ({})", _("Name"), _("Portuguese")))
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

    class Meta:
        model = ReferenceData
        fields = (
            *translation_fields("name"),
            *translation_fields("description"),
        )


class ReferenceDataViewSet(BaseModelViewSet):
    serializer_class = ReferenceDataSerializer
    filterset_class = ReferenceDataFilterSet
    search_fields = (
        "code",
        *translation_fields("name"),
        *translation_fields("description"),
        "aliases",
    )


class LivelihoodCategoryViewSet(ReferenceDataViewSet):
    queryset = LivelihoodCategory.objects.all()
    serializer_class = LivelihoodCategorySerializer


class WealthGroupCategoryViewSet(ReferenceDataViewSet):
    queryset = WealthGroupCategory.objects.all()
    serializer_class = WealthGroupCategorySerializer


class WealthCharacteristicFilterSet(ReferenceDataFilterSet):
    variable_type = filters.ChoiceFilter(
        choices=WealthCharacteristic.VariableType.choices,
    )

    class Meta:
        model = ReferenceData
        fields = (
            *translation_fields("name"),
            *translation_fields("description"),
            "variable_type",
        )


class WealthCharacteristicViewSet(ReferenceDataViewSet):
    queryset = WealthCharacteristic.objects.all()
    serializer_class = WealthCharacteristicSerializer
    filterset_class = WealthCharacteristicFilterSet
    search_fields = (
        "code",
        *translation_fields("name"),
        *translation_fields("description"),
        "variable_type",
        "aliases",
    )


class SeasonalActivityTypeFilterSet(ReferenceDataFilterSet):
    activity_category = filters.ChoiceFilter(
        choices=SeasonalActivityType.SeasonalActivityCategory.choices,
    )

    class Meta:
        model = ReferenceData
        fields = (
            *translation_fields("name"),
            *translation_fields("description"),
            "activity_category",
        )


class SeasonalActivityTypeViewSet(ReferenceDataViewSet):
    queryset = SeasonalActivityType.objects.all()
    serializer_class = SeasonalActivityTypeSerializer
    filterset_class = SeasonalActivityTypeFilterSet
    search_fields = (
        "code",
        *translation_fields("name"),
        *translation_fields("description"),
        "activity_category",
        "aliases",
    )


class HazardCategoryViewSet(ReferenceDataViewSet):
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
    name_en = filters.CharFilter(lookup_expr="icontains", label=format_lazy("{} ({})", _("Name"), _("English")))
    name_fr = filters.CharFilter(lookup_expr="icontains", label=format_lazy("{} ({})", _("Name"), _("French")))
    name_es = filters.CharFilter(lookup_expr="icontains", label=format_lazy("{} ({})", _("Name"), _("Spanish")))
    name_ar = filters.CharFilter(lookup_expr="icontains", label=format_lazy("{} ({})", _("Name"), _("Arabic")))
    name_pt = filters.CharFilter(lookup_expr="icontains", label=format_lazy("{} ({})", _("Name"), _("Portuguese")))
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

    class Meta:
        model = Season
        fields = (
            *translation_fields("name"),
            *translation_fields("description"),
            "season_type",
        )


class SeasonViewSet(BaseModelViewSet):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer
    filterset_class = SeasonFilterSet
    search_fields = (
        *translation_fields("name"),
        *translation_fields("description"),
        "season_type",
    )
