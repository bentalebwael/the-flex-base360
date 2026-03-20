from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def format_revenue_total(value: str) -> str:
    """Serialize money as a two-decimal string without floating-point drift."""
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError) as exc:
        raise ValueError("Invalid revenue total") from exc

    return format(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), ".2f")
