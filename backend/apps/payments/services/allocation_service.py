from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.debts.models import Debt

from apps.payments.models import Payment, PaymentAllocation


@transaction.atomic
def recalculate_customer_allocations(*, customer):
    debts = list(
        Debt.objects.filter(customer=customer)
        .order_by("created_at", "id")
    )

    payments = list(
        Payment.objects.filter(customer=customer)
        .order_by("paid_at", "id")
    )

    total_debt = sum(debt.total_amount for debt in debts)
    total_payments = sum(payment.amount for payment in payments)

    if total_payments > total_debt:
        raise ValidationError(
            "Total payments cannot exceed the customer's total debt."
        )

    # Track the remaining amount for every debt.
    remaining_by_debt = {
        debt.id: debt.total_amount
        for debt in debts
    }

    new_allocations = []

    for payment in payments:
        payment_remaining = payment.amount

        for debt in debts:
            if payment_remaining <= 0:
                break

            debt_remaining = remaining_by_debt[debt.id]

            if debt_remaining <= 0:
                continue

            allocated_amount = min(
                payment_remaining,
                debt_remaining,
            )

            new_allocations.append(
                PaymentAllocation(
                    payment=payment,
                    debt=debt,
                    amount=allocated_amount,
                )
            )

            remaining_by_debt[debt.id] -= allocated_amount
            payment_remaining -= allocated_amount

        if payment_remaining > 0:
            raise ValidationError(
                "Payment could not be fully allocated."
            )

    # Replace previous allocations with the recalculated allocations.
    PaymentAllocation.objects.filter(
        payment__customer=customer
    ).delete()

    PaymentAllocation.objects.bulk_create(new_allocations)

    return remaining_by_debt