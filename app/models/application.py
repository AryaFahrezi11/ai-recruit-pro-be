from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.models.video_task import VideoAnalysisJob
from app.core.database import Base


class CVDocument(Base):
    __tablename__ = "cv_documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    pelamar_id = Column(String, ForeignKey("pelamar_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    nama_file = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_type = Column(String(10), nullable=False)
    file_size_kb = Column(Integer)
    extracted_text = Column(Text)
    cleaned_text = Column(Text)
    # JSON disimpan sbg Text untuk kompatibilitas SQLite
    embedding_vector = Column(Text)
    
    # Hasil Ekstraksi Parser & OCR
    email = Column(String(255))
    phone = Column(String(50))
    pendidikan_tertinggi = Column(String(50))
    is_ocr_used = Column(Boolean, default=False)
    
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    pelamar = relationship("PelamarProfile", back_populates="cv_documents")
    applications = relationship("Application", back_populates="cv_document")


class Application(Base):
    __tablename__ = "applications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    pelamar_id = Column(String, ForeignKey("pelamar_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String, ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False, index=True)
    cv_document_id = Column(String, ForeignKey("cv_documents.id", ondelete="RESTRICT"), nullable=False)
    status = Column(String(20), default="dikirim", index=True)
    catatan_pelamar = Column(Text)
    video_url = Column(String(500), nullable=True)
    ai_result = Column(JSONB, nullable=True)
    catatan_perusahaan = Column(Text, nullable=True)
    interview_details = Column(JSONB, nullable=True)
    applied_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    pelamar = relationship("PelamarProfile", back_populates="applications")
    job = relationship("JobPosting", back_populates="applications")
    cv_document = relationship("CVDocument", back_populates="applications")
    cv_analysis = relationship("CVAnalysisResult", back_populates="application", uselist=False, cascade="all, delete-orphan")
    video_job = relationship("VideoAnalysisJob", back_populates="application", uselist=False, cascade="all, delete-orphan")
