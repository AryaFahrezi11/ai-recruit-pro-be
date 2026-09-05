"""
🛡️ Admin Service
Logika bisnis untuk manajemen pengguna dan verifikasi perusahaan.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from fastapi import HTTPException, status
from typing import List, Optional

from app.models.user import User, PerusahaanProfile, PelamarProfile, KampusProfile
from app.models.application import CVDocument
from app.core.security import hash_password
from app.schemas.admin import AdminUserCreateRequest, AdminUserUpdateRequest


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_users(self, role: Optional[str] = None, search: Optional[str] = None):
        """Mendapatkan daftar semua pengguna dengan filter role opsional dan pencarian"""
        query = select(User).order_by(User.created_at.desc())
        if role:
            query = query.where(User.role == role)
        
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        users_data = []
        search_lower = search.strip().lower() if search else None
        
        for user in users:
            # Dapatkan profil spesifik berdasarkan role
            profile_name = "-"
            verification_status = None
            is_verified = False
            rejection_reason = None
            
            if user.role == "perusahaan":
                p_result = await self.db.execute(select(PerusahaanProfile).where(PerusahaanProfile.user_id == user.id))
                profile = p_result.scalars().first()
                if profile:
                    profile_name = profile.nama_perusahaan or "-"
                    is_verified = bool(profile.is_verified)
                    rejection_reason = profile.rejection_reason
                    if profile.is_verified:
                        verification_status = "VERIFIED"
                    elif profile.status == "REJECTED":
                        verification_status = "REJECTED"
                    else:
                        verification_status = "PENDING"
                else:
                    verification_status = "PENDING"
            elif user.role == "pelamar":
                p_result = await self.db.execute(select(PelamarProfile).where(PelamarProfile.user_id == user.id))
                profile = p_result.scalars().first()
                if profile:
                    profile_name = profile.nama_lengkap or "-"
                verification_status = "VERIFIED" if user.is_active else "UNVERIFIED"
            elif user.role == "kampus":
                p_result = await self.db.execute(select(KampusProfile).where(KampusProfile.user_id == user.id))
                profile = p_result.scalars().first()
                if profile:
                    profile_name = profile.nama_kampus or "-"
                    is_verified = bool(profile.is_verified)
                    verification_status = "VERIFIED" if profile.is_verified else "PENDING"
                else:
                    verification_status = "PENDING"
            elif user.role == "admin":
                profile_name = "Administrator"
                verification_status = "VERIFIED"

            # Filter search if provided
            if search_lower:
                match_email = search_lower in (user.email or "").lower()
                match_name = search_lower in profile_name.lower()
                match_role = search_lower in (user.role or "").lower()
                if not (match_email or match_name or match_role):
                    continue

            users_data.append({
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "name": profile_name,
                "is_active": user.is_active,
                "is_banned": user.is_banned,
                "is_verified": is_verified,
                "verification_status": verification_status,
                "rejection_reason": rejection_reason,
                "created_at": user.created_at
            })
            
        return users_data

    async def get_user_detail(self, user_id: str):
        """Mendapatkan detail profile pengguna"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User tidak ditemukan")
            
        profile_data = {}
        if user.role == "perusahaan":
            p_result = await self.db.execute(select(PerusahaanProfile).where(PerusahaanProfile.user_id == user.id))
            profile = p_result.scalars().first()
            if profile:
                profile_data = {
                    "id": profile.id,
                    "nama_perusahaan": profile.nama_perusahaan,
                    "industri": profile.industri,
                    "ukuran": profile.ukuran,
                    "deskripsi": profile.deskripsi,
                    "alamat": profile.alamat,
                    "kota": profile.kota,
                    "provinsi": profile.provinsi,
                    "website_url": profile.website_url,
                    "logo_url": profile.logo_url,
                    "no_telepon": profile.no_telepon,
                    "tahun_berdiri": profile.tahun_berdiri,
                    "nib_number": profile.nib_number,
                    "nib_document_url": profile.nib_document_url,
                    "hr_name": profile.hr_name,
                    "hr_whatsapp": profile.hr_whatsapp,
                    "hr_position": profile.hr_position,
                    "hr_id_card_url": profile.hr_id_card_url,
                    "is_verified": profile.is_verified,
                    "status": profile.status,
                    "rejection_reason": profile.rejection_reason
                }
        elif user.role == "pelamar":
            p_result = await self.db.execute(select(PelamarProfile).where(PelamarProfile.user_id == user.id))
            profile = p_result.scalars().first()
            if profile:
                # Query CV Document terbaru dari pelamar
                cv_result = await self.db.execute(
                    select(CVDocument)
                    .where(CVDocument.pelamar_id == profile.id)
                    .order_by(CVDocument.uploaded_at.desc())
                )
                cv_docs = cv_result.scalars().all()
                
                cv_list = []
                for cv in cv_docs:
                    cv_list.append({
                        "id": cv.id,
                        "nama_file": cv.nama_file,
                        "file_url": cv.file_url,
                        "file_type": cv.file_type,
                        "file_size_kb": cv.file_size_kb,
                        "pendidikan_tertinggi": cv.pendidikan_tertinggi,
                        "extracted_text": cv.extracted_text,
                        "email": cv.email,
                        "phone": cv.phone,
                        "uploaded_at": cv.uploaded_at
                    })
                    
                latest_cv = cv_list[0] if cv_list else None

                profile_data = {
                    "id": profile.id,
                    "nama_lengkap": profile.nama_lengkap,
                    "judul_posisi": profile.judul_posisi,
                    "no_telepon": profile.no_telepon,
                    "alamat": profile.alamat,
                    "ringkasan_diri": profile.ringkasan_diri,
                    "keahlian": profile.keahlian,
                    "pengalaman_kerja": profile.pengalaman_kerja,
                    "riwayat_pendidikan": profile.riwayat_pendidikan,
                    "sertifikasi": profile.sertifikasi,
                    "linkedin_url": profile.linkedin_url,
                    "portfolio_url": profile.portfolio_url,
                    "social_links": profile.social_links,
                    "latest_cv": latest_cv,
                    "cv_documents": cv_list
                }
        elif user.role == "kampus":
            p_result = await self.db.execute(select(KampusProfile).where(KampusProfile.user_id == user.id))
            profile = p_result.scalars().first()
            if profile:
                profile_data = {
                    "nama_kampus": profile.nama_kampus,
                    "alamat": profile.alamat,
                    "kota": profile.kota,
                    "provinsi": profile.provinsi,
                    "website_url": profile.website_url,
                    "no_telepon": profile.no_telepon,
                    "akreditasi": profile.akreditasi,
                    "is_verified": profile.is_verified
                }
                
        return {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "is_banned": user.is_banned,
            "created_at": user.created_at,
            "profile": profile_data
        }

    async def create_user_manual(self, req: AdminUserCreateRequest):
        """Membuat user baru secara manual (tanpa OTP, langsung aktif)"""
        # Cek apakah email sudah terdaftar
        existing_user = await self.db.execute(select(User).where(User.email == req.email))
        if existing_user.scalars().first():
            raise HTTPException(status_code=400, detail="Email sudah terdaftar")
            
        hashed_password = hash_password(req.password)
        
        new_user = User(
            email=req.email,
            password_hash=hashed_password,
            role=req.role,
            is_active=True
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        
        # Buat profil default sesuai role
        if req.role == "pelamar":
            profile = PelamarProfile(user_id=new_user.id, nama_lengkap=req.name)
            self.db.add(profile)
        elif req.role == "perusahaan":
            profile = PerusahaanProfile(user_id=new_user.id, nama_perusahaan=req.name)
            self.db.add(profile)
        elif req.role == "kampus":
            profile = KampusProfile(user_id=new_user.id, nama_kampus=req.name)
            self.db.add(profile)
            
        await self.db.commit()
        return {"status": "success", "message": "User berhasil dibuat", "user_id": new_user.id}

    async def update_user_manual(self, user_id: str, req: AdminUserUpdateRequest):
        """Memperbarui email, role, atau nama profil user secara manual"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User tidak ditemukan")
            
        if user.email != req.email:
            # Cek apakah email baru sudah dipakai orang lain
            existing = await self.db.execute(select(User).where(User.email == req.email))
            if existing.scalars().first():
                raise HTTPException(status_code=400, detail="Email sudah dipakai pengguna lain")
            user.email = req.email
            
        old_role = user.role
        user.role = req.role
        
        # Update nama di tabel profil
        if req.role == "pelamar":
            p_result = await self.db.execute(select(PelamarProfile).where(PelamarProfile.user_id == user_id))
            profile = p_result.scalars().first()
            if profile:
                profile.nama_lengkap = req.name
            else:
                self.db.add(PelamarProfile(user_id=user_id, nama_lengkap=req.name))
        elif req.role == "perusahaan":
            p_result = await self.db.execute(select(PerusahaanProfile).where(PerusahaanProfile.user_id == user_id))
            profile = p_result.scalars().first()
            if profile:
                profile.nama_perusahaan = req.name
            else:
                self.db.add(PerusahaanProfile(user_id=user_id, nama_perusahaan=req.name))
        elif req.role == "kampus":
            p_result = await self.db.execute(select(KampusProfile).where(KampusProfile.user_id == user_id))
            profile = p_result.scalars().first()
            if profile:
                profile.nama_kampus = req.name
            else:
                self.db.add(KampusProfile(user_id=user_id, nama_kampus=req.name))
                
        # Jika role berubah, mungkin profil lama harusnya dihapus? Tapi untuk kesederhanaan, biarkan saja atau bisa dibuat cleanup
        
        await self.db.commit()
        return {"status": "success", "message": "User berhasil diperbarui"}

    async def delete_user(self, user_id: str):
        """Menghapus pengguna secara permanen"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User tidak ditemukan")
            
        await self.db.delete(user)
        await self.db.commit()
        return {"status": "success", "message": "User berhasil dihapus"}

    async def ban_user(self, user_id: str, status: bool):
        """Mengubah status banned pengguna"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        if not user:
            raise HTTPException(status_code=404, detail="User tidak ditemukan")
            
        user.is_banned = status
        await self.db.commit()
        return {"status": "success", "message": f"User {'banned' if status else 'unbanned'} successfully"}

    async def get_pending_companies(self, search: Optional[str] = None):
        """Mendapatkan daftar perusahaan yang belum diverifikasi"""
        query = select(PerusahaanProfile).where(PerusahaanProfile.is_verified == False)
        if search and search.strip():
            s = "%" + search.strip() + "%"
            query = query.where(
                or_(
                    PerusahaanProfile.nama_perusahaan.ilike(s),
                    PerusahaanProfile.nib_number.ilike(s),
                    PerusahaanProfile.hr_name.ilike(s),
                    PerusahaanProfile.hr_whatsapp.ilike(s),
                    PerusahaanProfile.kota.ilike(s),
                    PerusahaanProfile.industri.ilike(s)
                )
            )
        result = await self.db.execute(query)
        companies = result.scalars().all()
        return companies

    async def verify_company(self, company_id: str):
        """Memverifikasi perusahaan berdasarkan profile ID"""
        result = await self.db.execute(select(PerusahaanProfile).where(PerusahaanProfile.id == company_id))
        company = result.scalars().first()
        
        if not company:
            raise HTTPException(status_code=404, detail="Perusahaan tidak ditemukan")
            
        company.is_verified = True
        company.status = "VERIFIED"
        company.rejection_reason = None
        await self.db.commit()
        
        # Kirim email notifikasi persetujuan ke perusahaan
        try:
            user_res = await self.db.execute(select(User).where(User.id == company.user_id))
            company_user = user_res.scalars().first()
            if company_user and company_user.email:
                from app.services.email_service import send_company_approved_email
                await send_company_approved_email(
                    db=self.db,
                    company_name=company.nama_perusahaan or "Perusahaan",
                    recipient_email=company_user.email
                )
        except Exception as e:
            print(f"[AdminService] Notifikasi email approve gagal: {e}")

        return {"status": "success", "message": "Perusahaan berhasil diverifikasi"}

    async def reject_company(self, company_id: str, reason: str):
        """Menolak verifikasi perusahaan dan meminta kelengkapan ulang data/dokumen (step 3)"""
        result = await self.db.execute(select(PerusahaanProfile).where(PerusahaanProfile.id == company_id))
        company = result.scalars().first()
        
        if not company:
            raise HTTPException(status_code=404, detail="Perusahaan tidak ditemukan")
            
        company.is_verified = False
        company.status = "REJECTED"
        company.rejection_reason = reason.strip() if reason else "Persyaratan dokumen belum lengkap/sesuai"
        await self.db.commit()
        
        # Kirim email notifikasi penolakan ke perusahaan
        try:
            user_res = await self.db.execute(select(User).where(User.id == company.user_id))
            company_user = user_res.scalars().first()
            if company_user and company_user.email:
                from app.services.email_service import send_company_rejected_email
                await send_company_rejected_email(
                    db=self.db,
                    company_name=company.nama_perusahaan or "Perusahaan",
                    recipient_email=company_user.email,
                    reason=company.rejection_reason
                )
        except Exception as e:
            print(f"[AdminService] Notifikasi email reject gagal: {e}")

        return {"status": "success", "message": "Verifikasi perusahaan berhasil ditolak"}
