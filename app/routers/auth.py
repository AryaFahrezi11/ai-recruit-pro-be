"""
🛣️ Auth Router
Endpoint: POST /api/auth/register, POST /api/auth/login
"""
from fastapi import APIRouter, HTTPException, status
from app.schemas.user import RegisterRequest, LoginRequest, TokenResponse

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    """
    Mendaftarkan user baru (pelamar/perusahaan/kampus).
    """
    # TODO: Implementasi dengan database
    # 1. Cek apakah email sudah terdaftar
    # 2. Hash password
    # 3. Simpan user ke database
    # 4. Buat JWT token
    return {
        "access_token": "token-placeholder",
        "token_type": "bearer",
        "role": req.role,
        "user_id": "user-id-placeholder"
    }


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """
    Login user dan dapatkan JWT token.
    """
    # TODO: Implementasi dengan database
    # 1. Cari user berdasarkan email
    # 2. Verifikasi password
    # 3. Buat JWT token
    return {
        "access_token": "token-placeholder",
        "token_type": "bearer",
        "role": "pelamar",
        "user_id": "user-id-placeholder"
    }
