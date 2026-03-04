from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PropertyCreate(BaseModel):
    mls_number: str | None = None
    property_type: str = Field(..., pattern="^(single_family|condo|townhouse|multi_family|land)$")
    address_line1: str
    address_line2: str | None = None
    city: str
    state: str = Field(..., min_length=2, max_length=2)
    zip_code: str
    county: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    list_price: Decimal
    bedrooms: int | None = None
    bathrooms: Decimal | None = None
    square_feet: int | None = None
    lot_size_sqft: int | None = None
    year_built: int | None = None
    description: str | None = None
    listing_date: date | None = None
    expiration_date: date | None = None
    listing_agent_id: UUID | None = None


class PropertyUpdate(BaseModel):
    mls_number: str | None = None
    property_type: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    county: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    list_price: Decimal | None = None
    bedrooms: int | None = None
    bathrooms: Decimal | None = None
    square_feet: int | None = None
    lot_size_sqft: int | None = None
    year_built: int | None = None
    description: str | None = None
    listing_date: date | None = None
    expiration_date: date | None = None
    listing_agent_id: UUID | None = None


class PropertyResponse(BaseModel):
    id: UUID
    mls_number: str | None = None
    status: str
    property_type: str
    address_line1: str
    address_line2: str | None = None
    city: str
    state: str
    zip_code: str
    county: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    list_price: Decimal
    bedrooms: int | None = None
    bathrooms: Decimal | None = None
    square_feet: int | None = None
    lot_size_sqft: int | None = None
    year_built: int | None = None
    description: str | None = None
    listing_date: date | None = None
    expiration_date: date | None = None
    listing_agent_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PropertyPhotoResponse(BaseModel):
    id: UUID
    property_id: UUID
    url: str
    caption: str | None = None
    sort_order: int
    created_at: datetime

    model_config = {"from_attributes": True}
