import logging
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.events.producer import emit_listing_event
from app.services import listing_service
from shared.schemas.property import PropertyCreate, PropertyResponse, PropertyUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/listings", tags=["listings"])


class StatusUpdate(BaseModel):
    status: str


class PaginatedResponse(BaseModel):
    items: list[PropertyResponse]
    total: int
    page: int
    limit: int


def _get_producer(request: Request):
    """Return the Kafka producer from app state (may be None)."""
    return getattr(request.app.state, "kafka_producer", None)


@router.post("", response_model=PropertyResponse, status_code=201)
async def create_listing(
    data: PropertyCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Create a new property listing."""
    listing = await listing_service.create_listing(db, data)

    producer = _get_producer(request)
    if producer:
        await emit_listing_event(
            producer,
            event_type="listing.created",
            payload=PropertyResponse.model_validate(listing).model_dump(mode="json"),
            key=str(listing.id),
        )

    return listing


@router.get("", response_model=PaginatedResponse)
async def list_listings(
    status: str | None = Query(None),
    city: str | None = Query(None),
    zip_code: str | None = Query(None),
    min_price: Decimal | None = Query(None, ge=0),
    max_price: Decimal | None = Query(None, ge=0),
    bedrooms: int | None = Query(None, ge=0),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List and search property listings with optional filters."""
    items, total = await listing_service.list_listings(
        db,
        status=status,
        city=city,
        zip_code=zip_code,
        min_price=min_price,
        max_price=max_price,
        bedrooms=bedrooms,
        page=page,
        limit=limit,
    )
    return PaginatedResponse(
        items=[PropertyResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{listing_id}", response_model=PropertyResponse)
async def get_listing(
    listing_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single listing by ID."""
    listing = await listing_service.get_listing(db, listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@router.put("/{listing_id}", response_model=PropertyResponse)
async def update_listing(
    listing_id: UUID,
    data: PropertyUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Update an existing listing."""
    listing = await listing_service.update_listing(db, listing_id, data)
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")

    producer = _get_producer(request)
    if producer:
        await emit_listing_event(
            producer,
            event_type="listing.updated",
            payload=PropertyResponse.model_validate(listing).model_dump(mode="json"),
            key=str(listing.id),
        )

    return listing


@router.patch("/{listing_id}/status", response_model=PropertyResponse)
async def update_listing_status(
    listing_id: UUID,
    body: StatusUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Update the status of a listing (with transition validation)."""
    try:
        listing = await listing_service.update_status(db, listing_id, body.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")

    producer = _get_producer(request)
    if producer:
        await emit_listing_event(
            producer,
            event_type="listing.status_changed",
            payload={
                "listing_id": str(listing.id),
                "new_status": listing.status,
            },
            key=str(listing.id),
        )

    return listing


@router.delete("/{listing_id}", status_code=204)
async def delete_listing(
    listing_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a listing (sets status to withdrawn)."""
    deleted = await listing_service.delete_listing(db, listing_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Listing not found")
    return None
