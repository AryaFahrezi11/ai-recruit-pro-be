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
from app.core.security import hash_password
from app.schemas.admin import AdminUserCreateRequest, AdminUserUpdateRequest


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_users(self, role: Optional[str] = None):
        """Mendapatkan daftar semua pengguna dengan filter role opsional"""
        query = select(User)
        if role:
            query = query.where(User.role == role)
        
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        users_data = []
        for user in users:
            # Dapatkan profil spesifik berdasarkan role
            profile_name = "-"
            
            if user.role == "perusahaan":
                p_result = await self.db.execute(select(PerusahaanProfile).where(PerusahaanProfile.user_id == user.id))
                profile = p_result.scalars().first()
                if profile:
                    profile_name = profile.nama_perusahaan
            elif user.role == "pelamar":
                p_result = await self.db.execute(select(PelamarProfile).where(PelamarProfile.user_id == user.id))
                profile = p_result.scalars().first()
                if profile:
                    profile_name = profile.nama_lengkap
            elif user.role == "kampus":
                p_result = await self.db.execute(select(KampusProfile).where(KampusProfile.user_id == user.id))
                profile = p_result.scalars().first()
                if profile:
                    profile_name = profile.nama_kampus

            users_data.append({
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "name": profile_name,
                "is_active": user.is_active,
                "is_banned": user.is_banned,
                "created_at": user.created_at
            })
            
        return users_data

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

    async def get_pending_companies(self):
        """Mendapatkan daftar perusahaan yang belum diverifikasi"""
        query = select(PerusahaanProfile).where(PerusahaanProfile.is_verified == False)
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
        await self.db.commit()
        return {"status": "success", "message": "Perusahaan berhasil diverifikasi"}
