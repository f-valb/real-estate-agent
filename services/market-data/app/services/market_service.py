import logging
import statistics
from datetime import date, datetime, timezone
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.market import MarketStats, Sale
from shared.schemas.market import SaleCreate

logger = logging.getLogger(__name__)


async def record_sale(db: AsyncSession, data: SaleCreate) -> Sale:
    """Persist a new property sale record."""
    sale = Sale(**data.model_dump())
    db.add(sale)
    await db.flush()
    await db.refresh(sale)
    logger.info("Recorded sale %s for %s", sale.id, sale.address)
    return sale


async def list_sales(
    db: AsyncSession,
    city: str | None = None,
    zip_code: str | None = None,
    min_date: date | None = None,
    max_date: date | None = None,
    property_type: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Sale], int]:
    """List sales with optional filters and pagination. Returns (items, total_count)."""
    query = select(Sale)
    count_query = select(func.count(Sale.id))

    if city:
        query = query.where(Sale.city.ilike(f"%{city}%"))
        count_query = count_query.where(Sale.city.ilike(f"%{city}%"))
    if zip_code:
        query = query.where(Sale.zip_code == zip_code)
        count_query = count_query.where(Sale.zip_code == zip_code)
    if min_date:
        query = query.where(Sale.sale_date >= min_date)
        count_query = count_query.where(Sale.sale_date >= min_date)
    if max_date:
        query = query.where(Sale.sale_date <= max_date)
        count_query = count_query.where(Sale.sale_date <= max_date)
    if property_type:
        query = query.where(Sale.property_type == property_type)
        count_query = count_query.where(Sale.property_type == property_type)

    total = (await db.execute(count_query)).scalar() or 0

    offset = (page - 1) * limit
    query = query.order_by(Sale.sale_date.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    items = list(result.scalars().all())

    return items, total


async def get_comps(
    db: AsyncSession,
    zip_code: str,
    bedrooms: int | None = None,
    sqft_min: int | None = None,
    sqft_max: int | None = None,
    limit: int = 10,
) -> list[Sale]:
    """Find comparable sales by matching criteria, ordered by most recent."""
    query = select(Sale).where(Sale.zip_code == zip_code)

    if bedrooms is not None:
        query = query.where(Sale.bedrooms == bedrooms)
    if sqft_min is not None:
        query = query.where(Sale.square_feet >= sqft_min)
    if sqft_max is not None:
        query = query.where(Sale.square_feet <= sqft_max)

    query = query.order_by(Sale.sale_date.desc()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_market_stats(db: AsyncSession, zip_code: str) -> MarketStats | None:
    """Return the most recently computed market stats for a zip code."""
    query = (
        select(MarketStats)
        .where(MarketStats.zip_code == zip_code)
        .order_by(MarketStats.computed_at.desc())
        .limit(1)
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def compute_market_stats(db: AsyncSession, zip_code: str) -> MarketStats:
    """Compute market statistics from sales in the last 6 months and upsert."""
    now = date.today()
    period_end = now
    period_start = now - relativedelta(months=6)

    # Fetch sales in the period
    query = (
        select(Sale)
        .where(
            Sale.zip_code == zip_code,
            Sale.sale_date >= period_start,
            Sale.sale_date <= period_end,
        )
        .order_by(Sale.sale_date.desc())
    )
    result = await db.execute(query)
    sales = list(result.scalars().all())

    # Compute aggregates
    prices = [float(s.sale_price) for s in sales if s.sale_price is not None]
    dom_values = [s.days_on_market for s in sales if s.days_on_market is not None]
    price_per_sqft_values = [
        float(s.sale_price) / s.square_feet
        for s in sales
        if s.sale_price is not None and s.square_feet and s.square_feet > 0
    ]

    median_price = Decimal(str(round(statistics.median(prices), 2))) if prices else None
    avg_price = Decimal(str(round(statistics.mean(prices), 2))) if prices else None
    avg_price_sqft = (
        Decimal(str(round(statistics.mean(price_per_sqft_values), 2)))
        if price_per_sqft_values
        else None
    )
    median_dom = int(statistics.median(dom_values)) if dom_values else None
    total_sales = len(sales)

    # Check for existing stats row for this exact period
    existing_query = select(MarketStats).where(
        MarketStats.zip_code == zip_code,
        MarketStats.period_start == period_start,
        MarketStats.period_end == period_end,
    )
    existing = (await db.execute(existing_query)).scalar_one_or_none()

    if existing:
        existing.median_price = median_price
        existing.avg_price = avg_price
        existing.avg_price_sqft = avg_price_sqft
        existing.median_dom = median_dom
        existing.total_sales = total_sales
        existing.computed_at = datetime.now(timezone.utc)
        await db.flush()
        await db.refresh(existing)
        logger.info("Updated market stats for %s (period %s to %s)", zip_code, period_start, period_end)
        return existing

    stats = MarketStats(
        zip_code=zip_code,
        period_start=period_start,
        period_end=period_end,
        median_price=median_price,
        avg_price=avg_price,
        avg_price_sqft=avg_price_sqft,
        median_dom=median_dom,
        total_sales=total_sales,
        computed_at=datetime.now(timezone.utc),
    )
    db.add(stats)
    await db.flush()
    await db.refresh(stats)
    logger.info("Computed market stats for %s (period %s to %s)", zip_code, period_start, period_end)
    return stats


async def get_price_trends(
    db: AsyncSession,
    zip_code: str,
    months: int = 12,
) -> list[dict]:
    """Return monthly average sale prices for a zip code over the last N months."""
    now = date.today()
    start = now - relativedelta(months=months)

    query = (
        select(
            func.date_trunc("month", Sale.sale_date).label("month"),
            func.avg(Sale.sale_price).label("avg_price"),
            func.count(Sale.id).label("sale_count"),
            func.avg(
                func.case(
                    (Sale.square_feet > 0, Sale.sale_price / Sale.square_feet),
                    else_=None,
                )
            ).label("avg_price_sqft"),
        )
        .where(Sale.zip_code == zip_code, Sale.sale_date >= start)
        .group_by(func.date_trunc("month", Sale.sale_date))
        .order_by(func.date_trunc("month", Sale.sale_date))
    )

    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "month": row.month.strftime("%Y-%m") if row.month else None,
            "avg_price": round(float(row.avg_price), 2) if row.avg_price else None,
            "sale_count": row.sale_count,
            "avg_price_sqft": round(float(row.avg_price_sqft), 2) if row.avg_price_sqft else None,
        }
        for row in rows
    ]
