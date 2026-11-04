from django.contrib import admin

from .models import Customer, CustomerTag


class CustomerTagInline(admin.TabularInline):
    model = CustomerTag
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "phone",
        "shop",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "name",
        "phone",
        "shop__name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    inlines = [CustomerTagInline]

    list_per_page = 25


@admin.register(CustomerTag)
class CustomerTagAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "customer",
    )

    search_fields = (
        "name",
        "customer__name",
    )