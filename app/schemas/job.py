"""
📋 Schemas untuk Job Postings
"""
import json
from pydantic import BaseModel, field_validator
from datetime import date, datetime


class JobPostingCreate(BaseModel):
    judul_posisi: str
    deskripsi_pekerjaan: str
    kategori_id: str | None = None

    @field_validator("deskripsi_pekerjaan")
    @classmethod
    def validate_deskripsi(cls, v: str) -> str:
        if not v or len(v.strip()) < 150:
            raise ValueError(
                "Deskripsi pekerjaan minimal 150 karakter agar AI dapat membaca dan menganalisis kualifikasi secara optimal."
            )
        return v

    @field_validator("tanggung_jawab")
    @classmethod
    def validate_tanggung_jawab(cls, v: str | None) -> str | None:
        if v:
            try:
                items = json.loads(v) if isinstance(v, str) else v
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, str) and len(item.strip()) < 20:
                            raise ValueError("Setiap butir tanggung jawab minimal 20 karakter agar terbaca jelas oleh AI.")
            except (json.JSONDecodeError, TypeError):
                pass
        return v

    @field_validator("kualifikasi")
    @classmethod
    def validate_kualifikasi(cls, v: str | None) -> str | None:
        if v:
            try:
                items = json.loads(v) if isinstance(v, str) else v
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, str) and len(item.strip()) < 20:
                            raise ValueError("Setiap butir persyaratan/kualifikasi minimal 20 karakter agar terbaca jelas oleh AI.")
            except (json.JSONDecodeError, TypeError):
                pass
        return v

    @field_validator("video_questions_json")
    @classmethod
    def validate_video_questions(cls, v: str | None) -> str | None:
        if v:
            try:
                items = json.loads(v) if isinstance(v, str) else v
                if isinstance(items, list) and len(items) > 0:
                    if len(items) < 3:
                        raise ValueError(f"Pertanyaan wawancara minimal 3 pertanyaan (saat ini {len(items)}).")
                    for q in items:
                        if isinstance(q, str) and len(q.strip()) < 15:
                            raise ValueError("Setiap pertanyaan wawancara minimal 15 karakter agar pertanyaan jelas dijawab.")
            except (json.JSONDecodeError, TypeError):
                pass
        return v

    kualifikasi: str | None = None
    tanggung_jawab: str | None = None
    tipe_pekerjaan: str = "full_time"
    lokasi_kerja: str = "onsite"
    kota: str | None = None
    gaji_min: float | None = None
    gaji_max: float | None = None
    tampilkan_gaji: bool = False
    pengalaman_min_tahun: int = 0
    pendidikan_min: str | None = None
    cv_threshold: float = 40.0
    interview_threshold: float = 40.0
    tanggal_buka: date | None = None
    tanggal_tutup: date | None = None
    department: str | None = None
    experience_level: str | None = None
    benefits_json: str | None = None
    ai_keywords_json: str | None = None
    video_questions_json: str | None = None
    openings_count: int = 1
    status: str = "draft"


class JobPostingResponse(BaseModel):
    id: str
    judul_posisi: str
    deskripsi_pekerjaan: str
    kategori_id: str | None = None
    kualifikasi: str | None = None
    tanggung_jawab: str | None = None
    tipe_pekerjaan: str
    lokasi_kerja: str
    kota: str | None = None
    gaji_min: float | None = None
    gaji_max: float | None = None
    tampilkan_gaji: bool = False
    pengalaman_min_tahun: int = 0
    pendidikan_min: str | None = None
    cv_threshold: float = 40.0
    interview_threshold: float = 40.0
    tanggal_buka: date | None = None
    tanggal_tutup: date | None = None
    department: str | None = None
    experience_level: str | None = None
    benefits_json: str | None = None
    ai_keywords_json: str | None = None
    video_questions_json: str | None = None
    openings_count: int = 1
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
