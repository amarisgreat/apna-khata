
from decimal import Decimal, ROUND_HALF_UP


def calculate_line_total(quantity, price_per_unit):
    """
    Calculate item total in paise.
    """

    quantity = Decimal(str(quantity))
    price_per_unit = Decimal(str(price_per_unit))

    total = quantity * price_per_unit

    return int(
        total.quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP
        )
    )


def calculate_debt_total(items):
    """
    Calculate the grand total of all debt items.
    """

    return sum(
        calculate_line_total(
            item["quantity"],
            item["price_per_unit"]
        )
        for item in items
    )
