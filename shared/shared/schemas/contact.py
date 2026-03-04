from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ContactCreate(BaseModel):
    contact_type: str = Field(..., pattern="^(buyer|seller|agent|vendor|lead)$")
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    address: str | None = None
    pipeline_stage: str = "new"
    lead_source: str | None = None
    notes: str | None = None
    preferences: dict | None = None


class ContactUpdate(BaseModel):
    contact_type: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    address: str | None = None
    pipeline_stage: str | None = None
    lead_source: str | None = None
    notes: str | None = None
    preferences: dict | None = None


class ContactResponse(BaseModel):
    id: UUID
    contact_type: str
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    address: str | None = None
    pipeline_stage: str
    lead_source: str | None = None
    notes: str | None = None
    preferences: dict | None = None
    tags: list[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InteractionCreate(BaseModel):
    type: str = Field(..., pattern="^(call|email|showing|note|meeting|text)$")
    direction: str | None = Field(None, pattern="^(inbound|outbound)$")
    subject: str | None = None
    body: str | None = None
    created_by: str | None = None
    metadata: dict | None = None


class InteractionResponse(BaseModel):
    id: UUID
    contact_id: UUID
    type: str
    direction: str | None = None
    subject: str | None = None
    body: str | None = None
    occurred_at: datetime
    created_by: str | None = None
    # Use validation_alias to read from ORM attr `metadata_` (avoids clash
    # with SQLAlchemy's built-in `MetaData` that lives on every ORM class)
    metadata: dict | None = Field(None, validation_alias="metadata_")

    model_config = {"from_attributes": True, "populate_by_name": True}
