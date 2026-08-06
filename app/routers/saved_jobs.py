"""
🛣️ Saved Jobs Router
Endpoint: GET /api/saved-jobs/, POST /api/saved-jobs/{job_id}, DELETE /api/saved-jobs/{job_id}
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import uuid

from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import PelamarProfile
from app.models.job import JobPosting, SavedJob

router = APIRouter()


@router.get("/")
async def get_saved_jobs(
    current_user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Mendapatkan daftar lowongan yang disimpan oleh pelamar yang sedang login.
    """
    user_id = current_user.get("sub")
    role = current_user.get("role")

    if role != "pelamar":
        return []

    # Get PelamarProfile
    res_p = await db.execute(select(PelamarProfile).where(PelamarProfile.user_id == user_id))
    profile = res_p.scalars().first()

    if not profile:
        return []

    # Fetch saved jobs
    result = await db.execute(
        select(SavedJob)
        .where(SavedJob.pelamar_id == profile.id)
        .order_by(SavedJob.created_at.desc())
    )
    saved_items = result.scalars().all()

    response = []
    for item in saved_items:
        # Check if job_id maps to real JobPosting
        res_j = await db.execute(
            select(JobPosting)
            .options(selectinload(JobPosting.perusahaan))
            .where(JobPosting.id == item.job_id)
        )
        job = res_j.scalars().first()

        if job:
            company = job.perusahaan
            response.append({
                "id": job.id,
                "saved_id": item.id,
                "title": job.judul_posisi,
                "company": company.nama_perusahaan if company else "Perusahaan",
                "logo": company.logo_url if company and company.logo_url else "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=120&auto=format&fit=crop&q=80",
                "location": f"{job.kota or 'Jakarta'}, DKI Jakarta",
                "education": job.pendidikan_min or "Minimal D3/S1",
                "workPolicy": f"{job.tipe_pekerjaan or 'Full time'} • {job.lokasi_kerja or 'WFO'}",
                "salary": f"Rp {int(job.gaji_min):,} - Rp {int(job.gaji_max):,}" if job.gaji_min and job.gaji_max else "Gaji Kompetitif",
                "postedAgo": "Terakhir diperbarui",
                "matchScore": 95,
                "descriptionBullets": [job.deskripsi_pekerjaan[:150] if job.deskripsi_pekerjaan else ""],
                "criteriaBullets": [job.kualifikasi[:150] if job.kualifikasi else ""],
                "savedAt": str(item.created_at.strftime("%d %B %Y")) if item.created_at else "Baru saja"
            })
        else:
            # Numeric ID or mock job ID
            try:
                numeric_id = int(item.job_id)
            except ValueError:
                numeric_id = item.job_id

            response.append({
                "id": numeric_id,
                "saved_id": item.id,
                "savedAt": str(item.created_at.strftime("%d %B %Y")) if item.created_at else "Baru saja"
            })

    return response


@router.post("/{job_id}")
async def save_job(
    job_id: str,
    current_user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Menyimpan lowongan ke daftar tersimpan pelamar.
    """
    user_id = current_user.get("sub")
    role = current_user.get("role")

    if role != "pelamar":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya pelamar yang dapat menyimpan lowongan pekerjaan",
        )

    # Get or create PelamarProfile
    res_p = await db.execute(select(PelamarProfile).where(PelamarProfile.user_id == user_id))
    profile = res_p.scalars().first()

    if not profile:
        profile = PelamarProfile(user_id=user_id, nama_lengkap="Pelamar")
        db.add(profile)
        await db.flush()

    # Check if already saved
    res_s = await db.execute(
        select(SavedJob).where(
            SavedJob.pelamar_id == profile.id,
            SavedJob.job_id == str(job_id)
        )
    )
    existing = res_s.scalars().first()
    if existing:
        return {"message": "Lowongan sudah ada di daftar tersimpan", "saved": True}

    new_saved = SavedJob(
        pelamar_id=profile.id,
        job_id=str(job_id)
    )
    db.add(new_saved)
    await db.commit()

    return {"message": "Lowongan berhasil disimpan", "saved": True}


@router.delete("/{job_id}")
async def remove_saved_job(
    job_id: str,
    current_user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Menghapus lowongan dari daftar tersimpan pelamar.
    """
    user_id = current_user.get("sub")
    role = current_user.get("role")

    if role != "pelamar":
        raise HTTPException(status_code=403, detail="Akses ditolak")

    res_p = await db.execute(select(PelamarProfile).where(PelamarProfile.user_id == user_id))
    profile = res_p.scalars().first()

    if not profile:
        return {"message": "Daftar tersimpan diperbarui", "saved": False}

    res_s = await db.execute(
        select(SavedJob).where(
            SavedJob.pelamar_id == profile.id,
            SavedJob.job_id == str(job_id)
        )
    )
    existing = res_s.scalars().first()
    if existing:
        await db.delete(existing)
        await db.commit()

    return {"message": "Lowongan berhasil dihapus dari daftar tersimpan", "saved": False}
