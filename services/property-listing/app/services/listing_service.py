from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.property import Property
from shared.schemas.property import PropertyCreate, PropertyUpdate

# Valid status transitions: {current_status: {allowed_next_statuses}}
_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"active"},
    "active": {"pending", "withdrawn"},
    "pending": {"sold", "active"},
}


async def create_listing(db: AsyncSession, data: PropertyCreate) -> Property:
    """Create a new property listing."""
    listing = Property(**data.model_dump())
    db.add(listing)
    await db.flush()
    await db.refresh(listing)
    return listing


async def get_listing(db: AsyncSession, listing_id: UUID) -> Property | None:
    """Retrieve a single property listing by ID."""
    result = await db.execute(select(Property).where(Property.id == listing_id))
    return result.scalar_one_or_none()


async def list_listings(
    db: AsyncSession,
    status: str | None = None,
    city: str | None = None,
    zip_code: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    bedrooms: int | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Property], int]:
    """List property listings with optional filtering and pagination.

    Returns a tuple of (items, total_count).
    """
    query = select(Property)
    count_query = select(func.count()).select_from(Property)

    # Apply filters
    if status is not None:
        query = query.where(Property.status == status)
        count_query = count_query.where(Property.status == status)
    if city is not None:
        query = query.where(Property.city.ilike(f"%{city}%"))
        count_query = count_query.where(Property.city.ilike(f"%{city}%"))
    if zip_code is not None:
        query = query.where(Property.zip_code == zip_code)
        count_query = count_query.where(Property.zip_code == zip_code)
    if min_price is not None:
        query = query.where(Property.list_price >= min_price)
        count_query = count_query.where(Property.list_price >= min_price)
    if max_price is not None:
        query = query.where(Property.list_price <= max_price)
        count_query = count_query.where(Property.list_price <= max_price)
    if bedrooms is not None:
        query = query.where(Property.bedrooms >= bedrooms)
        count_query = count_query.where(Property.bedrooms >= bedrooms)

    # Get total count
    total_result = await db.execute(count_query)
    total_count = total_result.scalar_one()

    # Apply ordering and pagination
    offset = (page - 1) * limit
    query = query.order_by(Property.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    items = list(result.scalars().all())

    return items, total_count


async def update_listing(
    db: AsyncSession, listing_id: UUID, data: PropertyUpdate
) -> Property | None:
    """Update an existing property listing."""
    listing = await get_listing(db, listing_id)
    if listing is None:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(listing, field, value)

    await db.flush()
    await db.refresh(listing)
    return listing


async def update_status(
    db: AsyncSession, listing_id: UUID, new_status: str
) -> Property | None:
    """Update the status of a listing with transition validation.

    Valid transitions:
        draft    -> active
        active   -> pending, withdrawn
        pending  -> sold, active

    Raises ValueError if the transition is not allowed.
    """
    listing = await get_listing(db, listing_id)
    if listing is None:
        return None

    current = listing.status
    allowed = _STATUS_TRANSITIONS.get(current, set())
    if new_status not in allowed:
        raise ValueError(
            f"Cannot transition from '{current}' to '{new_status}'. "
            f"Allowed transitions: {sorted(allowed) if allowed else 'none'}"
        )

    listing.status = new_status
    await db.flush()
    await db.refresh(listing)
    return listing


async def delete_listing(db: AsyncSession, listing_id: UUID) -> bool:
    """Soft-delete a listing by setting its status to 'withdrawn'."""
    listing = await get_listing(db, listing_id)
    if listing is None:
        return False

    listing.status = "withdrawn"
    await db.flush()
    return True
