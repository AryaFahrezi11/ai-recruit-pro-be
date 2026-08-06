"""
🛣️ Jobs Router
Endpoint: CRUD /api/jobs
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import verify_token
from app.schemas.job import JobPostingCreate, JobPostingResponse
from app.services.job_service import JobService
from typing import List

router = APIRouter()

async def get_current_user(current_user: dict = Depends(verify_token)):
    return current_user

@router.get("/categories")
async def get_job_categories(db: AsyncSession = Depends(get_db)):
    """Mendapatkan daftar semua kategori lowongan kerja."""
    service = JobService(db)
    return await service.get_categories()

@router.get("/my-jobs", response_model=List[JobPostingResponse])
async def get_my_jobs(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Mendapatkan daftar semua lowongan milik perusahaan yang sedang login."""
    service = JobService(db)
    return await service.get_my_jobs(current_user["sub"])

@router.put("/{job_id}", response_model=JobPostingResponse)
async def update_job(job_id: str, job_data: JobPostingCreate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Mengupdate data lowongan kerja."""
    service = JobService(db)
    return await service.update_job(current_user["sub"], job_id, job_data)

@router.get("/")
async def get_jobs():
    """Mendapatkan daftar semua lowongan kerja yang aktif."""
    # TODO: Implementasi dengan database
    return {"message": "Daftar lowongan kerja", "data": []}

@router.get("/{job_id}", response_model=JobPostingResponse)
async def get_job(job_id: str, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Mendapatkan detail satu lowongan kerja."""
    service = JobService(db)
    return await service.get_job_by_id(current_user["sub"], job_id)

@router.post("/", response_model=JobPostingResponse)
async def create_job(job_data: JobPostingCreate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Membuat lowongan kerja baru (hanya perusahaan)."""
    service = JobService(db)
    return await service.create_job(current_user["sub"], job_data)

class StatusUpdate(BaseModel):
    status: str

@router.patch("/{job_id}/status", response_model=JobPostingResponse)
async def update_job_status(job_id: str, body: StatusUpdate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Mengubah status lowongan (draft/active/closed)."""
    if body.status not in ("draft", "active", "closed"):
        raise HTTPException(status_code=400, detail="Status tidak valid. Gunakan: draft, active, atau closed.")
    service = JobService(db)
    return await service.update_job_status(current_user["sub"], job_id, body.status)

@router.delete("/{job_id}")
async def delete_job(job_id: str, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Menghapus lowongan kerja."""
    service = JobService(db)
    return await service.delete_job(current_user["sub"], job_id)
