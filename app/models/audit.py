from sqlalchemy import Column, String, DateTime, Integer, Text
from sqlalchemy.sql import func
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    action = Column(String(100), index=True)
    user_id = Column(String(36), nullable=True, index=True)
    user_name = Column(String(255), nullable=True)
    details = Column(Text, nullable=True) # store JSON as text
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
