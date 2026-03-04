import logging
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.events.producer import emit_market_event
from app.services import market_service
from shared.schemas.market import MarketStatsResponse, SaleCreate, SaleResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/market", tags=["market"])


class PaginatedSales(BaseModel):
    items: list[SaleResponse]
    total: int
    page: int
    limit: int


@router.post("/sales", response_model=SaleResponse, status_code=201)
async def record_sale(
    data: SaleCreate,
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    sale = await market_service.record_sale(db, data)

    producer = getattr(request.app.state, "kafka_producer", None)
    if producer:
        await emit_market_event(
            producer,
            event_type="market.sale_recorded",
            payload=SaleResponse.model_validate(sale).model_dump(mode="json"),
            key=sale.zip_code,
        )

    return sale


@router.get("/sales", response_model=PaginatedSales)
async def list_sales(
    city: str | None = Query(None),
    zip_code: str | None = Query(None),
    min_date: date | None = Query(None),
    max_date: date | None = Query(None),
    property_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
):
    items, total = await market_service.list_sales(
        db,
        city=city,
        zip_code=zip_code,
        min_date=min_date,
        max_date=max_date,
        property_type=property_type,
        page=page,
        limit=limit,
    )
    return PaginatedSales(
        items=[SaleResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/comps", response_model=list[SaleResponse])
async def get_comps(
    zip_code: str = Query(...),
    bedrooms: int | None = Query(None),
    sqft_min: int | None = Query(None),
    sqft_max: int | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_session),
):
    comps = await market_service.get_comps(
        db, zip_code=zip_code, bedrooms=bedrooms,
        sqft_min=sqft_min, sqft_max=sqft_max, limit=limit,
    )
    return [SaleResponse.model_validate(c) for c in comps]


@router.get("/stats/{zip_code}", response_model=MarketStatsResponse | None)
async def get_market_stats(
    zip_code: str,
    db: AsyncSession = Depends(get_session),
):
    stats = await market_service.get_market_stats(db, zip_code)
    if stats is None:
        stats = await market_service.compute_market_stats(db, zip_code)
    return stats


@router.post("/stats/{zip_code}/compute", response_model=MarketStatsResponse)
async def compute_market_stats(
    zip_code: str,
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    stats = await market_service.compute_market_stats(db, zip_code)

    producer = getattr(request.app.state, "kafka_producer", None)
    if producer:
        await emit_market_event(
            producer,
            event_type="market.stats_updated",
            payload=MarketStatsResponse.model_validate(stats).model_dump(mode="json"),
            key=zip_code,
        )

    return stats


@router.get("/trends/{zip_code}")
async def get_price_trends(
    zip_code: str,
    months: int = Query(12, ge=1, le=60),
    db: AsyncSession = Depends(get_session),
):
    return await market_service.get_price_trends(db, zip_code, months=months)
