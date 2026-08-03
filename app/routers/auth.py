"""
🛣️ Auth Router
Endpoint: POST /api/auth/register, POST /api/auth/login
"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.user import RegisterRequest, LoginRequest, TokenResponse
from app.core.database import get_db
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Mendaftarkan user baru (pelamar/perusahaan/kampus).
    """
    auth_service = AuthService(db)
    return await auth_service.register(email=req.email, password=req.password, role=req.role)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login user dan dapatkan JWT token.
    """
    auth_service = AuthService(db)
    return await auth_service.login(email=req.email, password=req.password)
