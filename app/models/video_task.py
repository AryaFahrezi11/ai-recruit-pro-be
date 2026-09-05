from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class VideoAnalysisJob(Base):
    __tablename__ = "video_analysis_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    status = Column(String(30), default="queued", index=True)  # queued, downloading, processing_frames, transcribing, summarizing, completed, failed
    progress = Column(Integer, default=0)  # 0 to 100
    current_step = Column(String(255), default="Menunggu antrean...")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    application = relationship("Application", back_populates="video_job")