from django.contrib import admin
from django.db import transaction

from .models import Debt, DebtItem
from .services.debt_calculator import (
    calculate_line_total,
    calculate_debt_total,
)


class DebtItemInline(admin.TabularInline):

    model = DebtItem

    extra = 1

    fields = (
        "name",
        "quantity",
        "unit",
        "price_per_unit",
        "line_total",
    )

    readonly_fields = ("line_total",)


@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "customer",
        "total_amount",
        "created_at",
        "created_by",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "customer__name",
        "customer__phone",
    )

    readonly_fields = (
        "created_by",
        "updated_at",
    )

    date_hierarchy = "created_at"

    inlines = [DebtItemInline]

    list_per_page = 25

    def save_model(self, request, obj, form, change):

        if not change:
            obj.created_by = request.user

        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):

        with transaction.atomic():

            super().save_related(
                request,
                form,
                formsets,
                change
            )

            debt = form.instance

            items = list(debt.items.all())

            total = 0

            for item in items:

                item.line_total = calculate_line_total(
                    item.quantity,
                    item.price_per_unit
                )

                item.save(update_fields=["line_total"])

                total += item.line_total

            debt.total_amount = total

            debt.save(update_fields=["total_amount"])


@admin.register(DebtItem)
class DebtItemAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "debt",
        "name",
        "quantity",
        "unit",
        "price_per_unit",
        "line_total",
    )

    search_fields = (
        "name",
        "debt__customer__name",
    )

    readonly_fields = ("line_total",)
