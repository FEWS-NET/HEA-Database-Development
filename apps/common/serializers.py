from django.contrib.auth.models import User
from rest_framework import serializers

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
