"""
🛣️ Applications Router
Endpoint: /api/applications
Proses melamar kerja dengan upload CV, analisis AI, dan penyimpanan ke database.
"""
import os
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
import shutil
import cloudinary
import cloudinary.uploader
from app.core.config import settings
from app.services.video_ai_service import video_ai_service
from supabase import create_client, Client

# Konfigurasi Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)

# Hubungkan ke Supabase (gunakan konfigurasi asli milik user)
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

from app.core.database import get_db, async_session
from app.core.security import verify_token
from app.models.user import PelamarProfile, PerusahaanProfile
from app.models.job import JobPosting
from app.models.application import CVDocument, Application
from app.models.video_task import VideoAnalysisJob
from app.models.analysis import CVAnalysisResult
from app.services.cv_analysis_service import CVAnalysisService
from app.utils.pdf_extractor import clean_text
from app.schemas.application import ApplicationCreate

# Folder untuk menyimpan file CV yang diupload
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()


@router.get("/")
async def get_applications(
    current_user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Mendapatkan daftar lamaran.
    - Pelamar: Melihat semua lamaran miliknya.
    - Perusahaan: Melihat semua lamaran yang masuk ke lowongan miliknya.
    """
    user_id = current_user.get("sub")
    role = current_user.get("role")

    if role == "pelamar":
        # Cari profil pelamar
        result = await db.execute(
            select(PelamarProfile).where(PelamarProfile.user_id == user_id)
        )
        pelamar = result.scalars().first()

        if not pelamar:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profil pelamar tidak ditemukan",
            )

        # Ambil semua lamaran pelamar beserta info job dan hasil analisis
        result = await db.execute(
            select(Application)
            .options(
                selectinload(Application.job).selectinload(JobPosting.perusahaan),
                selectinload(Application.cv_analysis),
            )
            .where(Application.pelamar_id == pelamar.id)
            .order_by(Application.applied_at.desc())
        )
        applications = result.scalars().all()

        data = []
        for app in applications:
            app_dict = {
                "id": app.id,
                "status": app.status,
                "catatan_pelamar": app.catatan_pelamar,
                "applied_at": str(app.applied_at) if app.applied_at else None,
            }
            if app.job:
                app_dict["job"] = {
                    "id": app.job.id,
                    "judul_posisi": app.job.judul_posisi,
                    "tipe_pekerjaan": app.job.tipe_pekerjaan,
                    "kota": app.job.kota,
                    "video_questions_json": app.job.video_questions_json,
                    "video_questions": json.loads(app.job.video_questions_json) if (app.job.video_questions_json and app.job.video_questions_json.strip().startswith('[')) else ([q.strip() for q in app.job.video_questions_json.split('\n') if q.strip()] if app.job.video_questions_json else []),
                }
                if app.job.perusahaan:
                    app_dict["job"]["perusahaan"] = {
                        "nama_perusahaan": app.job.perusahaan.nama_perusahaan,
                        "logo_url": app.job.perusahaan.logo_url,
                    }
            if app.cv_analysis:
                app_dict["analisis_cv"] = {
                    "skor_kecocokan": float(app.cv_analysis.skor_kecocokan),
                    "kategori": app.cv_analysis.kategori,
                    "hasil": app.cv_analysis.hasil,
                    "hybrid_details": json.loads(app.cv_analysis.detail_analisis) if app.cv_analysis.detail_analisis else None,
                }
            if hasattr(app, "ai_result") and app.ai_result:
                app_dict["ai_result"] = app.ai_result
            if hasattr(app, "video_url") and app.video_url:
                app_dict["video_url"] = app.video_url
            data.append(app_dict)

        return {"message": "Daftar lamaran Anda", "total": len(data), "data": data}

    elif role == "perusahaan":
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

        # Ambil semua lowongan perusahaan
        result = await db.execute(
            select(JobPosting.id).where(JobPosting.perusahaan_id == perusahaan.id)
        )
        job_ids = [row[0] for row in result.all()]

        if not job_ids:
            return {"message": "Belum ada lamaran masuk", "total": 0, "data": []}

        # Ambil semua lamaran untuk lowongan-lowongan tersebut
        result = await db.execute(
            select(Application)
            .options(
                selectinload(Application.pelamar).selectinload(PelamarProfile.user),
                selectinload(Application.job),
                selectinload(Application.cv_analysis),
                selectinload(Application.cv_document),
            )
            .where(Application.job_id.in_(job_ids))
            .order_by(Application.applied_at.desc())
        )
        applications = result.scalars().all()

        data = []
        for app in applications:
            app_dict = {
                "id": app.id,
                "status": app.status,
                "catatan_pelamar": app.catatan_pelamar,
                "applied_at": str(app.applied_at) if app.applied_at else None,
            }
            if app.pelamar:
                app_dict["pelamar"] = {
                    "id": app.pelamar.id,
                    "nama_lengkap": app.pelamar.nama_lengkap,
                    "no_telepon": app.pelamar.no_telepon,
                }
                
                # Parsing stringified JSON fields safely
                def safe_json(val):
                    if not val:
                        return []
                    try:
                        parsed = json.loads(val)
                        return parsed if isinstance(parsed, list) else []
                    except:
                        return []

                app_dict["cvData"] = {
                    "fullName": app.pelamar.nama_lengkap,
                    "jobTitle": app.pelamar.judul_posisi,
                    "email": getattr(app.pelamar.user, "email", "") if getattr(app.pelamar, "user", None) else "",
                    "phone": app.pelamar.no_telepon,
                    "location": app.pelamar.alamat,
                    "linkedinUrl": app.pelamar.linkedin_url,
                    "portfolioUrl": app.pelamar.portfolio_url,
                    "socialLinks": safe_json(app.pelamar.social_links),
                    "summary": app.pelamar.ringkasan_diri,
                    "skills": app.pelamar.keahlian,
                    "experiences": safe_json(app.pelamar.pengalaman_kerja),
                    "education": safe_json(app.pelamar.riwayat_pendidikan),
                    "certifications": safe_json(app.pelamar.sertifikasi),
                }
            if app.cv_document:
                app_dict["cv_document"] = {
                    "id": app.cv_document.id,
                    "file_url": app.cv_document.file_url,
                    "file_type": app.cv_document.file_type,
                    "file_size_kb": app.cv_document.file_size_kb,
                    "email": app.cv_document.email,
                    "phone": app.cv_document.phone,
                    "pendidikan_tertinggi": app.cv_document.pendidikan_tertinggi,
                    "is_ocr_used": app.cv_document.is_ocr_used,
                }
            if app.job:
                app_dict["job"] = {
                    "id": app.job.id,
                    "judul_posisi": app.job.judul_posisi,
                    "tipe_pekerjaan": app.job.tipe_pekerjaan,
                    "lokasi_kerja": app.job.lokasi_kerja,
                    "kota": app.job.kota,
                    "pengalaman_min_tahun": app.job.pengalaman_min_tahun,
                    "pendidikan_min": app.job.pendidikan_min,
                    "deskripsi_pekerjaan": safe_json(app.job.deskripsi_pekerjaan) if app.job.deskripsi_pekerjaan else [],
                    "tanggung_jawab": safe_json(app.job.tanggung_jawab) if app.job.tanggung_jawab else [],
                    "kualifikasi": safe_json(app.job.kualifikasi) if app.job.kualifikasi else [],
                    "gaji_min": float(app.job.gaji_min) if app.job.gaji_min else None,
                    "gaji_max": float(app.job.gaji_max) if app.job.gaji_max else None,
                    "tampilkan_gaji": app.job.tampilkan_gaji,
                    "department": app.job.department,
                    "experience_level": app.job.experience_level,
                    "benefits": safe_json(app.job.benefits_json) if app.job.benefits_json else [],
                    "ai_keywords": safe_json(app.job.ai_keywords_json) if app.job.ai_keywords_json else [],
                    "tanggal_buka": str(app.job.tanggal_buka) if app.job.tanggal_buka else None,
                    "tanggal_tutup": str(app.job.tanggal_tutup) if app.job.tanggal_tutup else None,
                    "cv_threshold": float(app.job.cv_threshold) if app.job.cv_threshold else 40,
                    "interview_threshold": float(app.job.interview_threshold) if app.job.interview_threshold else 40,
                    "video_questions_json": app.job.video_questions_json,
                    "video_questions": safe_json(app.job.video_questions_json),
                }
            if app.cv_analysis:
                app_dict["analisis_cv"] = {
                    "skor_kecocokan": float(app.cv_analysis.skor_kecocokan),
                    "kategori": app.cv_analysis.kategori,
                    "hasil": app.cv_analysis.hasil,
                    "hybrid_details": json.loads(app.cv_analysis.detail_analisis) if app.cv_analysis.detail_analisis else None,
                }
            if hasattr(app, "ai_result") and app.ai_result:
                app_dict["ai_result"] = app.ai_result
            if hasattr(app, "video_url") and app.video_url:
                app_dict["video_url"] = app.video_url
            data.append(app_dict)

        return {"message": "Daftar lamaran masuk", "total": len(data), "data": data}

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role Anda tidak memiliki akses ke daftar lamaran",
        )



async def run_ai_screening_background(application_id: str, embedding_service):
    async with async_session() as db:
        try:
            # Cari Lamaran beserta Relasinya
            result = await db.execute(
                select(Application)
                .options(
                    selectinload(Application.job),
                    selectinload(Application.cv_document),
                    selectinload(Application.cv_analysis)
                )
                .where(Application.id == application_id)
            )
            app_record = result.scalars().first()
            if not app_record or not app_record.cv_document or not app_record.job:
                return
            
            cv_doc = app_record.cv_document
            job = app_record.job

            cv_text = cv_doc.extracted_text
            jd_text = f"{job.deskripsi_pekerjaan}\n{job.kualifikasi}\n{job.tanggung_jawab}"
            threshold = float(job.cv_threshold) if job.cv_threshold else 60.0
            
            ai_keywords = []
            if job.ai_keywords_json:
                try:
                    ai_keywords = json.loads(job.ai_keywords_json)
                except Exception:
                    pass

            cv_service = CVAnalysisService(embedding_service)
            
            cv_embedding_json = cv_doc.embedding_vector
            jd_embedding_json = job.jd_embedding
            
            cv_embedding = json.loads(cv_embedding_json) if cv_embedding_json else None
            jd_embedding = json.loads(jd_embedding_json) if jd_embedding_json else None
            
            if cv_embedding and jd_embedding:
                analysis_result = await cv_service.analyze_match_from_embeddings(
                    cv_embedding=cv_embedding,
                    jd_embedding=jd_embedding,
                    threshold=threshold,
                    cv_text=cv_text,
                    ai_keywords=ai_keywords,
                    cv_education=cv_doc.pendidikan_tertinggi,
                    job_education=job.pendidikan_min
                )
            else:
                analysis_result = await cv_service.analyze_cv(
                    cv_text=cv_text,
                    job_description=jd_text,
                    threshold=threshold,
                    ai_keywords=ai_keywords,
                    cv_education=cv_doc.pendidikan_tertinggi,
                    job_education=job.pendidikan_min
                )

            # Update Application Status & Simpan Hasil
            app_record.status = "virtual_interview" if analysis_result["hasil"] == "lolos" else "ditolak"
            
            cv_analysis = CVAnalysisResult(
                application_id=app_record.id,
                cv_document_id=app_record.cv_document_id,
                job_id=app_record.job_id,
                cosine_similarity_score=analysis_result["cosine_similarity_score"],
                skor_kecocokan=analysis_result["skor_kecocokan"],
                threshold_digunakan=analysis_result["threshold_digunakan"],
                kategori=analysis_result["kategori"],
                hasil=analysis_result["hasil"],
                waktu_proses_ms=analysis_result.get("waktu_proses_ms", 0),
                detail_analisis=json.dumps(analysis_result.get("hybrid_details", {})) if "hybrid_details" in analysis_result else None,
            )
            db.add(cv_analysis)
            
            await db.commit()
        except Exception as e:
            print("Background AI Screening failed:", e)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_application(
    request: Request,
    payload: ApplicationCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Pelamar melamar ke suatu posisi menggunakan Profil CV Dashboard.
    """
    user_id = current_user.get("sub")
    role = current_user.get("role")

    if role != "pelamar":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya pelamar yang dapat melamar pekerjaan",
        )

    # 1. Verifikasi Pelamar
    result = await db.execute(
        select(PelamarProfile).where(PelamarProfile.user_id == user_id)
    )
    pelamar = result.scalars().first()
    if not pelamar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil pelamar tidak ditemukan",
        )

    # 2. Verifikasi Job
    result = await db.execute(
        select(JobPosting).where(
            JobPosting.id == payload.job_id, JobPosting.status == "active"
        )
    )
    job = result.scalars().first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lowongan kerja tidak ditemukan atau sudah ditutup",
        )

    # Cek apakah sudah melamar
    result = await db.execute(
        select(Application).where(
            Application.pelamar_id == pelamar.id, Application.job_id == job.id
        )
    )
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Anda sudah melamar ke posisi ini",
        )

    # 3. Ambil CVDocument master terakhir dari pelamar
    result = await db.execute(
        select(CVDocument)
        .where(CVDocument.pelamar_id == pelamar.id, CVDocument.nama_file == "Profil_CV_Dashboard.json")
        .order_by(CVDocument.uploaded_at.desc())
    )
    cv_doc = result.scalars().first()
    
    if not cv_doc:
        # Otomatis generate CVDocument dari profil pelamar jika belum ada di database
        from starlette.concurrency import run_in_threadpool
        from app.utils.pdf_extractor import extract_contact, extract_education
        
        cv_text_parts = [
            f"Nama: {pelamar.nama_lengkap or ''}",
            f"Posisi/Jabatan: {pelamar.judul_posisi or ''}",
            f"Deskripsi Diri: {pelamar.ringkasan_diri or ''}",
            f"Keahlian (Skills): {pelamar.keahlian or ''}",
            f"Pengalaman Kerja:\n{pelamar.pengalaman_kerja or ''}",
            f"Pendidikan:\n{pelamar.riwayat_pendidikan or ''}"
        ]
        cv_text = "\n".join(cv_text_parts)
        
        try:
            embedding_service = request.app.state.embedding_service
            cv_embedding = await run_in_threadpool(embedding_service.get_embedding, cv_text)
            kontak = extract_contact(cv_text)
            pendidikan_tertinggi = extract_education(cv_text)
            
            cv_doc = CVDocument(
                pelamar_id=pelamar.id,
                nama_file="Profil_CV_Dashboard.json",
                file_url="profil-dashboard",
                file_type="json",
                file_size_kb=len(cv_text) // 1024,
                extracted_text=cv_text,
                cleaned_text=clean_text(cv_text),
                embedding_vector=json.dumps(cv_embedding),
                email=kontak["email"],
                phone=kontak["phone"],
                pendidikan_tertinggi=pendidikan_tertinggi,
                is_ocr_used=False
            )
            db.add(cv_doc)
            await db.flush()
        except Exception as e:
            print("Failed to auto-generate CVDocument on apply:", e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CV Profil tidak ditemukan. Silakan lengkapi dan simpan Profil/CV di dashboard terlebih dahulu.",
            )

    # 5. Buat Application 
    new_application = Application(
        pelamar_id=pelamar.id,
        job_id=job.id,
        cv_document_id=cv_doc.id,
        catatan_pelamar=payload.catatan_pelamar,
        status="upload_cv"
    )
    db.add(new_application)
    await db.commit()
    await db.refresh(new_application)
    
    # 6. Jalankan Seleksi AI di Background agar API sangat cepat merespons (Skala besar)
    background_tasks.add_task(
        run_ai_screening_background,
        application_id=new_application.id,
        embedding_service=request.app.state.embedding_service
    )

    return {
        "message": "Lamaran berhasil dikirim (Sedang dianalisis AI)",
        "data": {
            "application_id": new_application.id,
            "status": new_application.status,
            "analisis_cv": None
        }
    }


@router.post("/{application_id}/analyze", status_code=status.HTTP_200_OK)
async def analyze_application_cv(
    application_id: str,
    request: Request,
    current_user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Menjalankan proses seleksi AI (PO-FIT) secara manual untuk suatu lamaran.
    Hanya bisa dilakukan oleh perusahaan pemilik lowongan.
    """
    user_id = current_user.get("sub")
    # Role check diabaikan sementara karena pengecekan profil perusahaan di bawah 
    # sudah cukup untuk memastikan otorisasi.

    # 1. Cari Profil Perusahaan
    result = await db.execute(
        select(PerusahaanProfile).where(PerusahaanProfile.user_id == user_id)
    )
    perusahaan = result.scalars().first()
    if not perusahaan:
        raise HTTPException(status_code=404, detail="Profil perusahaan tidak ditemukan")

    # 2. Cari Lamaran beserta Relasinya
    result = await db.execute(
        select(Application)
        .options(
            selectinload(Application.job),
            selectinload(Application.cv_document),
            selectinload(Application.cv_analysis)
        )
        .where(Application.id == application_id)
    )
    app_record = result.scalars().first()

    if not app_record:
        raise HTTPException(status_code=404, detail="Lamaran tidak ditemukan")

    if app_record.job.perusahaan_id != perusahaan.id:
        raise HTTPException(status_code=403, detail="Anda tidak memiliki akses ke lamaran ini")

    if app_record.status != "upload_cv":
        raise HTTPException(status_code=400, detail=f"Lamaran ini sudah diproses (Status: {app_record.status})")
        
    if app_record.cv_analysis:
         raise HTTPException(status_code=400, detail="Analisis AI sudah pernah dilakukan untuk lamaran ini")

    # 3. Ambil Teks dari CVDocument dan JD
    cv_text = app_record.cv_document.extracted_text
    job = app_record.job
    jd_text = f"{job.deskripsi_pekerjaan}\n{job.kualifikasi}\n{job.tanggung_jawab}"
    threshold = float(job.cv_threshold) if job.cv_threshold else 60.0
    
    ai_keywords = []
    if job.ai_keywords_json:
        try:
            ai_keywords = json.loads(job.ai_keywords_json)
        except Exception:
            pass

    # 4. Jalankan AI CV Analysis menggunakan Pre-computed Vector
    embedding_service = request.app.state.embedding_service
    cv_service = CVAnalysisService(embedding_service)
    
    cv_embedding_json = app_record.cv_document.embedding_vector
    jd_embedding_json = app_record.job.jd_embedding
    
    cv_embedding = json.loads(cv_embedding_json) if cv_embedding_json else None
    jd_embedding = json.loads(jd_embedding_json) if jd_embedding_json else None
    
    if cv_embedding and jd_embedding:
        analysis_result = await cv_service.analyze_match_from_embeddings(
            cv_embedding=cv_embedding,
            jd_embedding=jd_embedding,
            threshold=threshold,
            cv_text=cv_text,
            ai_keywords=ai_keywords,
            cv_education=app_record.cv_document.pendidikan_tertinggi,
            job_education=job.pendidikan_min
        )
    else:
        # Fallback jika vektor belum ada di database
        analysis_result = await cv_service.analyze_cv(
            cv_text=cv_text,
            job_description=jd_text,
            threshold=threshold,
            ai_keywords=ai_keywords,
            cv_education=app_record.cv_document.pendidikan_tertinggi,
            job_education=job.pendidikan_min
        )

    # 5. Update Application Status & Simpan Hasil
    app_record.status = "cv_screening" if analysis_result["hasil"] == "lolos" else "ditolak_sistem"
    
    cv_analysis = CVAnalysisResult(
        application_id=app_record.id,
        cv_document_id=app_record.cv_document_id,
        job_id=app_record.job_id,
        cosine_similarity_score=analysis_result["cosine_similarity_score"],
        skor_kecocokan=analysis_result["skor_kecocokan"],
        threshold_digunakan=analysis_result["threshold_digunakan"],
        kategori=analysis_result["kategori"],
        hasil=analysis_result["hasil"],
        waktu_proses_ms=analysis_result.get("waktu_proses_ms", 0),
        detail_analisis=json.dumps(analysis_result.get("hybrid_details", {})) if "hybrid_details" in analysis_result else None,
    )
    db.add(cv_analysis)
    
    await db.commit()
    await db.refresh(app_record)

    return {
        "message": "Analisis AI selesai",
        "data": {
            "application_id": app_record.id,
            "status": app_record.status,
            "analisis_cv": {
                "skor_kecocokan": float(cv_analysis.skor_kecocokan),
                "kategori": cv_analysis.kategori,
                "hasil": cv_analysis.hasil,
            }
        }
    }


@router.get("/{application_id}")
async def get_application(
    application_id: str,
    current_user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    """Mendapatkan detail lamaran beserta status pipeline dan hasil analisa AI."""
    user_id = current_user.get("sub")
    role = current_user.get("role")

    # Query lamaran dengan relasi
    result = await db.execute(
        select(Application)
        .options(
            selectinload(Application.job).selectinload(JobPosting.perusahaan),
            selectinload(Application.pelamar),
            selectinload(Application.cv_document),
            selectinload(Application.cv_analysis),
        )
        .where(Application.id == application_id)
    )
    application = result.scalars().first()

    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lamaran tidak ditemukan",
        )

    # Verifikasi akses
    if role == "pelamar":
        # Pelamar hanya bisa melihat lamarannya sendiri
        result = await db.execute(
            select(PelamarProfile).where(PelamarProfile.user_id == user_id)
        )
        pelamar = result.scalars().first()
        if not pelamar or application.pelamar_id != pelamar.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda tidak memiliki akses ke lamaran ini",
            )
    elif role == "perusahaan":
        # Perusahaan hanya bisa melihat lamaran ke lowongannya
        result = await db.execute(
            select(PerusahaanProfile).where(PerusahaanProfile.user_id == user_id)
        )
        perusahaan = result.scalars().first()
        if not perusahaan:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda tidak memiliki akses ke lamaran ini",
            )
        # Cek apakah lowongan milik perusahaan ini
        result = await db.execute(
            select(JobPosting).where(
                JobPosting.id == application.job_id,
                JobPosting.perusahaan_id == perusahaan.id,
            )
        )
        if not result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Anda tidak memiliki akses ke lamaran ini",
            )

    # Bangun response
    response = {
        "id": application.id,
        "status": application.status,
        "catatan_pelamar": application.catatan_pelamar,
        "applied_at": str(application.applied_at) if application.applied_at else None,
        "updated_at": str(application.updated_at) if application.updated_at else None,
    }

    # Info Job
    if application.job:
        response["job"] = {
            "id": application.job.id,
            "judul_posisi": application.job.judul_posisi,
            "deskripsi_pekerjaan": application.job.deskripsi_pekerjaan,
            "tipe_pekerjaan": application.job.tipe_pekerjaan,
            "lokasi_kerja": application.job.lokasi_kerja,
            "kota": application.job.kota,
            "video_questions_json": application.job.video_questions_json,
            "video_questions": json.loads(application.job.video_questions_json) if (application.job.video_questions_json and application.job.video_questions_json.strip().startswith('[')) else ([q.strip() for q in application.job.video_questions_json.split('\n') if q.strip()] if application.job.video_questions_json else []),
        }
        if application.job.perusahaan:
            response["job"]["perusahaan"] = {
                "nama_perusahaan": application.job.perusahaan.nama_perusahaan,
                "industri": application.job.perusahaan.industri,
                "logo_url": application.job.perusahaan.logo_url,
            }

    # Info Pelamar (hanya untuk perusahaan)
    if role == "perusahaan" and application.pelamar:
        response["pelamar"] = {
            "id": application.pelamar.id,
            "nama_lengkap": application.pelamar.nama_lengkap,
            "no_telepon": application.pelamar.no_telepon,
            "linkedin_url": application.pelamar.linkedin_url,
            "portfolio_url": application.pelamar.portfolio_url,
        }

    # Info CV Document
    if application.cv_document:
        response["cv_document"] = {
            "id": application.cv_document.id,
            "nama_file": application.cv_document.nama_file,
            "file_url": application.cv_document.file_url,
            "file_type": application.cv_document.file_type,
            "file_size_kb": application.cv_document.file_size_kb,
            "email": application.cv_document.email,
            "phone": application.cv_document.phone,
            "pendidikan_tertinggi": application.cv_document.pendidikan_tertinggi,
            "is_ocr_used": application.cv_document.is_ocr_used,
            "extracted_text_preview": (
                application.cv_document.extracted_text[:500] + "..."
                if application.cv_document.extracted_text and len(application.cv_document.extracted_text) > 500
                else application.cv_document.extracted_text
            ),
        }

    # Hasil Analisis AI
    if application.cv_analysis:
        response["analisis_cv"] = {
            "cosine_similarity_score": float(application.cv_analysis.cosine_similarity_score),
            "skor_kecocokan": float(application.cv_analysis.skor_kecocokan),
            "threshold_digunakan": float(application.cv_analysis.threshold_digunakan),
            "kategori": application.cv_analysis.kategori,
            "hasil": application.cv_analysis.hasil,
            "model_ai": application.cv_analysis.model_ai,
            "waktu_proses_ms": application.cv_analysis.waktu_proses_ms,
            "analyzed_at": str(application.cv_analysis.analyzed_at) if application.cv_analysis.analyzed_at else None,
            "hybrid_details": json.loads(application.cv_analysis.detail_analisis) if application.cv_analysis.detail_analisis else None,
        }
        
    if hasattr(application, "ai_result") and application.ai_result:
        response["ai_result"] = application.ai_result
    if hasattr(application, "video_url") and application.video_url:
        response["video_url"] = application.video_url

    return response

class ApplicationStatusUpdate(BaseModel):
    status: str

@router.patch("/{application_id}/status", status_code=status.HTTP_200_OK)
async def update_application_status(
    application_id: str,
    payload: ApplicationStatusUpdate,
    current_user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Mengubah status lamaran (misalnya dari cv_screening ke virtual_interview atau ditolak).
    Hanya bisa dilakukan oleh perusahaan/admin.
    """
    role = current_user.get("role")
    if role not in ["perusahaan", "admin"]:
        raise HTTPException(status_code=403, detail="Hanya perusahaan/admin yang dapat mengubah status")
        
    result = await db.execute(select(Application).where(Application.id == application_id).options(joinedload(Application.job)))
    app_record = result.scalars().first()
    
    if not app_record:
        raise HTTPException(status_code=404, detail="Lamaran tidak ditemukan")
        
    if role == "perusahaan":
        perusahaan_result = await db.execute(select(PerusahaanProfile).where(PerusahaanProfile.user_id == current_user.get("sub")))
        perusahaan = perusahaan_result.scalars().first()
        if not perusahaan or app_record.job.perusahaan_id != perusahaan.id:
            raise HTTPException(status_code=403, detail="Anda tidak memiliki akses ke lamaran ini")

    app_record.status = payload.status
    await db.commit()
    
    return {"message": f"Status berhasil diubah menjadi {payload.status}", "status": payload.status}

import urllib.request
import asyncio
import os
import time
from fastapi import BackgroundTasks, File, UploadFile, HTTPException, Depends, status
from app.core.database import async_session


# Event untuk membangunkan async worker secara instan saat ada tugas baru
worker_wake_event = asyncio.Event()

# In-memory dictionary untuk progress aktif secara real-time
# Menghilangkan beban query database berulang & race condition pada asyncpg saat polling progress
ACTIVE_JOB_PROGRESS = {}

async def update_job(application_id: str, progress: int = None, current_step: str = None, job_status: str = None, error_message: str = None):
    """Memperbarui status VideoAnalysisJob baik di RAM maupun di database."""
    if application_id not in ACTIVE_JOB_PROGRESS:
        ACTIVE_JOB_PROGRESS[application_id] = {}
    if progress is not None:
        ACTIVE_JOB_PROGRESS[application_id]["progress"] = progress
    if current_step is not None:
        ACTIVE_JOB_PROGRESS[application_id]["message"] = current_step
    if job_status is not None:
        ACTIVE_JOB_PROGRESS[application_id]["status"] = job_status
    if error_message is not None:
        ACTIVE_JOB_PROGRESS[application_id]["error"] = error_message

    try:
        async with async_session() as session:
            result = await session.execute(select(VideoAnalysisJob).where(VideoAnalysisJob.application_id == application_id))
            job = result.scalars().first()
            if job:
                if progress is not None:
                    job.progress = progress
                if current_step is not None:
                    job.current_step = current_step
                if job_status is not None:
                    job.status = job_status
                if error_message is not None:
                    job.error_message = error_message
                await session.commit()
    except Exception as e:
        print(f"[ERROR UPDATE JOB DB] {e}")

async def process_video_job(job_id: str, application_id: str):
    """Menjalankan proses analisis video dengan progress tracking yang persisten."""
    print(f"[VIDEO WORKER] Memulai analisis untuk aplikasi: {application_id}")
    temp_video_path = f"temp_videos/analyze_{application_id}.mp4"

    try:
        # 1. Ambil URL video dan pertanyaan lowongan dari database
        async with async_session() as session:
            res = await session.execute(
                select(Application)
                .options(selectinload(Application.job))
                .where(Application.id == application_id)
            )
            app_record = res.scalars().first()
            if not app_record or not app_record.video_url:
                await update_job(application_id, job_status="failed", error_message="Video URL tidak ditemukan", current_step="Gagal: Video tidak ditemukan")
                return
            video_url = app_record.video_url

            pertanyaan_list = []
            if app_record.job and app_record.job.video_questions_json:
                try:
                    parsed_q = json.loads(app_record.job.video_questions_json)
                    if isinstance(parsed_q, list):
                        pertanyaan_list = [str(q).strip() for q in parsed_q if str(q).strip()]
                except Exception:
                    pertanyaan_list = [q.strip() for q in app_record.job.video_questions_json.split('\n') if q.strip()]

            if pertanyaan_list:
                pertanyaan_perusahaan = "\n".join(pertanyaan_list)
            else:
                pertanyaan_perusahaan = "Ceritakan tentang diri Anda, latar belakang pengalaman, dan keahlian utama yang relevan."

        # 2. Update status: Downloading video
        await update_job(application_id, progress=5, job_status="downloading", current_step="Mengunduh video wawancara dari Cloudinary...")
        os.makedirs("temp_videos", exist_ok=True)
        await asyncio.to_thread(urllib.request.urlretrieve, video_url, temp_video_path)

        # 3. Callback untuk melacak progress AI visual & suara langsung di RAM (thread-safe, O(1), no DB collision)
        def progress_cb(pct: int, msg: str):
            if application_id in ACTIVE_JOB_PROGRESS:
                ACTIVE_JOB_PROGRESS[application_id]["progress"] = pct
                ACTIVE_JOB_PROGRESS[application_id]["message"] = msg
                ACTIVE_JOB_PROGRESS[application_id]["status"] = "processing"

        # 4. Jalankan analisis AI nyata di background thread (non-blocking untuk event loop)
        await update_job(application_id, progress=10, job_status="processing", current_step="Memulai analisis AI visual & suara...")
        hasil_ai = await asyncio.to_thread(
            video_ai_service.analisa_video,
            temp_video_path,
            pertanyaan_perusahaan,
            pertanyaan_list=pertanyaan_list,
            progress_callback=progress_cb
        )

        # 5. Cek validitas hasil
        if isinstance(hasil_ai, dict) and hasil_ai.get("status") == "INVALID":
            pesan_error = hasil_ai.get("pesan", "Video tidak memenuhi standar analisis AI.")
            await update_job(application_id, job_status="failed", error_message=pesan_error, current_step=f"Gagal: {pesan_error}")
            return

        # 6. Simpan Hasil Akhir ke Database & Ubah Status Lamaran ke human_validation
        await update_job(application_id, progress=98, current_step="Menyimpan hasil evaluasi AI...")

        async with async_session() as session:
            res = await session.execute(select(Application).where(Application.id == application_id))
            app_to_update = res.scalars().first()
            if app_to_update:
                app_to_update.ai_result = hasil_ai if isinstance(hasil_ai, dict) else {"raw": str(hasil_ai)}
                app_to_update.status = "human_validation"
                await session.commit()

        # 7. Tandai Job Selesai (100%)
        await update_job(application_id, progress=100, job_status="completed", current_step="Analisis video AI selesai!")
        print(f"[VIDEO WORKER] Selesai memproses aplikasi: {application_id}")

    except Exception as e:
        print(f"[ERROR VIDEO WORKER PROCESS] {e}")
        await update_job(application_id, job_status="failed", error_message=str(e), current_step=f"Terjadi kesalahan: {str(e)}")
    finally:
        if os.path.exists(temp_video_path):
            try:
                os.remove(temp_video_path)
            except:
                pass
        # Tunggu beberapa detik sebelum membersihkan cache agar frontend sempat menangkap progress 100%
        await asyncio.sleep(6.0)
        ACTIVE_JOB_PROGRESS.pop(application_id, None)

async def persistent_video_worker():
    """Worker loop asinkron yang mengambil antrean langsung dari database."""
    print("[INFO] Persistent Video Worker telah aktif (Async Loop).")
    while True:
        try:
            # Query job berikutnya yang berstatus queued atau processing (recovery)
            next_job_info = None
            async with async_session() as session:
                result = await session.execute(
                    select(VideoAnalysisJob)
                    .where(VideoAnalysisJob.status.in_(["queued", "processing"]))
                    .order_by(VideoAnalysisJob.created_at.asc())
                )
                job = result.scalars().first()
                if job:
                    next_job_info = (job.id, job.application_id)
                else:
                    # Cek jika ada lamaran dengan status 'video_analysis' yang belum memiliki record job
                    missing_res = await session.execute(
                        select(Application)
                        .outerjoin(VideoAnalysisJob, Application.id == VideoAnalysisJob.application_id)
                        .where(
                            Application.status == "video_analysis",
                            Application.video_url.isnot(None),
                            VideoAnalysisJob.id.is_(None)
                        )
                    )
                    missing_app = missing_res.scalars().first()
                    if missing_app:
                        new_job = VideoAnalysisJob(
                            application_id=missing_app.id,
                            status="queued",
                            progress=0,
                            current_step="Menunggu antrean pemrosesan AI...",
                        )
                        session.add(new_job)
                        await session.commit()
                        next_job_info = (new_job.id, new_job.application_id)

            if next_job_info:
                job_id, app_id = next_job_info
                await process_video_job(job_id, app_id)
            else:
                # Tunggu sinyal job baru atau timeout 3 detik
                try:
                    await asyncio.wait_for(worker_wake_event.wait(), timeout=3.0)
                    worker_wake_event.clear()
                except asyncio.TimeoutError:
                    pass
        except asyncio.CancelledError:
            print("[INFO] Persistent Video Worker dihentikan.")
            break
        except Exception as e:
            print(f"[ERROR PERSISTENT WORKER LOOP] {e}")
            await asyncio.sleep(2.0)

@router.post("/{application_id}/upload-video")
async def upload_interview_video(
    application_id: str,
    video: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if not video.filename.endswith(".mp4"):
        raise HTTPException(status_code=400, detail="Hanya format .mp4 yang diizinkan.")

    try:
        result = await db.execute(select(Application).where(Application.id == application_id))
        app_data = result.scalars().first()
        if app_data:
            if app_data.video_url or app_data.status == "video_analysis":
                raise HTTPException(status_code=400, detail="Anda sudah mengunggah video. Proses ini hanya dapat dilakukan satu kali.")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        print(f"Error checking application data: {e}")

    temp_dir = "temp_videos"
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, video.filename)

    import shutil
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)

    try:
        import cloudinary.uploader
        upload_result = cloudinary.uploader.upload(
            temp_path, 
            resource_type="video",
            folder="ai_recruit_interviews"
        )
        video_url = upload_result.get("secure_url")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengunggah video ke Cloudinary: {e}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    try:
        result = await db.execute(select(Application).where(Application.id == application_id))
        app_record = result.scalars().first()
        if app_record:
            app_record.status = "video_analysis"
            app_record.video_url = video_url

            # Otomatis daftarkan ke antrean pemrosesan AI persisten
            job_result = await db.execute(select(VideoAnalysisJob).where(VideoAnalysisJob.application_id == application_id))
            existing_job = job_result.scalars().first()
            if existing_job:
                existing_job.status = "queued"
                existing_job.progress = 0
                existing_job.current_step = "Menunggu antrean pemrosesan AI..."
                existing_job.error_message = None
            else:
                new_job = VideoAnalysisJob(
                    application_id=application_id,
                    status="queued",
                    progress=0,
                    current_step="Menunggu antrean pemrosesan AI...",
                )
                db.add(new_job)

            await db.commit()
            worker_wake_event.set()
    except Exception as e:
        print(f"Gagal update status via SQLAlchemy: {e}")

    return {
        "status": "success",
        "message": "Video Wawancara Berhasil Disimpan. Terima kasih telah menyelesaikan tahap ini. Rekaman Anda telah diterima oleh sistem dan sedang menunggu peninjauan lebih lanjut oleh HRD. Anda dapat menutup halaman ini dengan aman."
    }

@router.post("/{application_id}/analyze-video")
async def analyze_interview_video(
    application_id: str,
    db: AsyncSession = Depends(get_db)
):
    # Dapatkan URL video dari Database
    result = await db.execute(select(Application).where(Application.id == application_id))
    app_data = result.scalars().first()
    
    if not app_data or not app_data.video_url:
        raise HTTPException(status_code=400, detail="Video tidak ditemukan untuk kandidat ini.")
    
    # Masukkan atau perbarui antrean persisten di database
    job_result = await db.execute(select(VideoAnalysisJob).where(VideoAnalysisJob.application_id == application_id))
    existing_job = job_result.scalars().first()
    
    if existing_job:
        existing_job.status = "queued"
        existing_job.progress = 0
        existing_job.current_step = "Menunggu antrean pemrosesan AI..."
        existing_job.error_message = None
    else:
        new_job = VideoAnalysisJob(
            application_id=application_id,
            status="queued",
            progress=0,
            current_step="Menunggu antrean pemrosesan AI...",
        )
        db.add(new_job)

    # Pastikan status lamaran adalah video_analysis
    app_data.status = "video_analysis"
    await db.commit()

    # Bangunkan worker
    worker_wake_event.set()

    return {"status": "success", "message": "Proses analisis AI video berhasil dimasukkan ke antrean persisten."}

@router.get("/{application_id}/video-progress")
async def get_video_analysis_progress(
    application_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint khusus untuk memantau progress nyata pemrosesan video AI kandidat.
    """
    # 1. Cek in-memory progress terlebih dahulu (jika sedang aktif diproses)
    if application_id in ACTIVE_JOB_PROGRESS:
        cached = ACTIVE_JOB_PROGRESS[application_id]
        return {
            "application_id": application_id,
            "status": cached.get("status", "processing"),
            "progress": cached.get("progress", 0),
            "message": cached.get("message", "Memproses video..."),
            "error": cached.get("error"),
            "updated_at": None
        }

    # 2. Jika tidak ada di cache aktif, ambil dari database
    result = await db.execute(select(VideoAnalysisJob).where(VideoAnalysisJob.application_id == application_id))
    job = result.scalars().first()

    if job:
        return {
            "application_id": application_id,
            "status": job.status,
            "progress": job.progress,
            "message": job.current_step,
            "error": job.error_message,
            "updated_at": str(job.updated_at) if job.updated_at else None
        }

    # Jika job belum dibuat di tabel, periksa apakah lamaran sudah selesai sebelumnya
    app_result = await db.execute(select(Application).where(Application.id == application_id))
    app_record = app_result.scalars().first()

    if app_record and app_record.status == "human_validation":
        return {
            "application_id": application_id,
            "status": "completed",
            "progress": 100,
            "message": "Analisis AI selesai",
            "error": None
        }

    return {
        "application_id": application_id,
        "status": "idle",
        "progress": 0,
        "message": "Belum ada analisis video yang berjalan",
        "error": None
    }
