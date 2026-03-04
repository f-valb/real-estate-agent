from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class SaleCreate(BaseModel):
    mls_number: str | None = None
    address: str | None = None
    city: str
    state: str
    zip_code: str
    property_type: str | None = None
    sale_price: Decimal
    list_price: Decimal | None = None
    bedrooms: int | None = None
    bathrooms: Decimal | None = None
    square_feet: int | None = None
    lot_size_sqft: int | None = None
    year_built: int | None = None
    sale_date: date
    days_on_market: int | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None


class SaleResponse(BaseModel):
    id: UUID
    mls_number: str | None = None
    address: str | None = None
    city: str
    state: str
    zip_code: str
    property_type: str | None = None
    sale_price: Decimal
    list_price: Decimal | None = None
    bedrooms: int | None = None
    bathrooms: Decimal | None = None
    square_feet: int | None = None
    lot_size_sqft: int | None = None
    year_built: int | None = None
    sale_date: date
    days_on_market: int | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MarketStatsResponse(BaseModel):
    id: UUID
    zip_code: str
    period_start: date
    period_end: date
    median_price: Decimal | None = None
    avg_price: Decimal | None = None
    avg_price_sqft: Decimal | None = None
    median_dom: int | None = None
    total_sales: int | None = None
    active_listings: int | None = None
    months_supply: Decimal | None = None
    computed_at: datetime

    model_config = {"from_attributes": True}


class CompRequest(BaseModel):
    zip_code: str
    bedrooms: int | None = None
    sqft_min: int | None = None
    sqft_max: int | None = None
    radius_miles: float = 5.0
    limit: int = 10
