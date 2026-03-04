import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.contact import Contact, ContactTag, Interaction
from shared.schemas.contact import ContactCreate, ContactUpdate, InteractionCreate

logger = logging.getLogger(__name__)

VALID_PIPELINE_STAGES = ["new", "contacted", "qualified", "proposal", "negotiation", "closed_won", "closed_lost"]

STAGE_TRANSITIONS: dict[str, list[str]] = {
    "new": ["contacted", "closed_lost"],
    "contacted": ["qualified", "closed_lost"],
    "qualified": ["proposal", "closed_lost"],
    "proposal": ["negotiation", "closed_lost"],
    "negotiation": ["closed_won", "closed_lost"],
    "closed_won": [],
    "closed_lost": ["new"],
}


async def create_contact(db: AsyncSession, data: ContactCreate) -> Contact:
    contact = Contact(
        contact_type=data.contact_type,
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        phone=data.phone,
        company=data.company,
        address=data.address,
        pipeline_stage=data.pipeline_stage,
        lead_source=data.lead_source,
        notes=data.notes,
        preferences=data.preferences,
    )
    db.add(contact)
    await db.flush()
    await db.refresh(contact)
    return contact


async def get_contact(db: AsyncSession, contact_id: UUID) -> Contact | None:
    stmt = (
        select(Contact)
        .where(Contact.id == contact_id)
        .options(selectinload(Contact.tags))
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_contacts(
    db: AsyncSession,
    contact_type: str | None = None,
    pipeline_stage: str | None = None,
    tag: str | None = None,
    q: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[Contact], int]:
    stmt = select(Contact).options(selectinload(Contact.tags))
    count_stmt = select(func.count(Contact.id))

    if contact_type:
        stmt = stmt.where(Contact.contact_type == contact_type)
        count_stmt = count_stmt.where(Contact.contact_type == contact_type)

    if pipeline_stage:
        stmt = stmt.where(Contact.pipeline_stage == pipeline_stage)
        count_stmt = count_stmt.where(Contact.pipeline_stage == pipeline_stage)

    if tag:
        stmt = stmt.join(ContactTag).where(ContactTag.tag == tag)
        count_stmt = count_stmt.join(ContactTag).where(ContactTag.tag == tag)

    if q:
        search = f"%{q}%"
        search_filter = (
            Contact.first_name.ilike(search)
            | Contact.last_name.ilike(search)
            | Contact.email.ilike(search)
        )
        stmt = stmt.where(search_filter)
        count_stmt = count_stmt.where(search_filter)

    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    offset = (page - 1) * limit
    stmt = stmt.order_by(Contact.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    contacts = list(result.scalars().unique().all())

    return contacts, total


async def update_contact(
    db: AsyncSession, contact_id: UUID, data: ContactUpdate
) -> Contact | None:
    contact = await get_contact(db, contact_id)
    if not contact:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contact, field, value)

    await db.flush()
    await db.refresh(contact)
    return contact


async def update_pipeline(
    db: AsyncSession, contact_id: UUID, new_stage: str
) -> Contact | None:
    contact = await get_contact(db, contact_id)
    if not contact:
        return None

    if new_stage not in VALID_PIPELINE_STAGES:
        raise ValueError(f"Invalid pipeline stage: {new_stage}")

    allowed = STAGE_TRANSITIONS.get(contact.pipeline_stage, [])
    if new_stage not in allowed:
        raise ValueError(
            f"Cannot transition from '{contact.pipeline_stage}' to '{new_stage}'. "
            f"Allowed transitions: {allowed}"
        )

    contact.pipeline_stage = new_stage
    await db.flush()
    await db.refresh(contact)
    return contact


async def delete_contact(db: AsyncSession, contact_id: UUID) -> bool:
    contact = await get_contact(db, contact_id)
    if not contact:
        return False

    await db.delete(contact)
    await db.flush()
    return True


async def add_interaction(
    db: AsyncSession, contact_id: UUID, data: InteractionCreate
) -> Interaction:
    interaction = Interaction(
        contact_id=contact_id,
        type=data.type,
        direction=data.direction,
        subject=data.subject,
        body=data.body,
        created_by=data.created_by,
        metadata_=data.metadata,
    )
    db.add(interaction)
    await db.flush()
    await db.refresh(interaction)
    return interaction


async def list_interactions(
    db: AsyncSession, contact_id: UUID, limit: int = 50
) -> list[Interaction]:
    stmt = (
        select(Interaction)
        .where(Interaction.contact_id == contact_id)
        .order_by(Interaction.occurred_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def add_tag(db: AsyncSession, contact_id: UUID, tag: str) -> bool:
    existing = await db.execute(
        select(ContactTag).where(
            ContactTag.contact_id == contact_id, ContactTag.tag == tag
        )
    )
    if existing.scalar_one_or_none():
        return False

    contact_tag = ContactTag(contact_id=contact_id, tag=tag)
    db.add(contact_tag)
    await db.flush()
    return True


async def get_tags(db: AsyncSession, contact_id: UUID) -> list[str]:
    stmt = (
        select(ContactTag.tag)
        .where(ContactTag.contact_id == contact_id)
        .order_by(ContactTag.tag)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
