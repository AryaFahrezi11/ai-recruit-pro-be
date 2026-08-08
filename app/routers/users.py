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
    nama_perusahaan: Optional[str] = Form(None),
    industri: Optional[str] = Form(None),
    ukuran: Optional[str] = Form(None),
    website_url: Optional[str] = Form(None),
    alamat: Optional[str] = Form(None),
    no_telepon: Optional[str] = Form(None),
    nib_number: Optional[str] = Form(None),
    hr_name: Optional[str] = Form(None),
    hr_whatsapp: Optional[str] = Form(None),
    hr_position: Optional[str] = Form(None),
    nib_file: Optional[UploadFile] = File(None),
    id_card_file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    user_id = current_user.get("sub")
    role = current_user.get("role")

    if role == "perusahaan":
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

        if nama_perusahaan is not None: profile.nama_perusahaan = nama_perusahaan
        if industri is not None: profile.industri = industri
        if ukuran is not None: profile.ukuran = ukuran
        if website_url is not None: profile.website_url = website_url
        if alamat is not None: profile.alamat = alamat
        if no_telepon is not None: profile.no_telepon = no_telepon
        if nib_number is not None: profile.nib_number = nib_number
        if hr_name is not None: profile.hr_name = hr_name
        if hr_whatsapp is not None: profile.hr_whatsapp = hr_whatsapp
        if hr_position is not None: profile.hr_position = hr_position
        
        if nib_file is not None:
            profile.nib_document_url = save_upload(nib_file)
            
        if id_card_file is not None:
            profile.hr_id_card_url = save_upload(id_card_file)
            
        await db.commit()
        return {"message": "Profil perusahaan berhasil diupdate"}
        
    return {"message": "Role tidak didukung untuk update saat ini"}
