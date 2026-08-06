from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Date, Numeric, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class JobCategory(Base):
    __tablename__ = "job_categories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nama_kategori = Column(String(100), unique=True, nullable=False)
    deskripsi = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job_postings = relationship("JobPosting", back_populates="kategori")


class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    perusahaan_id = Column(String, ForeignKey("perusahaan_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    kategori_id = Column(String, ForeignKey("job_categories.id", ondelete="SET NULL"), index=True)
    judul_posisi = Column(String(255), nullable=False)
    deskripsi_pekerjaan = Column(Text, nullable=False)
    kualifikasi = Column(Text)
    tanggung_jawab = Column(Text)
    tipe_pekerjaan = Column(String(20), default="full_time", index=True)
    lokasi_kerja = Column(String(10), default="onsite")
    kota = Column(String(100))
    gaji_min = Column(Numeric(15, 2))
    gaji_max = Column(Numeric(15, 2))
    tampilkan_gaji = Column(Boolean, default=False)
    pengalaman_min_tahun = Column(Integer, default=0)
    pendidikan_min = Column(String(50))
    cv_threshold = Column(Numeric(5, 2), default=40.00)
    interview_threshold = Column(Numeric(5, 2), default=40.00)
    status = Column(String(10), default="draft", index=True)
    tanggal_buka = Column(Date)
    tanggal_tutup = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Untuk nyimpan embedding JSON dari SQLite/Postgres (pakai Text dulu agar kompatibel)
    jd_embedding = Column(Text) 

    # Relationships
    perusahaan = relationship("PerusahaanProfile", back_populates="job_postings")
    kategori = relationship("JobCategory", back_populates="job_postings")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")


class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    pelamar_id = Column(String, ForeignKey("pelamar_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    pelamar = relationship("PelamarProfile")
