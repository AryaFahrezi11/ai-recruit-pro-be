"""
🛣️ Jobs Router
Endpoint: CRUD /api/jobs
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_jobs():
    """Mendapatkan daftar semua lowongan kerja yang aktif."""
    # TODO: Implementasi dengan database
    return {"message": "Daftar lowongan kerja", "data": []}


@router.get("/{job_id}")
async def get_job(job_id: str):
    """Mendapatkan detail satu lowongan kerja."""
    # TODO: Implementasi dengan database
    return {"message": f"Detail lowongan {job_id}"}


@router.post("/")
async def create_job():
    """Membuat lowongan kerja baru (hanya perusahaan)."""
    # TODO: Implementasi dengan database
    return {"message": "Lowongan berhasil dibuat (placeholder)"}


@router.put("/{job_id}")
async def update_job(job_id: str):
    """Mengupdate lowongan kerja."""
    # TODO: Implementasi dengan database
    return {"message": f"Lowongan {job_id} berhasil diupdate (placeholder)"}


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    """Menghapus/menutup lowongan kerja."""
    # TODO: Implementasi dengan database
    return {"message": f"Lowongan {job_id} berhasil dihapus (placeholder)"}
