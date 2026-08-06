from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from app.models.user import PerusahaanProfile, PerusahaanSettings
from app.schemas.perusahaan import PerusahaanSettingsUpdate

class PerusahaanService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_settings(self, user_id: str):
        # Ambil Profil
        profile_result = await self.db.execute(select(PerusahaanProfile).where(PerusahaanProfile.user_id == user_id))
        profile = profile_result.scalars().first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profil Perusahaan tidak ditemukan")

        # Ambil Settings
        settings_result = await self.db.execute(select(PerusahaanSettings).where(PerusahaanSettings.user_id == user_id))
        settings = settings_result.scalars().first()

        # Buat default jika belum ada
        if not settings:
            settings = PerusahaanSettings(user_id=user_id)
            self.db.add(settings)
            await self.db.commit()
            await self.db.refresh(settings)

        return {
            "profile": {
                "nama_perusahaan": profile.nama_perusahaan,
                "industri": profile.industri,
                "ukuran": profile.ukuran,
                "website_url": profile.website_url,
                "deskripsi": profile.deskripsi,
                "logo_url": profile.logo_url
            },
            "ai_settings": {
                "ai_default_threshold": settings.ai_default_threshold,
                "auto_invite_interview": settings.auto_invite_interview,
                "auto_archive_rejected": settings.auto_archive_rejected,
                "video_weights_json": settings.video_weights_json
            },
            "email_templates": {
                "email_invitation_subject": settings.email_invitation_subject,
                "email_invitation_body": settings.email_invitation_body,
                "email_hire_subject": settings.email_hire_subject
            }
        }

    async def update_settings(self, user_id: str, req: PerusahaanSettingsUpdate):
        profile_result = await self.db.execute(select(PerusahaanProfile).where(PerusahaanProfile.user_id == user_id))
        profile = profile_result.scalars().first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profil Perusahaan tidak ditemukan")

        settings_result = await self.db.execute(select(PerusahaanSettings).where(PerusahaanSettings.user_id == user_id))
        settings = settings_result.scalars().first()
        if not settings:
            settings = PerusahaanSettings(user_id=user_id)
            self.db.add(settings)

        # Update Profil
        if req.nama_perusahaan is not None: profile.nama_perusahaan = req.nama_perusahaan
        if req.industri is not None: profile.industri = req.industri
        if req.ukuran is not None: profile.ukuran = req.ukuran
        if req.website_url is not None: profile.website_url = req.website_url
        if req.deskripsi is not None: profile.deskripsi = req.deskripsi

        # Update Settings
        if req.ai_default_threshold is not None: settings.ai_default_threshold = req.ai_default_threshold
        if req.auto_invite_interview is not None: settings.auto_invite_interview = req.auto_invite_interview
        if req.auto_archive_rejected is not None: settings.auto_archive_rejected = req.auto_archive_rejected
        if req.video_weights_json is not None: settings.video_weights_json = req.video_weights_json
        if req.email_invitation_subject is not None: settings.email_invitation_subject = req.email_invitation_subject
        if req.email_invitation_body is not None: settings.email_invitation_body = req.email_invitation_body
        if req.email_hire_subject is not None: settings.email_hire_subject = req.email_hire_subject

        await self.db.commit()
        
        return await self.get_settings(user_id)
