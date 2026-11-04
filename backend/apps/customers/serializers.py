from django.db.models import Sum

from rest_framework import serializers

from .models import Customer
from .services.trust_score_service import calculate_trust_score


class CustomerSerializer(serializers.ModelSerializer):

    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False,
    )

    tag_names = serializers.SerializerMethodField()

    total_debt = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()
    outstanding_balance = serializers.SerializerMethodField()

    last_activity = serializers.SerializerMethodField()

    trust_score = serializers.SerializerMethodField()
    trust_label = serializers.SerializerMethodField()

    class Meta:
        model = Customer

        fields = [
            "id",
            "name",
            "phone",
            "address",
            "notes",
            "photo",
            "status",
            "tags",
            "tag_names",
            "total_debt",
            "total_paid",
            "outstanding_balance",
            "last_activity",
            "trust_score",
            "trust_label",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "status",
            "tag_names",
            "total_debt",
            "total_paid",
            "outstanding_balance",
            "last_activity",
            "trust_score",
            "trust_label",
            "created_at",
            "updated_at",
        ]

    # ==============================================
    # TAG VALIDATION
    # ==============================================

    def validate_tags(self, value):
        cleaned_tags = []

        for tag in value:
            tag = tag.strip()

            if not tag:
                raise serializers.ValidationError(
                    "Tag names cannot be empty."
                )

            if tag not in cleaned_tags:
                cleaned_tags.append(tag)

        return cleaned_tags

    # ==============================================
    # TAG NAMES
    # ==============================================

    def get_tag_names(self, obj):
        return list(
            obj.tags.values_list("name", flat=True)
        )

    # ==============================================
    # FINANCIAL SUMMARY
    # ==============================================

    def get_financial_summary(self, obj):

        # Use selector annotations when available.
        if (
            hasattr(obj, "total_debt")
            and hasattr(obj, "total_paid")
            and hasattr(obj, "outstanding_balance")
        ):
            return {
                "total_debt": obj.total_debt,
                "total_paid": obj.total_paid,
                "outstanding_balance": obj.outstanding_balance,
            }

        # Otherwise calculate directly from related records.
        if not hasattr(obj, "_financial_summary_cache"):

            total_debt = (
                obj.debts.aggregate(
                    total=Sum("total_amount")
                )["total"] or 0
            )

            total_paid = (
                obj.payments.aggregate(
                    total=Sum("amount")
                )["total"] or 0
            )

            obj._financial_summary_cache = {
                "total_debt": total_debt,
                "total_paid": total_paid,
                "outstanding_balance": max(
                    total_debt - total_paid,
                    0,
                ),
            }

        return obj._financial_summary_cache

    def get_total_debt(self, obj):
        return self.get_financial_summary(obj)["total_debt"]

    def get_total_paid(self, obj):
        return self.get_financial_summary(obj)["total_paid"]

    def get_outstanding_balance(self, obj):
        return self.get_financial_summary(obj)["outstanding_balance"]

    # ==============================================
    # LAST ACTIVITY
    # ==============================================

    def get_last_activity(self, obj):
        return getattr(obj, "last_activity", None) or obj.created_at

    # ==============================================
    # TRUST SCORE
    # ==============================================

    def get_trust_summary(self, obj):

        if not hasattr(obj, "_trust_summary_cache"):
            obj._trust_summary_cache = calculate_trust_score(obj)

        return obj._trust_summary_cache

    def get_trust_score(self, obj):
        return self.get_trust_summary(obj)["score"]

    def get_trust_label(self, obj):
        return self.get_trust_summary(obj)["label"]