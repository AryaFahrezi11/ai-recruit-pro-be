from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import os
import uuid
import shutil
from app.core.database import get_db
from app.core.security import verify_token
from app.schemas.perusahaan import PerusahaanSettingsUpdate
from app.services.perusahaan_service import PerusahaanService
from app.models.user import PerusahaanProfile

router = APIRouter()

async def verify_perusahaan(current_user: dict = Depends(verify_token)):
    if current_user.get("role") != "perusahaan":
        raise HTTPException(status_code=403, detail="Akses ditolak. Bukan akun perusahaan.")
    return current_user

@router.get("/settings")
async def get_perusahaan_settings(current_user: dict = Depends(verify_perusahaan), db: AsyncSession = Depends(get_db)):
    service = PerusahaanService(db)
    return await service.get_settings(current_user["sub"])

@router.put("/settings")
async def update_perusahaan_settings(req: PerusahaanSettingsUpdate, current_user: dict = Depends(verify_perusahaan), db: AsyncSession = Depends(get_db)):
    service = PerusahaanService(db)
    return await service.update_settings(current_user["sub"], req)

@router.post("/settings/logo")
async def upload_company_logo(file: UploadFile = File(...), current_user: dict = Depends(verify_perusahaan), db: AsyncSession = Depends(get_db)):
    # Validasi format file (hanya gambar)
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Format file tidak didukung. Harap upload gambar (JPG, PNG, WEBP).")

    # Ambil ekstensi dan buat nama file baru
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    filename = f"logo_{current_user['sub']}_{uuid.uuid4().hex[:8]}.{ext}"
    
    # Simpan ke folder uploads
    filepath = os.path.join("uploads", filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    logo_url = f"/uploads/{filename}"

    # Simpan ke database
    result = await db.execute(select(PerusahaanProfile).where(PerusahaanProfile.user_id == current_user["sub"]))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profil Perusahaan tidak ditemukan")
        
    profile.logo_url = logo_url
    await db.commit()
    
    return {"status": "success", "logo_url": logo_url}


@router.get("/verified")
async def get_verified_companies_public(db: AsyncSession = Depends(get_db)):
    """Mendapatkan daftar perusahaan terverifikasi untuk halaman utama (publik)."""
    service = PerusahaanService(db)
    return await service.get_verified_companies_public()

@router.get("/{company_id}")
async def get_company_profile(company_id: str, db: AsyncSession = Depends(get_db)):
    """Mendapatkan profil publik perusahaan beserta loker aktifnya."""
    service = PerusahaanService(db)
    return await service.get_company_profile(company_id)


from fastapi import Body
from app.services.email_service import send_rendered_email

@router.post("/settings/test-email")
async def test_perusahaan_email(
    payload: dict = Body(...),
    current_user: dict = Depends(verify_perusahaan),
    db: AsyncSession = Depends(get_db)
):
    recipient = payload.get("recipient", "").strip()
    subject = payload.get("subject", "Uji Coba Email Perusahaan").strip()
    body = payload.get("body", "Halo, ini adalah email uji coba dari template pesan perusahaan.").strip()
    
    if not recipient:
        raise HTTPException(status_code=400, detail="Alamat email penerima wajib diisi")
        
    success = await send_rendered_email(db, recipient=recipient, subject=subject, body=body)
    if success:
        return {"status": "success", "message": f"Email uji coba berhasil dikirim ke {recipient}"}
    else:
        return {"status": "warning", "message": "Konfigurasi SMTP belum aktif atau pengiriman gagal. Silakan periksa pengaturan SMTP admin."}
