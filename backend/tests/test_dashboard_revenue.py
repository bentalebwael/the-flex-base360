import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.services import cache as cache_service
from app.services.properties import list_tenant_properties
from app.services.revenue_format import format_revenue_total
from app.services.reservations import calculate_total_revenue


class FakeRedis:
    def __init__(self):
        self.store = {}

    async def get(self, key):
        return self.store.get(key)

    async def setex(self, key, ttl, value):
        self.store[key] = value


class FakeResult:
    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = rows or []

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class FakeSession:
    def __init__(self, result):
        self.result = result

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, query, params):
        return self.result


class DashboardRevenueTests(unittest.IsolatedAsyncioTestCase):
    async def test_revenue_cache_is_scoped_by_tenant(self):
        fake_redis = FakeRedis()
        calculate_total = AsyncMock(
            side_effect=[
                {
                    "property_id": "prop-001",
                    "tenant_id": "tenant-a",
                    "total": "2250.000",
                    "currency": "USD",
                    "count": 4,
                },
                {
                    "property_id": "prop-001",
                    "tenant_id": "tenant-b",
                    "total": "0",
                    "currency": "USD",
                    "count": 0,
                },
            ]
        )

        with patch.object(cache_service, "redis_client", fake_redis), patch(
            "app.services.reservations.calculate_total_revenue",
            new=calculate_total,
        ):
            tenant_a_first = await cache_service.get_revenue_summary("prop-001", "tenant-a")
            tenant_b = await cache_service.get_revenue_summary("prop-001", "tenant-b")
            tenant_a_second = await cache_service.get_revenue_summary("prop-001", "tenant-a")

        self.assertEqual(tenant_a_first["total"], "2250.000")
        self.assertEqual(tenant_b["total"], "0")
        self.assertEqual(tenant_a_second, tenant_a_first)
        self.assertEqual(calculate_total.await_count, 2)
        self.assertCountEqual(
            fake_redis.store.keys(),
            [
                "revenue:tenant-a:prop-001",
                "revenue:tenant-b:prop-001",
            ],
        )

    async def test_calculate_total_revenue_returns_exact_database_values(self):
        row = SimpleNamespace(
            property_id="prop-001",
            total_revenue=Decimal("2250.000"),
            reservation_count=4,
            currency="USD",
        )
        fake_session = FakeSession(FakeResult(row=row))

        with patch("app.services.reservations.db_pool.initialize", new=AsyncMock()), patch(
            "app.services.reservations.db_pool.get_session",
            new=MagicMock(return_value=fake_session),
        ):
            result = await calculate_total_revenue("prop-001", "tenant-a")

        self.assertEqual(
            result,
            {
                "property_id": "prop-001",
                "tenant_id": "tenant-a",
                "total": "2250.000",
                "currency": "USD",
                "count": 4,
            },
        )

    async def test_calculate_total_revenue_returns_none_for_unknown_property(self):
        fake_session = FakeSession(FakeResult(row=None))

        with patch("app.services.reservations.db_pool.initialize", new=AsyncMock()), patch(
            "app.services.reservations.db_pool.get_session",
            new=MagicMock(return_value=fake_session),
        ):
            result = await calculate_total_revenue("prop-999", "tenant-a")

        self.assertIsNone(result)

    async def test_list_tenant_properties_returns_only_requested_tenant_rows(self):
        rows = [
            SimpleNamespace(id="prop-001", name="Beach House Alpha", timezone="Europe/Paris"),
            SimpleNamespace(id="prop-002", name="City Apartment Downtown", timezone="Europe/Paris"),
        ]
        fake_session = FakeSession(FakeResult(rows=rows))

        with patch("app.services.properties.db_pool.initialize", new=AsyncMock()), patch(
            "app.services.properties.db_pool.get_session",
            new=MagicMock(return_value=fake_session),
        ):
            result = await list_tenant_properties("tenant-a")

        self.assertEqual(
            result,
            [
                {"id": "prop-001", "name": "Beach House Alpha", "timezone": "Europe/Paris"},
                {"id": "prop-002", "name": "City Apartment Downtown", "timezone": "Europe/Paris"},
            ],
        )

    def test_format_revenue_total_rounds_without_float_drift(self):
        self.assertEqual(format_revenue_total("1000"), "1000.00")
        self.assertEqual(format_revenue_total("10.005"), "10.01")


if __name__ == "__main__":
    unittest.main()
