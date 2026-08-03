"""
🛣️ Users Router
Endpoint: GET /api/users/profile, PUT /api/users/profile
"""
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import verify_token
from app.models.user import User, PelamarProfile, PerusahaanProfile, KampusProfile
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
    Mengupdate profil user yang sedang login.
    Field yang dikirim akan diupdate, field yang tidak dikirim tidak berubah.
    """
    user_id = current_user.get("sub")
    role = current_user.get("role")

    # Update field user dasar (avatar_url)
    user_fields = {}
    if "avatar_url" in update_data:
        user_fields["avatar_url"] = update_data.pop("avatar_url")

    if user_fields:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User tidak ditemukan",
            )
        for key, value in user_fields.items():
            setattr(user, key, value)

    # Update profil spesifik berdasarkan role
    if role == "pelamar":
        result = await db.execute(
            select(PelamarProfile).where(PelamarProfile.user_id == user_id)
        )
        profile = result.scalars().first()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profil pelamar tidak ditemukan",
            )

        # Validasi dengan schema
        valid_fields = PelamarProfileUpdate.model_fields.keys()
        for key, value in update_data.items():
            if key in valid_fields:
                setattr(profile, key, value)

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
        result = await db.execute(
            select(KampusProfile).where(KampusProfile.user_id == user_id)
        )
        profile = result.scalars().first()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profil kampus tidak ditemukan",
            )

        # Kampus fields - update langsung
        kampus_fields = [
            "nama_kampus", "jenis", "alamat", "kota", "provinsi",
            "website_url", "logo_url", "akreditasi", "nama_pic",
            "jabatan_pic", "no_telepon_pic",
        ]
        for key, value in update_data.items():
            if key in kampus_fields:
                setattr(profile, key, value)

    return {"message": "Profil berhasil diupdate", "role": role}
