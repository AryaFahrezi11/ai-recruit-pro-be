from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from app.models.job import JobPosting, JobCategory, SavedJob
from app.models.user import PerusahaanProfile
from app.schemas.job import JobPostingCreate

class JobService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_categories(self):
        result = await self.db.execute(select(JobCategory))
        categories = result.scalars().all()
        return [{"id": cat.id, "nama_kategori": cat.nama_kategori, "deskripsi": cat.deskripsi} for cat in categories]

    async def get_job_by_id(self, user_id: str, job_id: str):
        """Mengambil detail satu lowongan milik perusahaan yang sedang login."""
        result = await self.db.execute(select(PerusahaanProfile).where(PerusahaanProfile.user_id == user_id))
        perusahaan = result.scalars().first()
        if not perusahaan:
            raise HTTPException(status_code=403, detail="Hanya perusahaan yang dapat melihat lowongan ini.")

        result = await self.db.execute(
            select(JobPosting).where(JobPosting.id == job_id, JobPosting.perusahaan_id == perusahaan.id)
        )
        job = result.scalars().first()
        if not job:
            raise HTTPException(status_code=404, detail="Lowongan tidak ditemukan.")
        return job

    async def create_job(self, user_id: str, job_data: JobPostingCreate):
        # Ambil profil perusahaan
        result = await self.db.execute(select(PerusahaanProfile).where(PerusahaanProfile.user_id == user_id))
        perusahaan = result.scalars().first()
        if not perusahaan:
            raise HTTPException(status_code=403, detail="Hanya perusahaan yang dapat membuat lowongan.")

        new_job = JobPosting(
            perusahaan_id=perusahaan.id,
            kategori_id=job_data.kategori_id,
            judul_posisi=job_data.judul_posisi,
            deskripsi_pekerjaan=job_data.deskripsi_pekerjaan,
            kualifikasi=job_data.kualifikasi,
            tanggung_jawab=job_data.tanggung_jawab,
            tipe_pekerjaan=job_data.tipe_pekerjaan,
            lokasi_kerja=job_data.lokasi_kerja,
            kota=job_data.kota,
            gaji_min=job_data.gaji_min,
            gaji_max=job_data.gaji_max,
            tampilkan_gaji=job_data.tampilkan_gaji,
            pengalaman_min_tahun=job_data.pengalaman_min_tahun,
            pendidikan_min=job_data.pendidikan_min,
            cv_threshold=job_data.cv_threshold,
            interview_threshold=job_data.interview_threshold,
            tanggal_buka=job_data.tanggal_buka,
            tanggal_tutup=job_data.tanggal_tutup,
            department=job_data.department,
            experience_level=job_data.experience_level,
            benefits_json=job_data.benefits_json,
            ai_keywords_json=job_data.ai_keywords_json,
            video_questions_json=job_data.video_questions_json,
            openings_count=job_data.openings_count,
            status=job_data.status
        )
        
        self.db.add(new_job)
        await self.db.commit()
        await self.db.refresh(new_job)
        return new_job

    async def update_job(self, user_id: str, job_id: str, job_data: JobPostingCreate):
        """Mengupdate data lowongan milik perusahaan."""
        result = await self.db.execute(select(PerusahaanProfile).where(PerusahaanProfile.user_id == user_id))
        perusahaan = result.scalars().first()
        if not perusahaan:
            raise HTTPException(status_code=403, detail="Hanya perusahaan yang dapat mengupdate lowongan ini.")

        result = await self.db.execute(
            select(JobPosting).where(JobPosting.id == job_id, JobPosting.perusahaan_id == perusahaan.id)
        )
        job = result.scalars().first()
        if not job:
            raise HTTPException(status_code=404, detail="Lowongan tidak ditemukan.")

        job.kategori_id = job_data.kategori_id
        job.judul_posisi = job_data.judul_posisi
        job.deskripsi_pekerjaan = job_data.deskripsi_pekerjaan
        job.kualifikasi = job_data.kualifikasi
        job.tanggung_jawab = job_data.tanggung_jawab
        job.tipe_pekerjaan = job_data.tipe_pekerjaan
        job.lokasi_kerja = job_data.lokasi_kerja
        job.kota = job_data.kota
        job.gaji_min = job_data.gaji_min
        job.gaji_max = job_data.gaji_max
        job.tampilkan_gaji = job_data.tampilkan_gaji
        job.pengalaman_min_tahun = job_data.pengalaman_min_tahun
        job.pendidikan_min = job_data.pendidikan_min
        job.cv_threshold = job_data.cv_threshold
        job.interview_threshold = job_data.interview_threshold
        job.tanggal_buka = job_data.tanggal_buka
        job.tanggal_tutup = job_data.tanggal_tutup
        job.department = job_data.department
        job.experience_level = job_data.experience_level
        job.benefits_json = job_data.benefits_json
        job.ai_keywords_json = job_data.ai_keywords_json
        job.video_questions_json = job_data.video_questions_json
        job.openings_count = job_data.openings_count
        job.status = job_data.status

        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get_my_jobs(self, user_id: str):
        """Mengambil semua lowongan milik perusahaan yang sedang login."""
        result = await self.db.execute(select(PerusahaanProfile).where(PerusahaanProfile.user_id == user_id))
        perusahaan = result.scalars().first()
        if not perusahaan:
            raise HTTPException(status_code=403, detail="Hanya perusahaan yang dapat melihat lowongan ini.")

        result = await self.db.execute(
            select(JobPosting)
            .where(JobPosting.perusahaan_id == perusahaan.id)
            .order_by(JobPosting.created_at.desc())
        )
        return result.scalars().all()

    async def delete_job(self, user_id: str, job_id: str):
        """Menghapus lowongan milik perusahaan yang sedang login."""
        result = await self.db.execute(select(PerusahaanProfile).where(PerusahaanProfile.user_id == user_id))
        perusahaan = result.scalars().first()
        if not perusahaan:
            raise HTTPException(status_code=403, detail="Hanya perusahaan yang dapat menghapus lowongan.")

        result = await self.db.execute(
            select(JobPosting).where(JobPosting.id == job_id, JobPosting.perusahaan_id == perusahaan.id)
        )
        job = result.scalars().first()
        if not job:
            raise HTTPException(status_code=404, detail="Lowongan tidak ditemukan.")

        await self.db.delete(job)
        await self.db.commit()
        return {"message": "Lowongan berhasil dihapus."}

    async def update_job_status(self, user_id: str, job_id: str, new_status: str):
        """Mengubah status lowongan (draft/active/closed)."""
        result = await self.db.execute(select(PerusahaanProfile).where(PerusahaanProfile.user_id == user_id))
        perusahaan = result.scalars().first()
        if not perusahaan:
            raise HTTPException(status_code=403, detail="Hanya perusahaan yang dapat mengubah status lowongan.")

        result = await self.db.execute(
            select(JobPosting).where(JobPosting.id == job_id, JobPosting.perusahaan_id == perusahaan.id)
        )
        job = result.scalars().first()
        if not job:
            raise HTTPException(status_code=404, detail="Lowongan tidak ditemukan.")

        job.status = new_status
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get_saved_jobs(self, user_id: str):
        """Mendapatkan daftar lowongan yang disimpan oleh pelamar."""
        from sqlalchemy.orm import selectinload
        result = await self.db.execute(
            select(SavedJob)
            .options(
                selectinload(SavedJob.job).selectinload(JobPosting.perusahaan)
            )
            .where(SavedJob.user_id == user_id)
            .order_by(SavedJob.created_at.desc())
        )
        saved_jobs = result.scalars().all()
        # Mengembalikan list of JobPosting untuk konsistensi dengan frontend
        return [sj.job for sj in saved_jobs if sj.job]

    async def save_job(self, user_id: str, job_id: str):
        """Menyimpan lowongan (bookmark)."""
        # Cek apakah job valid
        result = await self.db.execute(select(JobPosting).where(JobPosting.id == job_id))
        job = result.scalars().first()
        if not job:
            raise HTTPException(status_code=404, detail="Lowongan tidak ditemukan.")

        # Cek apakah sudah disimpan
        result = await self.db.execute(
            select(SavedJob).where(SavedJob.user_id == user_id, SavedJob.job_id == job_id)
        )
        existing = result.scalars().first()
        if existing:
            return {"message": "Lowongan sudah disimpan."}

        new_saved_job = SavedJob(user_id=user_id, job_id=job_id)
        self.db.add(new_saved_job)
        await self.db.commit()
        return {"message": "Lowongan berhasil disimpan."}

    async def remove_saved_job(self, user_id: str, job_id: str):
        """Menghapus lowongan dari daftar simpanan."""
        result = await self.db.execute(
            select(SavedJob).where(SavedJob.user_id == user_id, SavedJob.job_id == job_id)
        )
        saved_job = result.scalars().first()
        if not saved_job:
            raise HTTPException(status_code=404, detail="Lowongan tersimpan tidak ditemukan.")

        await self.db.delete(saved_job)
        await self.db.commit()
        return {"message": "Lowongan berhasil dihapus dari daftar simpanan."}
