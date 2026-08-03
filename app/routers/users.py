from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import os
import uuid
import shutil

from app.core.security import verify_token
from app.core.database import get_db
from app.models.user import User, PelamarProfile, PerusahaanProfile, KampusProfile
from app.schemas.user import PelamarProfileUpdate, PerusahaanProfileUpdate
from pydantic import BaseModel
from typing import Union, Optional

router = APIRouter()

class ProfileUpdateRequest(BaseModel):
    # This is a generic request schema that can accept fields for any profile type
    nama_perusahaan: str | None = None
    alamat: str | None = None
    no_telepon: str | None = None
    # Add more fields as needed

@router.get("/profile")
async def get_profile(current_user: dict = Depends(verify_token)):
    """
    Mendapatkan profil user yang sedang login.
    """
    return {
        "user_id": current_user.get("sub"),
        "role": current_user.get("role"),
        "message": "Endpoint profil - akan diimplementasi penuh nanti"
    }

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
    """
    Mengupdate profil user yang sedang login menggunakan FormData.
    """
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
