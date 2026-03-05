from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple

from sqlalchemy import text


def _next_month_start(year: int, month: int) -> datetime:
    if month < 12:
        return datetime(year, month + 1, 1)
    return datetime(year + 1, 1, 1)


def _validate_month_year(month: int, year: int) -> None:
    if month < 1 or month > 12:
        raise ValueError("month must be between 1 and 12")
    if year < 1970 or year > 9999:
        raise ValueError("year is out of range")


async def _get_property_timezone(session, property_id: str, tenant_id: str) -> str:
    tz_query = text(
        """
        SELECT timezone
        FROM properties
        WHERE id = :property_id AND tenant_id = :tenant_id
        LIMIT 1
        """
    )
    tz_result = await session.execute(
        tz_query,
        {"property_id": property_id, "tenant_id": tenant_id},
    )
    tz_row = tz_result.fetchone()
    return (tz_row.timezone if tz_row and tz_row.timezone else "UTC")


async def _get_latest_reporting_period(
    session,
    property_id: str,
    tenant_id: str,
    property_timezone: str,
) -> Optional[Tuple[int, int]]:
    latest_month_query = text(
        """
        SELECT DATE_TRUNC(
            'month',
            MAX(check_in_date AT TIME ZONE :property_timezone)
        ) AS latest_month
        FROM reservations
        WHERE property_id = :property_id AND tenant_id = :tenant_id
        """
    )
    latest_result = await session.execute(
        latest_month_query,
        {
            "property_id": property_id,
            "tenant_id": tenant_id,
            "property_timezone": property_timezone,
        },
    )
    latest_row = latest_result.fetchone()
    if not latest_row or not latest_row.latest_month:
        return None
    return latest_row.latest_month.month, latest_row.latest_month.year


async def calculate_monthly_revenue(
    property_id: str,
    month: int,
    year: int,
    db_session=None,
    tenant_id: Optional[str] = None,
) -> Decimal:
    """
    Calculate monthly revenue using the property's local timezone boundaries.
    """
    if not db_session:
        raise ValueError("db_session is required")
    if not tenant_id:
        raise ValueError("tenant_id is required")

    _validate_month_year(month, year)
    property_timezone = await _get_property_timezone(db_session, property_id, tenant_id)
    period_start = datetime(year, month, 1)
    period_end = _next_month_start(year, month)

    monthly_query = text(
        """
        SELECT COALESCE(SUM(total_amount), 0) AS total_revenue
        FROM reservations
        WHERE property_id = :property_id
          AND tenant_id = :tenant_id
          AND (check_in_date AT TIME ZONE :property_timezone) >= :period_start
          AND (check_in_date AT TIME ZONE :property_timezone) < :period_end
        """
    )
    monthly_result = await db_session.execute(
        monthly_query,
        {
            "property_id": property_id,
            "tenant_id": tenant_id,
            "property_timezone": property_timezone,
            "period_start": period_start,
            "period_end": period_end,
        },
    )
    monthly_row = monthly_result.fetchone()
    return Decimal(str(monthly_row.total_revenue if monthly_row else "0"))


async def calculate_total_revenue(
    property_id: str,
    tenant_id: str,
    month: Optional[int] = None,
    year: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Aggregate revenue for a monthly reporting window based on property-local time.

    If month/year are not provided, uses the latest month that has reservation data
    for the property within the tenant.
    """
    from app.core.database_pool import db_pool

    await db_pool.initialize()
    if not db_pool.session_factory:
        raise RuntimeError("Database pool not available")

    async with db_pool.get_session() as session:
        property_timezone = await _get_property_timezone(session, property_id, tenant_id)

        if month is None or year is None:
            latest_period = await _get_latest_reporting_period(
                session,
                property_id,
                tenant_id,
                property_timezone,
            )
            if not latest_period:
                return {
                    "property_id": property_id,
                    "tenant_id": tenant_id,
                    "total": "0.00",
                    "currency": "USD",
                    "count": 0,
                    "report_month": None,
                    "report_year": None,
                    "property_timezone": property_timezone,
                }
            report_month, report_year = latest_period
        else:
            _validate_month_year(month, year)
            report_month, report_year = month, year

        period_start = datetime(report_year, report_month, 1)
        period_end = _next_month_start(report_year, report_month)

        monthly_summary_query = text(
            """
            SELECT
                COALESCE(SUM(total_amount), 0) AS total_revenue,
                COUNT(*) AS reservation_count
            FROM reservations
            WHERE property_id = :property_id
              AND tenant_id = :tenant_id
              AND (check_in_date AT TIME ZONE :property_timezone) >= :period_start
              AND (check_in_date AT TIME ZONE :property_timezone) < :period_end
            """
        )

        result = await session.execute(
            monthly_summary_query,
            {
                "property_id": property_id,
                "tenant_id": tenant_id,
                "property_timezone": property_timezone,
                "period_start": period_start,
                "period_end": period_end,
            },
        )
        row = result.fetchone()

        total_revenue = Decimal(str(row.total_revenue if row else "0"))
        reservation_count = int(row.reservation_count if row else 0)

        return {
            "property_id": property_id,
            "tenant_id": tenant_id,
            "total": str(total_revenue),
            "currency": "USD",
            "count": reservation_count,
            "report_month": report_month,
            "report_year": report_year,
            "property_timezone": property_timezone,
        }
