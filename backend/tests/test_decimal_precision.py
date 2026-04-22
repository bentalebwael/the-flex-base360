"""
Bug #2: dashboard.py converts DB revenue totals to float before returning them.
The database stores amounts as NUMERIC(10,3); IEEE 754 float cannot represent all
3-decimal fractions exactly, so sub-cent values are silently corrupted.
"""
from decimal import Decimal, ROUND_HALF_UP


# ── mirror the current and proposed code paths ────────────────────────────

def current_conversion(raw: str) -> float:
    """Reproduces dashboard.py line 18: float(revenue_data['total'])"""
    return float(raw)


def fixed_conversion(raw: str) -> str:
    """Fix: round to cents with Decimal arithmetic, return as a string."""
    return str(Decimal(raw).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


# ── tests ─────────────────────────────────────────────────────────────────

def test_ieee754_float_cannot_represent_all_decimal_fractions():
    """float arithmetic is unsafe for financial data (canonical example)."""
    assert 0.1 + 0.2 != 0.3


def test_decimal_sum_of_seed_amounts_is_exact():
    """
    prop-001/tenant-a has three reservations: 333.333, 333.333, 333.334.
    PostgreSQL NUMERIC arithmetic produces exactly 1000.000.
    """
    amounts = [Decimal("333.333"), Decimal("333.333"), Decimal("333.334")]
    assert sum(amounts) == Decimal("1000.000")


def test_float_rounds_half_cent_in_wrong_direction():
    """
    float("2249.005") is represented internally as slightly below 2249.005
    in IEEE 754, so it rounds DOWN to 2249.00 instead of UP to 2249.01.
    This directly causes the 'few cents off' complaints from the finance team.
    """
    raw = "2249.005"
    via_float = round(current_conversion(raw) * 100) / 100
    assert via_float == 2249.0, (
        f"Expected float to round incorrectly to 2249.00, got {via_float}"
    )


def test_buggy_conversion_rounds_sub_cent_boundary_incorrectly():
    """
    A total of 2249.005 sits on a half-cent boundary.
    Decimal (ROUND_HALF_UP) correctly rounds to 2249.01.
    float may represent 2249.005 as slightly below, rounding to 2249.00.
    """
    raw = "2249.005"
    via_float = round(current_conversion(raw) * 100) / 100
    via_decimal = float(fixed_conversion(raw))

    assert via_decimal == 2249.01, "Decimal must round .005 up to .01"
    assert via_float != via_decimal, (
        f"float rounded {raw!r} to {via_float} — should differ from Decimal's {via_decimal}"
    )


def test_fixed_conversion_is_correct_for_all_seed_totals():
    """After the fix, all known DB totals map to the right cent value."""
    cases = [
        ("1000.000", "1000.00"),
        ("4975.500", "4975.50"),
        ("6100.500", "6100.50"),
        ("1776.500", "1776.50"),
        ("3256.000", "3256.00"),
    ]
    for raw, expected in cases:
        assert fixed_conversion(raw) == expected, f"fixed_conversion({raw!r}) != {expected!r}"
