"""
🛣️ Users Router
Endpoint: GET /api/users/profile, PUT /api/users/profile, POST /api/users/cv/upload
"""
from fastapi import APIRouter, Body, Depends, HTTPException, status, UploadFile, File, Form
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
            "tanggal_lahir": str(p.tanggal_lahir) if p.tanggal_lahir else None,
            "jenis_kelamin": p.jenis_kelamin,
            "alamat": p.alamat,
            "kota": p.kota,
            "provinsi": p.provinsi,
            "pendidikan_terakhir": p.pendidikan_terakhir,
            "institusi_pendidikan": p.institusi_pendidikan,
            "jurusan": p.jurusan,
            "tahun_lulus": p.tahun_lulus,
            "ipk": float(p.ipk) if p.ipk else None,
            "ringkasan_diri": p.ringkasan_diri,
            "linkedin_url": p.linkedin_url,
            "portfolio_url": p.portfolio_url,
            "judul_posisi": p.judul_posisi,
            "keahlian": p.keahlian,
            "sertifikasi": p.sertifikasi,
            "pengalaman_kerja": p.pengalaman_kerja,
            "riwayat_pendidikan": p.riwayat_pendidikan,
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
    update_data: dict = Body(...),
    current_user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Mengupdate profil user yang sedang login di database PostgreSQL.
    Mendukung role pelamar, perusahaan, dan kampus.
    """
    user_id = current_user.get("sub")
    role = current_user.get("role")

    # Fetch User
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User tidak ditemukan",
        )

    # Update User base fields if provided
    if "avatar_url" in update_data and update_data["avatar_url"] is not None:
        user.avatar_url = update_data["avatar_url"]

    # Update role-specific profile
    if role == "pelamar":
        res_p = await db.execute(
            select(PelamarProfile).where(PelamarProfile.user_id == user_id)
        )
        profile = res_p.scalars().first()

        if not profile:
            profile = PelamarProfile(
                user_id=user_id,
                nama_lengkap=update_data.get("nama_lengkap") or user.email.split("@")[0]
            )
            db.add(profile)

        pelamar_fields = [
            "nama_lengkap", "no_telepon", "tanggal_lahir", "jenis_kelamin",
            "alamat", "kota", "provinsi", "pendidikan_terakhir",
            "institusi_pendidikan", "jurusan", "tahun_lulus", "ipk",
            "ringkasan_diri", "linkedin_url", "portfolio_url",
            "judul_posisi", "keahlian", "sertifikasi", "pengalaman_kerja", "riwayat_pendidikan"
        ]
        for key in pelamar_fields:
            if key in update_data and update_data[key] is not None:
                val = update_data[key]
                if isinstance(val, (list, dict)):
                    val = json.dumps(val)
                setattr(profile, key, val)

    elif role == "perusahaan":
        result = await db.execute(
            select(PerusahaanProfile).where(PerusahaanProfile.user_id == user_id)
        )
        profile = result.scalars().first()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profil perusahaan tidak ditemukan",
            )

        valid_fields = PerusahaanProfileUpdate.model_fields.keys()
        for key, value in update_data.items():
            if key in valid_fields:
                setattr(profile, key, value)

    elif role == "kampus":
        res_k = await db.execute(
            select(KampusProfile).where(KampusProfile.user_id == user_id)
        )
        profile = res_k.scalars().first()

        if not profile:
            profile = KampusProfile(
                user_id=user_id,
                nama_kampus=update_data.get("nama_kampus") or "Kampus"
            )
            db.add(profile)

        kampus_fields = [
            "nama_kampus", "jenis", "alamat", "kota", "provinsi",
            "website_url", "logo_url", "akreditasi", "nama_pic",
            "jabatan_pic", "no_telepon_pic"
        ]
        for key in kampus_fields:
            if key in update_data and update_data[key] is not None:
                setattr(profile, key, update_data[key])

    await db.commit()
    return {"message": "CV Berhasil Disimpan", "status": "success", "role": role}


@router.post("/cv/upload")
async def upload_cv_document(
    cv_file: UploadFile = File(...),
    current_user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
):
    """
    Mengunggah berkas CV PDF pelamar dan menyimpannya ke tabel database cv_documents.
    """
    user_id = current_user.get("sub")
    role = current_user.get("role")

    if role != "pelamar":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya pelamar yang dapat mengunggah berkas CV",
        )

    # Get PelamarProfile
    res = await db.execute(select(PelamarProfile).where(PelamarProfile.user_id == user_id))
    profile = res.scalars().first()

    if not profile:
        profile = PelamarProfile(
            user_id=user_id,
            nama_lengkap=current_user.get("email", "").split("@")[0] or "Pelamar"
        )
        db.add(profile)
        await db.flush()

    # Save PDF file to /uploads directory
    os.makedirs("uploads", exist_ok=True)
    ext = cv_file.filename.split(".")[-1] if "." in cv_file.filename else "pdf"
    filename = f"cv_{uuid.uuid4()}.{ext}"
    filepath = os.path.join("uploads", filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(cv_file.file, buffer)

    file_url = f"/uploads/{filename}"
    file_size_kb = int(os.path.getsize(filepath) / 1024) if os.path.exists(filepath) else 0

    # Save to cv_documents database table
    cv_doc = CVDocument(
        pelamar_id=profile.id,
        nama_file=cv_file.filename,
        file_url=file_url,
        file_type=ext.lower(),
        file_size_kb=file_size_kb,
        extracted_text=f"File CV: {cv_file.filename}"
    )
    db.add(cv_doc)
    await db.commit()
    await db.refresh(cv_doc)

    return {
        "message": "CV Berhasil Disimpan",
        "status": "success",
        "cv_id": cv_doc.id,
        "nama_file": cv_doc.nama_file,
        "file_url": cv_doc.file_url
    }
