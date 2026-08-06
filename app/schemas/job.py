"""
📋 Schemas untuk Job Postings
"""
from pydantic import BaseModel
from datetime import date, datetime


class JobPostingCreate(BaseModel):
    judul_posisi: str
    deskripsi_pekerjaan: str
    kategori_id: str | None = None
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
