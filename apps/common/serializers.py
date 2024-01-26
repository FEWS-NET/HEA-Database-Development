from rest_framework import serializers

from .models import ClassifiedProduct, Country, Currency, UnitOfMeasure


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
        fields = ["cpc", "description", "common_name", "scientific_name", "unit_of_measure", "kcals_per_unit"]
