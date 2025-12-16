from collections import OrderedDict
from inspect import isclass

from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.fields import Field
from rest_framework.settings import api_settings

from .enums import AggregationScope
from .models import ClassifiedProduct, Country, Currency, UnitOfMeasure, UserProfile


class CountrySerializer(serializers.ModelSerializer):
    """
    Serializer class for the Country model.
    """

    class Meta:
        model = Country
        fields = [
            "iso3166a2",
            "name",
            "iso3166a3",
            "iso3166n3",
            "iso_en_name",
            "iso_en_proper",
            "iso_en_ro_name",
            "iso_en_ro_proper",
            "iso_fr_name",
            "iso_fr_proper",
            "iso_es_name",
        ]


class CurrencySerializer(serializers.ModelSerializer):
    """
    Serializer class for the Currency model
    """

    class Meta:
        model = Currency
        fields = ["iso4217a3", "iso4217n3", "iso_en_name"]


class UnitOfMeasureSerializer(serializers.ModelSerializer):
    """
    Serializer class for UnitOfMeasure model
    """

    class Meta:
        model = UnitOfMeasure
        fields = ["abbreviation", "description", "unit_type"]


class ClassifiedProductSerializer(serializers.ModelSerializer):
    """
    Serializer class for ClassifiedProduct model
    """

    class Meta:
        model = ClassifiedProduct
        fields = [
            "cpc",
            "description",
            "common_name",
            "display_name",
            "scientific_name",
            "unit_of_measure",
            "kcals_per_unit",
            "aliases",
        ]

    display_name = serializers.SerializerMethodField()

    def get_display_name(self, obj):
        return obj.display_name()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name"]


class CurrentUserSerializer(serializers.ModelSerializer):
    permissions = serializers.ListField(source="get_all_permissions", read_only=True)
    groups = serializers.SerializerMethodField()

    def get_groups(self, user):
        return user.groups.values_list("name", flat=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "permissions",
            "groups",
            "is_staff",
            "is_superuser",
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ("user", "profile_data")


class AggregatingSerializer(serializers.ModelSerializer):
    """
    A serializer that works with the AggregatingViewSet to provide aggregating functionality on a viewset.

    See the AggregatingViewSet docstring for a description of usage. The viewset must inherit from AggregatingViewSet,
    and specify a serializer that sub-classes this AggregatingSerializer.

    All aggregation configuration is on the following serializer properties:

     * Meta.model: As standard, the base model of the endpoint
     * Meta.fields: The maximum list of field names the endpoint can return. These are user-friendly field names,
        converted to Django field paths by the field_to_database_path method if necessary. These can span model
        joins in the usual way using double underscore. Do not include the auto-generated calculated fields, and
        do not add Field class attributes on the serializer class.
     * aggregates: A dictionary of {field name: expression or aggregate} pairs. These field names are also converted
     to Django field paths by the field_to_database_path method if necessary. These can span model joins using __.
     * slice_fields: A dict of {field name: database filter expression} pairs, eg,
        {"kcals_consumed": "path__product__cpc__istartswith"}. This implements the parameter slice_by_product.
     * field_to_database_path: A method that converts a user-friendly field name used in the results and parameter
        names into a Django field path, eg, product_cpc into path__product__cpc.

    Field class attributes are not necessary. The values are rendered as returned by the database query, and this
    endpoint is read-only.
    """

    # A dict of {field name: aggregate class} pairs, eg, {"kcals_consumed": Sum}.
    # For each of these aggregates the following calculation columns are added:
    #   (a) Total at the row level (filtered and drilled down), eg, kcals_consumed_sum_row.
    #   (b) Total for the selected product/strategy type slice, eg, kcals_consumed_sum_slice.
    #   (c) The percentage the slice represents of the whole, eg, kcals_consumed_sum_slice_percentage_of_row.
    # Filters are automatically created for all three, by prefixing min_ or max_ to any calculated field name.
    # If no ordering is specified by the FilterSet, the results are ordered by percent descending in the order here.
    # If specifying a custom expression, include how the field is aggregated, eg, the 'sum' in kcal_income_sum.
    aggregates = {}

    # A dict of {field name: database filter expression} pairs, eg,
    # {"product": "livelihood_strategies__product__cpc__istartswith"}
    # For each of these pairs, a URL parameter is created "slice_by_{field}", eg, ?slice_by_product=
    # They can appear zero, one or multiple times in the URL, and define a sub-slice of the row-level data.
    # A slice includes activities with ANY of the products, AND, ANY of the strategy types.
    # For example: (product=R0 OR product=L0) AND (strategy_type=MilkProd OR strategy_type=CropProd)
    slice_fields = {}

    @staticmethod
    def field_to_database_path(field_name):
        """
        Convert user-friendly field name specified in Meta.fields, eg, strategy_name to database field path, eg,
        join_path__strategies__name.
        """
        return field_name

    def get_fields(self):
        """
        User can specify a ?fields= URL parameter to specify a field list, comma-delimited. This also
        determines the level of aggregation drill-down.

        The user need not specify the aggregate field names - these are all always included.

        The fields in the returned data will be in the same order as specified in this ?fields= parameter.

        Ignores any fields requested not found in self.Meta.fields.

        If the ?fields= URL parameter is not specified, defaults to self.Meta.fields.
        """
        field_list = "request" in self.context and self.context["request"].query_params.get("fields", None)
        if not field_list:
            return {f: Field() for f in self.Meta.fields}

        # User-provided list of fields
        field_names = field_list.split(",")

        # Add the ordering field if specified
        ordering = self.context["request"].query_params.get(api_settings.ORDERING_PARAM)
        if ordering:
            field_names.append(ordering)

        # Remove any that don't match one of self.Meta.fields
        # Return Field() to save sub-classes having to specify Field class attributes for model and aggregate fields.
        return {f: Field() for f in field_names if f in self.Meta.fields}

    def get_aggregate_field_names(self):
        """
        The order of the fields here determines the order in which they are returned by the endpoint
        (see self.to_representation()).
        """
        aggregate_fields = []
        for field_name, aggregate in self.aggregates.items():
            aggregate_fields.extend(
                [
                    self.get_aggregate_field_name(field_name, aggregate, AggregationScope.ROW),
                    # eg, kcals_consumed_sum_row
                    self.get_aggregate_field_name(field_name, aggregate, AggregationScope.SLICE),
                    # eg, kcals_consumed_sum_slice
                    self.get_aggregate_field_name(field_name, aggregate, AggregationScope.SLICE, AggregationScope.ROW),
                    # eg, kcals_consumed_sum_slice_percentage_of_row
                ]
            )
        return aggregate_fields

    def to_representation(self, instance):
        """
        Order the fields in the order they are specified in self.Meta.fields, followed by the aggregates in the order
        they are specified in self.aggregates.

        Raises an exception if a field in Meta.fields is not returned by the queryset (after conversion by
        field_to_database_path).

        Ignores any aggregate fields that are not returned by the queryset, as this depends on the request.
        Slice and percentage fields are only calculated when a slice is specified, for example.
        """
        ret = OrderedDict()
        for field_name in self.get_fields():
            field_path = self.field_to_database_path(field_name)
            ret[field_name] = instance[field_path]
        for field_name in self.get_aggregate_field_names():
            if field_name in instance:
                ret[field_name] = instance[field_name]
        return ret

    @classmethod
    def get_aggregate_field_name(cls, field_name, aggregate, scope, percentage_of=None):
        """
        Returns the field name for the auto-generated aggregate fields.

        field_name is the original column name, or the name provided in serializer.aggregates.
        aggregate is the aggregation class, eg, Sum, or the fully formed expression. It is ignored in the latter case.
        scope is the level of aggregation, and can be "row" or "slice".
        percentage_of can also be "row" or "slice", for fields that are the scope-level aggregate as a
          percentage of the percentage_of field, for example, the percentage a "slice" represents of its "row".

        Returns the field name of the aggregate output column as:

        f"{field_name}_{aggregate}_{scope}[_percentage_of_{percentage_of}]"

        scope and percentage_of may be "row" or "slice". percentage_of is optional.

        Examples:
          * expenditure_avg_row
          * kcals_consumed_sum_slice
          * kcals_consumed_sum_slice_percentage_of_row
        """

        assert scope in AggregationScope
        assert percentage_of in AggregationScope or percentage_of is None

        if isclass(aggregate):
            field_name += "_" + aggregate.name.lower()  # eg, kcals_consumed_sum

        field_name += "_" + scope  # eg, kcals_consumed_sum_slice

        if percentage_of:
            field_name += "_percentage_of_" + percentage_of  # eg, kcals_consumed_sum_slice_percentage_of_row

        return field_name
