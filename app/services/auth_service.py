"""
🔐 Auth Service (Placeholder)
Logika bisnis untuk autentikasi.
Akan diimplementasi setelah database siap.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from datetime import datetime, timedelta, timezone
import random
import string

from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User, PelamarProfile, PerusahaanProfile, KampusProfile


class AuthService:
    """
    Service untuk autentikasi user dan manajemen akun.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, email: str, password: str, role: str) -> dict:
        """Mendaftarkan user baru."""
        # 1. Cek apakah email sudah terdaftar
        result = await self.db.execute(select(User).where(User.email == email))
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email sudah terdaftar"
            )

        # 2. Hash password & Buat User baru
        hashed = hash_password(password)
        new_user = User(email=email, password_hash=hashed, role=role)
        self.db.add(new_user)
        
        # Flush agar new_user mendapatkan ID sebelum di-commit
        await self.db.flush() 

        # 3. Buat profil default sesuai role
        if role == "pelamar":
            profile = PelamarProfile(user_id=new_user.id, nama_lengkap="Nama Pelamar")
            self.db.add(profile)
        elif role == "perusahaan":
            profile = PerusahaanProfile(user_id=new_user.id, nama_perusahaan="Nama Perusahaan")
            self.db.add(profile)
        elif role == "kampus":
            profile = KampusProfile(user_id=new_user.id, nama_kampus="Nama Kampus")
            self.db.add(profile)

        # Simpan semua perubahan ke database
        await self.db.commit()

        # 4. Generate OTP
        otp_code = "".join(random.choices(string.digits, k=6))
        new_user.otp_code = otp_code
        new_user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        
        await self.db.commit()

        # 5. Mock Email Sending
        print("=======================================")
        print(f"📧 MOCK EMAIL DIKIRIM KE: {email}")
        print(f"🔑 KODE OTP ANDA: {otp_code}")
        print("=======================================")

        return {
            "status": "success",
            "message": f"Kode OTP telah dikirim ke {email}"
        }

    async def verify_otp(self, email: str, otp_code: str) -> dict:
        """Memverifikasi kode OTP yang diinput user."""
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalars().first()

        if not user:
            raise HTTPException(status_code=400, detail="User tidak ditemukan")

        if user.is_active:
            raise HTTPException(status_code=400, detail="Akun sudah aktif")

        if user.otp_code != otp_code:
            raise HTTPException(status_code=400, detail="Kode OTP salah")

        if not user.otp_expires_at or datetime.now(timezone.utc) > user.otp_expires_at:
            raise HTTPException(status_code=400, detail="Kode OTP sudah kadaluarsa")

        # OTP Benar, aktifkan akun
        user.is_active = True
        user.email_verified_at = datetime.now(timezone.utc)
        user.otp_code = None
        user.otp_expires_at = None

        await self.db.commit()

        # Generate Token
        token = create_access_token(data={"sub": str(user.id), "role": user.role})
        return {
            "access_token": token,
            "token_type": "bearer",
            "role": user.role,
            "user_id": str(user.id)
        }

    async def login(self, email: str, password: str) -> dict:
        """Login user."""
        # 1. Cari user
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email atau password salah",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 2. Verifikasi password
        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email atau password salah",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 3. Buat token
        token = create_access_token(data={"sub": str(user.id), "role": user.role})
        return {
            "access_token": token,
            "token_type": "bearer",
            "role": user.role,
            "user_id": str(user.id)
        }
