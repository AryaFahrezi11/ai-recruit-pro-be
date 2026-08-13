"""
🛣️ Users Router
Endpoint: GET /api/users/profile, PUT /api/users/profile, POST /api/users/cv/upload
"""
from starlette.concurrency import run_in_threadpool
from app.utils.pdf_extractor import clean_text
from fastapi import APIRouter, Body, Depends, HTTPException, status, UploadFile, File, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Optional
import os
import uuid
import shutil
import json

from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User, PelamarProfile, PerusahaanProfile, KampusProfile
from app.models.application import CVDocument
from app.schemas.user import PelamarProfileUpdate, PerusahaanProfileUpdate

router = APIRouter()


@router.get("/profile")
async def get_profile(
    current_user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Mendapatkan profil user yang sedang login.
    Mengembalikan data user beserta profil spesifik sesuai role.
    """
    user_id = current_user.get("sub")
    role = current_user.get("role")

    # Query user dari database
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.pelamar_profile),
            selectinload(User.perusahaan_profile),
            selectinload(User.kampus_profile),
        )
        .where(User.id == user_id)
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User tidak ditemukan",
        )

    # Base response
    response = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "avatar_url": user.avatar_url,
        "email_verified_at": str(user.email_verified_at) if user.email_verified_at else None,
        "created_at": str(user.created_at) if user.created_at else None,
    }

    # Tambahkan profil spesifik sesuai role
    if role == "pelamar" and user.pelamar_profile:
        p = user.pelamar_profile
        response["profil"] = {
            "id": p.id,
            "nama_lengkap": p.nama_lengkap,
            "no_telepon": p.no_telepon,
            "alamat": p.alamat,
            "ringkasan_diri": p.ringkasan_diri,
            "linkedin_url": p.linkedin_url,
            "portfolio_url": p.portfolio_url,
            "judul_posisi": p.judul_posisi,
            "keahlian": p.keahlian,
            "sertifikasi": p.sertifikasi,
            "pengalaman_kerja": p.pengalaman_kerja,
            "riwayat_pendidikan": p.riwayat_pendidikan,
            "social_links": p.social_links,
        }
    elif role == "perusahaan" and user.perusahaan_profile:
        c = user.perusahaan_profile
        response["profil"] = {
            "id": c.id,
            "nama_perusahaan": c.nama_perusahaan,
            "industri": c.industri,
            "ukuran": c.ukuran,
            "deskripsi": c.deskripsi,
            "alamat": c.alamat,
            "kota": c.kota,
            "provinsi": c.provinsi,
            "website_url": c.website_url,
            "logo_url": c.logo_url,
            "no_telepon": c.no_telepon,
            "tahun_berdiri": c.tahun_berdiri,
            "nib_number": c.nib_number,
            "hr_name": c.hr_name,
            "hr_whatsapp": c.hr_whatsapp,
            "hr_position": c.hr_position,
        }
    elif role == "kampus" and user.kampus_profile:
        k = user.kampus_profile
        response["profil"] = {
            "id": k.id,
            "nama_kampus": k.nama_kampus,
            "jenis": k.jenis,
            "alamat": k.alamat,
            "kota": k.kota,
            "provinsi": k.provinsi,
            "website_url": k.website_url,
            "logo_url": k.logo_url,
            "akreditasi": k.akreditasi,
            "nama_pic": k.nama_pic,
            "jabatan_pic": k.jabatan_pic,
            "no_telepon_pic": k.no_telepon_pic,
        }
    else:
        response["profil"] = None

    return response


@router.put("/profile")
async def update_profile(
    request: Request,
    current_user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    user_id = current_user.get("sub")
    role = current_user.get("role")
    content_type = request.headers.get("content-type", "")

    if role == "pelamar":
        result = await db.execute(select(PelamarProfile).where(PelamarProfile.user_id == user_id))
        profile = result.scalars().first()

        if not profile:
            profile = PelamarProfile(user_id=user_id, nama_lengkap="Pelamar")
            db.add(profile)
            await db.flush()

        try:
            data = await request.json()
        except Exception:
            data = {}

        if "nama_lengkap" in data and data["nama_lengkap"] is not None: profile.nama_lengkap = data["nama_lengkap"]
        if "judul_posisi" in data and data["judul_posisi"] is not None: profile.judul_posisi = data["judul_posisi"]
        if "no_telepon" in data and data["no_telepon"] is not None: profile.no_telepon = data["no_telepon"]
        if "alamat" in data and data["alamat"] is not None: profile.alamat = data["alamat"]
        if "linkedin_url" in data and data["linkedin_url"] is not None:
            profile.linkedin_url = str(data["linkedin_url"]) if not isinstance(data["linkedin_url"], str) else data["linkedin_url"]
        if "portfolio_url" in data and data["portfolio_url"] is not None:
            profile.portfolio_url = str(data["portfolio_url"])
        if "ringkasan_diri" in data and data["ringkasan_diri"] is not None: profile.ringkasan_diri = data["ringkasan_diri"]
        if "pengalaman_kerja" in data and data["pengalaman_kerja"] is not None:
            profile.pengalaman_kerja = json.dumps(data["pengalaman_kerja"]) if isinstance(data["pengalaman_kerja"], (list, dict)) else str(data["pengalaman_kerja"])
        if "riwayat_pendidikan" in data and data["riwayat_pendidikan"] is not None:
            profile.riwayat_pendidikan = json.dumps(data["riwayat_pendidikan"]) if isinstance(data["riwayat_pendidikan"], (list, dict)) else str(data["riwayat_pendidikan"])
        if "keahlian" in data and data["keahlian"] is not None: profile.keahlian = data["keahlian"]
        if "sertifikasi" in data and data["sertifikasi"] is not None: profile.sertifikasi = data["sertifikasi"]
        if "social_links" in data and data["social_links"] is not None:
            profile.social_links = json.dumps(data["social_links"]) if isinstance(data["social_links"], (list, dict)) else str(data["social_links"])

        await db.commit()
        await db.refresh(profile)

        # --- PRE-COMPUTE CV EMBEDDING ---
        cv_text_parts = [
            f"Nama: {profile.nama_lengkap or ''}",
            f"Posisi/Jabatan: {profile.judul_posisi or ''}",
            f"Deskripsi Diri: {profile.ringkasan_diri or ''}",
            f"Keahlian (Skills): {profile.keahlian or ''}",
            f"Pengalaman Kerja:\n{profile.pengalaman_kerja or ''}",
            f"Pendidikan:\n{profile.riwayat_pendidikan or ''}"
        ]
        cv_text = "\n".join(cv_text_parts)
        
        try:
            embedding_service = request.app.state.embedding_service
            cv_embedding = await run_in_threadpool(embedding_service.get_embedding, cv_text)
            
            cv_doc = CVDocument(
                pelamar_id=profile.id,
                nama_file="Profil_CV_Dashboard.json",
                file_url="profil-dashboard",
                file_type="json",
                file_size_kb=len(cv_text) // 1024,
                extracted_text=cv_text,
                cleaned_text=clean_text(cv_text),
                embedding_vector=json.dumps(cv_embedding)
            )
            db.add(cv_doc)
            await db.commit()
        except Exception as e:
            print("Failed to generate embedding on profile update:", e)
        # ---------------------------------

        return {"message": "Profil pelamar berhasil disimpan ke database"}

    elif role == "perusahaan":
        result = await db.execute(select(PerusahaanProfile).where(PerusahaanProfile.user_id == user_id))
        profile = result.scalars().first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profil tidak ditemukan")
        
        # Helper function to save file
        def save_upload(file_upload: UploadFile) -> str:
            ext = file_upload.filename.split('.')[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            os.makedirs("uploads", exist_ok=True)
            filepath = os.path.join("uploads", filename)
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(file_upload.file, buffer)
            return f"/uploads/{filename}"

        if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
            form = await request.form()
            if "nama_perusahaan" in form: profile.nama_perusahaan = str(form["nama_perusahaan"])
            if "industri" in form: profile.industri = str(form["industri"])
            if "ukuran" in form: profile.ukuran = str(form["ukuran"])
            if "website_url" in form: profile.website_url = str(form["website_url"])
            if "alamat" in form: profile.alamat = str(form["alamat"])
            if "no_telepon" in form: profile.no_telepon = str(form["no_telepon"])
            if "nib_number" in form: profile.nib_number = str(form["nib_number"])
            if "hr_name" in form: profile.hr_name = str(form["hr_name"])
            if "hr_whatsapp" in form: profile.hr_whatsapp = str(form["hr_whatsapp"])
            if "hr_position" in form: profile.hr_position = str(form["hr_position"])
            
            if "nib_file" in form and hasattr(form["nib_file"], "filename"):
                profile.nib_document_url = save_upload(form["nib_file"])  # type: ignore
                
            if "id_card_file" in form and hasattr(form["id_card_file"], "filename"):
                profile.hr_id_card_url = save_upload(form["id_card_file"])  # type: ignore
        else:
            try:
                data = await request.json()
                for key, value in data.items():
                    if hasattr(profile, key) and value is not None:
                        setattr(profile, key, value)
            except Exception:
                pass
            
        await db.commit()
        return {"message": "Profil perusahaan berhasil diupdate"}
        
    return {"message": "Role tidak didukung untuk update saat ini"}
