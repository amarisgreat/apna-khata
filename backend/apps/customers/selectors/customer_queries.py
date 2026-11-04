from datetime import timedelta

from django.db.models import (
    OuterRef,
    Subquery,
    Sum,
    Value,
    BigIntegerField,
    DateTimeField,
    F,
    Exists,
)
from django.db.models.functions import Coalesce, Greatest
from django.utils import timezone

from apps.customers.models import Customer
from apps.debts.models import Debt
from apps.payments.models import Payment


OVERDUE_DAYS = 30


def get_shop_customers(shop):

    # Total debt per customer
    debt_totals = (
        Debt.objects
        .filter(customer_id=OuterRef("pk"))
        .values("customer_id")
        .annotate(total=Sum("total_amount"))
        .values("total")[:1]
    )

    # Total payments per customer
    payment_totals = (
        Payment.objects
        .filter(customer_id=OuterRef("pk"))
        .values("customer_id")
        .annotate(total=Sum("amount"))
        .values("total")[:1]
    )

    # Latest debt activity
    latest_debt = (
        Debt.objects
        .filter(customer_id=OuterRef("pk"))
        .order_by("-created_at", "-id")
        .values("created_at")[:1]
    )

    # Latest payment activity
    latest_payment = (
        Payment.objects
        .filter(customer_id=OuterRef("pk"))
        .order_by("-paid_at", "-id")
        .values("paid_at")[:1]
    )

    # Find individual debts that are overdue and unpaid
    overdue_cutoff = timezone.now() - timedelta(
        days=OVERDUE_DAYS
    )

    overdue_debts = (
        Debt.objects
        .filter(
            customer_id=OuterRef("pk"),
            created_at__lte=overdue_cutoff,
        )
        .annotate(
            total_allocated=Coalesce(
                Sum("allocations__amount"),
                Value(0),
                output_field=BigIntegerField(),
            )
        )
        .filter(
            total_amount__gt=F("total_allocated")
        )
    )

    return (
        Customer.objects
        .filter(shop=shop)
        .annotate(
            total_debt=Coalesce(
                Subquery(
                    debt_totals,
                    output_field=BigIntegerField(),
                ),
                Value(0),
                output_field=BigIntegerField(),
            ),

            total_paid=Coalesce(
                Subquery(
                    payment_totals,
                    output_field=BigIntegerField(),
                ),
                Value(0),
                output_field=BigIntegerField(),
            ),

            latest_debt_activity=Coalesce(
                Subquery(
                    latest_debt,
                    output_field=DateTimeField(),
                ),
                F("created_at"),
                output_field=DateTimeField(),
            ),

            latest_payment_activity=Coalesce(
                Subquery(
                    latest_payment,
                    output_field=DateTimeField(),
                ),
                F("created_at"),
                output_field=DateTimeField(),
            ),

            # This annotation was missing
            has_overdue_debt=Exists(overdue_debts),
        )
        .annotate(
            outstanding_balance=F("total_debt") - F("total_paid"),

            last_activity=Greatest(
                "latest_debt_activity",
                "latest_payment_activity",
            ),
        )
        .prefetch_related("tags")
        .order_by("name", "id")
    )


def get_customer_by_id(*, shop, customer_id):
    return (
        get_shop_customers(shop)
        .filter(id=customer_id)
        .first()
    )