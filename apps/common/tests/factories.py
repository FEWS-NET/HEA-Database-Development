import factory
from factory import fuzzy

from common.models import ClassifiedProduct, UnitOfMeasure, CountryClassifiedProductAliases, UnitOfMeasureConversion


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


class CountryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.Country"
        django_get_or_create = ("iso3166a2", "name")

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

    iso4217a3 = factory.Iterator(["XAC", "XBC", "XCC", "XDC", "XEC", "XFC", "XGC", "XHC", "XIC", "XJC", "XLC", "XMC"])


class UnitOfMeasureFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "common.UnitOfMeasure"
        django_get_or_create = ("abbreviation",)

    abbreviation = factory.Sequence(lambda n: "U%d" % n)
    unit_type = UnitOfMeasure.WEIGHT
    description = factory.Sequence(lambda n: "Unit %d" % n)


class ClassifiedProductFactory(TreebeardFactory):
    class Meta:
        model = "common.ClassifiedProduct"
        django_get_or_create = (
            "cpcv2",
            "description",
            "common_name",
        )

    cpcv2 = factory.Iterator(["R09999AA", "R09999BB", "L09999CB", "R09999DC", "S90999EE"])
    description = factory.LazyAttribute(lambda o: f"Product Description {o.cpcv2}")
    common_name = factory.LazyAttribute(lambda o: f"Product {o.cpcv2}")
    scientific_name = factory.LazyAttribute(lambda o: f"Product Scientific {o.cpcv2}")
    unit_of_measure = factory.SubFactory(UnitOfMeasureFactory)
    kcals_per_unit = fuzzy.FuzzyInteger(50, 7500)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """
        Create a parent for "detail" products, e.g. R01234AA.
        """
        if kwargs.get("parent", False) is True:
            try:
                parent = ClassifiedProduct.objects.get(cpcv2=kwargs["cpcv2"][:-2])
            except ClassifiedProduct.DoesNotExist:
                parent = ClassifiedProduct(
                    cpcv2=kwargs["cpcv2"][:-2], description=f'Product Description {kwargs["cpcv2"][:-2]}'
                )
                ClassifiedProduct.add_root(instance=parent)
            kwargs["parent"] = parent
        return super()._create(model_class, *args, **kwargs)


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

class UnitOfMeasureConversionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UnitOfMeasureConversion

    from_unit = factory.SubFactory("common.tests.factories.UnitOfMeasureFactory")
    to_unit = factory.SubFactory("common.tests.factories.UnitOfMeasureFactory")
    conversion_factor = factory.Sequence(lambda n: n + 1)


class CountryClassifiedProductAliasesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CountryClassifiedProductAliases

    country = factory.SubFactory("common.tests.factories.CountryFactory")
    product = factory.SubFactory("common.tests.factories.ClassifiedProductFactory")
