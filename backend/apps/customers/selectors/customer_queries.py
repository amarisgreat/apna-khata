from apps.customers.models import Customer


def get_shop_customers(shop):
    return (
        Customer.objects
        .filter(shop=shop)
        .prefetch_related("tags")
    )


def get_customer_by_id(*, shop, customer_id):

    return get_shop_customers(shop).filter(
        id=customer_id
    ).first()