"""
🛣️ Applications Router
Endpoint: /api/applications
Proses melamar kerja dengan upload CV, analisis AI, dan penyimpanan ke database.
"""
import os
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import PelamarProfile, PerusahaanProfile
from app.models.job import JobPosting
from app.models.application import CVDocument, Application
from app.models.analysis import CVAnalysisResult
from app.services.cv_analysis_service import CVAnalysisService
from app.utils.pdf_extractor import clean_text

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
                }
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
                selectinload(Application.pelamar),
                selectinload(Application.job),
                selectinload(Application.cv_analysis),
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
                    "pendidikan_terakhir": app.pelamar.pendidikan_terakhir,
                    "institusi_pendidikan": app.pelamar.institusi_pendidikan,
                }
            if app.job:
                app_dict["job"] = {
                    "id": app.job.id,
                    "judul_posisi": app.job.judul_posisi,
                }
            if app.cv_analysis:
                app_dict["analisis_cv"] = {
                    "skor_kecocokan": float(app.cv_analysis.skor_kecocokan),
                    "kategori": app.cv_analysis.kategori,
                    "hasil": app.cv_analysis.hasil,
                }
            data.append(app_dict)

        return {"message": "Daftar lamaran masuk", "total": len(data), "data": data}

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Role Anda tidak memiliki akses ke daftar lamaran",
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_application(
    request: Request,
    job_id: str = Form(..., description="ID lowongan kerja yang dilamar"),
    catatan_pelamar: str = Form(default=None, description="Catatan tambahan dari pelamar"),
    file: UploadFile = File(..., description="File CV (PDF atau TXT)"),
    current_user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Pelamar melamar ke suatu posisi dengan mengupload CV.
    Sistem akan otomatis:
    1. Menyimpan file CV
    2. Mengekstrak teks dari CV
    3. Menganalisis kecocokan CV dengan Job Description (AI)
    4. Menentukan status awal lamaran berdasarkan skor AI
    """
    # Validasi role
    if current_user.get("role") != "pelamar":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya akun pelamar yang bisa melamar pekerjaan",
        )

    user_id = current_user.get("sub")

    # Cari profil pelamar
    result = await db.execute(
        select(PelamarProfile).where(PelamarProfile.user_id == user_id)
    )
    pelamar = result.scalars().first()

    if not pelamar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profil pelamar tidak ditemukan. Silakan lengkapi profil terlebih dahulu.",
        )

    # Cari lowongan kerja
    result = await db.execute(
        select(JobPosting).where(
            JobPosting.id == job_id,
            JobPosting.status == "active",
        )
    )
    job = result.scalars().first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lowongan kerja tidak ditemukan atau sudah ditutup",
        )

    # Cek apakah sudah pernah melamar ke lowongan ini
    result = await db.execute(
        select(Application).where(
            Application.pelamar_id == pelamar.id,
            Application.job_id == job_id,
        )
    )
    existing = result.scalars().first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Anda sudah pernah melamar ke lowongan ini",
        )

    # Validasi tipe file
    allowed_types = ["application/pdf", "text/plain"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipe file '{file.content_type}' tidak didukung. Gunakan PDF atau TXT.",
        )

    # Baca file
    file_content = await file.read()
    file_size_kb = len(file_content) // 1024
    file_type = "pdf" if file.content_type == "application/pdf" else "txt"

    # Simpan file ke disk
    file_ext = "pdf" if file_type == "pdf" else "txt"
    saved_filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, saved_filename)

    with open(file_path, "wb") as f:
        f.write(file_content)

    file_url = f"/uploads/{saved_filename}"

    # Jalankan analisis AI
    embedding_service = request.app.state.embedding_service
    cv_service = CVAnalysisService(embedding_service)

    try:
        analysis_result = await cv_service.process_cv_file(
            file_content=file_content,
            file_type=file_type,
            job_description=job.deskripsi_pekerjaan,
            threshold=float(job.cv_threshold) if job.cv_threshold else None,
        )
    except ValueError as e:
        # Hapus file yang sudah disimpan jika analisis gagal
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    extracted_text = analysis_result.get("extracted_text", "")
    cleaned_text_val = analysis_result.get("cleaned_text", "")
    cv_embedding = analysis_result.get("cv_embedding", [])

    # 1. Simpan CVDocument
    cv_doc = CVDocument(
        pelamar_id=pelamar.id,
        nama_file=file.filename or saved_filename,
        file_url=file_url,
        file_type=file_type,
        file_size_kb=file_size_kb,
        extracted_text=extracted_text,
        cleaned_text=cleaned_text_val,
        embedding_vector=json.dumps(cv_embedding) if cv_embedding else None,
    )
    db.add(cv_doc)
    await db.flush()

    # 2. Simpan Application
    # Tentukan status awal berdasarkan hasil analisis
    skor = analysis_result.get("skor_kecocokan", 0)
    threshold = analysis_result.get("threshold_digunakan", 40.0)
    initial_status = "lolos_cv" if skor >= threshold else "gagal_cv"

    application = Application(
        pelamar_id=pelamar.id,
        job_id=job_id,
        cv_document_id=cv_doc.id,
        status=initial_status,
        catatan_pelamar=catatan_pelamar,
    )
    db.add(application)
    await db.flush()

    # 3. Simpan CVAnalysisResult
    cv_analysis = CVAnalysisResult(
        application_id=application.id,
        cv_document_id=cv_doc.id,
        job_id=job_id,
        cosine_similarity_score=analysis_result.get("cosine_similarity_score", 0),
        skor_kecocokan=skor,
        threshold_digunakan=threshold,
        kategori=analysis_result.get("kategori", "tidak_cocok"),
        hasil=analysis_result.get("hasil", "gagal"),
        model_ai=analysis_result.get("model_ai", ""),
        waktu_proses_ms=int(analysis_result.get("waktu_proses_ms", 0)),
    )
    db.add(cv_analysis)

    return {
        "message": "Lamaran berhasil dikirim dan CV berhasil dianalisis",
        "data": {
            "application_id": application.id,
            "job_id": job_id,
            "status": initial_status,
            "cv_document_id": cv_doc.id,
            "analisis_cv": {
                "cosine_similarity_score": analysis_result.get("cosine_similarity_score"),
                "skor_kecocokan": skor,
                "threshold_digunakan": threshold,
                "kategori": analysis_result.get("kategori"),
                "hasil": analysis_result.get("hasil"),
                "model_ai": analysis_result.get("model_ai"),
                "waktu_proses_ms": analysis_result.get("waktu_proses_ms"),
            },
        },
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
            "pendidikan_terakhir": application.pelamar.pendidikan_terakhir,
            "institusi_pendidikan": application.pelamar.institusi_pendidikan,
            "jurusan": application.pelamar.jurusan,
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
        }

    return response
