from django.db import transaction
from django.utils import timezone

from apps.debts.models import Debt, DebtItem
from apps.debts.services.debt_calculator import (
    calculate_line_total,
    calculate_debt_total,
)


@transaction.atomic
def create_debt(*, customer, created_by, created_at=None, items, note=""):
    if not items:
        raise ValueError("A debt must contain at least one item.")

    total = calculate_debt_total(items)

    if total <= 0:
        raise ValueError("Debt total must be greater than zero.")

    debt = Debt.objects.create(
        customer=customer,
        created_by=created_by,
        created_at=created_at or timezone.now(),
        note=note,
        total_amount=total,
    )

    debt_items = []

    for item in items:
        line_total = calculate_line_total(
            item["quantity"],
            item["price_per_unit"],
        )

        debt_items.append(
            DebtItem(
                debt=debt,
                name=item["name"],
                quantity=item["quantity"],
                unit=item["unit"],
                price_per_unit=item["price_per_unit"],
                line_total=line_total,
            )
        )

    DebtItem.objects.bulk_create(debt_items)

    return debt


@transaction.atomic
def update_debt(*, debt, data):
    items = data.pop("items", None)

    if "created_at" in data:
        debt.created_at = data["created_at"]

    if "note" in data:
        debt.note = data["note"]

    if items is not None:
        if not items:
            raise ValueError("A debt must contain at least one item.")

        total = calculate_debt_total(items)

        if total <= 0:
            raise ValueError("Debt total must be greater than zero.")

        debt.items.all().delete()

        new_items = []

        for item in items:
            new_items.append(
                DebtItem(
                    debt=debt,
                    name=item["name"],
                    quantity=item["quantity"],
                    unit=item["unit"],
                    price_per_unit=item["price_per_unit"],
                    line_total=calculate_line_total(
                        item["quantity"],
                        item["price_per_unit"],
                    ),
                )
            )

        DebtItem.objects.bulk_create(new_items)
        debt.total_amount = total

    debt.save()

    return debt