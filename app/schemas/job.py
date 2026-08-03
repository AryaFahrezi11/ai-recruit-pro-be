"""
📋 Schemas untuk Job Postings
"""
from pydantic import BaseModel
from datetime import date, datetime


class JobPostingCreate(BaseModel):
    judul_posisi: str
    deskripsi_pekerjaan: str
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


class JobPostingResponse(BaseModel):
    id: str
    judul_posisi: str
    deskripsi_pekerjaan: str
    tipe_pekerjaan: str
    lokasi_kerja: str
    kota: str | None = None
    status: str
    cv_threshold: float
    created_at: datetime | None = None

    class Config:
        from_attributes = True
