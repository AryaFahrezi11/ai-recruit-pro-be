from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.database import get_db
from app.core.security import verify_token
from app.services.admin_service import AdminService
from pydantic import BaseModel
from app.schemas.admin import AdminUserCreateRequest, AdminUserUpdateRequest

router = APIRouter()

def verify_admin(current_user: dict = Depends(verify_token)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Akses ditolak, hanya untuk admin.")
    return current_user


@router.get("/users")
async def get_users(role: Optional[str] = None, current_user: dict = Depends(verify_admin), db: AsyncSession = Depends(get_db)):
    admin_service = AdminService(db)
    return await admin_service.get_all_users(role)

@router.post("/users")
async def create_user(req: AdminUserCreateRequest, current_user: dict = Depends(verify_admin), db: AsyncSession = Depends(get_db)):
    admin_service = AdminService(db)
    return await admin_service.create_user_manual(req)

@router.put("/users/{user_id}")
async def update_user(user_id: str, req: AdminUserUpdateRequest, current_user: dict = Depends(verify_admin), db: AsyncSession = Depends(get_db)):
    admin_service = AdminService(db)
    return await admin_service.update_user_manual(user_id, req)

@router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(verify_admin), db: AsyncSession = Depends(get_db)):
    admin_service = AdminService(db)
    return await admin_service.delete_user(user_id)

class BanRequest(BaseModel):
    is_banned: bool

@router.put("/users/{user_id}/ban")
async def ban_user(user_id: str, req: BanRequest, current_user: dict = Depends(verify_admin), db: AsyncSession = Depends(get_db)):
    admin_service = AdminService(db)
    return await admin_service.ban_user(user_id, req.is_banned)

@router.get("/perusahaan/pending")
async def get_pending_companies(current_user: dict = Depends(verify_admin), db: AsyncSession = Depends(get_db)):
    admin_service = AdminService(db)
    return await admin_service.get_pending_companies()

@router.put("/perusahaan/{company_id}/verify")
async def verify_company(company_id: str, current_user: dict = Depends(verify_admin), db: AsyncSession = Depends(get_db)):
    admin_service = AdminService(db)
    return await admin_service.verify_company(company_id)
