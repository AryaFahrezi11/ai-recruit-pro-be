"""
🛣️ Jobs Router
Endpoint: CRUD /api/jobs
"""
import json
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload, defer
from starlette.concurrency import run_in_threadpool

from app.core.database import get_db
from app.core.security import verify_token, verify_token_optional
from app.models.user import PerusahaanProfile, PelamarProfile
import re

def calculate_pofit_score(job: JobPosting, user_profile: PelamarProfile) -> int:
    """Menghitung persentase kecocokan antara lowongan dan pelamar secara sederhana."""
    if not user_profile:
        return 92 # Default score jika user belum login atau profil kosong
        
    job_text = f"{job.judul_posisi or ''} {job.deskripsi_pekerjaan or ''} {job.kualifikasi or ''} {job.pendidikan_min or ''}".lower()
    job_words = set(re.findall(r'\w+', job_text))
    
    user_text = f"{user_profile.keahlian or ''} {user_profile.judul_posisi or ''} {user_profile.pengalaman_kerja or ''} {user_profile.riwayat_pendidikan or ''}".lower()
    user_words = set(re.findall(r'\w+', user_text))
    
    if not job_words or not user_words:
        return 50
        
    intersection = job_words.intersection(user_words)
    base_score = 60
    match_percentage = (len(intersection) / len(job_words)) * 100 if len(job_words) > 0 else 0
    final_score = base_score + (match_percentage * 1.5)
    
    return int(min(98, max(60, final_score)))
from app.models.job import JobPosting, JobCategory
from app.schemas.job import JobPostingCreate, JobPostingResponse
from app.services.job_service import JobService

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

@router.get("/")
async def get_jobs(
    request: Request,
    db: AsyncSession = Depends(get_db),
    search: str = Query(default=None, description="Cari berdasarkan judul posisi atau kota"),
    tipe_pekerjaan: str = Query(default=None, description="Filter: full_time, part_time, contract, internship"),
    lokasi_kerja: str = Query(default=None, description="Filter: onsite, remote, hybrid"),
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """Mendapatkan daftar semua lowongan kerja yang aktif."""
    query = (
        select(JobPosting)
        .options(
            selectinload(JobPosting.perusahaan),
            selectinload(JobPosting.kategori),
            defer(JobPosting.jd_embedding)
        )
        .where(JobPosting.status == "active")
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

    # Ambil user token untuk hitung score
    token_payload = verify_token_optional(request)
    user_profile = None
    if token_payload and token_payload.get("sub"):
        result_profile = await db.execute(select(PelamarProfile).where(PelamarProfile.user_id == token_payload["sub"]))
        user_profile = result_profile.scalars().first()

    # Format response
    data = []
    for job in jobs:
        match_score = calculate_pofit_score(job, user_profile)
        
        # Penentuan alasan (reason) berdasar score
        if match_score >= 85:
            reason = "Sangat Cocok! Keahlian dan pengalaman Anda sangat relevan dengan posisi ini."
        elif match_score >= 70:
            reason = "Cukup Cocok. Anda memenuhi sebagian kriteria yang dibutuhkan."
        else:
            reason = "Kualifikasi Anda memiliki sedikit kecocokan dengan posisi ini."

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
            
            "department": job.department,
            "experience_level": job.experience_level,
            "benefits_json": job.benefits_json,
            "ai_keywords_json": job.ai_keywords_json,
            "video_questions_json": job.video_questions_json,
            "openings_count": job.openings_count,
            "match_score": match_score,
            "reason": reason,
        }
        # Tambahkan info perusahaan
        if job.perusahaan:
            job_dict["perusahaan"] = {
                "id": job.perusahaan.id,
                "nama_perusahaan": job.perusahaan.nama_perusahaan,
                "industri": job.perusahaan.industri,
                "logo_url": job.perusahaan.logo_url,
                "kota": job.perusahaan.kota,
                "deskripsi": job.perusahaan.deskripsi,
                "ukuran": job.perusahaan.ukuran,
                "alamat": job.perusahaan.alamat,
                "website_url": job.perusahaan.website_url,
            }
        if job.kategori:
            job_dict["kategori"] = {
                "id": job.kategori.id,
                "nama_kategori": job.kategori.nama_kategori,
            }
        data.append(job_dict)

    return {"message": "Daftar lowongan kerja", "total": len(data), "data": data}


@router.get("/saved", response_model=List[dict])
async def get_saved_jobs(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Mendapatkan daftar lowongan yang disimpan oleh pelamar."""
    service = JobService(db)
    # the frontend expects a list of jobs with their IDs, which get_saved_jobs returns.
    # since response_model is List[dict], we can just return it or rely on FastAPI to serialize.
    jobs = await service.get_saved_jobs(current_user["sub"])
    
    # Format the same way as get_jobs
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
        if job.perusahaan:
            job_dict["perusahaan"] = {
                "id": job.perusahaan.id,
                "nama_perusahaan": job.perusahaan.nama_perusahaan,
                "industri": job.perusahaan.industri,
                "logo_url": job.perusahaan.logo_url,
                "kota": job.perusahaan.kota,
            }
        data.append(job_dict)
    return data

@router.post("/{job_id}/save")
async def save_job(job_id: str, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Menyimpan lowongan (bookmark)."""
    if current_user.get("role") != "pelamar":
        raise HTTPException(status_code=403, detail="Hanya pelamar yang bisa menyimpan lowongan.")
    service = JobService(db)
    return await service.save_job(current_user["sub"], job_id)

@router.delete("/{job_id}/save")
async def remove_saved_job(job_id: str, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Menghapus lowongan dari daftar simpanan."""
    if current_user.get("role") != "pelamar":
        raise HTTPException(status_code=403, detail="Hanya pelamar yang bisa menghapus simpanan.")
    service = JobService(db)
    return await service.remove_saved_job(current_user["sub"], job_id)


@router.get("/{job_id}")
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Mendapatkan detail satu lowongan kerja beserta info perusahaan."""
    result = await db.execute(
        select(JobPosting)
        .options(
            selectinload(JobPosting.perusahaan),
            selectinload(JobPosting.kategori),
            defer(JobPosting.jd_embedding)
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
        "department": job.department,
        "experience_level": job.experience_level,
        "benefits_json": job.benefits_json,
        "ai_keywords_json": job.ai_keywords_json,
        "video_questions_json": job.video_questions_json,
        "openings_count": job.openings_count,
        "kategori_id": job.kategori_id,
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

    import json
    
    # Extract AI keywords
    ai_keywords = []
    if req.ai_keywords_json:
        try:
            ai_keywords = json.loads(req.ai_keywords_json)
        except Exception:
            pass
    keywords_str = ", ".join(ai_keywords)
    
    # Generate embedding untuk deskripsi pekerjaan gabungan
    embedding_service = request.app.state.embedding_service
    full_jd_text = f"{req.deskripsi_pekerjaan}\n{req.kualifikasi}\n{req.tanggung_jawab}\nKeahlian Utama: {keywords_str}"
    jd_embedding = await run_in_threadpool(embedding_service.get_embedding, full_jd_text)

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
        status=req.status,
        kategori_id=req.kategori_id,
        department=req.department,
        experience_level=req.experience_level,
        benefits_json=req.benefits_json,
        ai_keywords_json=req.ai_keywords_json,
        video_questions_json=req.video_questions_json,
        openings_count=req.openings_count,
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

class StatusUpdate(BaseModel):
    status: str

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
        "tanggal_buka", "tanggal_tutup", "kategori_id", "department",
        "experience_level", "benefits_json", "ai_keywords_json",
        "video_questions_json", "openings_count"
    ]

    for key, value in update_data.items():
        if key in allowed_fields:
            if key in ["tanggal_buka", "tanggal_tutup"] and isinstance(value, str) and value:
                try:
                    value = datetime.strptime(value, "%Y-%m-%d").date()
                except ValueError:
                    pass
            setattr(job, key, value)

    # Check if any text field changed that affects embeddings
    text_fields_changed = any(field in update_data for field in ["deskripsi_pekerjaan", "kualifikasi", "tanggung_jawab", "ai_keywords_json"])
    
    if text_fields_changed:
        ai_keywords = []
        if job.ai_keywords_json:
            try:
                ai_keywords = json.loads(job.ai_keywords_json)
            except Exception:
                pass
        keywords_str = ", ".join(ai_keywords)
        
        full_jd_text = f"{job.deskripsi_pekerjaan or ''}\n{job.kualifikasi or ''}\n{job.tanggung_jawab or ''}\nKeahlian Utama: {keywords_str}"
        
        embedding_service = request.app.state.embedding_service
        jd_embedding = await run_in_threadpool(embedding_service.get_embedding, full_jd_text)
        job.jd_embedding = json.dumps(jd_embedding)

    await db.commit()
    await db.refresh(job)

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
    """Menghapus lowongan kerja (hanya pemilik perusahaan)."""
    service = JobService(db)
    return await service.delete_job(current_user["sub"], job_id)

@router.patch("/{job_id}/status")
async def update_job_status(
    job_id: str,
    status_data: StatusUpdate,
    current_user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    """Mengubah status lowongan."""
    service = JobService(db)
    return await service.update_job_status(current_user["sub"], job_id, status_data.status)
