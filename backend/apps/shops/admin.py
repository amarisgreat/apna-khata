from django.contrib import admin
from .models import Shop


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "owner",
        "created_at",
    )

    search_fields = (
        "name",
        "owner__name",
        "owner__phone",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )