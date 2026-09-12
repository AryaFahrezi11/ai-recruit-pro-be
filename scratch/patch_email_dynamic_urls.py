path = 'c:/ai-recruit-pro-be/app/services/email_service.py'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

old_approved = """async def send_company_approved_email(db: AsyncSession, company_name: str, recipient_email: str, login_url: str = "http://localhost:3000/login"):
    \"\"\"Mengirim email notifikasi bahwa akun perusahaan telah diverifikasi.\"\"\"
    settings = await get_all_settings_dict(db)
    subject_tpl = settings.get("email_tpl_company_approved_subject") or DEFAULT_TEMPLATES["email_tpl_company_approved_subject"]
    body_tpl = settings.get("email_tpl_company_approved_body") or DEFAULT_TEMPLATES["email_tpl_company_approved_body"]

    subject = subject_tpl.replace("{nama_perusahaan}", company_name).replace("{email_perusahaan}", recipient_email).replace("{login_url}", login_url)
    body = body_tpl.replace("{nama_perusahaan}", company_name).replace("{email_perusahaan}", recipient_email).replace("{login_url}", login_url)"""

new_approved = """async def send_company_approved_email(db: AsyncSession, company_name: str, recipient_email: str, login_url: str = None):
    \"\"\"Mengirim email notifikasi bahwa akun perusahaan telah diverifikasi.\"\"\"
    settings = await get_all_settings_dict(db)
    base_url = settings.get("public_domain_url") or os.getenv("FRONTEND_URL", "http://localhost:3000")
    if not login_url:
        login_url = f"{base_url.rstrip('/')}/login"

    subject_tpl = settings.get("email_tpl_company_approved_subject") or DEFAULT_TEMPLATES["email_tpl_company_approved_subject"]
    body_tpl = settings.get("email_tpl_company_approved_body") or DEFAULT_TEMPLATES["email_tpl_company_approved_body"]

    subject = subject_tpl.replace("{nama_perusahaan}", company_name).replace("{email_perusahaan}", recipient_email).replace("{login_url}", login_url)
    body = body_tpl.replace("{nama_perusahaan}", company_name).replace("{email_perusahaan}", recipient_email).replace("{login_url}", login_url)"""

old_rejected = """async def send_company_rejected_email(db: AsyncSession, company_name: str, recipient_email: str, reason: str, revisi_url: str = "http://localhost:3000/login"):
    \"\"\"Mengirim email notifikasi bahwa verifikasi perusahaan ditolak beserta alasannya.\"\"\"
    settings = await get_all_settings_dict(db)
    subject_tpl = settings.get("email_tpl_company_rejected_subject") or DEFAULT_TEMPLATES["email_tpl_company_rejected_subject"]
    body_tpl = settings.get("email_tpl_company_rejected_body") or DEFAULT_TEMPLATES["email_tpl_company_rejected_body"]

    subject = subject_tpl.replace("{nama_perusahaan}", company_name).replace("{alasan_penolakan}", reason).replace("{revisi_url}", revisi_url)
    body = body_tpl.replace("{nama_perusahaan}", company_name).replace("{alasan_penolakan}", reason).replace("{revisi_url}", revisi_url)"""

new_rejected = """async def send_company_rejected_email(db: AsyncSession, company_name: str, recipient_email: str, reason: str, revisi_url: str = None):
    \"\"\"Mengirim email notifikasi bahwa verifikasi perusahaan ditolak beserta alasannya.\"\"\"
    settings = await get_all_settings_dict(db)
    base_url = settings.get("public_domain_url") or os.getenv("FRONTEND_URL", "http://localhost:3000")
    if not revisi_url:
        revisi_url = f"{base_url.rstrip('/')}/login"

    subject_tpl = settings.get("email_tpl_company_rejected_subject") or DEFAULT_TEMPLATES["email_tpl_company_rejected_subject"]
    body_tpl = settings.get("email_tpl_company_rejected_body") or DEFAULT_TEMPLATES["email_tpl_company_rejected_body"]

    subject = subject_tpl.replace("{nama_perusahaan}", company_name).replace("{alasan_penolakan}", reason).replace("{revisi_url}", revisi_url)
    body = body_tpl.replace("{nama_perusahaan}", company_name).replace("{alasan_penolakan}", reason).replace("{revisi_url}", revisi_url)"""

if old_approved in content:
    content = content.replace(old_approved, new_approved)
    print("Patched send_company_approved_email to use dynamic domain URL")

if old_rejected in content:
    content = content.replace(old_rejected, new_rejected)
    print("Patched send_company_rejected_email to use dynamic domain URL")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Email dynamic URLs patch complete!")
