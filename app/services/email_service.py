import os
import json
import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.setting import SystemSetting

DEFAULT_TEMPLATES: Dict[str, str] = {
    "email_tpl_otp_subject": "Kode OTP Verifikasi - AI Recruit Pro",
    "email_tpl_otp_body": (
        "Halo {nama_penerima},\n\n"
        "Kode OTP verifikasi akun Anda adalah:\n\n"
        "{otp_code}\n\n"
        "Kode ini berlaku selama {kadaluarsa_menit} menit. Harap jangan memberikan kode ini kepada siapapun demi keamanan akun Anda.\n\n"
        "Salam hormat,\n"
        "Tim AI Recruit Pro"
    ),
    "email_tpl_company_approved_subject": "Selamat! Pengajuan Akun Perusahaan {nama_perusahaan} Telah Terverifikasi",
    "email_tpl_company_approved_body": (
        "Halo Tim {nama_perusahaan},\n\n"
        "Kabar baik! Dokumen legalitas dan data profil perusahaan Anda telah diverifikasi dan disetujui oleh tim kurator AI Recruit Pro.\n\n"
        "Akun perusahaan Anda kini berstatus Resmi & Terverifikasi (Verified). Anda sudah dapat membuat lowongan kerja baru, mengelola pelamar, dan memanfaatkan fitur AI ATS.\n\n"
        "Silakan login ke portal dashboard perusahaan Anda:\n"
        "{login_url}\n\n"
        "Terima kasih telah mempercayakan kebutuhan rekrutmen Anda kepada AI Recruit Pro!\n\n"
        "Salam sukses,\n"
        "Tim AI Recruit Pro"
    ),
    "email_tpl_company_rejected_subject": "Pemberitahuan Status Verifikasi Akun Perusahaan {nama_perusahaan}",
    "email_tpl_company_rejected_body": (
        "Halo Tim {nama_perusahaan},\n\n"
        "Terima kasih telah mendaftar dan mengajukan verifikasi profil perusahaan di platform AI Recruit Pro.\n\n"
        "Setelah dilakukan peninjauan dokumen, saat ini pengajuan verifikasi perusahaan Anda belum dapat kami setujui dengan catatan penolakan berikut:\n"
        "\"{alasan_penolakan}\"\n\n"
        "Anda dapat memperbarui data atau mengunggah ulang dokumen legalitas yang sesuai dengan masuk kembali ke akun Anda melalui tautan berikut:\n"
        "{revisi_url}\n\n"
        "Jika ada kendala atau pertanyaan lebih lanjut, silakan hubungi tim dukungan kami.\n\n"
        "Salam hormat,\n"
        "Tim Verifikasi AI Recruit Pro"
    ),
}

async def get_all_settings_dict(db: AsyncSession) -> Dict[str, Any]:
    """Mengambil semua pengaturan sistem dan menggabungkannya dengan default templates."""
    result = dict(DEFAULT_TEMPLATES)
    query = await db.execute(select(SystemSetting))
    records = query.scalars().all()
    for s in records:
        try:
            val = json.loads(s.value)
            if isinstance(val, str) and val.lower() == "true":
                val = True
            elif isinstance(val, str) and val.lower() == "false":
                val = False
            result[s.key] = val
        except Exception:
            result[s.key] = s.value
    return result

def _send_email_sync(host: str, port: int, user: str, password: str, sender_email: str, recipient: str, subject: str, body: str):
    """Fungsi sinkronus untuk mengirim email melalui SMTP."""
    if not host or not sender_email or not recipient:
        print("[SMTP] Konfigurasi host atau sender email belum lengkap. Email tidak dikirimkan.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        server = smtplib.SMTP(host, int(port), timeout=15)
        server.starttls()
        if user and password:
            server.login(user, password)
        server.send_message(msg)
        server.quit()
        print(f"[SMTP] Email berhasil dikirim ke {recipient} dengan subjek: {subject}")
        return True
    except Exception as e:
        print(f"[SMTP Error] Gagal mengirim email ke {recipient}: {e}")
        return False

async def send_rendered_email(db: AsyncSession, recipient: str, subject: str, body: str) -> bool:
    """Mengambil konfigurasi SMTP dari DB dan mengirimkan email secara asinkron."""
    settings = await get_all_settings_dict(db)
    host = settings.get("smtp_host") or os.getenv("SMTP_HOST", "")
    port = settings.get("smtp_port") or os.getenv("SMTP_PORT", 587)
    user = settings.get("smtp_user") or os.getenv("SMTP_USER", "")
    password = settings.get("smtp_pass") or os.getenv("SMTP_PASSWORD", "")
    sender = settings.get("smtp_from") or os.getenv("SMTP_FROM", "")

    return await asyncio.to_thread(
        _send_email_sync,
        host=host,
        port=port,
        user=user,
        password=password,
        sender_email=sender,
        recipient=recipient,
        subject=subject,
        body=body
    )

async def send_company_approved_email(db: AsyncSession, company_name: str, recipient_email: str, login_url: str = "http://localhost:3000/login"):
    """Mengirim email notifikasi bahwa akun perusahaan telah diverifikasi."""
    settings = await get_all_settings_dict(db)
    subject_tpl = settings.get("email_tpl_company_approved_subject") or DEFAULT_TEMPLATES["email_tpl_company_approved_subject"]
    body_tpl = settings.get("email_tpl_company_approved_body") or DEFAULT_TEMPLATES["email_tpl_company_approved_body"]

    subject = subject_tpl.replace("{nama_perusahaan}", company_name).replace("{email_perusahaan}", recipient_email).replace("{login_url}", login_url)
    body = body_tpl.replace("{nama_perusahaan}", company_name).replace("{email_perusahaan}", recipient_email).replace("{login_url}", login_url)

    return await send_rendered_email(db, recipient_email, subject, body)

async def send_company_rejected_email(db: AsyncSession, company_name: str, recipient_email: str, reason: str, revisi_url: str = "http://localhost:3000/login"):
    """Mengirim email notifikasi bahwa verifikasi perusahaan ditolak beserta alasannya."""
    settings = await get_all_settings_dict(db)
    subject_tpl = settings.get("email_tpl_company_rejected_subject") or DEFAULT_TEMPLATES["email_tpl_company_rejected_subject"]
    body_tpl = settings.get("email_tpl_company_rejected_body") or DEFAULT_TEMPLATES["email_tpl_company_rejected_body"]

    subject = subject_tpl.replace("{nama_perusahaan}", company_name).replace("{alasan_penolakan}", reason).replace("{revisi_url}", revisi_url)
    body = body_tpl.replace("{nama_perusahaan}", company_name).replace("{alasan_penolakan}", reason).replace("{revisi_url}", revisi_url)

    return await send_rendered_email(db, recipient_email, subject, body)

async def send_otp_email_templated(db: AsyncSession, recipient_email: str, otp_code: str, recipient_name: str = "Pengguna", expiry_minutes: int = 10):
    """Mengirim email OTP menggunakan template dari pengaturan sistem."""
    settings = await get_all_settings_dict(db)
    subject_tpl = settings.get("email_tpl_otp_subject") or DEFAULT_TEMPLATES["email_tpl_otp_subject"]
    body_tpl = settings.get("email_tpl_otp_body") or DEFAULT_TEMPLATES["email_tpl_otp_body"]

    subject = subject_tpl.replace("{otp_code}", otp_code).replace("{nama_penerima}", recipient_name).replace("{kadaluarsa_menit}", str(expiry_minutes))
    body = body_tpl.replace("{otp_code}", otp_code).replace("{nama_penerima}", recipient_name).replace("{kadaluarsa_menit}", str(expiry_minutes))

    return await send_rendered_email(db, recipient_email, subject, body)
