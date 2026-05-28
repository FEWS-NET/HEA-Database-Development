from rest_framework import serializers

from common.utils import get_month_from_day_number

from .models import (
    HazardCategory,
    LivelihoodCategory,
    ReferenceData,
    Season,
    SeasonalActivityType,
    WealthCharacteristic,
    WealthGroupCategory,
)


class ReferenceDataSerializer(serializers.ModelSerializer):
    """
    Serializer class for the ReferenceData base model.
    """

    class Meta:
        model = ReferenceData
        fields = ["code", "name", "description", "ordering", "aliases"]


class LivelihoodCategorySerializer(ReferenceDataSerializer):
    """
    Serializer class for the LivelihoodCategory model
    """

    class Meta(ReferenceDataSerializer.Meta):
        model = LivelihoodCategory
        fields = ["code", "name", "description", "aliases", "color"]


class WealthCharacteristicSerializer(ReferenceDataSerializer):
    """
    Serializer class for ReferenceDataSerializer model
    """

    variable_type = serializers.CharField()
    characteristic_group = serializers.CharField(source="characteristic_group.name", read_only=True)
    characteristic_group_ordering = serializers.IntegerField(source="characteristic_group.ordering", read_only=True)

    class Meta(ReferenceDataSerializer.Meta):
        model = WealthCharacteristic
        fields = ReferenceDataSerializer.Meta.fields + [
            "variable_type",
            "characteristic_group",
            "characteristic_group_ordering",
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
            "has_product",
            "is_key",
        ]


class WealthGroupCategorySerializer(ReferenceDataSerializer):
    """
    Serializer class for the WealthGroupCategory model
    """

    class Meta(ReferenceDataSerializer.Meta):
        model = WealthGroupCategory


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
        return get_month_from_day_number(obj.start)

    def get_end_month(self, obj):
        return get_month_from_day_number(obj.end)

    class Meta:
        model = Season
        fields = [
            "country",
            "name",
            "description",
            "season_type",
            "purpose",
            "start_month",
            "end_month",
            "alignment",
            "order",
        ]
