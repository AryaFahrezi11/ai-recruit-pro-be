"""
🛣️ Auth Router
Endpoint: POST /api/auth/register, POST /api/auth/login
"""
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import RegisterRequest, LoginRequest, TokenResponse, RegisterResponse, VerifyOTPRequest
from app.core.database import get_db
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=RegisterResponse)
async def register(req: RegisterRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Mendaftarkan user baru (pelamar/perusahaan/kampus) dan mengirimkan OTP.
    """
    auth_service = AuthService(db)
    return await auth_service.register(email=req.email, password=req.password, role=req.role, background_tasks=background_tasks)


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(req: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    """
    Memverifikasi OTP dan mengembalikan token JWT.
    """
    auth_service = AuthService(db)
    return await auth_service.verify_otp(email=req.email, otp_code=req.otp_code)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login user dan dapatkan JWT token.
    """
    auth_service = AuthService(db)
    return await auth_service.login(email=req.email, password=req.password, expected_role=req.role)
