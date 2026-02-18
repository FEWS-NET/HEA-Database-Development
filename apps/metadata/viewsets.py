from django.apps import apps
from django.db.models import Exists, OuterRef, Q
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _
from django_filters import rest_framework as filters

from common.fields import translation_fields
from common.filters import CaseInsensitiveModelMultipleChoiceFilter
from common.models import Country
from common.viewsets import BaseModelViewSet
from metadata.models import (
    HazardCategory,
    LivelihoodCategory,
    LivelihoodStrategyType,
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


class LivelihoodCategoryFilter(ReferenceDataFilterSet):

    has_wealthgroups = filters.BooleanFilter(method="filter_has_wealthgroups")
    country = CaseInsensitiveModelMultipleChoiceFilter(queryset=Country.objects.all(), method="filter_country")

    def filter_has_wealthgroups(self, queryset, name, value):
        if value is None:
            return queryset
        WealthGroup = apps.get_model("baseline", "WealthGroup")
        wealth_group_exists = WealthGroup.objects.filter(
            livelihood_zone_baseline__main_livelihood_category=OuterRef("pk")
        )
        if value:
            return queryset.filter(Exists(wealth_group_exists))
        else:
            return queryset.exclude(Exists(wealth_group_exists))

    def filter_country(self, queryset, name, value):
        if not value:
            return queryset

        country_queries = Q()
        for country in value:
            country_queries |= Q(livelihoodzonebaseline__livelihood_zone__country__iso3166a2__iexact=country.iso3166a2)

        return queryset.filter(country_queries).distinct()


class LivelihoodCategoryViewSet(ReferenceDataViewSet):
    queryset = LivelihoodCategory.objects.all()
    serializer_class = LivelihoodCategorySerializer
    filterset_class = LivelihoodCategoryFilter


class WealthGroupCategoryFilter(ReferenceDataFilterSet):

    has_wealthgroups = filters.BooleanFilter(
        field_name="wealth_groups",
        lookup_expr="isnull",
        exclude=True,
        label="Has wealth groups",
    )


class WealthGroupCategoryViewSet(ReferenceDataViewSet):
    queryset = WealthGroupCategory.objects.all()
    filterset_class = WealthGroupCategoryFilter
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
    purpose = filters.ChoiceFilter(
        choices=LivelihoodStrategyType.choices,
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
        "purpose",
    )
    ordering = ("country", "order")
