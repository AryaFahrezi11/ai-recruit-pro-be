from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.sql import func
import uuid

from app.core.database import Base

class PlatformReview(Base):
    __tablename__ = "platform_reviews"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(255))
    role = Column(String(100))
    rating = Column(Integer, default=5)
    category = Column(String(100))
    comment = Column(Text)
    is_anonymous = Column(Boolean, default=False)
    context_event = Column(String(100), index=True)  # 'applied_job', 'uploaded_video', 'status_changed'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
