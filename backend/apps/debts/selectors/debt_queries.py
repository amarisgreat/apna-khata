from datetime import timedelta

from django.utils import timezone
from django.db.models import Prefetch

from apps.debts.models import Debt
from apps.payments.models import PaymentAllocation


OVERDUE_DAYS = 30


def get_customer_debts(customer):
    allocations = (
        PaymentAllocation.objects
        .select_related("payment")
        .order_by("payment__paid_at", "payment_id", "id")
    )

    return (
        Debt.objects
        .filter(customer=customer)
        .select_related("customer", "created_by")
        .prefetch_related(
            "items",
            Prefetch(
                "allocations",
                queryset=allocations,
            ),
        )
        .order_by("created_at", "id")
    )


def get_debt_financials(debt):
    allocations = list(debt.allocations.all())

    paid_amount = sum(
        allocation.amount for allocation in allocations
    )

    remaining_amount = max(
        debt.total_amount - paid_amount,
        0,
    )

    cleared_at = None

    if remaining_amount == 0:
        running_total = 0

        for allocation in allocations:
            running_total += allocation.amount

            if running_total >= debt.total_amount:
                cleared_at = allocation.payment.paid_at
                break

    is_overdue = (
        remaining_amount > 0
        and timezone.now() >= debt.created_at + timedelta(days=OVERDUE_DAYS)
    )

    return {
        "total_amount": debt.total_amount,
        "paid_amount": paid_amount,
        "remaining_amount": remaining_amount,
        "status": "CLEARED" if remaining_amount == 0 else "ACTIVE",
        "cleared_at": cleared_at,
        "is_overdue": is_overdue,
    }