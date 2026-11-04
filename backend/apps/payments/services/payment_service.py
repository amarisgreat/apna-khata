from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.customers.models import Customer
from apps.payments.models import Payment

from apps.payments.services.allocation_service import (
    recalculate_customer_allocations,
)


@transaction.atomic
def create_payment(
    *,
    customer,
    created_by,
    amount,
    paid_at=None,
    note="",
):
    if amount <= 0:
        raise ValidationError(
            {"amount": "Payment amount must be greater than zero."}
        )

    Customer.objects.select_for_update().get(id=customer.id)

    total_debt = sum(
        customer.debts.values_list("total_amount", flat=True)
    )

    total_paid = sum(
        customer.payments.values_list("amount", flat=True)
    )

    outstanding = total_debt - total_paid

    if amount > outstanding:
        raise ValidationError(
            {
                "amount": (
                    f"Payment exceeds outstanding balance "
                    f"of {outstanding} paise."
                )
            }
        )

    payment = Payment.objects.create(
        customer=customer,
        amount=amount,
        paid_at=paid_at or timezone.now(),
        note=note,
        created_by=created_by,
    )

    recalculate_customer_allocations(customer=customer)

    return payment


@transaction.atomic
def update_payment(*, payment, data):
    Customer.objects.select_for_update().get(
        id=payment.customer_id
    )

    payment = Payment.objects.select_for_update().get(
        id=payment.id
    )

    if "amount" in data:
        if data["amount"] <= 0:
            raise ValidationError(
                {"amount": "Payment amount must be greater than zero."}
            )
        payment.amount = data["amount"]

    if "paid_at" in data:
        payment.paid_at = data["paid_at"]

    if "note" in data:
        payment.note = data["note"]

    payment.save()

    recalculate_customer_allocations(
        customer=payment.customer
    )

    return payment