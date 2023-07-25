from django.contrib import admin

from .models import HazardCategory, LivelihoodCategory, WealthCharacteristic


@admin.register(LivelihoodCategory)
class LivelihoodCategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(WealthCharacteristic)
class WealthCharacteristicAdmin(admin.ModelAdmin):
    pass


@admin.register(HazardCategory)
class HazardCategoryAdmin(admin.ModelAdmin):
    pass
