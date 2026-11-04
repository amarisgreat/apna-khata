from django.contrib import admin

from .models import Payment, PaymentAllocation


class PaymentAllocationInline(admin.TabularInline):
    model = PaymentAllocation
    extra = 0
    can_delete = False

    fields = ("debt", "amount")
    readonly_fields = ("debt", "amount")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer",
        "amount",
        "paid_at",
        "created_by",
    )

    list_filter = ("paid_at",)
    search_fields = (
        "customer__name",
        "customer__phone",
        "note",
    )

    readonly_fields = (
        "created_by",
        "created_at",
        "updated_at",
    )

    date_hierarchy = "paid_at"
    inlines = [PaymentAllocationInline]


@admin.register(PaymentAllocation)
class PaymentAllocationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "payment",
        "debt",
        "amount",
    )

    list_filter = ("payment__paid_at",)

    readonly_fields = (
        "payment",
        "debt",
        "amount",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False