"""
📋 Schemas untuk Auth & User
"""
import re
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime


# ============================================
# AUTH
# ============================================
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: str  # pelamar | perusahaan | kampus

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Kata sandi minimal 8 karakter")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Kata sandi harus mengandung minimal satu huruf kapital")
        if not re.search(r"[a-z]", v):
            raise ValueError("Kata sandi harus mengandung minimal satu huruf kecil")
        if not re.search(r"\d", v):
            raise ValueError("Kata sandi harus mengandung minimal satu angka")
        if not re.search(r"[@$!%*?&#^_\-]", v):
            raise ValueError("Kata sandi harus mengandung minimal satu karakter spesial (@$!%*?&#^_-)")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "pelamar@example.com",
                "password": "password123",
                "role": "pelamar"
            }
        }
class RegisterResponse(BaseModel):
    status: str
    message: str

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp_code: str

class ResendOTPRequest(BaseModel):
    email: EmailStr
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str
    has_completed_profile: bool = True
    is_verified: bool = True


# ============================================
# USER PROFILE
# ============================================
class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    is_active: bool
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class PelamarProfileUpdate(BaseModel):
    nama_lengkap: str | None = None
    no_telepon: str | None = None
    tanggal_lahir: str | None = None
    jenis_kelamin: str | None = None
    alamat: str | None = None
    kota: str | None = None
    provinsi: str | None = None
    pendidikan_terakhir: str | None = None
    institusi_pendidikan: str | None = None
    jurusan: str | None = None
    tahun_lulus: int | None = None
    ipk: float | None = None
    ringkasan_diri: str | None = None
    linkedin_url: str | None = None
    portfolio_url: str | None = None
    judul_posisi: str | None = None
    keahlian: str | None = None
    sertifikasi: str | None = None
    pengalaman_kerja: str | None = None
    riwayat_pendidikan: str | None = None


class PerusahaanProfileUpdate(BaseModel):
    nama_perusahaan: str | None = None
    industri: str | None = None
    ukuran: str | None = None
    deskripsi: str | None = None
    alamat: str | None = None
    kota: str | None = None
    provinsi: str | None = None
    website_url: str | None = None
    no_telepon: str | None = None
    tahun_berdiri: int | None = None
