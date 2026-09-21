import uuid
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.auth import AuditLog


async def log_action(
    db: AsyncSession,
    action: str,
    entity_type: str,
    user_id: Optional[uuid.UUID] = None,
    entity_id: Optional[str] = None,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
    )
    db.add(log_entry)
    await db.flush()
    return log_entry
