from django.db import transaction

from apps.accounts.models import User
from apps.shops.models import Shop


@transaction.atomic
def register_shopkeeper(*, name, shop_name, phone, password):

    user = User.objects.create_user(
        name=name,
        phone=phone,
        password=password
    )

    shop = Shop.objects.create(
        owner=user,
        name=shop_name
    )

    return user, shop