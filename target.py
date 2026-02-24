def calculate_discount(price: float, discount_percentage: float) -> float:
    """
    Calculate the final price after applying a discount.

    :param price: Original price (must be non-negative)
    :param discount_percentage: Discount percentage (0 to 100)
    :return: Final price after discount
    """

    if price < 0:
        raise ValueError("Price cannot be negative.")

    if discount_percentage < 0 or discount_percentage > 100:
        raise ValueError("Discount percentage must be between 0 and 100.")

    discount_amount = price * (discount_percentage / 100)
    final_price = price - discount_amount

    return round(final_price, 2)