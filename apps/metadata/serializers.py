from datetime import datetime, timedelta

from rest_framework import serializers

from .models import (
    HazardCategory,
    LivelihoodCategory,
    ReferenceData,
    Season,
    SeasonalActivityType,
    WealthCategory,
    WealthCharacteristic,
)


class ReferenceDataSerializer(serializers.ModelSerializer):
    """
    Serializer class for the ReferenceData base model.
    """

    class Meta:
        model = ReferenceData
        fields = ["code", "name", "description", "aliases"]


class LivelihoodCategorySerializer(ReferenceDataSerializer):
    """
    Serializer class for the LivelihoodCategory model
    """

    class Meta(ReferenceDataSerializer.Meta):
        model = LivelihoodCategory


class WealthCharacteristicSerializer(ReferenceDataSerializer):
    """
    Serializer class for ReferenceDataSerializer model
    """

    variable_type = serializers.CharField()

    class Meta(ReferenceDataSerializer.Meta):
        model = WealthCharacteristic
        fields = ReferenceDataSerializer.Meta.fields + [
            "variable_type",
        ]


class SeasonalActivityTypeSerializer(ReferenceDataSerializer):
    """
    Serializer class for SeasonalActivityType model
    """

    activity_category = serializers.CharField()

    class Meta(ReferenceDataSerializer.Meta):
        model = SeasonalActivityType
        fields = ReferenceDataSerializer.Meta.fields + [
            "activity_category",
        ]


class WealthCategorySerializer(ReferenceDataSerializer):
    """
    Serializer class for the WealthCategory model
    """

    class Meta(ReferenceDataSerializer.Meta):
        model = WealthCategory


class HazardCategorySerializer(ReferenceDataSerializer):
    """
    Serializer class for the HazardCategory model
    """

    class Meta(ReferenceDataSerializer.Meta):
        model = HazardCategory


class SeasonSerializer(serializers.ModelSerializer):
    """
    Serializer class for the Season model
    """

    start_month = serializers.SerializerMethodField()
    end_month = serializers.SerializerMethodField()

    def get_start_month(self, obj):
        return self.get_month_from_day_number(obj.start)

    def get_end_month(self, obj):
        return self.get_month_from_day_number(obj.end)

    def get_month_from_day_number(self, day_number):
        # @TODO is it better to lookup the reference year from the livelihood_zone_baseline via
        # e.g. obj.country.livelihoodzone_set.first().livelihoodzonebaseline_set.first().reference_year_start_date.year
        first_day_of_year = datetime(datetime.today().year, 1, 1)
        _date = first_day_of_year + timedelta(days=day_number - 1)
        return _date.month

    class Meta:
        model = Season
        fields = ["country", "name", "description", "season_type", "start_month", "end_month", "alignment", "order"]
