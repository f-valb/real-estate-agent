import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Index, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.database.base import Base


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    mls_number: Mapped[str | None] = mapped_column(String, nullable=True)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    city: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=False)
    zip_code: Mapped[str] = mapped_column(String, nullable=False, index=True)
    property_type: Mapped[str | None] = mapped_column(String, nullable=True)
    sale_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    list_price: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    bedrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bathrooms: Mapped[float | None] = mapped_column(Numeric(4, 1), nullable=True)
    square_feet: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lot_size_sqft: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year_built: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sale_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    days_on_market: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    __table_args__ = (
        Index("ix_sales_city", "city"),
        Index("ix_sales_property_type", "property_type"),
    )


class MarketStats(Base):
    __tablename__ = "market_stats"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    zip_code: Mapped[str] = mapped_column(String, nullable=False, index=True)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    median_price: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    avg_price: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    avg_price_sqft: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    median_dom: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_sales: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active_listings: Mapped[int | None] = mapped_column(Integer, nullable=True)
    months_supply: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("zip_code", "period_start", "period_end", name="uq_market_stats_zip_period"),
    )
