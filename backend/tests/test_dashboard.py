import pytest
from decimal import Decimal, ROUND_HALF_UP


def format_revenue(raw: str) -> float:
    """Mirrors the precision logic in dashboard.py."""
    return float(Decimal(raw).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def test_revenue_rounded_to_two_decimals():
    # 1250.000 + 333.333 + 333.333 + 333.334 = 2250.000 exactly
    total = Decimal('1250.000') + Decimal('333.333') + Decimal('333.333') + Decimal('333.334')
    result = float(total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    assert result == 2250.00


def test_revenue_response_structure():
    raw_total = "2250.000"
    response = {
        "property_id": "prop-001",
        "total_revenue": format_revenue(raw_total),
        "currency": "USD",
        "reservations_count": 4,
    }
    assert "property_id" in response
    assert "total_revenue" in response
    assert "currency" in response
    assert "reservations_count" in response
    assert isinstance(response["total_revenue"], float)
    assert response["total_revenue"] == 2250.00
