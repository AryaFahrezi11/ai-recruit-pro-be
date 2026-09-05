from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict

class PerusahaanSettingsUpdate(BaseModel):
    # Profile
    nama_perusahaan: Optional[str] = None
    industri: Optional[str] = None
    ukuran: Optional[str] = None
    website_url: Optional[str] = None
    deskripsi: Optional[str] = None
    alamat: Optional[str] = None
    kota: Optional[str] = None
    provinsi: Optional[str] = None
    no_telepon: Optional[str] = None
    tahun_berdiri: Optional[int] = None
    hr_name: Optional[str] = None
    hr_whatsapp: Optional[str] = None
    hr_position: Optional[str] = None

    # AI Settings (Optional, frontend may stop sending these)
    ai_default_threshold: Optional[int] = None
    auto_invite_interview: Optional[bool] = None
    auto_archive_rejected: Optional[bool] = None
    video_weights_json: Optional[str] = None
    
    # Email Templates
    email_invitation_subject: Optional[str] = None
    email_invitation_body: Optional[str] = None
    email_hire_subject: Optional[str] = None
    email_hire_body: Optional[str] = None
    email_reject_subject: Optional[str] = None
    email_reject_body: Optional[str] = None
    email_interview_user_subject: Optional[str] = None
    email_interview_user_body: Optional[str] = None
