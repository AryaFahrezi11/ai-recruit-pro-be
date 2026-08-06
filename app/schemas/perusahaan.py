from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict

class PerusahaanSettingsUpdate(BaseModel):
    # Profile
    nama_perusahaan: Optional[str] = None
    industri: Optional[str] = None
    ukuran: Optional[str] = None
    website_url: Optional[str] = None
    deskripsi: Optional[str] = None

    # AI Settings
    ai_default_threshold: Optional[int] = None
    auto_invite_interview: Optional[bool] = None
    auto_archive_rejected: Optional[bool] = None
    video_weights_json: Optional[str] = None
    
    # Email Templates
    email_invitation_subject: Optional[str] = None
    email_invitation_body: Optional[str] = None
    email_hire_subject: Optional[str] = None
