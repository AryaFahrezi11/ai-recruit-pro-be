from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Date, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, index=True)  # pelamar, perusahaan, kampus, admin
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=False)
    email_verified_at = Column(DateTime(timezone=True))
    otp_code = Column(String(6), nullable=True)
    otp_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    pelamar_profile = relationship("PelamarProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    perusahaan_profile = relationship("PerusahaanProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    kampus_profile = relationship("KampusProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")


class PelamarProfile(Base):
    __tablename__ = "pelamar_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    nama_lengkap = Column(String(255), nullable=False)
    no_telepon = Column(String(20))
    tanggal_lahir = Column(Date)
    jenis_kelamin = Column(String(1))
    alamat = Column(Text)
    kota = Column(String(100))
    provinsi = Column(String(100))
    pendidikan_terakhir = Column(String(50))
    institusi_pendidikan = Column(String(255))
    jurusan = Column(String(255))
    tahun_lulus = Column(Integer)
    ipk = Column(Numeric(3, 2))
    ringkasan_diri = Column(Text)
    linkedin_url = Column(String(500))
    portfolio_url = Column(String(500))
    judul_posisi = Column(String(255))
    keahlian = Column(Text)
    sertifikasi = Column(Text)
    pengalaman_kerja = Column(Text)
    riwayat_pendidikan = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="pelamar_profile")
    cv_documents = relationship("CVDocument", back_populates="pelamar", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="pelamar", cascade="all, delete-orphan")


class PerusahaanProfile(Base):
    __tablename__ = "perusahaan_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    nama_perusahaan = Column(String(255), nullable=False)
    industri = Column(String(100))
    ukuran = Column(String(100))
    deskripsi = Column(Text)
    alamat = Column(Text)
    kota = Column(String(100))
    provinsi = Column(String(100))
    website_url = Column(String(500))
    logo_url = Column(String(500))
    no_telepon = Column(String(20))
    tahun_berdiri = Column(Integer)
    nib_number = Column(String(255))
    nib_document_url = Column(String(500))
    hr_name = Column(String(255))
    hr_whatsapp = Column(String(20))
    hr_position = Column(String(100))
    hr_id_card_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="perusahaan_profile")
    job_postings = relationship("JobPosting", back_populates="perusahaan", cascade="all, delete-orphan")


class KampusProfile(Base):
    __tablename__ = "kampus_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    nama_kampus = Column(String(255), nullable=False)
    jenis = Column(String(10))
    alamat = Column(Text)
    kota = Column(String(100))
    provinsi = Column(String(100))
    website_url = Column(String(500))
    logo_url = Column(String(500))
    akreditasi = Column(String(10))
    nama_pic = Column(String(255))
    jabatan_pic = Column(String(100))
    no_telepon_pic = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="kampus_profile")
