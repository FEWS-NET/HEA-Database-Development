from datetime import datetime, timedelta

from rest_framework import serializers

from .models import (
    Dimension,
    HazardCategory,
    LivelihoodCategory,
    Season,
    SeasonalActivityType,
    WealthCategory,
    WealthCharacteristic,
)


class DimensionSerializer(serializers.ModelSerializer):
    """
    Serializer class for the Dimension base model.
    """

    class Meta:
        model = Dimension
        fields = ["code", "name", "description", "aliases"]


class LivelihoodCategorySerializer(DimensionSerializer):
    """
    Serializer class for the LivelihoodCategory model
    """

    class Meta(DimensionSerializer.Meta):
        model = LivelihoodCategory


class WealthCharacteristicSerializer(DimensionSerializer):
    """
    Serializer class for DimensionSerializer model
    """

    variable_type = serializers.CharField()

    class Meta(DimensionSerializer.Meta):
        model = WealthCharacteristic
        fields = DimensionSerializer.Meta.fields + [
            "variable_type",
        ]


class SeasonalActivityTypeSerializer(DimensionSerializer):
    """
    Serializer class for SeasonalActivityType model
    """

    activity_category = serializers.CharField()

    class Meta(DimensionSerializer.Meta):
        model = SeasonalActivityType
        fields = DimensionSerializer.Meta.fields + [
            "activity_category",
        ]


class WealthCategorySerializer(DimensionSerializer):
    """
    Serializer class for the WealthCategory model
    """

    class Meta(DimensionSerializer.Meta):
        model = WealthCategory


class HazardCategorySerializer(DimensionSerializer):
    """
    Serializer class for the HazardCategory model
    """

    class Meta(DimensionSerializer.Meta):
        model = HazardCategory


class SeasonSerializer(serializers.ModelSerializer):
    """
    Serializer class for the Season model
    """

    start_month = serializers.SerializerMethodField()
    end_month = serializers.SerializerMethodField()

    def get_start_month(self, obj):
        return self.get_month_from_day_number(obj, obj.start)

    def get_end_month(self, obj):
        return self.get_month_from_day_number(obj, obj.end)

    def get_month_from_day_number(self, obj, day_number):
        # @TODO is it better to lookup the reference year from the livelihood_zone_baseline via
        # e.g. obj.country.livelihoodzone_set.first().livelihoodzonebaseline_set.first().reference_year_start_date.year
        first_day_of_reference_year = datetime(datetime.today().year, 1, 1)
        _date = first_day_of_reference_year + timedelta(days=day_number - 1)
        return _date.month

    class Meta:
        model = Season
        fields = ["country", "name", "description", "season_type", "start_month", "end_month", "alignment", "order"]
