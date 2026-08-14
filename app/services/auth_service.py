"""
🔐 Auth Service (Placeholder)
Logika bisnis untuk autentikasi.
Akan diimplementasi setelah database siap.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from datetime import datetime, timedelta, timezone
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from fastapi import BackgroundTasks

from app.models.setting import SystemSetting
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User, PelamarProfile, PerusahaanProfile, KampusProfile


def send_otp_email_sync(host: str, port: int, user: str, password: str, sender_email: str, recipient: str, otp_code: str):
    if not host or not sender_email:
        print("SMTP settings are incomplete. Skipping email.")
        return
        
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = "Kode OTP Anda - AI Recruit Pro"
        
        body = f"Halo,\n\nKode OTP Anda adalah: {otp_code}\n\nKode ini berlaku selama 10 menit. Jangan berikan kode ini kepada siapapun.\n\nTerima kasih,\nTim AI Recruit Pro"
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(host, port)
        server.starttls()
        if user and password:
            server.login(user, password)
        server.send_message(msg)
        server.quit()
        print(f"✅ OTP email sent to {recipient}")
    except Exception as e:
        print(f"❌ Failed to send OTP email: {e}")

class AuthService:
    """
    Service untuk autentikasi user dan manajemen akun.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, email: str, password: str, role: str, background_tasks: BackgroundTasks = None) -> dict:
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

        # 3. Buat profil default sesuai role (kosong untuk pelamar baru)
        if role == "pelamar":
            profile = PelamarProfile(user_id=new_user.id, nama_lengkap="")
            self.db.add(profile)
        elif role == "perusahaan":
            profile = PerusahaanProfile(user_id=new_user.id, nama_perusahaan="")
            self.db.add(profile)
        elif role == "kampus":
            profile = KampusProfile(user_id=new_user.id, nama_kampus="")
            self.db.add(profile)

        # Simpan semua perubahan ke database
        await self.db.commit()

        # 4. Generate OTP
        otp_code = "".join(random.choices(string.digits, k=6))
        new_user.otp_code = otp_code
        new_user.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        
        await self.db.commit()

        # 5. Send OTP Email
        settings_query = await self.db.execute(select(SystemSetting).where(
            SystemSetting.key.in_(['smtp_host', 'smtp_port', 'smtp_user', 'smtp_pass', 'smtp_from'])
        ))
        settings_db = settings_query.scalars().all()
        
        smtp_config = {
            'smtp_host': '',
            'smtp_port': 587,
            'smtp_user': '',
            'smtp_pass': '',
            'smtp_from': ''
        }
        
        for s in settings_db:
            try: val = json.loads(s.value)
            except: val = s.value
            
            if s.key == 'smtp_port':
                try: smtp_config[s.key] = int(val)
                except: pass
            else:
                smtp_config[s.key] = val
                
        if background_tasks and smtp_config.get('smtp_host') and smtp_config.get('smtp_from'):
            background_tasks.add_task(
                send_otp_email_sync,
                smtp_config['smtp_host'],
                smtp_config['smtp_port'],
                smtp_config['smtp_user'],
                smtp_config['smtp_pass'],
                smtp_config['smtp_from'],
                email,
                otp_code
            )
        else:
            print("=======================================")
            print("⚠️ SMTP not configured or background_tasks missing.")
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

    async def login(self, email: str, password: str, expected_role: str | None = None) -> dict:
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

        # 3. Verifikasi role spesifik jika diminta
        if expected_role and user.role != expected_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Akses ditolak. Silakan gunakan form login untuk {user.role}.",
            )

        # 3. Buat token
        token = create_access_token(data={"sub": str(user.id), "role": user.role})
        return {
            "access_token": token,
            "token_type": "bearer",
            "role": user.role,
            "user_id": str(user.id)
        }
