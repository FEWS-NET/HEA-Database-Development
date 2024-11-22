import factory
from factory import fuzzy

from common.models import (
    ClassifiedProduct,
    CountryClassifiedProductAliases,
    UnitOfMeasure,
    UnitOfMeasureConversion,
)


class TreebeardFactory(factory.django.DjangoModelFactory):
    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Create an instance of the model, and save it to the database."""

        # Attempt to find an existing instance first
        if cls._meta.django_get_or_create:
            try:
                return cls._get_manager(model_class).get(
                    **{key: value for (key, value) in kwargs.items() if key in cls._meta.django_get_or_create}
                )
            except model_class.DoesNotExist:
                pass

        # If we pass kwargs and let Treebeard create the instance and then save it,
        # it fails for models that are non-proxy subclasses
        # because the additional attributes don't exist on the parent model,
        # which is what Treebeard uses to create the new instance.
        if "parent" in kwargs:
            parent = kwargs.pop("parent")
            instance = model_class(*args, **kwargs)
            return parent.add_child(instance=instance)
        else:
            instance = model_class(*args, **kwargs)
            return model_class.add_root(instance=instance)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "auth.User"
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda n: "user_%d" % n)
    password = factory.PostGenerationMethodCall("set_password", "password")

    is_superuser = True
    is_staff = True
    is_active = True

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for group in extracted:
                self.groups.add(group)


class UserProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.UserProfile"
        django_get_or_create = ("user",)

    user = factory.SubFactory(UserFactory)


class GroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "auth.Group"
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: "group_%d" % n)

    @factory.post_generation
    def permissions(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of permissions were passed in, use them
            for permission in extracted:
                self.permissions.add(permission)


class CountryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.Country"
        django_get_or_create = ("iso3166a2",)

    # Note that we skip XK because it is actually a code in real use for Kosovo
    iso3166a2 = factory.Iterator(["XA", "XB", "XC", "XD", "XE", "XF", "XG", "XH", "XI", "XJ", "XL", "XM"])
    iso3166a3 = factory.LazyAttribute(lambda o: f"{o.iso3166a2}{o.iso3166a2[-1]}")
    iso3166n3 = factory.LazyAttribute(lambda o: 900 + ord(o.iso3166a2[-1]) - 64)
    iso_en_ro_name = factory.LazyAttribute(lambda o: f"{o.iso3166a2} Country")
    iso_en_name = factory.LazyAttribute(lambda o: f"{o.iso3166a2} Country")
    name = factory.LazyAttribute(lambda o: f"{o.iso3166a2} Country")

    @classmethod
    def _get_manager(cls, target_class):
        return super()._get_manager(target_class)


class CurrencyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.Currency"
        django_get_or_create = ("iso4217a3",)

    # Note that we skip XKC because XK because it is actually an iso3166a2 code in real use for Kosovo
    iso4217a3 = factory.Iterator(["XAC", "XBC", "XCC", "XDC", "XEC", "XFC", "XGC", "XHC", "XIC", "XJC", "XLC", "XMC"])


class UnitOfMeasureFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.UnitOfMeasure"
        django_get_or_create = ("abbreviation",)

    abbreviation = factory.Sequence(lambda n: "U%d" % n)
    unit_type = UnitOfMeasure.WEIGHT
    description_en = factory.Sequence(lambda n: "Unit %d en" % n)
    description_fr = factory.Sequence(lambda n: "Unit %d fr" % n)
    description_ar = factory.Sequence(lambda n: "Unit %d ar" % n)
    description_es = factory.Sequence(lambda n: "Unit %d es" % n)
    description_pt = factory.Sequence(lambda n: "Unit %d pt" % n)
    conversion = factory.RelatedFactory("common.tests.factories.UnitOfMeasureConversionFactory", "from_unit")


class UnitOfMeasureConversionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UnitOfMeasureConversion
        django_get_or_create = [
            "from_unit",
            "to_unit",
        ]

    from_unit = factory.SubFactory(UnitOfMeasureFactory, conversion=None)
    conversion_factor = fuzzy.FuzzyInteger(2, 10)

    @factory.lazy_attribute
    def to_unit(self):
        if self.from_unit.unit_type == UnitOfMeasure.WEIGHT:
            return UnitOfMeasure.objects.get_or_create(abbreviation="kg", unit_type=self.from_unit.unit_type)[0]
        elif self.from_unit.unit_type == UnitOfMeasure.VOLUME:
            return UnitOfMeasure.objects.get_or_create(abbreviation="L", unit_type=self.from_unit.unit_type)[0]
        elif self.from_unit.unit_type == UnitOfMeasure.ITEM:
            return UnitOfMeasure.objects.get_or_create(abbreviation="ea", unit_type=self.from_unit.unit_type)[0]
        elif self.from_unit.unit_type == UnitOfMeasure.AREA:
            return UnitOfMeasure.objects.get_or_create(abbreviation="ha", unit_type=self.from_unit.unit_type)[0]
        elif self.from_unit.unit_type == UnitOfMeasure.YIELD:
            return UnitOfMeasure.objects.get_or_create(abbreviation="MT/ha", unit_type=self.from_unit.unit_type)[0]


class ClassifiedProductFactory(TreebeardFactory):
    class Meta:
        model = "common.ClassifiedProduct"
        django_get_or_create = ("cpc",)

    cpc = factory.Iterator(["R09999AA", "R09999BB", "L09999CB", "R09999DC", "S90999EE"])
    scientific_name = factory.LazyAttribute(lambda o: f"Scientific Name {o.cpc}")
    aliases = factory.LazyAttribute(lambda o: [f"Prod {o.cpc}", f"Crop {o.cpc}"])
    unit_of_measure = factory.SubFactory(UnitOfMeasureFactory)
    kcals_per_unit = fuzzy.FuzzyInteger(50, 7500)
    description_en = factory.LazyAttribute(lambda o: f"Product Description {o.cpc} en")
    description_fr = factory.LazyAttribute(lambda o: f"Product Description {o.cpc} fr")
    description_es = factory.LazyAttribute(lambda o: f"Product Description {o.cpc} es")
    description_ar = factory.LazyAttribute(lambda o: f"Product Description {o.cpc} ar")
    description_pt = factory.LazyAttribute(lambda o: f"Product Description {o.cpc} pt")
    common_name_en = factory.LazyAttribute(lambda o: f"Product {o.cpc} en")
    common_name_fr = factory.LazyAttribute(lambda o: f"Product {o.cpc} fr")
    common_name_es = factory.LazyAttribute(lambda o: f"Product {o.cpc} es")
    common_name_ar = factory.LazyAttribute(lambda o: f"Product {o.cpc} ar")
    common_name_pt = factory.LazyAttribute(lambda o: f"Product {o.cpc} pt")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """
        Create a parent for "detail" products, e.g. R01234AA.
        """
        if kwargs.get("parent", False) is True:
            try:
                parent = ClassifiedProduct.objects.get(cpc=kwargs["cpc"][:-2])
            except ClassifiedProduct.DoesNotExist:
                parent = ClassifiedProduct(
                    cpc=kwargs["cpc"][:-2], description_en=f'Product Description {kwargs["cpc"][:-2]}'
                )
                ClassifiedProduct.add_root(instance=parent)
            kwargs["parent"] = parent
        return super()._create(model_class, *args, **kwargs)


class CountryClassifiedProductAliasesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CountryClassifiedProductAliases
        django_get_or_create = [
            "country",
            "product",
        ]

    country = factory.SubFactory(CountryFactory)
    product = factory.SubFactory(ClassifiedProductFactory)
    aliases = factory.LazyAttribute(
        lambda o: [
            "{}-{}-{}".format(
                o.product.cpc[0].lower(),
                o.product.cpc[1:6],
                o.product.cpc[6:].lower(),
            )
        ]
    )
