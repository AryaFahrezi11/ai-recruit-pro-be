from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Date, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, index=True)  # pelamar, perusahaan, kampus, admin
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    email_verified_at = Column(DateTime(timezone=True))
    otp_code = Column(String(6), nullable=True)
    otp_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    pelamar_profile = relationship("PelamarProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    perusahaan_profile = relationship("PerusahaanProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    kampus_profile = relationship("KampusProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")


class PelamarProfile(Base):
    __tablename__ = "pelamar_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    nama_lengkap = Column(String(255), nullable=False)
    no_telepon = Column(String(20))
    alamat = Column(Text)
    ringkasan_diri = Column(Text)
    linkedin_url = Column(String(500))
    portfolio_url = Column(String(500))
    judul_posisi = Column(String(255))
    keahlian = Column(Text)
    sertifikasi = Column(Text)
    pengalaman_kerja = Column(Text)
    riwayat_pendidikan = Column(Text)
    social_links = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="pelamar_profile")
    cv_documents = relationship("CVDocument", back_populates="pelamar", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="pelamar", cascade="all, delete-orphan")


class PerusahaanProfile(Base):
    __tablename__ = "perusahaan_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    nama_perusahaan = Column(String(255), nullable=False)
    industri = Column(String(100))
    ukuran = Column(String(100))
    deskripsi = Column(Text)
    is_verified = Column(Boolean, default=False)
    status = Column(String(50), default="PENDING")
    rejection_reason = Column(Text, nullable=True)
    alamat = Column(Text)
    kota = Column(String(100))
    provinsi = Column(String(100))
    website_url = Column(String(500))
    logo_url = Column(String(500))
    no_telepon = Column(String(20))
    tahun_berdiri = Column(Integer)
    nib_number = Column(String(255))
    nib_document_url = Column(String(500))
    hr_name = Column(String(255))
    hr_whatsapp = Column(String(20))
    hr_position = Column(String(100))
    hr_id_card_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="perusahaan_profile")
    job_postings = relationship("JobPosting", back_populates="perusahaan", cascade="all, delete-orphan")


class KampusProfile(Base):
    __tablename__ = "kampus_profiles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    nama_kampus = Column(String(255), nullable=False)
    jenis = Column(String(10))
    alamat = Column(Text)
    kota = Column(String(100))
    provinsi = Column(String(100))
    website_url = Column(String(500))
    logo_url = Column(String(500))
    akreditasi = Column(String(10))
    nama_pic = Column(String(255))
    jabatan_pic = Column(String(100))
    no_telepon_pic = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="kampus_profile")


class PerusahaanSettings(Base):
    __tablename__ = "perusahaan_settings"
    
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    ai_default_threshold = Column(Integer, default=60)
    auto_invite_interview = Column(Boolean, default=True)
    auto_archive_rejected = Column(Boolean, default=True)
    video_weights_json = Column(Text, default='{"ability":20,"intelligent":20,"personality":20,"attitude":20,"emotionalIntelligence":20}')
    email_invitation_subject = Column(String, default="[Pemberitahuan Resmi] Undangan Wawancara Video - {{job_title}} di {{company_name}}")
    email_invitation_body = Column(Text, default="Yth. {{candidate_name}},\n\nSelamat! Kami menyampaikan bahwa profil dan kualifikasi Anda telah berhasil melewati tahap seleksi awal (CV Screening) untuk posisi {{job_title}} di {{company_name}}.\n\nSebagai tahapan selanjutnya, kami mengundang Anda untuk mengikuti sesi Wawancara Video AI (Virtual Interview). Sesi ini dirancang secara terstruktur dan dapat Anda akses melalui portal resmi kami berikut:\n{{interview_link}}\n\nMohon pastikan Anda menyelesaikan perekaman wawancara video ini sebelum tenggat waktu yang telah ditentukan pada sistem.\n\nKami sangat menghargai ketertarikan Anda untuk bergabung dengan {{company_name}} dan menantikan partisipasi Anda.\n\nHormat kami,\nTim Akuisisi Talenta (Talent Acquisition)\n{{company_name}}")
    email_hire_subject = Column(String, default="[Pemberitahuan Resmi] Penawaran Pekerjaan: Selamat Bergabung di {{company_name}}")
    email_hire_body = Column(Text, default="Yth. {{candidate_name}},\n\nKami membawa kabar gembira! Menindaklanjuti seluruh rangkaian proses rekrutmen yang telah Anda jalani, kami sangat terkesan dengan kualifikasi, pengalaman, dan potensi yang Anda tunjukkan.\n\nDengan ini, kami bermaksud menawarkan Anda posisi {{job_title}} di {{company_name}}.\n\nTim HR kami akan segera menghubungi Anda melalui email terpisah atau telepon untuk menyampaikan Dokumen Penawaran Resmi (Offering Letter) serta panduan proses administrasi (Onboarding) selanjutnya.\n\nKami sangat antusias menyambut Anda sebagai bagian dari tim kami.\n\nHormat kami,\nTim Manajemen & HR\n{{company_name}}")
    email_reject_subject = Column(String, default="[Pemberitahuan Resmi] Pembaruan Status Lamaran - {{job_title}} di {{company_name}}")
    email_reject_body = Column(Text, default="Yth. {{candidate_name}},\n\nTerima kasih atas waktu, usaha, dan antusiasme yang telah Anda berikan selama proses seleksi untuk posisi {{job_title}} di {{company_name}}.\n\nSetelah melalui serangkaian pertimbangan yang matang dari tim kami, dengan berat hati kami menyampaikan bahwa saat ini kami belum dapat melanjutkan proses pencalonan Anda ke tahapan berikutnya. Keputusan ini didasarkan pada penyesuaian kualifikasi dengan kebutuhan posisi saat ini.\n\nCatatan Evaluasi Tim HR:\n\"{{alasan_penolakan}}\"\n\nKami sangat mengapresiasi minat Anda terhadap {{company_name}}. Profil Anda akan tetap tersimpan dalam sistem basis data talenta kami, dan kami akan menghubungi Anda kembali apabila terdapat peluang karir lain yang lebih sesuai dengan kualifikasi Anda di masa mendatang.\n\nKami senantiasa mendoakan kesuksesan untuk perjalanan karir Anda selanjutnya.\n\nHormat kami,\nTim Akuisisi Talenta (Talent Acquisition)\n{{company_name}}")
    email_interview_user_subject = Column(String, default="[Pemberitahuan Resmi] Undangan Wawancara Lanjutan - {{job_title}} di {{company_name}}")
    email_interview_user_body = Column(Text, default="Yth. {{candidate_name}},\n\nSelamat! Berdasarkan hasil peninjauan menyeluruh terhadap tahapan wawancara sebelumnya, kami dengan senang hati mengundang Anda untuk melanjutkan ke tahapan Wawancara Lanjutan bersama Tim User/Manajemen kami.\n\nDetail jadwal wawancara Anda adalah sebagai berikut:\nPosisi: {{job_title}}\nJadwal: {{jadwal_wawancara}}\nLokasi / Tautan Meeting: {{lokasi_atau_link}}\n\nInstruksi tambahan dari Tim HR:\n{{catatan_hr}}\n\nUntuk keperluan kelancaran jadwal, kami memohon kesediaan Anda untuk mengonfirmasi kehadiran dengan membalas email ini secara langsung.\n\nTerima kasih atas dedikasi dan antusiasme Anda.\n\nHormat kami,\nTim Akuisisi Talenta (Talent Acquisition)\n{{company_name}}")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="perusahaan_settings")
