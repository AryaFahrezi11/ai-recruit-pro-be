"""
📋 Schemas untuk AI Analysis
"""
from pydantic import BaseModel
from datetime import datetime


# ============================================
# CV ANALYSIS
# ============================================
class CVAnalysisRequest(BaseModel):
    """Request untuk analisis CV langsung (teks)."""
    cv_text: str
    job_description: str
    threshold: float | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "cv_text": "Saya seorang Frontend Developer dengan 3 tahun pengalaman...",
                "job_description": "Kami mencari Frontend Developer yang menguasai React.js...",
                "threshold": 40.0
            }
        }


class CVAnalysisResponse(BaseModel):
    """Response hasil analisis CV."""
    cosine_similarity_score: float
    skor_kecocokan: float
    threshold_digunakan: float
    kategori: str
    hasil: str
    model_ai: str
    waktu_proses_ms: float

    class Config:
        json_schema_extra = {
            "example": {
                "cosine_similarity_score": 0.5823,
                "skor_kecocokan": 58.23,
                "threshold_digunakan": 40.0,
                "kategori": "cocok",
                "hasil": "lolos",
                "model_ai": "paraphrase-multilingual-MiniLM-L12-v2",
                "waktu_proses_ms": 35.2,
            }
        }


class CVUploadAnalysisResponse(BaseModel):
    """Response hasil analisis dari file CV yang diupload."""
    cosine_similarity_score: float
    skor_kecocokan: float
    threshold_digunakan: float
    kategori: str
    hasil: str
    model_ai: str
    waktu_proses_ms: float
    
    # Tambahan Data dari Parser & OCR
    is_ocr_used: bool
    email: str
    phone: str
    pendidikan_tertinggi: str
    
    extracted_text_preview: str
    jumlah_karakter: int
