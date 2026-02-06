from django.apps import apps
from django.conf import settings
from django.db import models
from django.db.models import Expression, F, Q, Subquery, TextField, Value
from django.db.models.functions import Coalesce, NullIf
from django.utils import translation
from django.utils.decorators import method_decorator
from django.utils.translation import override
from django.views.decorators.cache import cache_page
from django.views.decorators.http import condition
from django_filters import rest_framework as filters
from django_filters.filters import CharFilter
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from common.fields import translation_fields
from common.filters import MultiFieldFilter, UpperCaseFilter
from common.utils import make_condition_funcs
from common.filters import DefaultingDateFilter, MultiFieldFilter, UpperCaseFilter
from common.viewsets import AggregatingViewSet, BaseModelViewSet
from metadata.models import WealthGroupCategory

from .models import (
    BaselineLivelihoodActivity,
    BaselineWealthGroup,
    BaselineWealthGroupCharacteristicValue,
    ButterProduction,
    Community,
    CommunityCropProduction,
    CommunityLivestock,
    CommunityWealthGroup,
    CommunityWealthGroupCharacteristicValue,
    CopingStrategy,
    CropProduction,
    Event,
    ExpandabilityFactor,
    Fishing,
    FoodPurchase,
    Hazard,
    Hunting,
    LivelihoodActivity,
    LivelihoodProductCategory,
    LivelihoodStrategy,
    LivelihoodZone,
    LivelihoodZoneBaseline,
    LivestockSale,
    MarketPrice,
    MeatProduction,
    MilkProduction,
    OtherCashIncome,
    OtherPurchase,
    PaymentInKind,
    ReliefGiftOther,
    ResponseLivelihoodActivity,
    SeasonalActivity,
    SeasonalActivityOccurrence,
    SeasonalProductionPerformance,
    SourceOrganization,
    WealthGroup,
    WealthGroupCharacteristicValue,
    WildFoodGathering,
)
from .serializers import (
    BaselineLivelihoodActivitySerializer,
    BaselineWealthGroupCharacteristicValueSerializer,
    BaselineWealthGroupSerializer,
    ButterProductionSerializer,
    CommunityCropProductionSerializer,
    CommunityLivestockSerializer,
    CommunitySerializer,
    CommunityWealthGroupCharacteristicValueSerializer,
    CommunityWealthGroupSerializer,
    CopingStrategySerializer,
    CropProductionSerializer,
    EventSerializer,
    ExpandabilityFactorSerializer,
    FishingSerializer,
    FoodPurchaseSerializer,
    HazardSerializer,
    HuntingSerializer,
    LivelihoodActivitySerializer,
    LivelihoodActivitySummarySerializer,
    LivelihoodProductCategorySerializer,
    LivelihoodStrategySerializer,
    LivelihoodZoneBaselineGeoSerializer,
    LivelihoodZoneBaselineSerializer,
    LivelihoodZoneSerializer,
    LivestockSaleSerializer,
    MarketPriceSerializer,
    MeatProductionSerializer,
    MilkProductionSerializer,
    OtherCashIncomeSerializer,
    OtherPurchaseSerializer,
    PaymentInKindSerializer,
    ReliefGiftOtherSerializer,
    ResponseLivelihoodActivitySerializer,
    SeasonalActivityOccurrenceSerializer,
    SeasonalActivitySerializer,
    SeasonalProductionPerformanceSerializer,
    SourceOrganizationSerializer,
    WealthGroupCharacteristicValueSerializer,
    WealthGroupSerializer,
    WildFoodGatheringSerializer,
)

# Create condition functions for LivelihoodZoneBaseline endpoint caching
get_baseline_etag, get_baseline_last_modified = make_condition_funcs(LivelihoodZoneBaseline)


class SourceOrganizationFilterSet(filters.FilterSet):
    class Meta:
        model = SourceOrganization
        fields = [
            "name",
            "full_name",
            "description",
        ]


class SourceOrganizationViewSet(BaseModelViewSet):
    """
    API endpoint that allows source organizations to be viewed or edited.
    """

    queryset = SourceOrganization.objects.all()
    serializer_class = SourceOrganizationSerializer
    filterset_class = SourceOrganizationFilterSet
    search_fields = [
        "description",
        "full_name",
        "name",
    ]


class LivelihoodZoneFilterSet(filters.FilterSet):
    class Meta:
        model = LivelihoodZone
        fields = (
            "code",
            *translation_fields("description"),
            *translation_fields("name"),
        )

    country = MultiFieldFilter(
        [
            "country__iso3166a2",
            "country__iso_en_ro_name",
            "country__iso_en_name",
            "country__iso_en_ro_proper",
            "country__iso_en_proper",
            "country__iso_fr_name",
            "country__iso_fr_proper",
            "country__iso_es_name",
        ],
        lookup_expr="iexact",
        label="Country",
    )


class LivelihoodZoneViewSet(BaseModelViewSet):
    """
    API endpoint that allows livelihood zones to be viewed or edited.
    """

    queryset = LivelihoodZone.objects.select_related(
        "country",
    )
    serializer_class = LivelihoodZoneSerializer
    filterset_class = LivelihoodZoneFilterSet
    search_fields = (
        "code",
        "alternate_code",
        *translation_fields("description"),
        *translation_fields("name"),
    )


class LivelihoodZoneBaselineFilterSet(filters.FilterSet):
    class Meta:
        model = LivelihoodZoneBaseline
        fields = (
            "livelihood_zone",
            "main_livelihood_category",
            "source_organization",
            "reference_year_start_date",
            "reference_year_end_date",
            "valid_from_date",
            "valid_to_date",
            "population_source",
            "currency",
            *translation_fields("description"),
            *translation_fields("name"),
        )

    country = MultiFieldFilter(
        [
            "livelihood_zone__country__iso3166a2",
            "livelihood_zone__country__iso_en_ro_name",
            "livelihood_zone__country__iso_en_name",
            "livelihood_zone__country__iso_en_ro_proper",
            "livelihood_zone__country__iso_en_proper",
            "livelihood_zone__country__iso_fr_name",
            "livelihood_zone__country__iso_fr_proper",
            "livelihood_zone__country__iso_es_name",
        ],
        lookup_expr="iexact",
        label="Country",
    )
    population_estimate = filters.RangeFilter(label="Population estimate range")
    product = CharFilter(method="filter_by_product", label="Filter by Product")
    wealth_characteristic = CharFilter(
        method="filter_by_wealth_characteristic", label="Filter by Wealth Characteristic"
    )
    as_of_date = DefaultingDateFilter(
        label="As of Date",
        help_text="Filter baselines valid as of this date (YYYY-MM-DD format or special values like 'today').",
    )

    def filter_by_product(self, queryset, name, value):
        """
        Filter the baseline by matching products
        """
        field_lookups = [
            *[(field, "icontains") for field in translation_fields("product__common_name")],
            ("product__cpc", "istartswith"),
            *[(field, "icontains") for field in translation_fields("product__description")],
            ("product__aliases", "icontains"),
        ]

        q_object = Q()
        for field, lookup in field_lookups:
            q_object |= Q(**{f"{field}__{lookup}": value})

        matching_baselines = LivelihoodStrategy.objects.filter(q_object).values("livelihood_zone_baseline")

        return queryset.filter(id__in=Subquery(matching_baselines))

    def filter_by_wealth_characteristic(self, queryset, name, value):
        """
        Filter the baseline by matching wealth_characteristic
        """
        field_lookups = [
            *[(field, "icontains") for field in translation_fields("wealth_characteristic__name")],
            ("wealth_characteristic__code", "iexact"),
            *[(field, "icontains") for field in translation_fields("wealth_characteristic__description")],
            ("wealth_characteristic__aliases", "icontains"),
        ]

        q_object = Q()
        for field, lookup in field_lookups:
            q_object |= Q(**{f"{field}__{lookup}": value})

        matching_baselines = WealthGroupCharacteristicValue.objects.filter(q_object).values(
            "wealth_group__livelihood_zone_baseline"
        )

        return queryset.filter(id__in=Subquery(matching_baselines))


class LivelihoodZoneBaselineViewSet(BaseModelViewSet):
    """
    API endpoint that allows livelihood zone baselines to be viewed or edited.
    """

    queryset = LivelihoodZoneBaseline.objects.select_related(
        "livelihood_zone__country",
        "source_organization",
    )
    serializer_class = LivelihoodZoneBaselineSerializer
    filterset_class = LivelihoodZoneBaselineFilterSet
    search_fields = (
        *translation_fields("description"),
        *translation_fields("name"),
        "population_source",
    )
    ordering_fields = ["livelihood_zone__code", "reference_year_end_date"]
    ordering = ["livelihood_zone__code", "reference_year_end_date"]

    def get_serializer_class(self):
        if self.request.accepted_renderer.format == "geojson":
            return LivelihoodZoneBaselineGeoSerializer  # Use GeoFeatureModelSerializer for GeoJSON
        return LivelihoodZoneBaselineSerializer

    @method_decorator(cache_page(60 * 60 * 24))  # Cache on server for 24 hours - must be above condition per RFC 9110
    @method_decorator(condition(etag_func=get_baseline_etag, last_modified_func=get_baseline_last_modified))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class LivelihoodProductCategoryFilterSet(filters.FilterSet):
    class Meta:
        model = LivelihoodProductCategory
        fields = [
            "baseline_livelihood_activity",
            "basket",
        ]


class LivelihoodProductCategoryViewSet(BaseModelViewSet):
    """
    API endpoint that allows livelihood product categories to be viewed or edited.
    """

    queryset = LivelihoodProductCategory.objects.select_related(
        "baseline_livelihood_activity__livelihood_zone_baseline__livelihood_zone__country",
        "baseline_livelihood_activity__livelihood_zone_baseline__source_organization",
        "baseline_livelihood_activity__livelihood_strategy__product",
    )
    serializer_class = LivelihoodProductCategorySerializer
    filterset_class = LivelihoodProductCategoryFilterSet


class CommunityFilterSet(filters.FilterSet):
    class Meta:
        model = Community
        fields = [
            "code",
            "name",
            "full_name",
            "livelihood_zone_baseline",
        ]

    country = MultiFieldFilter(
        [
            "livelihood_zone_baseline__livelihood_zone__country__iso3166a2",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_ro_name",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_name",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_ro_proper",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_proper",
            "livelihood_zone_baseline__livelihood_zone__country__iso_fr_name",
            "livelihood_zone_baseline__livelihood_zone__country__iso_fr_proper",
            "livelihood_zone_baseline__livelihood_zone__country__iso_es_name",
        ],
        lookup_expr="iexact",
        label="Country",
    )


class CommunityViewSet(BaseModelViewSet):
    """
    API endpoint that allows communities to be viewed or edited.
    """

    queryset = Community.objects.select_related(
        "livelihood_zone_baseline__livelihood_zone__country",
        "livelihood_zone_baseline__source_organization",
    )
    serializer_class = CommunitySerializer
    filterset_class = CommunityFilterSet
    search_fields = [
        "code",
        "name",
    ]


class WealthGroupFilterSet(filters.FilterSet):
    class Meta:
        model = WealthGroup
        fields = [
            "livelihood_zone_baseline",
            "community",
            "wealth_group_category",
        ]

    country = MultiFieldFilter(
        [
            "livelihood_zone_baseline__livelihood_zone__country__iso3166a2",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_ro_name",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_name",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_ro_proper",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_proper",
            "livelihood_zone_baseline__livelihood_zone__country__iso_fr_name",
            "livelihood_zone_baseline__livelihood_zone__country__iso_fr_proper",
            "livelihood_zone_baseline__livelihood_zone__country__iso_es_name",
        ],
        lookup_expr="iexact",
        label="Country",
    )


class WealthGroupViewSet(BaseModelViewSet):
    """
    API endpoint that allows wealth groups to be viewed or edited.
    """

    queryset = WealthGroup.objects.select_related(
        # Normally it would be better to join to livelihood_zone_baseline via community,
        # but baseline wealth groups don't have a community join.
        "community",
        "livelihood_zone_baseline__livelihood_zone__country",
        "livelihood_zone_baseline__source_organization",
    )
    serializer_class = WealthGroupSerializer
    filterset_class = WealthGroupFilterSet
    ordering = [
        "livelihood_zone_baseline__livelihood_zone__code",
        "livelihood_zone_baseline__reference_year_end_date",
        "wealth_group_category__ordering",
        "community__name",
    ]


class BaselineWealthGroupFilterSet(filters.FilterSet):
    class Meta:
        model = BaselineWealthGroup
        fields = [
            "livelihood_zone_baseline",
            "wealth_group_category",
        ]

    country = MultiFieldFilter(
        [
            "livelihood_zone_baseline__livelihood_zone__country__iso3166a2",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_ro_name",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_name",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_ro_proper",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_proper",
            "livelihood_zone_baseline__livelihood_zone__country__iso_fr_name",
            "livelihood_zone_baseline__livelihood_zone__country__iso_fr_proper",
            "livelihood_zone_baseline__livelihood_zone__country__iso_es_name",
        ],
        lookup_expr="iexact",
        label="Country",
    )


class BaselineWealthGroupViewSet(BaseModelViewSet):
    """
    API endpoint that allows baseline wealth groups to be viewed or edited.
    """

    queryset = BaselineWealthGroup.objects.select_related(
        "livelihood_zone_baseline__livelihood_zone__country",
        "livelihood_zone_baseline__source_organization",
    )
    serializer_class = BaselineWealthGroupSerializer
    filterset_class = BaselineWealthGroupFilterSet


class CommunityWealthGroupFilterSet(filters.FilterSet):
    class Meta:
        model = CommunityWealthGroup
        fields = [
            "livelihood_zone_baseline",
            "community",
            "wealth_group_category",
        ]

    country = MultiFieldFilter(
        [
            "community__livelihood_zone_baseline__livelihood_zone__country__iso3166a2",
            "community__livelihood_zone_baseline__livelihood_zone__country__iso_en_ro_name",
            "community__livelihood_zone_baseline__livelihood_zone__country__iso_en_name",
            "community__livelihood_zone_baseline__livelihood_zone__country__iso_en_ro_proper",
            "community__livelihood_zone_baseline__livelihood_zone__country__iso_en_proper",
            "community__livelihood_zone_baseline__livelihood_zone__country__iso_fr_name",
            "community__livelihood_zone_baseline__livelihood_zone__country__iso_fr_proper",
            "community__livelihood_zone_baseline__livelihood_zone__country__iso_es_name",
        ],
        lookup_expr="iexact",
        label="Country",
    )


class CommunityWealthGroupViewSet(BaseModelViewSet):
    """
    API endpoint that allows community wealth groups to be viewed or edited.
    """

    queryset = CommunityWealthGroup.objects.select_related(
        "community__livelihood_zone_baseline__livelihood_zone__country",
        "community__livelihood_zone_baseline__source_organization",
    )
    serializer_class = CommunityWealthGroupSerializer
    filterset_class = CommunityWealthGroupFilterSet


class WealthGroupCharacteristicValueFilterSet(filters.FilterSet):
    class Meta:
        model = WealthGroupCharacteristicValue
        fields = [
            "wealth_characteristic",
            "wealth_group",
        ]

    livelihood_zone_baseline = filters.ModelMultipleChoiceFilter(
        field_name="wealth_group__community__livelihood_zone_baseline",
        queryset=LivelihoodZoneBaseline.objects.all(),
        label="Livelihood zone baseline",
    )
    wealth_group_category = filters.ModelMultipleChoiceFilter(
        field_name="wealth_group__community__wealth_group_category",
        queryset=WealthGroupCategory.objects.all(),
        label="Wealth group category",
    )
    country = MultiFieldFilter(
        [
            "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country__iso3166a2",
            "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country__iso_en_ro_name",
            "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country__iso_en_name",
            "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country__iso_en_ro_proper",
            "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country__iso_en_proper",
            "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country__iso_fr_name",
            "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country__iso_fr_proper",
            "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country__iso_es_name",
        ],
        lookup_expr="iexact",
        label="Country",
    )
    product = MultiFieldFilter(
        [
            *[(field, "icontains") for field in translation_fields("product__common_name")],
            ("product__cpc", "istartswith"),
            *[(field, "icontains") for field in translation_fields("product__description")],
            ("product__aliases", "icontains"),
        ],
        label="Product",
    )


class WealthGroupCharacteristicValueViewSet(BaseModelViewSet):
    """
    API endpoint that allows wealth characteristic values to be viewed or edited.
    """

    queryset = WealthGroupCharacteristicValue.objects.select_related(
        # Rule of thumb: When there is a choice of routes, eg, here we could use
        # "wealth_group__community__livelihood_zone_baseline" or
        # "wealth_group__livelihood_zone_baseline" (ie, not going via community),
        # favour the option with the lowest cardinality.
        # Here for example, if I use wealth_group__livelihood_zone_baseline, the
        # Django ORM will have to populate a LivelihoodZoneBaseline instance for
        # every WealthGroup instance. By going via the community join, the Django
        # ORM only has to populate a LivelihoodZoneBaseline per Community, which
        # will be 4 or 5 times fewer instances. We also remove the need for a third
        # select_related parameter "wealth_group__community". Performance is not
        # critical, but we need a rule of thumb so everything matches up.
        "wealth_characteristic",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = WealthGroupCharacteristicValueSerializer
    filterset_class = WealthGroupCharacteristicValueFilterSet
    ordering = [
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__code",
        "wealth_group__community__livelihood_zone_baseline__reference_year_end_date",
        "wealth_group__wealth_group_category__ordering",
        "wealth_group__community__name",
        "wealth_characteristic__ordering",
        "product",
        "wealth_characteristic__code",
    ]


class BaselineWealthGroupCharacteristicValueFilterSet(filters.FilterSet):
    class Meta:
        model = BaselineWealthGroupCharacteristicValue
        fields = [
            "wealth_characteristic",
            "wealth_group",
        ]

    livelihood_zone_baseline = filters.ModelMultipleChoiceFilter(
        field_name="wealth_group__livelihood_zone_baseline",
        queryset=LivelihoodZoneBaseline.objects.all(),
        label="Livelihood zone baseline",
    )
    wealth_group_category = filters.ModelMultipleChoiceFilter(
        field_name="wealth_group__wealth_group_category",
        queryset=WealthGroupCategory.objects.all(),
        label="Wealth group category",
    )
    country = MultiFieldFilter(
        [
            "wealth_group__livelihood_zone_baseline__livelihood_zone__country__iso3166a2",
            "wealth_group__livelihood_zone_baseline__livelihood_zone__country__iso_en_ro_name",
            "wealth_group__livelihood_zone_baseline__livelihood_zone__country__iso_en_name",
            "wealth_group__livelihood_zone_baseline__livelihood_zone__country__iso_en_ro_proper",
            "wealth_group__livelihood_zone_baseline__livelihood_zone__country__iso_en_proper",
            "wealth_group__livelihood_zone_baseline__livelihood_zone__country__iso_fr_name",
            "wealth_group__livelihood_zone_baseline__livelihood_zone__country__iso_fr_proper",
            "wealth_group__livelihood_zone_baseline__livelihood_zone__country__iso_es_name",
        ],
        lookup_expr="iexact",
        label="Country",
    )
    product = MultiFieldFilter(
        [
            *[(field, "icontains") for field in translation_fields("product__common_name")],
            ("product__cpc", "istartswith"),
            *[(field, "icontains") for field in translation_fields("product__description")],
            ("product__aliases", "icontains"),
        ],
        label="Product",
    )

    has_value = filters.BooleanFilter(
        method="filter_has_value",
        label="Has Value",
    )

    def filter_has_value(self, queryset, name, value):
        """
        Filter records based on whether they have meaningful values.
        """
        if value is False:
            return queryset.filter(
                Q(value__isnull=True)
                | Q(value__exact="")
                | Q(value__exact=0)
                | Q(value__exact=[])
                | Q(value__exact={})
            )
        else:
            # This ensures that specifying the filter without a value still returns only records with meaningful values
            return queryset.exclude(
                Q(value__isnull=True)
                | Q(value__exact="")
                | Q(value__exact=0)
                | Q(value__exact=[])
                | Q(value__exact={})
            )


class BaselineWealthGroupCharacteristicValueViewSet(BaseModelViewSet):
    """
    API endpoint that allows wealth characteristic values for baseline wealth groups to be viewed or edited.
    """

    queryset = BaselineWealthGroupCharacteristicValue.objects.select_related(
        "wealth_characteristic",
        "wealth_group__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = BaselineWealthGroupCharacteristicValueSerializer
    filterset_class = BaselineWealthGroupCharacteristicValueFilterSet
    ordering = [
        "wealth_group__livelihood_zone_baseline__livelihood_zone__code",
        "wealth_group__livelihood_zone_baseline__reference_year_end_date",
        "wealth_group__wealth_group_category__ordering",
        "wealth_characteristic__ordering",
        "product",
        "wealth_characteristic__code",
    ]


class CommunityWealthGroupCharacteristicValueFilterSet(filters.FilterSet):
    class Meta:
        model = CommunityWealthGroupCharacteristicValue
        fields = [
            "wealth_characteristic",
            "wealth_group",
        ]

    livelihood_zone_baseline = filters.ModelMultipleChoiceFilter(
        field_name="wealth_group__community__livelihood_zone_baseline",
        queryset=LivelihoodZoneBaseline.objects.all(),
        label="Livelihood zone baseline",
    )
    country = MultiFieldFilter(
        [
            "wealth_group__livelihood_zone_baseline__livelihood_zone__country__iso3166a2",
            "wealth_group__livelihood_zone_baseline__livelihood_zone__country__iso_en_ro_name",
            "wealth_group__livelihood_zone_baseline__livelihood_zone__country__iso_en_name",
            "wealth_group__livelihood_zone_baseline__livelihood_zone__country__iso_en_ro_proper",
            "wealth_group__livelihood_zone_baseline__livelihood_zone__country__iso_en_proper",
            "wealth_group__livelihood_zone_baseline__livelihood_zone__country__iso_fr_name",
            "wealth_group__livelihood_zone_baseline__livelihood_zone__country__iso_fr_proper",
            "wealth_group__livelihood_zone_baseline__livelihood_zone__country__iso_es_name",
        ],
        lookup_expr="iexact",
        label="Country",
    )
    product = MultiFieldFilter(
        [
            *[(field, "icontains") for field in translation_fields("product__common_name")],
            ("product__cpc", "istartswith"),
            *[(field, "icontains") for field in translation_fields("product__description")],
            ("product__aliases", "icontains"),
        ],
        label="Product",
    )
    has_value = filters.BooleanFilter(
        method="filter_has_value",
        label="Has Value",
    )

    def filter_has_value(self, queryset, name, value):
        """
        Filter records based on whether they have meaningful values.
        """
        if value is False:
            return queryset.filter(
                Q(value__isnull=True)
                | Q(value__exact="")
                | Q(value__exact=0)
                | Q(value__exact=[])
                | Q(value__exact={})
            )
        else:
            return queryset.exclude(
                Q(value__isnull=True)
                | Q(value__exact="")
                | Q(value__exact=0)
                | Q(value__exact=[])
                | Q(value__exact={})
            )


class CommunityWealthGroupCharacteristicValueViewSet(BaseModelViewSet):
    """
    API endpoint that allows wealth characteristic values for community wealth groups to be viewed or edited.
    """

    queryset = CommunityWealthGroupCharacteristicValue.objects.select_related(
        # Rule of thumb: When there is a choice of routes, eg, here we could use
        # "wealth_group__community__livelihood_zone_baseline" or
        # "wealth_group__livelihood_zone_baseline" (ie, not going via community),
        # favour the option with the lowest cardinality.
        # Here for example, if I use wealth_group__livelihood_zone_baseline, the
        # Django ORM will have to populate a LivelihoodZoneBaseline instance for
        # every WealthGroup instance. By going via the community join, the Django
        # ORM only has to populate a LivelihoodZoneBaseline per Community, which
        # will be 4 or 5 times fewer instances. We also remove the need for a third
        # select_related parameter "wealth_group__community". Performance is not
        # critical, but we need a rule of thumb so everything matches up.
        "wealth_characteristic",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = CommunityWealthGroupCharacteristicValueSerializer
    filterset_class = CommunityWealthGroupCharacteristicValueFilterSet
    ordering = [
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__code",
        "wealth_group__community__livelihood_zone_baseline__reference_year_end_date",
        "wealth_group__wealth_group_category__ordering",
        "wealth_group__community__name",
        "wealth_characteristic__ordering",
        "product",
        "wealth_characteristic__code",
    ]


class LivelihoodStrategyFilterSet(filters.FilterSet):
    class Meta:
        model = LivelihoodStrategy
        fields = [
            "livelihood_zone_baseline",
            "strategy_type",
            "season",
            "product",
            "unit_of_measure",
            "currency",
            "additional_identifier",
        ]

    country = MultiFieldFilter(
        [
            "livelihood_zone_baseline__livelihood_zone__country__iso3166a2",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_ro_name",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_name",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_ro_proper",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_proper",
            "livelihood_zone_baseline__livelihood_zone__country__iso_fr_name",
            "livelihood_zone_baseline__livelihood_zone__country__iso_fr_proper",
            "livelihood_zone_baseline__livelihood_zone__country__iso_es_name",
        ],
        lookup_expr="iexact",
        label="Country",
    )
    product = MultiFieldFilter(
        [
            *[(field, "icontains") for field in translation_fields("product__common_name")],
            ("product__cpc", "istartswith"),
            *[(field, "icontains") for field in translation_fields("product__description")],
            ("product__aliases", "icontains"),
        ],
        label="Product",
    )
    cpc = UpperCaseFilter("product__cpc", lookup_expr="startswith", label="Product code (CPC)")


class LivelihoodStrategyViewSet(BaseModelViewSet):
    """
    API endpoint that allows livelihood strategies to be viewed or edited.
    """

    queryset = LivelihoodStrategy.objects.select_related(
        "livelihood_zone_baseline__livelihood_zone__country",
        "livelihood_zone_baseline__source_organization",
        "season",
        "unit_of_measure",
    )
    serializer_class = LivelihoodStrategySerializer
    filterset_class = LivelihoodStrategyFilterSet
    search_fields = [
        "additional_identifier",
        "strategy_type",
    ]


class LivelihoodActivityFilterSet(filters.FilterSet):
    class Meta:
        model = LivelihoodActivity
        fields = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
        ]

    country = MultiFieldFilter(
        [
            "livelihood_zone_baseline__livelihood_zone__country__iso3166a2",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_ro_name",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_name",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_ro_proper",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_proper",
            "livelihood_zone_baseline__livelihood_zone__country__iso_fr_name",
            "livelihood_zone_baseline__livelihood_zone__country__iso_fr_proper",
            "livelihood_zone_baseline__livelihood_zone__country__iso_es_name",
        ],
        lookup_expr="iexact",
        label="Country",
    )
    product = MultiFieldFilter(
        [
            *[(field, "icontains") for field in translation_fields("livelihood_strategy__product__common_name")],
            ("livelihood_strategy__product__cpc", "istartswith"),
            *[(field, "icontains") for field in translation_fields("livelihood_strategy__product__description")],
            ("livelihood_strategy__product__aliases", "icontains"),
        ],
        label="Product",
    )
    cpc = UpperCaseFilter("livelihood_strategy__product__cpc", lookup_expr="startswith", label="Product code (CPC)")


class LivelihoodActivityViewSet(BaseModelViewSet):
    """
    API endpoint that allows livelihood activities to be viewed or edited.
    """

    queryset = LivelihoodActivity.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = LivelihoodActivitySerializer
    filterset_class = LivelihoodActivityFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class BaselineLivelihoodActivityFilterSet(filters.FilterSet):
    class Meta:
        model = BaselineLivelihoodActivity
        fields = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
        ]

    country = MultiFieldFilter(
        [
            "livelihood_zone_baseline__livelihood_zone__country__iso3166a2",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_ro_name",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_name",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_ro_proper",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_proper",
            "livelihood_zone_baseline__livelihood_zone__country__iso_fr_name",
            "livelihood_zone_baseline__livelihood_zone__country__iso_fr_proper",
            "livelihood_zone_baseline__livelihood_zone__country__iso_es_name",
        ],
        lookup_expr="iexact",
        label="Country",
    )


class BaselineLivelihoodActivityViewSet(BaseModelViewSet):
    """
    API endpoint that allows baseline livelihood activities to be viewed or edited.
    """

    queryset = BaselineLivelihoodActivity.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = BaselineLivelihoodActivitySerializer
    filterset_class = BaselineLivelihoodActivityFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class ResponseLivelihoodActivityFilterSet(filters.FilterSet):
    class Meta:
        model = ResponseLivelihoodActivity
        fields = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
        ]

    country = MultiFieldFilter(
        [
            "livelihood_zone_baseline__livelihood_zone__country__iso3166a2",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_ro_name",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_name",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_ro_proper",
            "livelihood_zone_baseline__livelihood_zone__country__iso_en_proper",
            "livelihood_zone_baseline__livelihood_zone__country__iso_fr_name",
            "livelihood_zone_baseline__livelihood_zone__country__iso_fr_proper",
            "livelihood_zone_baseline__livelihood_zone__country__iso_es_name",
        ],
        lookup_expr="iexact",
        label="Country",
    )


class ResponseLivelihoodActivityViewSet(BaseModelViewSet):
    """
    API endpoint that allows response livelihood activities to be viewed or edited.
    """

    queryset = ResponseLivelihoodActivity.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = ResponseLivelihoodActivitySerializer
    filterset_class = ResponseLivelihoodActivityFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class MilkProductionFilterSet(filters.FilterSet):
    class Meta:
        model = MilkProduction
        fields = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "milking_animals",
            "lactation_days",
            "daily_production",
            "type_of_milk_sold_or_other_uses",
        ]


class MilkProductionViewSet(BaseModelViewSet):
    """
    API endpoint that allows milk production to be viewed or edited.
    """

    queryset = MilkProduction.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = MilkProductionSerializer
    filterset_class = MilkProductionFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
        "type_of_milk_sold_or_other_uses",
    ]


class ButterProductionFilterSet(filters.FilterSet):
    class Meta:
        model = ButterProduction
        fields = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
        ]


class ButterProductionViewSet(BaseModelViewSet):
    """
    API endpoint that allows butter production to be viewed or edited.
    """

    queryset = ButterProduction.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = ButterProductionSerializer
    filterset_class = ButterProductionFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class MeatProductionFilterSet(filters.FilterSet):
    class Meta:
        model = MeatProduction
        fields = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "animals_slaughtered",
            "carcass_weight",
        ]


class MeatProductionViewSet(BaseModelViewSet):
    """
    API endpoint that allows meat production to be viewed or edited.
    """

    queryset = MeatProduction.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = MeatProductionSerializer
    filterset_class = MeatProductionFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class LivestockSaleFilterSet(filters.FilterSet):
    class Meta:
        model = LivestockSale
        fields = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
        ]


class LivestockSaleViewSet(BaseModelViewSet):
    """
    API endpoint that allows livestock sales to be viewed or edited.
    """

    queryset = LivestockSale.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = LivestockSaleSerializer
    filterset_class = LivestockSaleFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class CropProductionFilterSet(filters.FilterSet):
    class Meta:
        model = CropProduction
        fields = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
        ]


class CropProductionViewSet(BaseModelViewSet):
    """
    API endpoint that allows crop production to be viewed or edited.
    """

    queryset = CropProduction.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = CropProductionSerializer
    filterset_class = CropProductionFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class FoodPurchaseFilterSet(filters.FilterSet):
    class Meta:
        model = FoodPurchase
        fields = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "unit_multiple",
            "times_per_month",
            "months_per_year",
        ]


class FoodPurchaseViewSet(BaseModelViewSet):
    """
    API endpoint that allows food purchases to be viewed or edited.
    """

    queryset = FoodPurchase.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = FoodPurchaseSerializer
    filterset_class = FoodPurchaseFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class PaymentInKindFilterSet(filters.FilterSet):
    class Meta:
        model = PaymentInKind
        fields = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "payment_per_time",
            "people_per_household",
            "times_per_month",
            "months_per_year",
        ]


class PaymentInKindViewSet(BaseModelViewSet):
    """
    API endpoint that allows payments in kind to be viewed or edited.
    """

    queryset = PaymentInKind.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = PaymentInKindSerializer
    filterset_class = PaymentInKindFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class ReliefGiftOtherFilterSet(filters.FilterSet):
    class Meta:
        model = ReliefGiftOther
        fields = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "unit_multiple",
            "times_per_year",
        ]


class ReliefGiftOtherViewSet(BaseModelViewSet):
    """
    API endpoint that allows relief, gifts and other food to be viewed or edited.
    """

    queryset = ReliefGiftOther.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = ReliefGiftOtherSerializer
    filterset_class = ReliefGiftOtherFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class FishingFilterSet(filters.FilterSet):
    class Meta:
        model = Fishing
        fields = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
        ]


class HuntingFilterSet(filters.FilterSet):
    class Meta:
        model = Hunting
        fields = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
        ]


class HuntingViewSet(BaseModelViewSet):
    """
    API endpoint that allows hunting to be viewed or edited when available
    """

    queryset = Hunting.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = HuntingSerializer
    filterset_class = HuntingFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class FishingViewSet(BaseModelViewSet):
    """
    API endpoint that allows fishing to be viewed or edited.
    """

    queryset = Fishing.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = FishingSerializer
    filterset_class = FishingFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class WildFoodGatheringFilterSet(filters.FilterSet):
    class Meta:
        model = WildFoodGathering
        fields = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
        ]


class WildFoodGatheringViewSet(BaseModelViewSet):
    """
    API endpoint that allows wild food gathering to be viewed or edited.
    """

    queryset = WildFoodGathering.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = WildFoodGatheringSerializer
    filterset_class = WildFoodGatheringFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class OtherCashIncomeFilterSet(filters.FilterSet):
    class Meta:
        model = OtherCashIncome
        fields = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "payment_per_time",
            "people_per_household",
            "times_per_month",
            "months_per_year",
            "times_per_year",
        ]


class OtherCashIncomeViewSet(BaseModelViewSet):
    """
    API endpoint that allows other cash income to be viewed or edited.
    """

    queryset = OtherCashIncome.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = OtherCashIncomeSerializer
    filterset_class = OtherCashIncomeFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class OtherPurchaseFilterSet(filters.FilterSet):
    class Meta:
        model = OtherPurchase
        fields = [
            "livelihood_strategy",
            "livelihood_zone_baseline",
            "strategy_type",
            "scenario",
            "wealth_group",
            "quantity_produced",
            "quantity_sold",
            "quantity_other_uses",
            "quantity_consumed",
            "price",
            "income",
            "expenditure",
            "kcals_consumed",
            "percentage_kcals",
            "unit_multiple",
            "times_per_month",
            "months_per_year",
        ]


class OtherPurchaseViewSet(BaseModelViewSet):
    """
    API endpoint that allows other purchases to be viewed or edited.
    """

    queryset = OtherPurchase.objects.select_related(
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = OtherPurchaseSerializer
    filterset_class = OtherPurchaseFilterSet
    search_fields = [
        "scenario",
        "strategy_type",
    ]


class SeasonalActivityFilterSet(filters.FilterSet):
    class Meta:
        model = SeasonalActivity
        fields = [
            "livelihood_zone_baseline",
            "seasonal_activity_type",
            "season",
            "product",
        ]


class SeasonalActivityViewSet(BaseModelViewSet):
    """
    API endpoint that allows seasonal activities to be viewed or edited.
    """

    queryset = SeasonalActivity.objects.select_related(
        "seasonal_activity_type",
        "livelihood_zone_baseline__livelihood_zone__country",
        "livelihood_zone_baseline__source_organization",
        "livelihood_zone_baseline__source_organization",
        "product",
    ).prefetch_related("season")
    serializer_class = SeasonalActivitySerializer
    filterset_class = SeasonalActivityFilterSet


class SeasonalActivityOccurrenceFilterSet(filters.FilterSet):
    class Meta:
        model = SeasonalActivityOccurrence
        fields = [
            "seasonal_activity",
            "livelihood_zone_baseline",
            "community",
            "start",
            "end",
        ]


class SeasonalActivityOccurrenceViewSet(BaseModelViewSet):
    """
    API endpoint that allows seasonal activity occurrences to be viewed or edited.
    """

    queryset = SeasonalActivityOccurrence.objects.select_related(
        "community",
        "livelihood_zone_baseline__livelihood_zone__country",
        "livelihood_zone_baseline__source_organization",
        "seasonal_activity__product",
    ).prefetch_related("seasonal_activity__season")
    serializer_class = SeasonalActivityOccurrenceSerializer
    filterset_class = SeasonalActivityOccurrenceFilterSet


class CommunityCropProductionFilterSet(filters.FilterSet):
    class Meta:
        model = CommunityCropProduction
        fields = [
            "community",
            "crop",
            "crop_purpose",
            "season",
            "yield_with_inputs",
            "yield_without_inputs",
            "seed_requirement",
            "crop_unit_of_measure",
            "land_unit_of_measure",
        ]


class CommunityCropProductionViewSet(BaseModelViewSet):
    """
    API endpoint that allows community crop productions to be viewed or edited.
    """

    queryset = CommunityCropProduction.objects.select_related(
        "community__livelihood_zone_baseline__livelihood_zone__country",
        "community__livelihood_zone_baseline__source_organization",
        "crop",
        "season",
        "crop_unit_of_measure",
        "land_unit_of_measure",
    )
    serializer_class = CommunityCropProductionSerializer
    filterset_class = CommunityCropProductionFilterSet
    search_fields = [
        "crop_purpose",
    ]


class CommunityLivestockFilterSet(filters.FilterSet):
    class Meta:
        model = CommunityLivestock
        fields = [
            "community",
            "livestock",
            "birth_interval",
            "wet_season_lactation_period",
            "wet_season_milk_production",
            "dry_season_lactation_period",
            "dry_season_milk_production",
            "age_at_sale",
            "additional_attributes",
        ]
        filter_overrides = {
            models.JSONField: {
                "filter_class": filters.CharFilter,
                "additional_attributes": lambda f: {"lookup_expr": "icontains"},
            },
        }


class CommunityLivestockViewSet(BaseModelViewSet):
    """
    API endpoint that allows wealth group attributes to be viewed or edited.
    """

    queryset = CommunityLivestock.objects.select_related(
        "community__livelihood_zone_baseline__livelihood_zone__country",
        "community__livelihood_zone_baseline__source_organization",
        "livestock",
    )
    serializer_class = CommunityLivestockSerializer
    filterset_class = CommunityLivestockFilterSet


class MarketPriceFilterSet(filters.FilterSet):
    class Meta:
        model = MarketPrice
        fields = [
            "community",
            "product",
            "market",
            "description",
            "currency",
            "unit_of_measure",
            "low_price_start",
            "low_price_end",
            "low_price",
            "high_price_start",
            "high_price_end",
            "high_price",
        ]


class MarketPriceViewSet(BaseModelViewSet):
    """
    API endpoint that allows market prices to be viewed or edited.
    """

    queryset = MarketPrice.objects.select_related(
        "community__livelihood_zone_baseline__livelihood_zone__country",
        "community__livelihood_zone_baseline__source_organization",
        "market",
        "product",
        "unit_of_measure",
    )
    serializer_class = MarketPriceSerializer
    filterset_class = MarketPriceFilterSet
    search_fields = [
        "description",
    ]


class SeasonalProductionPerformanceFilterSet(filters.FilterSet):
    class Meta:
        model = SeasonalProductionPerformance
        fields = [
            "community",
            "performance_year_start_date",
            "performance_year_end_date",
            "seasonal_performance",
        ]


class SeasonalProductionPerformanceViewSet(BaseModelViewSet):
    """
    API endpoint that allows seasonal production performance to be viewed or edited.
    """

    queryset = SeasonalProductionPerformance.objects.select_related(
        "community__livelihood_zone_baseline__livelihood_zone__country",
        "community__livelihood_zone_baseline__source_organization",
    )
    serializer_class = SeasonalProductionPerformanceSerializer
    filterset_class = SeasonalProductionPerformanceFilterSet


class HazardFilterSet(filters.FilterSet):
    class Meta:
        model = Hazard
        fields = [
            "community",
            "chronic_or_periodic",
            "ranking",
            "hazard_category",
            "description",
        ]


class HazardViewSet(BaseModelViewSet):
    """
    API endpoint that allows hazards to be viewed or edited.
    """

    queryset = Hazard.objects.select_related(
        "community__livelihood_zone_baseline__livelihood_zone__country",
        "community__livelihood_zone_baseline__source_organization",
        "hazard_category",
    )
    serializer_class = HazardSerializer
    filterset_class = HazardFilterSet
    search_fields = [
        "chronic_or_periodic",
        "description",
    ]


class EventFilterSet(filters.FilterSet):
    class Meta:
        model = Event
        fields = [
            "community",
            "event_year_start_date",
            "event_year_end_date",
            "description",
        ]


class EventViewSet(BaseModelViewSet):
    """
    API endpoint that allows events to be viewed or edited.
    """

    queryset = Event.objects.select_related(
        "community__livelihood_zone_baseline__livelihood_zone__country",
        "community__livelihood_zone_baseline__source_organization",
    )
    serializer_class = EventSerializer
    filterset_class = EventFilterSet
    search_fields = [
        "description",
    ]


class ExpandabilityFactorFilterSet(filters.FilterSet):
    class Meta:
        model = ExpandabilityFactor
        fields = [
            "livelihood_strategy",
            "wealth_group",
            "percentage_produced",
            "percentage_sold",
            "percentage_other_uses",
            "percentage_consumed",
            "percentage_income",
            "percentage_expenditure",
            "remark",
        ]


class ExpandabilityFactorViewSet(BaseModelViewSet):
    """
    API endpoint that allows expandability factors to be viewed or edited.
    """

    queryset = ExpandabilityFactor.objects.select_related(
        "livelihood_strategy__currency",
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__community",
        "wealth_group__community__livelihood_zone_baseline__livelihood_zone__country",
        "wealth_group__community__livelihood_zone_baseline__source_organization",
        "wealth_group__wealth_group_category",
    )
    serializer_class = ExpandabilityFactorSerializer
    filterset_class = ExpandabilityFactorFilterSet
    search_fields = [
        "remark",
    ]


class CopingStrategyFilterSet(filters.FilterSet):
    class Meta:
        model = CopingStrategy
        fields = [
            "community",
            "leaders",
            "wealth_group",
            "livelihood_strategy",
            "strategy",
            "by_value",
        ]


class CopingStrategyViewSet(BaseModelViewSet):
    """
    API endpoint that allows coping strategies to be viewed or edited.
    """

    queryset = CopingStrategy.objects.select_related(
        "community__livelihood_zone_baseline__livelihood_zone__country",
        "community__livelihood_zone_baseline__livelihood_zone__country",
        "community__livelihood_zone_baseline__source_organization",
        "community__livelihood_zone_baseline__source_organization",
        "livelihood_strategy__currency",
        "livelihood_strategy__product",
        "livelihood_strategy__season",
        "livelihood_strategy__unit_of_measure",
        "wealth_group__wealth_group_category",
    )
    serializer_class = CopingStrategySerializer
    filterset_class = CopingStrategyFilterSet
    search_fields = [
        "leaders",
        "strategy",
    ]


class LivelihoodActivitySummaryViewSet(AggregatingViewSet):
    """
    Aggregated summary of LivelihoodActivity data for Baseline Wealth Groups.

    The viewset accepts additional `slice` parameters in addition to the regular filter parameters.  The regular
    filter parameters determine Livelihood Activities that are included in the data to be aggregated. The `slice`
    parameters are used to calculate the amount of overall income, expenditure, kcals_consumed and percentage_kcals
    that are derived from the slice.

    Each row in the results contains the total amount for each indicator (income, expenditure, kcals_consumed,
    percentage_kcals), the amount contributed by the slice, and the percentage of the total contributed by the slice.

    Each row contains the aggregated indicator values for a group based on a distinct set of metadata. The groups
    are defined using the `&fields` parameter. If you omit the fields parameter all fields are returned.

    Note that because the viewset aggregates across the requested fields, it is very easy to over count the values.
    It is important to understand exactly what data is being aggregated and ensure that appropriate filters have been
    applied. For example, if a Baseline contains data for both the Baseline and the Response scenario, and you don't
    specify a scenario filter, then the resulting indicator values will be the sum of the values for both scenarios.

    The slice parameters are:

      - slice_by_product (for multiple, repeat the parameter, eg, slice_by_product=R0&slice_by_product=B01). These
        match any CPC code that starts with the value. (The client needs to convert the selected product to CPC.)

      - slice_by_strategy_type - you can specify multiple, and you need to pass the code not the label (which could be
        translated). (These are case-insensitive but otherwise must be an exact match.)

    The slice selects Livelihood Activities that match both the Products and the Strategy Types. I.e. if you pass
    a slice_by_product for a Product that isn't relevant for the selected `slice_by_strategy_type` then no activities
    will be selected and the slice values will be zero.

    The aggregates produced are:

        income_sum_row
        expenditure_sum_row
        kcals_consumed_sum_row
        percentage_kcals_sum_row

    If a slice is specified, the following additional aggregates are produced:

        income_sum_slice
        income_sum_slice_percentage_of_row
        expenditure_sum_slice
        expenditure_sum_slice_percentage_of_row
        kcals_consumed_sum_slice
        kcals_consumed_sum_slice_percentage_of_row
        percentage_kcals_sum_slice
        percentage_kcals_sum_slice_percentage_of_row

    You can filter by any calculated slice or row aggregate by prefixing its name with `min_` or `max_`. For example:

        &min_income_sum_slice_percentage_of_row=52

    The viewset currently only supports a single slice at a time. For combining slices, run multiple searches, and
    compare them externally.

    Translated fields, eg, name, description, are rendered in the currently selected locale if possible. (Except
    Country, which has different translations following ISO.) This can be selected in the UI or set using
    `&language=pt`, for example, which overrides the UI selection.

    The product hierarchy can be retrieved from the classified product endpoint /api/classifiedproduct/.

    The ordering code is also shared with the normal LZB endpoint, which uses the standard &ordering= parameter. If
    none are specified, the results are sorted by the aggregations descending, ie, biggest percentage first.

    Example URL:

    http://localhost:8000/api/livelihoodactivitysummary/
        ?language=pt
        &country=KE
        &scenario=baseline
        &slice_by_product=R011
        &slice_by_strategy_type=CropProduction
        &fields=country,livelihood_zone_baseline_name,main_livelihood_category,currency,reference_year_start_date,
            reference_year_end_date,valid_from_date,valid_to_date,population_source,population_estimate,
            wealth_group_category,product,product_common_name
        &min_income_sum_slice_percentage_of_row=52

    The strategy type codes are:
        MilkProduction
        ButterProduction
        MeatProduction
        LivestockSale
        CropProduction
        FoodPurchase
        PaymentInKind
        ReliefGiftOther
        Hunting
        Fishing
        WildFoodGathering
        OtherCashIncome
        OtherPurchase

    """

    queryset = LivelihoodActivity.objects.filter(wealth_group__community__isnull=True).select_related(
        "livelihood_zone_baseline__livelihood_zone__country",
        "livelihood_zone_baseline__source_organization",
        "livelihood_zone_baseline__main_livelihood_category",
        "wealth_group__wealth_group_category",
        "livelihood_strategy__product",
        "livelihood_strategy__season",
    )
    serializer_class = LivelihoodActivitySummarySerializer
    filterset_class = LivelihoodActivityFilterSet

    def get_queryset_annotations(self) -> dict[str, F | Expression]:
        """
        AggregatingViewSet requires an annotation for every field in the Serializer that isn't a direct model field.
        """
        language_code = translation.get_language()

        def translated_field(path):
            """Return a Coalesce expression for a translated field so that we return the English value
            if the translation for the current language is empty."""
            return Coalesce(
                NullIf(
                    F(f"{path}_{language_code}"),
                    Value(""),
                ),
                F(f"{path}_en"),
                output_field=TextField(),
            )

        def country_field():
            """Return an expression for the country name based on ISO name fields, using the
            localized ISO name (e.g. French or Portuguese) when available and falling back to
            the English ISO romanized name if the localized value is empty or not defined."""
            path = {
                "fr": "livelihood_zone_baseline__livelihood_zone__country__iso_fr_name",
                "pt": "livelihood_zone_baseline__livelihood_zone__country__iso_pt_name",
            }.get(language_code)
            if path:
                return Coalesce(
                    NullIf(
                        F(path),
                        Value(""),
                    ),
                    F("livelihood_zone_baseline__livelihood_zone__country__iso_en_ro_name"),
                )
            return F("livelihood_zone_baseline__livelihood_zone__country__iso_en_ro_name")

        return {
            "country": country_field(),
            "source_organization_name": F("livelihood_zone_baseline__source_organization__name"),
            "livelihood_zone": F("livelihood_zone_baseline__livelihood_zone__code"),
            "livelihood_zone_baseline_name": translated_field("livelihood_zone_baseline__name"),
            "reference_year_start_date": F("livelihood_zone_baseline__reference_year_start_date"),
            "reference_year_end_date": F("livelihood_zone_baseline__reference_year_end_date"),
            "valid_from_date": F("livelihood_zone_baseline__valid_from_date"),
            "valid_to_date": F("livelihood_zone_baseline__valid_to_date"),
            "main_livelihood_category": F("livelihood_zone_baseline__main_livelihood_category__code"),
            "livelihood_zone_baseline_description": translated_field("livelihood_zone_baseline__description"),
            "wealth_group_category": F("wealth_group__wealth_group_category__code"),
            "wealth_group_category_name": translated_field(
                "wealth_group__wealth_group_category__name",
            ),
            "wealth_group_category_ordering": F("wealth_group__wealth_group_category__ordering"),
            "percentage_of_households": F("wealth_group__percentage_of_households"),
            "average_household_size": F("wealth_group__average_household_size"),
            "currency": F("livelihood_zone_baseline__currency__pk"),
            "population_source": F("livelihood_zone_baseline__population_source"),
            "population_estimate": F("livelihood_zone_baseline__population_estimate"),
            "product": F("livelihood_strategy__product__cpc"),
            "product_common_name": translated_field(
                "livelihood_strategy__product__common_name",
            ),
            "source_organization": F("livelihood_zone_baseline__source_organization__pk"),
            "iso3166a2": F("livelihood_zone_baseline__livelihood_zone__country__iso3166a2"),
        }


MODELS_TO_SEARCH = [
    {
        "app_name": "common",
        "model_name": "ClassifiedProduct",
        "filter": {"key": "product", "label": "Product", "category": "products"},
    },
    {
        "app_name": "metadata",
        "model_name": "LivelihoodCategory",
        "filter": {"key": "main_livelihood_category", "label": "Main Livelihood Category", "category": "zone_types"},
    },
    {
        "app_name": "baseline",
        "model_name": "LivelihoodZone",
        "filter": {"key": "livelihood_zone", "label": "Livelihood zone", "category": "zones"},
    },
    {
        "app_name": "metadata",
        "model_name": "WealthCharacteristic",
        "filter": {"key": "wealth_characteristic", "label": "Items", "category": "items"},
    },
    {
        "app_name": "common",
        "model_name": "Country",
        "filter": {"key": "country", "label": "Country", "category": "countries"},
    },
]


class LivelihoodZoneBaselineFacetedSearchView(APIView):
    """
    Performs a faceted search to find Livelihood Zone Baselines using a specified search term.

    The search applies to multiple related models, filtering results based on the configured
    criteria for each model. For each matching result, it calculates the number of unique
    livelihood zones associated with the filter and includes relevant metadata in the response.
    """

    renderer_classes = [JSONRenderer]
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        """
        Return a faceted set of matching filters
        """
        results = {}
        search_term = request.query_params.get(settings.REST_FRAMEWORK["SEARCH_PARAM"], "")
        language = request.query_params.get("language", "en")

        if search_term:
            for model_entry in MODELS_TO_SEARCH:
                app_name = model_entry["app_name"]
                model_name = model_entry["model_name"]
                filter, filter_label, filter_category = (
                    model_entry["filter"]["key"],
                    model_entry["filter"]["label"],
                    model_entry["filter"]["category"],
                )
                ModelClass = apps.get_model(app_name, model_name)
                search_per_model = ModelClass.objects.search(search_term)
                results[filter_category] = []
                # for activating language
                with override(language):
                    for search_result in search_per_model:
                        if model_name == "ClassifiedProduct":
                            unique_zones = (
                                LivelihoodStrategy.objects.filter(product=search_result)
                                .values("livelihood_zone_baseline")
                                .distinct()
                                .count()
                            )
                            value_label, value = search_result.description, search_result.pk
                        elif model_name == "LivelihoodCategory":
                            unique_zones = LivelihoodZoneBaseline.objects.filter(
                                main_livelihood_category=search_result
                            ).count()
                            value_label, value = search_result.description, search_result.pk
                        elif model_name == "LivelihoodZone":
                            unique_zones = LivelihoodZoneBaseline.objects.filter(livelihood_zone=search_result).count()
                            value_label, value = search_result.name, search_result.pk
                        elif model_name == "WealthCharacteristic":
                            unique_zones = (
                                WealthGroupCharacteristicValue.objects.filter(wealth_characteristic=search_result)
                                .values("wealth_group__livelihood_zone_baseline")
                                .distinct()
                                .count()
                            )
                            value_label, value = search_result.description, search_result.pk
                        elif model_name == "Country":
                            unique_zones = (
                                LivelihoodZoneBaseline.objects.filter(livelihood_zone__country=search_result)
                                .distinct()
                                .count()
                            )
                            value_label, value = search_result.iso_en_name, search_result.pk
                        if unique_zones > 0:
                            results[filter_category].append(
                                {
                                    "filter": filter,
                                    "filter_label": filter_label,
                                    "value_label": value_label,
                                    "value": value,
                                    "count": unique_zones,
                                }
                            )

        return Response(results)
