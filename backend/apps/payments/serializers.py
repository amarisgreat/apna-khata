from rest_framework import serializers

from .models import Payment, PaymentAllocation


class PaymentWriteSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1)
    paid_at = serializers.DateTimeField(required=False)
    note = serializers.CharField(required=False, allow_blank=True)


class PaymentAllocationReadSerializer(serializers.ModelSerializer):
    debt_created_at = serializers.DateTimeField(
        source="debt.created_at",
        read_only=True,
    )

    class Meta:
        model = PaymentAllocation
        fields = [
            "id",
            "debt",
            "debt_created_at",
            "amount",
        ]


class PaymentReadSerializer(serializers.ModelSerializer):
    customer_id = serializers.IntegerField(
        source="customer.id",
        read_only=True,
    )
    customer_name = serializers.CharField(
        source="customer.name",
        read_only=True,
    )
    allocations = PaymentAllocationReadSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = Payment
        fields = [
            "id",
            "customer_id",
            "customer_name",
            "amount",
            "paid_at",
            "note",
            "allocations",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields