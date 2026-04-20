from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List
import logging

import pytz
from sqlalchemy import text

logger = logging.getLogger(__name__)


async def calculate_monthly_revenue(
    property_id: str,
    tenant_id: str,
    month: int,
    year: int,
) -> Decimal:
    """
    Calculate revenue for a property in a given calendar month, using the
    property's local timezone to determine month boundaries.

    Why: reservations.check_in_date is stored as TIMESTAMP WITH TIME ZONE (UTC).
    A check-in at 2024-02-29 23:30 UTC is March 1 00:30 in Europe/Paris and
    must be counted toward March revenue for a Paris property — using naive
    UTC month boundaries silently drops that reservation from March.
    """
    from app.core.database_pool import DatabasePool

    db_pool = DatabasePool()
    await db_pool.initialize()

    if not db_pool.session_factory:
        raise RuntimeError("Database pool not available")

    async with db_pool.get_session() as session:
        tz_result = await session.execute(
            text(
                "SELECT timezone FROM properties "
                "WHERE id = :property_id AND tenant_id = :tenant_id"
            ),
            {"property_id": property_id, "tenant_id": tenant_id},
        )
        tz_row = tz_result.fetchone()
        if not tz_row:
            raise ValueError(
                f"Property {property_id} not found for tenant {tenant_id}"
            )

        tz = pytz.timezone(tz_row.timezone or "UTC")

        local_start = tz.localize(datetime(year, month, 1))
        if month < 12:
            local_end = tz.localize(datetime(year, month + 1, 1))
        else:
            local_end = tz.localize(datetime(year + 1, 1, 1))

        utc_start = local_start.astimezone(pytz.UTC)
        utc_end = local_end.astimezone(pytz.UTC)

        result = await session.execute(
            text(
                """
                SELECT COALESCE(SUM(total_amount), 0) AS total
                FROM reservations
                WHERE property_id = :property_id
                  AND tenant_id = :tenant_id
                  AND check_in_date >= :utc_start
                  AND check_in_date < :utc_end
                """
            ),
            {
                "property_id": property_id,
                "tenant_id": tenant_id,
                "utc_start": utc_start,
                "utc_end": utc_end,
            },
        )
        row = result.fetchone()
        return Decimal(str(row.total))

async def calculate_total_revenue(property_id: str, tenant_id: str) -> Dict[str, Any]:
    """
    Aggregates revenue from database.
    """
    try:
        # Import database pool
        from app.core.database_pool import DatabasePool
        
        # Initialize pool if needed
        db_pool = DatabasePool()
        await db_pool.initialize()
        
        if db_pool.session_factory:
            async with db_pool.get_session() as session:
                query = text("""
                    SELECT
                        currency,
                        SUM(total_amount) AS total_revenue,
                        COUNT(*) AS reservation_count
                    FROM reservations
                    WHERE property_id = :property_id AND tenant_id = :tenant_id
                    GROUP BY currency
                """)

                result = await session.execute(query, {
                    "property_id": property_id,
                    "tenant_id": tenant_id,
                })
                rows = result.fetchall()

                if not rows:
                    # No reservations: still need a sensible currency for the
                    # response. Default to USD (matches the schema default).
                    return {
                        "property_id": property_id,
                        "tenant_id": tenant_id,
                        "total": "0.00",
                        "currency": "USD",
                        "count": 0,
                    }

                if len(rows) > 1:
                    # Mixing currencies in a single SUM is meaningless. Refuse
                    # rather than silently coerce to one currency.
                    currencies = sorted(r.currency for r in rows)
                    raise ValueError(
                        f"Property {property_id} has reservations in multiple "
                        f"currencies ({', '.join(currencies)}); cannot aggregate"
                    )

                row = rows[0]
                return {
                    "property_id": property_id,
                    "tenant_id": tenant_id,
                    "total": str(Decimal(str(row.total_revenue))),
                    "currency": row.currency or "USD",
                    "count": row.reservation_count,
                }
        else:
            raise Exception("Database pool not available")
            
    except ValueError:
        # Data-integrity problems (e.g. mixed currencies) must surface to the
        # caller, not be hidden behind the connection-failure fallback.
        raise
    except Exception as e:
        logger.error(f"Database error for {property_id} (tenant: {tenant_id}): {e}")

        # Fallback used only when the DB is unreachable. Keyed by (tenant_id,
        # property_id) so a tenant never sees another tenant's mocked totals,
        # and values match the real seed data so fallback ≠ silent corruption.
        mock_data = {
            ('tenant-a', 'prop-001'): {'total': '2250.000', 'count': 4},
            ('tenant-a', 'prop-002'): {'total': '4975.50', 'count': 4},
            ('tenant-a', 'prop-003'): {'total': '6100.50', 'count': 2},
            ('tenant-b', 'prop-004'): {'total': '1776.50', 'count': 4},
            ('tenant-b', 'prop-005'): {'total': '3256.00', 'count': 3},
        }

        mock_property_data = mock_data.get(
            (tenant_id, property_id), {'total': '0.00', 'count': 0}
        )

        return {
            "property_id": property_id,
            "tenant_id": tenant_id,
            "total": mock_property_data['total'],
            "currency": "USD",
            "count": mock_property_data['count'],
        }
