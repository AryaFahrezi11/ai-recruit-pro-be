from sqlalchemy.ext.asyncio import AsyncSession
import json
from app.models.audit import AuditLog

async def log_audit(db: AsyncSession, action: str, user_id: str = None, user_name: str = None, details: dict = None, ip_address: str = None):
    try:
        details_str = json.dumps(details) if details else None
        new_log = AuditLog(
            action=action,
            user_id=user_id,
            user_name=user_name,
            details=details_str,
            ip_address=ip_address
        )
        db.add(new_log)
        await db.commit()
    except Exception as e:
        print(f"Failed to write audit log: {e}")
        await db.rollback()
