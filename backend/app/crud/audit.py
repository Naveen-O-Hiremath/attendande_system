import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def record(
    db: AsyncSession,
    *,
    actor_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: str | None,
    metadata: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            event_metadata=metadata,
        )
    )
