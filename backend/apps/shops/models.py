from django.db import models
from django.conf import settings


class Shop(models.Model):

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="shop"
    )

    name = models.CharField(max_length=200)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "shops"

    def __str__(self):
        return self.name