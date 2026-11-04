from decimal import Decimal

from rest_framework import serializers

from .models import Debt, DebtItem
from .selectors.debt_queries import get_debt_financials


class DebtItemInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)

    quantity = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        min_value=Decimal("0.001"),
    )

    unit = serializers.CharField(max_length=30)

    price_per_unit = serializers.IntegerField(min_value=1)


class DebtWriteSerializer(serializers.Serializer):
    created_at = serializers.DateTimeField(required=False)

    note = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    items = DebtItemInputSerializer(
        many=True,
        required=True,
    )

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError(
                "A debt must contain at least one item."
            )

        return value


class DebtItemReadSerializer(serializers.ModelSerializer):

    class Meta:
        model = DebtItem

        fields = [
            "id",
            "name",
            "quantity",
            "unit",
            "price_per_unit",
            "line_total",
        ]


class DebtReadSerializer(serializers.ModelSerializer):

    items = DebtItemReadSerializer(
        many=True,
        read_only=True,
    )

    customer_id = serializers.IntegerField(
        source="customer.id",
        read_only=True,
    )

    customer_name = serializers.CharField(
        source="customer.name",
        read_only=True,
    )

    paid_amount = serializers.SerializerMethodField()

    remaining_amount = serializers.SerializerMethodField()

    status = serializers.SerializerMethodField()

    cleared_at = serializers.SerializerMethodField()

    is_overdue = serializers.SerializerMethodField()

    def get_financials(self, obj):
        if not hasattr(obj, "_financials_cache"):
            obj._financials_cache = get_debt_financials(obj)

        return obj._financials_cache

    def get_paid_amount(self, obj):
        return self.get_financials(obj)["paid_amount"]

    def get_remaining_amount(self, obj):
        return self.get_financials(obj)["remaining_amount"]

    def get_status(self, obj):
        return self.get_financials(obj)["status"]

    def get_cleared_at(self, obj):
        return self.get_financials(obj)["cleared_at"]

    def get_is_overdue(self, obj):
        return self.get_financials(obj)["is_overdue"]

    class Meta:
        model = Debt

        fields = [
            "id",
            "customer_id",
            "customer_name",
            "created_at",
            "note",
            "total_amount",
            "paid_amount",
            "remaining_amount",
            "status",
            "cleared_at",
            "is_overdue",
            "items",
            "created_by",
            "updated_at",
        ]

        read_only_fields = fields