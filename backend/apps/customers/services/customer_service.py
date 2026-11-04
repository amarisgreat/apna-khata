from django.db import transaction

from apps.customers.models import Customer, CustomerTag


@transaction.atomic
def create_customer(*, shop, data):

    tags = data.pop("tags", [])

    customer = Customer.objects.create(
        shop=shop,
        **data
    )

    CustomerTag.objects.bulk_create([
        CustomerTag(customer=customer, name=tag)
        for tag in set(tags)
    ])

    return customer


@transaction.atomic
def update_customer(*, customer, data):

    tags = data.pop("tags", None)

    for field, value in data.items():
        setattr(customer, field, value)

    customer.save()

    if tags is not None:
        customer.tags.all().delete()

        CustomerTag.objects.bulk_create([
            CustomerTag(customer=customer, name=tag)
            for tag in set(tags)
        ])

    return customer


def change_customer_status(*, customer, status):

    customer.status = status
    customer.save(update_fields=["status", "updated_at"])

    return customer