"""
🔐 Auth Router
Endpoint: POST /api/auth/register, POST /api/auth/verify-otp, POST /api/auth/resend-otp, POST /api/auth/login
"""
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import (
    RegisterRequest, LoginRequest, TokenResponse, RegisterResponse,
    VerifyOTPRequest, ResendOTPRequest, ForgotPasswordRequest,
    VerifyResetOTPRequest, ResetPasswordRequest
)
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


@router.get("/check-email")
async def check_email(email: str, db: AsyncSession = Depends(get_db)):
    """
    Mengecek apakah email sudah terdaftar di sistem.
    """
    from sqlalchemy import select
    from app.models.user import User
    result = await db.execute(select(User).where(User.email == email.strip().lower()))
    user = result.scalars().first()
    return {
        "exists": user is not None,
        "is_active": user.is_active if user else False,
        "role": user.role if user else None
    }


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(req: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    """
    Memverifikasi OTP dan mengembalikan token JWT.
    """
    auth_service = AuthService(db)
    return await auth_service.verify_otp(email=req.email, otp_code=req.otp_code)


@router.post("/resend-otp", response_model=RegisterResponse)
async def resend_otp(req: ResendOTPRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Kirim ulang kode OTP untuk user yang belum aktif.
    """
    auth_service = AuthService(db)
    return await auth_service.resend_otp(email=req.email, background_tasks=background_tasks)


@router.post("/forgot-password", response_model=RegisterResponse)
async def forgot_password(req: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Mengirimkan kode OTP untuk reset password.
    """
    auth_service = AuthService(db)
    return await auth_service.forgot_password(email=req.email, background_tasks=background_tasks)


@router.post("/verify-reset-otp", response_model=RegisterResponse)
async def verify_reset_otp(req: VerifyResetOTPRequest, db: AsyncSession = Depends(get_db)):
    """
    Memverifikasi validitas kode OTP reset password.
    """
    auth_service = AuthService(db)
    return await auth_service.verify_reset_otp(email=req.email, otp_code=req.otp_code)


@router.post("/reset-password", response_model=RegisterResponse)
async def reset_password(req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Mereset password user dengan memasukkan OTP dan kata sandi baru.
    """
    auth_service = AuthService(db)
    return await auth_service.reset_password(email=req.email, otp_code=req.otp_code, new_password=req.new_password)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login user dan dapatkan JWT token (wajib is_active == True).
    """
    auth_service = AuthService(db)
    return await auth_service.login(email=req.email, password=req.password, expected_role=req.role)
