"""
🛣️ Jobs Router
Endpoint: CRUD /api/jobs
"""
import json
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import PerusahaanProfile
from app.models.job import JobPosting, JobCategory
from app.schemas.job import JobPostingCreate, JobPostingResponse

router = APIRouter()


@router.get("/")
async def get_jobs(
    db: AsyncSession = Depends(get_db),
    search: str = Query(default=None, description="Cari berdasarkan judul posisi atau kota"),
    tipe_pekerjaan: str = Query(default=None, description="Filter: full_time, part_time, contract, internship"),
    lokasi_kerja: str = Query(default=None, description="Filter: onsite, remote, hybrid"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """Mendapatkan daftar semua lowongan kerja yang aktif."""
    query = (
        select(JobPosting)
        .options(selectinload(JobPosting.perusahaan))
        .where(JobPosting.status == "aktif")
    )

    # Filter pencarian
    if search:
        query = query.where(
            or_(
                JobPosting.judul_posisi.ilike(f"%{search}%"),
                JobPosting.kota.ilike(f"%{search}%"),
            )
        )

    if tipe_pekerjaan:
        query = query.where(JobPosting.tipe_pekerjaan == tipe_pekerjaan)

    if lokasi_kerja:
        query = query.where(JobPosting.lokasi_kerja == lokasi_kerja)

    # Urutan terbaru dulu
    query = query.order_by(JobPosting.created_at.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    jobs = result.scalars().all()

    # Format response
    data = []
    for job in jobs:
        job_dict = {
            "id": job.id,
            "judul_posisi": job.judul_posisi,
            "deskripsi_pekerjaan": job.deskripsi_pekerjaan,
            "kualifikasi": job.kualifikasi,
            "tanggung_jawab": job.tanggung_jawab,
            "tipe_pekerjaan": job.tipe_pekerjaan,
            "lokasi_kerja": job.lokasi_kerja,
            "kota": job.kota,
            "gaji_min": float(job.gaji_min) if job.gaji_min else None,
            "gaji_max": float(job.gaji_max) if job.gaji_max else None,
            "tampilkan_gaji": job.tampilkan_gaji,
            "pengalaman_min_tahun": job.pengalaman_min_tahun,
            "pendidikan_min": job.pendidikan_min,
            "cv_threshold": float(job.cv_threshold) if job.cv_threshold else None,
            "status": job.status,
            "tanggal_buka": str(job.tanggal_buka) if job.tanggal_buka else None,
            "tanggal_tutup": str(job.tanggal_tutup) if job.tanggal_tutup else None,
            "created_at": str(job.created_at) if job.created_at else None,
        }
        # Tambahkan info perusahaan
        if job.perusahaan:
            job_dict["perusahaan"] = {
                "id": job.perusahaan.id,
                "nama_perusahaan": job.perusahaan.nama_perusahaan,
                "industri": job.perusahaan.industri,
                "logo_url": job.perusahaan.logo_url,
                "kota": job.perusahaan.kota,
            }
        data.append(job_dict)

    return {"message": "Daftar lowongan kerja", "total": len(data), "data": data}


@router.get("/{job_id}")
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Mendapatkan detail satu lowongan kerja beserta info perusahaan."""
    result = await db.execute(
        select(JobPosting)
        .options(
            selectinload(JobPosting.perusahaan),
            selectinload(JobPosting.kategori),
        )
        .where(JobPosting.id == job_id)
    )
    job = result.scalars().first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lowongan dengan ID '{job_id}' tidak ditemukan",
        )

    response = {
        "id": job.id,
        "judul_posisi": job.judul_posisi,
        "deskripsi_pekerjaan": job.deskripsi_pekerjaan,
        "kualifikasi": job.kualifikasi,
        "tanggung_jawab": job.tanggung_jawab,
        "tipe_pekerjaan": job.tipe_pekerjaan,
        "lokasi_kerja": job.lokasi_kerja,
        "kota": job.kota,
        "gaji_min": float(job.gaji_min) if job.gaji_min else None,
        "gaji_max": float(job.gaji_max) if job.gaji_max else None,
        "tampilkan_gaji": job.tampilkan_gaji,
        "pengalaman_min_tahun": job.pengalaman_min_tahun,
        "pendidikan_min": job.pendidikan_min,
        "cv_threshold": float(job.cv_threshold) if job.cv_threshold else None,
        "interview_threshold": float(job.interview_threshold) if job.interview_threshold else None,
        "status": job.status,
        "tanggal_buka": str(job.tanggal_buka) if job.tanggal_buka else None,
        "tanggal_tutup": str(job.tanggal_tutup) if job.tanggal_tutup else None,
        "created_at": str(job.created_at) if job.created_at else None,
        "updated_at": str(job.updated_at) if job.updated_at else None,
    }

    # Info perusahaan
    if job.perusahaan:
        response["perusahaan"] = {
            "id": job.perusahaan.id,
            "nama_perusahaan": job.perusahaan.nama_perusahaan,
            "industri": job.perusahaan.industri,
            "ukuran": job.perusahaan.ukuran,
            "deskripsi": job.perusahaan.deskripsi,
            "logo_url": job.perusahaan.logo_url,
            "website_url": job.perusahaan.website_url,
            "kota": job.perusahaan.kota,
            "provinsi": job.perusahaan.provinsi,
        }

    # Info kategori
    if job.kategori:
        response["kategori"] = {
            "id": job.kategori.id,
            "nama_kategori": job.kategori.nama_kategori,
        }

    return response


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_job(
    req: JobPostingCreate,
    request: Request,
    current_user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    """Membuat lowongan kerja baru (hanya perusahaan)."""
    # Validasi role
    if current_user.get("role") != "perusahaan":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya akun perusahaan yang bisa membuat lowongan kerja",
        )

    user_id = current_user.get("sub")

    # Cari profil perusahaan dari user
    result = await db.execute(
        select(PerusahaanProfile).where(PerusahaanProfile.user_id == user_id)
    )
    perusahaan = result.scalars().first()

    if not perusahaan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil perusahaan tidak ditemukan. Silakan lengkapi profil terlebih dahulu.",
        )

    # Generate embedding untuk deskripsi pekerjaan
    embedding_service = request.app.state.embedding_service
    jd_embedding = embedding_service.get_embedding(req.deskripsi_pekerjaan)

    # Buat lowongan baru
    new_job = JobPosting(
        perusahaan_id=perusahaan.id,
        judul_posisi=req.judul_posisi,
        deskripsi_pekerjaan=req.deskripsi_pekerjaan,
        kualifikasi=req.kualifikasi,
        tanggung_jawab=req.tanggung_jawab,
        tipe_pekerjaan=req.tipe_pekerjaan,
        lokasi_kerja=req.lokasi_kerja,
        kota=req.kota,
        gaji_min=req.gaji_min,
        gaji_max=req.gaji_max,
        tampilkan_gaji=req.tampilkan_gaji,
        pengalaman_min_tahun=req.pengalaman_min_tahun,
        pendidikan_min=req.pendidikan_min,
        cv_threshold=req.cv_threshold,
        interview_threshold=req.interview_threshold,
        tanggal_buka=req.tanggal_buka,
        tanggal_tutup=req.tanggal_tutup,
        status="aktif",
        jd_embedding=json.dumps(jd_embedding),
    )

    db.add(new_job)
    await db.flush()

    return {
        "message": "Lowongan kerja berhasil dibuat",
        "data": {
            "id": new_job.id,
            "judul_posisi": new_job.judul_posisi,
            "status": new_job.status,
            "perusahaan_id": new_job.perusahaan_id,
        },
    }


@router.put("/{job_id}")
async def update_job(
    job_id: str,
    update_data: dict,
    request: Request,
    current_user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    """Mengupdate lowongan kerja (hanya pemilik perusahaan)."""
    if current_user.get("role") != "perusahaan":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya akun perusahaan yang bisa mengupdate lowongan kerja",
        )

    user_id = current_user.get("sub")

    # Cari profil perusahaan
    result = await db.execute(
        select(PerusahaanProfile).where(PerusahaanProfile.user_id == user_id)
    )
    perusahaan = result.scalars().first()

    if not perusahaan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil perusahaan tidak ditemukan",
        )

    # Cari lowongan dan verifikasi kepemilikan
    result = await db.execute(
        select(JobPosting).where(
            JobPosting.id == job_id,
            JobPosting.perusahaan_id == perusahaan.id,
        )
    )
    job = result.scalars().first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lowongan tidak ditemukan atau Anda tidak memiliki akses",
        )

    # Field yang boleh diupdate
    allowed_fields = [
        "judul_posisi", "deskripsi_pekerjaan", "kualifikasi", "tanggung_jawab",
        "tipe_pekerjaan", "lokasi_kerja", "kota", "gaji_min", "gaji_max",
        "tampilkan_gaji", "pengalaman_min_tahun", "pendidikan_min",
        "cv_threshold", "interview_threshold", "status",
        "tanggal_buka", "tanggal_tutup",
    ]

    for key, value in update_data.items():
        if key in allowed_fields:
            setattr(job, key, value)

    # Jika deskripsi_pekerjaan berubah, perbarui embedding
    if "deskripsi_pekerjaan" in update_data:
        embedding_service = request.app.state.embedding_service
        jd_embedding = embedding_service.get_embedding(update_data["deskripsi_pekerjaan"])
        job.jd_embedding = json.dumps(jd_embedding)

    return {
        "message": f"Lowongan '{job.judul_posisi}' berhasil diupdate",
        "data": {
            "id": job.id,
            "judul_posisi": job.judul_posisi,
            "status": job.status,
        },
    }


@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    current_user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    """Menghapus/menutup lowongan kerja (hanya pemilik perusahaan)."""
    if current_user.get("role") != "perusahaan":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya akun perusahaan yang bisa menghapus lowongan kerja",
        )

    user_id = current_user.get("sub")

    # Cari profil perusahaan
    result = await db.execute(
        select(PerusahaanProfile).where(PerusahaanProfile.user_id == user_id)
    )
    perusahaan = result.scalars().first()

    if not perusahaan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil perusahaan tidak ditemukan",
        )

    # Cari lowongan dan verifikasi kepemilikan
    result = await db.execute(
        select(JobPosting).where(
            JobPosting.id == job_id,
            JobPosting.perusahaan_id == perusahaan.id,
        )
    )
    job = result.scalars().first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lowongan tidak ditemukan atau Anda tidak memiliki akses",
        )

    # Soft delete: ubah status menjadi 'tutup'
    job.status = "tutup"

    return {
        "message": f"Lowongan '{job.judul_posisi}' berhasil ditutup",
        "data": {"id": job.id, "status": job.status},
    }
