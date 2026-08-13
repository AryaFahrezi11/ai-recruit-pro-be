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
                "logo_url": profile.logo_url,
                "alamat": profile.alamat,
                "kota": profile.kota,
                "provinsi": profile.provinsi,
                "no_telepon": profile.no_telepon,
                "tahun_berdiri": profile.tahun_berdiri,
                "hr_name": profile.hr_name,
                "hr_whatsapp": profile.hr_whatsapp,
                "hr_position": profile.hr_position,
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
                "email_hire_subject": settings.email_hire_subject,
                "email_hire_body": settings.email_hire_body,
                "email_reject_subject": settings.email_reject_subject,
                "email_reject_body": settings.email_reject_body,
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
        if req.alamat is not None: profile.alamat = req.alamat
        if req.kota is not None: profile.kota = req.kota
        if req.provinsi is not None: profile.provinsi = req.provinsi
        if req.no_telepon is not None: profile.no_telepon = req.no_telepon
        if req.tahun_berdiri is not None: profile.tahun_berdiri = req.tahun_berdiri
        if req.hr_name is not None: profile.hr_name = req.hr_name
        if req.hr_whatsapp is not None: profile.hr_whatsapp = req.hr_whatsapp
        if req.hr_position is not None: profile.hr_position = req.hr_position

        # Update Settings
        if req.ai_default_threshold is not None: settings.ai_default_threshold = req.ai_default_threshold
        if req.auto_invite_interview is not None: settings.auto_invite_interview = req.auto_invite_interview
        if req.auto_archive_rejected is not None: settings.auto_archive_rejected = req.auto_archive_rejected
        if req.video_weights_json is not None: settings.video_weights_json = req.video_weights_json
        if req.email_invitation_subject is not None: settings.email_invitation_subject = req.email_invitation_subject
        if req.email_invitation_body is not None: settings.email_invitation_body = req.email_invitation_body
        if req.email_hire_subject is not None: settings.email_hire_subject = req.email_hire_subject
        if req.email_hire_body is not None: settings.email_hire_body = req.email_hire_body
        if req.email_reject_subject is not None: settings.email_reject_subject = req.email_reject_subject
        if req.email_reject_body is not None: settings.email_reject_body = req.email_reject_body

        await self.db.commit()
        return await self.get_settings(user_id)

    async def get_verified_companies_public(self):
        from sqlalchemy.orm import selectinload, defer
        from app.models.job import JobPosting
        result = await self.db.execute(
            select(PerusahaanProfile)
            .options(selectinload(PerusahaanProfile.job_postings).defer(JobPosting.jd_embedding))
            .where(PerusahaanProfile.is_verified == True)
        )
        companies = result.scalars().all()
        
        data = []
        for comp in companies:
            data.append({
                "id": comp.id,
                "nama_perusahaan": comp.nama_perusahaan,
                "logo_url": comp.logo_url,
                "industri": comp.industri,
                "rating": 5.0, # dummy rating
                "jobs_count": len([j for j in comp.job_postings if j.status == 'active'])
            })
        return data
        
    async def get_company_profile(self, company_id: str):
        from sqlalchemy.orm import selectinload, defer
        from app.models.job import JobPosting
        
        result = await self.db.execute(
            select(PerusahaanProfile)
            .options(selectinload(PerusahaanProfile.job_postings).defer(JobPosting.jd_embedding))
            .where(PerusahaanProfile.id == company_id)
            .where(PerusahaanProfile.is_verified == True)
        )
        comp = result.scalars().first()
        
        if not comp:
            raise HTTPException(status_code=404, detail="Perusahaan tidak ditemukan atau belum diverifikasi")
            
        active_jobs = [j for j in comp.job_postings if j.status == 'active']
        
        return {
            "id": comp.id,
            "nama_perusahaan": comp.nama_perusahaan,
            "logo_url": comp.logo_url,
            "industri": comp.industri,
            "ukuran": comp.ukuran,
            "website_url": comp.website_url,
            "deskripsi": comp.deskripsi,
            "alamat": comp.alamat,
            "kota": comp.kota,
            "provinsi": comp.provinsi,
            "tahun_berdiri": comp.tahun_berdiri,
            "rating": 5.0, # dummy rating
            "jobs_count": len(active_jobs),
            "jobs": [
                {
                    "id": j.id,
                    "judul_posisi": j.judul_posisi,
                    "lokasi_kerja": j.lokasi_kerja,
                    "kota": j.kota,
                    "tipe_pekerjaan": j.tipe_pekerjaan,
                    "kualifikasi": j.kualifikasi,
                    "pendidikan_min": j.pendidikan_min,
                    "pengalaman_min_tahun": j.pengalaman_min_tahun,
                    "experience_level": j.experience_level,
                    "gaji_min": j.gaji_min,
                    "gaji_max": j.gaji_max,
                    "tampilkan_gaji": j.tampilkan_gaji,
                    "openings_count": j.openings_count,
                    "benefits_json": j.benefits_json,
                    "deskripsi_pekerjaan": j.deskripsi_pekerjaan,
                    "tanggung_jawab": j.tanggung_jawab,
                    "tanggal_buka": j.tanggal_buka,
                    "tanggal_tutup": j.tanggal_tutup,
                    "is_promoted": j.is_promoted,
                } for j in active_jobs
            ]
        }
