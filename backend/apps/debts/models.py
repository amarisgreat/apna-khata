from django.db import models
from django.core.validators import MinValueValidator
from django.conf import settings


class Debt(models.Model):

    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.PROTECT,
        related_name="debts"
    )

    created_at = models.DateTimeField(
        db_index=True
    )

    note = models.TextField(blank=True)

    total_amount = models.PositiveBigIntegerField(
        default=0,
        validators=[MinValueValidator(1)]
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_debts"
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "debts"
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(fields=["customer", "created_at"]),
        ]

    def __str__(self):
        return f"Debt #{self.id} - {self.customer.name}"


class DebtItem(models.Model):

    debt = models.ForeignKey(
        Debt,
        on_delete=models.CASCADE,
        related_name="items"
    )

    name = models.CharField(max_length=150)

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        validators=[MinValueValidator(0.001)]
    )

    unit = models.CharField(max_length=30)

    price_per_unit = models.PositiveBigIntegerField(
        validators=[MinValueValidator(1)]
    )

    line_total = models.PositiveBigIntegerField(
        default=0
    )

    class Meta:
        db_table = "debt_items"
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="debt_item_quantity_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(price_per_unit__gt=0),
                name="debt_item_price_positive"
            ),
        ]

    def __str__(self):
        return f"{self.name} - Debt #{self.debt_id}"
