from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class CVAnalysisResult(Base):
    __tablename__ = "cv_analysis_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    cv_document_id = Column(String, ForeignKey("cv_documents.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(String, ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False, index=True)
    cosine_similarity_score = Column(Numeric(8, 6), nullable=False)
    skor_kecocokan = Column(Numeric(5, 2), nullable=False)
    threshold_digunakan = Column(Numeric(5, 2), nullable=False)
    kategori = Column(String(20), nullable=False)
    hasil = Column(String(10), nullable=False, index=True)
    model_ai = Column(String(100), default="paraphrase-multilingual-MiniLM-L12-v2")
    waktu_proses_ms = Column(Integer)
    # JSON kompatibel SQLite
    detail_analisis = Column(Text)
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    application = relationship("Application", back_populates="cv_analysis")
