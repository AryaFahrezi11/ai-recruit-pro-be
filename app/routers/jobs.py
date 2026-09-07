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
from app.models import JobPosting
import re

def calculate_pofit_score(job: JobPosting, user_profile: Optional[PelamarProfile]) -> tuple[int, str, bool]:
    """
    Menghitung persentase kecocokan antara lowongan dan pelamar berdasarkan data CV asli.
    Returns: (score, reason, has_cv)
    """
    if not user_profile:
        return 0, "Lengkapi profil/CV Anda untuk mendapatkan rekomendasi PO-Fit yang akurat.", False
        
    user_title = (user_profile.judul_posisi or "").strip()
    user_skills_raw = (user_profile.keahlian or "").strip()
    user_summary = (user_profile.ringkasan_diri or "").strip()
    user_exp = (user_profile.pengalaman_kerja or "").strip()

    # Cek apakah pengguna sudah melengkapi CV / data profil
    has_cv = bool(user_title or user_skills_raw or user_summary or user_exp)
    if not has_cv:
        return 0, "Lengkapi profil/CV Anda untuk melihat rekomendasi PO-Fit personal.", False

    job_title = (job.judul_posisi or "").lower().strip()
    job_desc = (job.deskripsi_pekerjaan or "").lower().strip()
    job_req = (job.kualifikasi or "").lower().strip()
    job_keywords = (job.ai_keywords_json or "").lower().strip()
    job_full_text = f"{job_title} {job_desc} {job_req} {job_keywords}"

    # 1. Judul Posisi / Peran Match (Bobot 45%)
    title_score = 40
    if user_title:
        u_title_lower = user_title.lower()
        if u_title_lower in job_title or job_title in u_title_lower:
            title_score = 100
        else:
            u_words = [w for w in re.findall(r'\w+', u_title_lower) if len(w) > 2]
            j_words = [w for w in re.findall(r'\w+', job_title) if len(w) > 2]
            if u_words and j_words:
                common = set(u_words).intersection(set(j_words))
                if common:
                    title_score = int(min(95, 60 + (len(common) / len(u_words)) * 35))

    # 2. Keahlian (Skills) Match (Bobot 35%)
    skills_score = 40
    if user_skills_raw:
        skills = [s.strip().lower() for s in re.split(r'[,;\n]+', user_skills_raw) if s.strip()]
        if skills:
            matched = [s for s in skills if s in job_full_text]
            skills_score = int(min(98, 45 + (len(matched) / len(skills)) * 53))

    # 3. Pengalaman & Ringkasan Diri Match (Bobot 20%)
    exp_score = 50
    if user_summary or user_exp:
        profile_words = set(re.findall(r'\w+', f"{user_summary} {user_exp}".lower()))
        common_words = profile_words.intersection(set(re.findall(r'\w+', job_full_text)))
        if common_words:
            exp_score = int(min(95, 50 + min(len(common_words) * 3, 45)))

    final_score = int((title_score * 0.45) + (skills_score * 0.35) + (exp_score * 0.20))
    final_score = int(min(98, max(45, final_score)))

    if final_score >= 80:
        reason = "Sangat Cocok! Posisi dan keahlian di CV Anda sangat relevan dengan lowongan ini."
    elif final_score >= 65:
        reason = "Cukup Cocok. Sebagian keahlian Anda sesuai dengan kualifikasi yang dicari."
    else:
        reason = "Kecocokan Standar. Kualifikasi Anda memenuhi persyaratan umum posisi ini."

    return final_score, reason, True


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


@router.get("/locations")
async def get_job_locations(db: AsyncSession = Depends(get_db)):
    """Mendapatkan daftar lokasi lowongan yang paling sering muncul."""
    from sqlalchemy import func
    query = (
        select(JobPosting.kota, func.count(JobPosting.id).label("total"))
        .where(JobPosting.kota.isnot(None), JobPosting.kota != "", JobPosting.status == "active")
        .group_by(JobPosting.kota)
        .order_by(func.count(JobPosting.id).desc())
        .limit(15)
    )
    result = await db.execute(query)
    rows = result.all()
    locations = [r[0].strip() for r in rows if r[0] and r[0].strip()]
    if not locations:
        locations = ["Jakarta", "Bandung", "Surabaya", "Yogyakarta", "Tangerang", "Remote"]
    return {"locations": locations}


@router.get("/my-jobs", response_model=List[JobPostingResponse])
async def get_my_jobs(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Mendapatkan daftar semua lowongan milik perusahaan yang sedang login."""
    service = JobService(db)
    return await service.get_my_jobs(current_user["sub"])


@router.get("")
async def get_jobs(
    request: Request,
    db: AsyncSession = Depends(get_db),
    search: Optional[str] = Query(default=None, description="Cari berdasarkan kata kunci"),
    keyword: Optional[str] = Query(default=None, description="Alias kata kunci pencarian"),
    location: Optional[str] = Query(default=None, description="Cari berdasarkan kota / lokasi"),
    kategori_id: Optional[str] = Query(default=None, description="Filter ID kategori lowongan"),
    tipe_pekerjaan: Optional[str] = Query(default=None, description="Filter: Full-time, Contract, Part-time, Internship, Freelance"),
    lokasi_kerja: Optional[str] = Query(default=None, description="Filter: On-site, Remote, Hybrid"),
    experience_level: Optional[str] = Query(default=None, description="Filter tingkat pengalaman"),
    pendidikan_min: Optional[str] = Query(default=None, description="Filter pendidikan minimal"),
    sort_by: Optional[str] = Query(default="rekomendasi", description="rekomendasi, terbaru, terlama"),
    limit: int = Query(default=100, ge=1, le=300),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = Query(default=None, description="Filter status lowongan: active, closed, draft"),
    include_all: bool = Query(default=False, description="Tampilkan semua status (untuk admin)"),
):
    """Mendapatkan daftar semua lowongan kerja yang aktif dengan filter lengkap & sortir PO-fit."""
    query = (
        select(JobPosting)
        .options(
            selectinload(JobPosting.perusahaan),
            selectinload(JobPosting.kategori),
            defer(JobPosting.jd_embedding)
        )
    )

    # Filter status lowongan
    if not include_all:
        if status:
            query = query.where(JobPosting.status == status)
        else:
            query = query.where(JobPosting.status == "active")
    elif status:
        query = query.where(JobPosting.status == status)

    # Filter kata kunci (search / keyword)
    kw = keyword or search
    if kw and kw.strip():
        kw_clean = kw.strip()
        query = query.where(
            or_(
                JobPosting.judul_posisi.ilike(f"%{kw_clean}%"),
                JobPosting.deskripsi_pekerjaan.ilike(f"%{kw_clean}%"),
                JobPosting.kualifikasi.ilike(f"%{kw_clean}%"),
                JobPosting.kota.ilike(f"%{kw_clean}%"),
            )
        )

    # Filter lokasi
    if location and location.strip() and location != "Semua":
        loc_clean = location.strip()
        query = query.where(
            or_(
                JobPosting.kota.ilike(f"%{loc_clean}%"),
                JobPosting.lokasi_kerja.ilike(f"%{loc_clean}%"),
            )
        )

    # Filter kategori ID
    if kategori_id and kategori_id.strip() and kategori_id != "Semua":
        query = query.where(JobPosting.kategori_id == kategori_id.strip())

    # Filter jenis pekerjaan (tipe_pekerjaan)
    if tipe_pekerjaan and tipe_pekerjaan.strip() and tipe_pekerjaan != "Semua":
        tp = tipe_pekerjaan.strip()
        # Mendukung variasi misal "Full-time" vs "full_time"
        tp_alt = tp.replace("-", "_").lower()
        query = query.where(
            or_(
                JobPosting.tipe_pekerjaan.ilike(f"%{tp}%"),
                JobPosting.tipe_pekerjaan.ilike(f"%{tp_alt}%")
            )
        )

    # Filter mode kerja (lokasi_kerja)
    if lokasi_kerja and lokasi_kerja.strip() and lokasi_kerja != "Semua":
        lk = lokasi_kerja.strip().lower()
        query = query.where(JobPosting.lokasi_kerja.ilike(f"%{lk}%"))

    # Filter tingkat pengalaman
    if experience_level and experience_level.strip() and experience_level != "Semua":
        el = experience_level.strip()
        conditions = [JobPosting.experience_level.ilike(f"%{el}%")]
        el_lower = el.lower()
        if "0" in el or "1" in el or "entry" in el_lower:
            conditions.extend([JobPosting.experience_level.ilike("%entry%"), JobPosting.experience_level.ilike("%0 - 1%"), JobPosting.experience_level.ilike("%0-1%")])
        elif "2" in el or "4" in el or "mid" in el_lower:
            conditions.extend([JobPosting.experience_level.ilike("%mid%"), JobPosting.experience_level.ilike("%2 - 4%"), JobPosting.experience_level.ilike("%2-4%")])
        elif "5" in el or "senior" in el_lower:
            conditions.extend([JobPosting.experience_level.ilike("%senior%"), JobPosting.experience_level.ilike("%5+%")])
        elif "8" in el or "lead" in el_lower or "manager" in el_lower:
            conditions.extend([JobPosting.experience_level.ilike("%lead%"), JobPosting.experience_level.ilike("%manager%"), JobPosting.experience_level.ilike("%8+%")])
        query = query.where(or_(*conditions))

    # Filter minimal pendidikan
    if pendidikan_min and pendidikan_min.strip() and pendidikan_min != "Semua":
        pm = pendidikan_min.strip()
        query = query.where(JobPosting.pendidikan_min.ilike(f"%{pm}%"))

    # Urutan dasar dari database
    query = query.order_by(JobPosting.created_at.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    jobs = result.scalars().all()

    # Ambil user profile jika token ada
    token_payload = verify_token_optional(request)
    user_profile = None
    user_has_cv = False
    if token_payload and token_payload.get("sub"):
        result_profile = await db.execute(select(PelamarProfile).where(PelamarProfile.user_id == token_payload["sub"]))
        user_profile = result_profile.scalars().first()

    # Format data
    data = []
    for job in jobs:
        match_score, reason, has_cv = calculate_pofit_score(job, user_profile)
        if has_cv:
            user_has_cv = True

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

    # Sortir hasil sesuai instruksi:
    # 1. Jika rekomendasi PO-Fit dan user punya CV: urutkan dari match_score tertinggi
    # 2. Jika user belum punya CV: urutkan dari yang terbaru
    if sort_by == "rekomendasi":
        if user_has_cv:
            data.sort(key=lambda x: (x["match_score"], x["created_at"] or ""), reverse=True)
        else:
            data.sort(key=lambda x: x["created_at"] or "", reverse=True)
    elif sort_by == "terbaru":
        data.sort(key=lambda x: x["created_at"] or "", reverse=True)
    elif sort_by == "terlama":
        data.sort(key=lambda x: x["created_at"] or "")

    return {
        "message": "Daftar lowongan kerja",
        "total": len(data),
        "user_has_cv": user_has_cv,
        "data": data
    }


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
    is_admin = current_user.get("role") == "admin"
    service = JobService(db)
    return await service.update_job_status(current_user["sub"], job_id, status_data.status, is_admin=is_admin)

