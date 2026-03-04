import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.events.producer import emit_contact_event
from app.services import contact_service
from shared.schemas.contact import (
    ContactCreate,
    ContactResponse,
    ContactUpdate,
    InteractionCreate,
    InteractionResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/contacts", tags=["contacts"])


class PipelineUpdate(BaseModel):
    stage: str


class TagBody(BaseModel):
    tag: str


class PaginatedContacts(BaseModel):
    items: list[ContactResponse]
    total: int
    page: int
    limit: int


def _contact_to_response(contact) -> ContactResponse:
    return ContactResponse(
        id=contact.id,
        contact_type=contact.contact_type,
        first_name=contact.first_name,
        last_name=contact.last_name,
        email=contact.email,
        phone=contact.phone,
        company=contact.company,
        address=contact.address,
        pipeline_stage=contact.pipeline_stage,
        lead_source=contact.lead_source,
        notes=contact.notes,
        preferences=contact.preferences,
        tags=[ct.tag for ct in contact.tags] if contact.tags else [],
        created_at=contact.created_at,
        updated_at=contact.updated_at,
    )


@router.post("", status_code=201, response_model=ContactResponse)
async def create_contact(
    data: ContactCreate,
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    contact = await contact_service.create_contact(db, data)
    # Reload with tags
    contact = await contact_service.get_contact(db, contact.id)

    producer = getattr(request.app.state, "kafka_producer", None)
    if producer:
        await emit_contact_event(
            producer,
            event_type="contact.created",
            payload=ContactResponse.model_validate(contact).model_dump(mode="json"),
            key=str(contact.id),
        )

    return _contact_to_response(contact)


@router.get("", response_model=PaginatedContacts)
async def list_contacts(
    contact_type: str | None = Query(None),
    pipeline_stage: str | None = Query(None),
    tag: str | None = Query(None),
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
):
    contacts, total = await contact_service.list_contacts(
        db,
        contact_type=contact_type,
        pipeline_stage=pipeline_stage,
        tag=tag,
        q=q,
        page=page,
        limit=limit,
    )
    return PaginatedContacts(
        items=[_contact_to_response(c) for c in contacts],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: UUID,
    db: AsyncSession = Depends(get_session),
):
    contact = await contact_service.get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return _contact_to_response(contact)


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: UUID,
    data: ContactUpdate,
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    contact = await contact_service.update_contact(db, contact_id, data)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    response = _contact_to_response(contact)

    producer = getattr(request.app.state, "kafka_producer", None)
    if producer:
        await emit_contact_event(
            producer,
            event_type="contact.updated",
            payload=response.model_dump(mode="json"),
            key=str(contact.id),
        )

    return response


@router.delete("/{contact_id}", status_code=204)
async def delete_contact(
    contact_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    deleted = await contact_service.delete_contact(db, contact_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Contact not found")

    producer = getattr(request.app.state, "kafka_producer", None)
    if producer:
        await emit_contact_event(
            producer,
            event_type="contact.deleted",
            payload={"contact_id": str(contact_id)},
            key=str(contact_id),
        )


@router.patch("/{contact_id}/pipeline", response_model=ContactResponse)
async def update_pipeline(
    contact_id: UUID,
    body: PipelineUpdate,
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    try:
        contact = await contact_service.update_pipeline(db, contact_id, body.stage)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    response = _contact_to_response(contact)

    producer = getattr(request.app.state, "kafka_producer", None)
    if producer:
        await emit_contact_event(
            producer,
            event_type="contact.pipeline_changed",
            payload=response.model_dump(mode="json"),
            key=str(contact.id),
        )

    return response


@router.get("/{contact_id}/interactions", response_model=list[InteractionResponse])
async def list_interactions(
    contact_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_session),
):
    contact = await contact_service.get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    interactions = await contact_service.list_interactions(db, contact_id, limit=limit)
    return interactions


@router.post(
    "/{contact_id}/interactions",
    status_code=201,
    response_model=InteractionResponse,
)
async def add_interaction(
    contact_id: UUID,
    data: InteractionCreate,
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    contact = await contact_service.get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    interaction = await contact_service.add_interaction(db, contact_id, data)

    producer = getattr(request.app.state, "kafka_producer", None)
    if producer:
        await emit_contact_event(
            producer,
            event_type="interaction.logged",
            payload=InteractionResponse.model_validate(interaction).model_dump(mode="json"),
            key=str(contact_id),
        )

    return interaction


@router.get("/{contact_id}/tags", response_model=list[str])
async def get_tags(
    contact_id: UUID,
    db: AsyncSession = Depends(get_session),
):
    contact = await contact_service.get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    return await contact_service.get_tags(db, contact_id)


@router.post("/{contact_id}/tags", status_code=201, response_model=list[str])
async def add_tag(
    contact_id: UUID,
    body: TagBody,
    db: AsyncSession = Depends(get_session),
):
    contact = await contact_service.get_contact(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    await contact_service.add_tag(db, contact_id, body.tag)
    return await contact_service.get_tags(db, contact_id)
