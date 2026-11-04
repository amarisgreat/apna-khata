from django.db import models
from django.conf import settings


class Customer(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    shop = models.ForeignKey(
        "shops.Shop",
        on_delete=models.PROTECT,
        related_name="customers"
    )

    name = models.CharField(max_length=150)

    phone = models.CharField(
        max_length=15,
        blank=True,
        db_index=True
    )

    address = models.TextField(blank=True)

    notes = models.TextField(blank=True)

    photo = models.ImageField(
        upload_to="customers/",
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "customers"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["shop", "status"]),
            models.Index(fields=["shop", "name"]),
            models.Index(fields=["shop", "phone"]),
        ]

    def __str__(self):
        return self.name


class CustomerTag(models.Model):

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="tags"
    )

    name = models.CharField(max_length=50)

    class Meta:
        db_table = "customer_tags"

        constraints = [
            models.UniqueConstraint(
                fields=["customer", "name"],
                name="unique_customer_tag"
            )
        ]

    def __str__(self):
        return self.name