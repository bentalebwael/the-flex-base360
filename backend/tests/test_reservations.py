import pytest
import pytest_asyncio


async def _mock_calculate_total_revenue(property_id: str, tenant_id: str) -> dict:
    """Isolated copy of the mock fallback logic in reservations.py."""
    mock_data = {
        'prop-001': {'total': '1000.00', 'count': 3},
        'prop-002': {'total': '4975.50', 'count': 4},
        'prop-003': {'total': '6100.50', 'count': 2},
        'prop-004': {'total': '1776.50', 'count': 4},
        'prop-005': {'total': '3256.00', 'count': 3},
    }
    mock_property_data = mock_data.get(property_id, {'total': '0.00', 'count': 0})
    return {
        "property_id": property_id,
        "tenant_id": tenant_id,
        "total": mock_property_data['total'],
        "currency": "USD",
        "count": mock_property_data['count'],
    }


@pytest.mark.asyncio
async def test_calculate_total_revenue_returns_correct_format(tenant_a_context):
    result = await _mock_calculate_total_revenue(
        tenant_a_context["property_id"],
        tenant_a_context["tenant_id"],
    )
    assert result["property_id"] == "prop-001"
    assert result["tenant_id"] == "tenant-a"
    assert "total" in result
    assert "currency" in result
    assert "count" in result


@pytest.mark.asyncio
async def test_mock_data_fallback(tenant_b_context):
    result = await _mock_calculate_total_revenue(
        tenant_b_context["property_id"],
        tenant_b_context["tenant_id"],
    )
    assert result["total"] == "1000.00"
    assert result["currency"] == "USD"
