from decimal import Decimal

from django.utils import timezone

from apps.debts.models import Debt
from apps.payments.models import PaymentAllocation


# Configurable weights
REPAYMENT_SPEED_WEIGHT = Decimal("0.50")
OVERDUE_WEIGHT = Decimal("0.30")
REPAYMENT_CONSISTENCY_WEIGHT = Decimal("0.20")

OVERDUE_DAYS = 30

INITIAL_SCORE = Decimal("50")

LABELS = [
    (80, "Excellent"),
    (60, "Good"),
    (40, "Average"),
    (0, "Risky"),
]


def get_trust_label(score):
    for minimum_score, label in LABELS:
        if score >= minimum_score:
            return label

    return "Risky"


def calculate_trust_score(customer):
    """
    Dynamically calculate a customer's trust score.

    Returns:
        {
            "score": int,
            "label": str
        }
    """

    debts = list(
        Debt.objects.filter(customer=customer)
        .prefetch_related("allocations__payment")
        .order_by("created_at", "id")
    )

    if not debts:
        return {
            "score": 50,
            "label": "Average",
        }

    now = timezone.now()

    total_debt = sum(debt.total_amount for debt in debts)

    if total_debt <= 0:
        return {
            "score": 50,
            "label": "Average",
        }

    total_paid = 0
    weighted_repayment_speed = Decimal("0")
    weighted_overdue_penalty = Decimal("0")

    for debt in debts:

        debt_amount = Decimal(debt.total_amount)

        if debt_amount <= 0:
            continue

        allocations = sorted(
            debt.allocations.all(),
            key=lambda allocation: (
                allocation.payment.paid_at,
                allocation.payment_id,
                allocation.id,
            ),
        )

        paid_amount = sum(
            allocation.amount for allocation in allocations
        )

        total_paid += paid_amount

        remaining_amount = max(
            debt.total_amount - paid_amount,
            0,
        )

        # Calculate the time taken to repay this debt.
        cumulative_paid = 0
        cleared_at = None

        for allocation in allocations:
            cumulative_paid += allocation.amount

            if cumulative_paid >= debt.total_amount:
                cleared_at = allocation.payment.paid_at
                break

        # Repayment speed score: 100 for immediate repayment,
        # declining to 0 at 90 days.
        if cleared_at:
            repayment_days = max(
                (cleared_at - debt.created_at).days,
                0,
            )

            speed_score = max(
                Decimal("0"),
                Decimal("100") * (
                    Decimal("1") -
                    Decimal(min(repayment_days, 90)) / Decimal("90")
                ),
            )

        elif remaining_amount > 0:
            elapsed_days = max(
                (now - debt.created_at).days,
                0,
            )

            speed_score = max(
                Decimal("0"),
                Decimal("100") * (
                    Decimal("1") -
                    Decimal(min(elapsed_days, 90)) / Decimal("90")
                ),
            )

        else:
            speed_score = Decimal("100")

        weighted_repayment_speed += (
            speed_score * debt_amount
        )

        # Overdue penalty: starts after 30 days.
        if remaining_amount > 0:
            overdue_days = max(
                (now - debt.created_at).days - OVERDUE_DAYS,
                0,
            )

            overdue_ratio = min(
                Decimal(overdue_days) / Decimal("90"),
                Decimal("1"),
            )

            overdue_penalty = (
                overdue_ratio * Decimal("100")
            )

        else:
            overdue_penalty = Decimal("0")

        weighted_overdue_penalty += (
            overdue_penalty * debt_amount
        )

    # Amount-weighted repayment speed.
    repayment_speed_score = (
        weighted_repayment_speed / Decimal(total_debt)
    )

    # Amount-weighted overdue score.
    overdue_score = (
        Decimal("100") -
        weighted_overdue_penalty / Decimal(total_debt)
    )

    # Percentage of total debt repaid.
    repayment_consistency_score = min(
        Decimal("100"),
        Decimal(total_paid) / Decimal(total_debt) * Decimal("100"),
    )

    # Combine the three components.
    final_score = (
        repayment_speed_score * REPAYMENT_SPEED_WEIGHT
        + overdue_score * OVERDUE_WEIGHT
        + repayment_consistency_score * REPAYMENT_CONSISTENCY_WEIGHT
    )

    final_score = max(
        Decimal("0"),
        min(Decimal("100"), final_score),
    )

    score = int(final_score.quantize(Decimal("1")))

    return {
        "score": score,
        "label": get_trust_label(score),
    }