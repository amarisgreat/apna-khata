from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings


class Payment(models.Model):
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="payments",
    )
    amount = models.PositiveBigIntegerField(
        validators=[MinValueValidator(1)],
    )
    paid_at = models.DateTimeField(db_index=True)
    note = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="recorded_payments",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payments"
        ordering = ["paid_at", "id"]
        indexes = [
            models.Index(fields=["customer", "paid_at"]),
        ]

    def __str__(self):
        return f"Payment #{self.id} - {self.customer.name}"


class PaymentAllocation(models.Model):
    payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        related_name="allocations",
    )
    debt = models.ForeignKey(
        "debts.Debt",
        on_delete=models.PROTECT,
        related_name="allocations",
    )
    amount = models.PositiveBigIntegerField(
        validators=[MinValueValidator(1)],
    )

    class Meta:
        db_table = "payment_allocations"
        ordering = ["payment__paid_at", "payment_id", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["payment", "debt"],
                name="unique_payment_debt_allocation",
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="payment_allocation_amount_positive",
            ),
        ]

    def __str__(self):
        return f"Payment #{self.payment_id} → Debt #{self.debt_id}"