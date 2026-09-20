# 📄 DOKUMEN SERAH TERIMA PROYEK (PROJECT HANDOVER)
## SISTEM INFORMASI REKRUTMEN BERBASIS ARTIFICIAL INTELLIGENCE
### **AI RECRUIT PRO**

---

| Dokumen | Keterangan |
| :--- | :--- |
| **Nama Proyek** | AI Recruit Pro Platform |
| **Versi Rilis** | v1.0.0 (Production Ready) |
| **Tanggal Serah Terima** | September 2026 |
| **Pihak Pertama (Pengembang)** | Tim Pengembang / Developer |
| **Pihak Kedua (Klien)** | Stakeholder / Klien Penerima |
| **Status Repositori** | Siap Rilis (*Production Deployment*) |

---

## 📑 DAFTAR ISI
1. [Ringkasan Eksekutif](#1-ringkasan-eksekutif)
2. [Spesifikasi Arsitektur & Teknologi (Tech Stack)](#2-spesifikasi-arsitektur--teknologi-tech-stack)
3. [Daftar Fitur & Hak Akses (User Role Matrix)](#3-daftar-fitur--hak-akses-user-role-matrix)
4. [Topologi Infrastruktur & Deployment](#4-topologi-infrastruktur--deployment)
5. [Inventaris Akun & Kredensial Sistem](#5-inventaris-akun--kredensial-sistem)
6. [Panduan Operasional & Pemeliharaan (SOP)](#6-panduan-operasional--pemeliharaan-sop)
7. [Prosedur Backup & Pemulihan Database](#7-prosedur-backup--pemulihan-database)
8. [Panduan Pemecahan Masalah (Troubleshooting)](#8-panduan-pemecahan-masalah-troubleshooting)
9. [Struktur Repositori & Kode Program](#9-struktur-repositori--kode-program)
10. [Lembar Pengesahan Serah Terima](#10-lembar-pengesahan-serah-terima)

---

## 1. Ringkasan Eksekutif

**AI Recruit Pro** adalah platform rekrutmen cerdas terintegrasi (*end-to-end recruitment platform*) yang dirancang untuk mempercepat proses seleksi kandidat menggunakan teknologi kecerdasan buatan (*Artificial Intelligence*).

### Nilai Utama Sistem:
* **ATS Resume AI Matcher:** Mencocokkan kualifikasi CV pelamar dengan deskripsi pekerjaan (*Job Description*) menggunakan pemrosesan bahasa alami multilingual (*SBERT Semantic Search*), menghasilkan skor kesesuaian objektif (0–100%).
* **AI Video Interview Screening:** Menganalisa ekspresi, kontak mata (*eye contact*), kestabilan postur, dan respon kandidat saat menjawab pertanyaan wawancara video secara otomatis menggunakan computer vision.
* **Multi-Portal Collaboration:** Menyediakan portal terpisah yang disesuaikan untuk Pelamar, Perusahaan (HR/Recruiter), Mitra Kampus (Career Center), dan Admin Sistem.

---

## 2. Spesifikasi Arsitektur & Teknologi (Tech Stack)

### A. Frontend (Antarmuka Pengguna)
* **Framework:** Next.js 16 (React 19, App Router architecture)
* **Bahasa Pemrograman:** TypeScript
* **Styling & Desain:** Tailwind CSS v4, Lucide React Icons
* **State Management:** Zustand
* **Data Fetching:** TanStack React Query v5
* **Grafik & Visualisasi:** Recharts
* **Hosting:** Vercel Global Edge Network

### B. Backend (Layanan API & Logika Bisnis)
* **Framework:** FastAPI (Python 3.10+ / 3.12)
* **Web Server:** Uvicorn ASGI Server
* **ORM / Database Layer:** SQLAlchemy (AsyncIO) dengan konektor `aiomysql`
* **Validasi Skema:** Pydantic v2
* **Keamanan:** JWT (*JSON Web Tokens*) dengan enkripsi password Bcrypt
* **Containerization:** Docker & Docker Compose
* **Hosting:** Virtual Private Server (VPS Linux Ubuntu KVM)

### C. Modul Kecerdasan Buatan (AI / ML)
* **Semantic Matching:** `SentenceTransformers` (`paraphrase-multilingual-MiniLM-L12-v2`) untuk pencocokan semantik teks bahasa Indonesia & Inggris.
* **Face & Gaze Tracking:** Google MediaPipe Face Landmarker (`face_landmarker.task`) untuk analisis kontak mata dan ekspresi.
* **Posture Analysis:** Ultralytics YOLOv8 Pose (`yolov8n-pose.pt`) untuk deteksi postur tegak pelamar selama wawancara.

### D. Layanan Eksternal (Third-Party Services)
* **Database:** MySQL 8.0 Engine
* **DNS & CDN:** Cloudflare (SSL/TLS Encryption, DDoS Protection, DNS Caching)
* **Email Gateway:** Resend API (Pengiriman email otomatis status lamaran & verifikasi akun)
* **Penyimpanan Berkas:** Cloudflare R2 / S3-compatible Object Storage & Local Mounted Storage

---

## 3. Daftar Fitur & Hak Akses (User Role Matrix)

| Modul / Fitur | Pelamar | Perusahaan (HR) | Kampus | Super Admin |
| :--- | :---: | :---: | :---: | :---: |
| Registrasi, Login & Autentikasi JWT | ✅ | ✅ | ✅ | ✅ |
| Eksplorasi Lowongan & Filter Kategori/Gaji | ✅ | ❌ | ✅ | ✅ |
| Submit Lamaran & Upload CV (PDF) | ✅ | ❌ | ❌ | ❌ |
| Skrining CV Otomatis oleh AI (Skor ATS) | ✅ *(Lihat Skor)* | ✅ *(Review & Urutkan)* | ❌ | ✅ |
| Wawancara Video AI Interaktif (Kamera & Mic) | ✅ | ❌ | ❌ | ❌ |
| Manajemen Loker (Buat, Edit, Tutup Loker) | ❌ | ✅ | ❌ | ✅ |
| Candidate Pipeline (Review, Terima, Tolak) | ❌ | ✅ | ❌ | ✅ |
| Undangan Wawancara via Email Otomatis | ❌ | ✅ | ❌ | ✅ |
| Manajemen Kemitraan Kampus / Magang | ❌ | ✅ *(Request Kemitraan)* | ✅ | ✅ |
| Tracking Alumni / Mahasiswa Kampus | ❌ | ❌ | ✅ | ✅ |
| Konfigurasi Ambang Batas AI (Threshold) | ❌ | ❌ | ❌ | ✅ |
| Audit Log & Manajemen Pengguna Platform | ❌ | ❌ | ❌ | ✅ |

---

## 4. Topologi Infrastruktur & Deployment

```
[ Pengguna Publik / Internet ]
             │
             ▼
     [ Cloudflare DNS & WAF ]
     (airecruit-pro.com)
     ├── CNAME (@, www) ──────────► [ Vercel Edge Hosting ]
     │                               ├── Next.js Frontend App
     │                               └── Auto-deploy via GitHub (main)
     │
     └── A Record (api) ──────────► [ VPS Arenhost KVM ]
                                     ├── Port 80/443 (Nginx Reverse Proxy)
                                     │         │
                                     │   (Proxy Pass 127.0.0.1:8000)
                                     │         ▼
                                     └── [ Docker Compose Environment ]
                                           ├── Backend Container (FastAPI)
                                           ├── Database Container (MySQL 8)
                                           └── Persistent Volumes (/uploads & AI Cache)
```

---

## 5. Inventaris Akun & Kredensial Sistem

> ⚠️ **PENTING:** Seluruh kata sandi di bawah wajib diperbarui oleh tim klien setelah serah terima selesai dilakukan.

| No | Layanan / Komponen | Tautan Akses / Host | Username / Identifier | Status / Catatan |
| :---: | :--- | :--- | :--- | :--- |
| 1 | **Domain Registrar** | Arenhost Client Area | `[Email Akun Klien]` | Domain: `airecruit-pro.com` |
| 2 | **DNS Manager & CDN** | Cloudflare Dashboard | `[Email Cloudflare Klien]` | Nameserver diarahkan dari Arenhost |
| 3 | **VPS Server (Backend)** | SSH `[IP_VPS]` Port `22` | `root` / `ubuntu` | KVM Ubuntu 22.04 LTS (Docker ready) |
| 4 | **Frontend Hosting** | Vercel Dashboard | `[Akun GitHub/Vercel]` | Terhubung ke branch `main` |
| 5 | **GitHub Backend Repo** | GitHub.com | `AryaFahrezi11/ai-recruit-pro-be` | Branch utama: `siap_deploy` |
| 6 | **GitHub Frontend Repo** | GitHub.com | `Aryafahrezi11/ai-recruit-pro-FE` | Branch utama: `main` |
| 7 | **Email Gateway** | Resend.com | `[Akun Resend]` | API Key tersimpan di `.env` backend |
| 8 | **Akun Super Admin** | `/auth/login` | `admin@airecruit-pro.com` | Akses penuh dashboard kontrol |

---

## 6. Panduan Operasional & Pemeliharaan (SOP)

### A. Memeriksa Status Layanan di VPS
Buka terminal dan masuk ke VPS via SSH:
```bash
ssh root@IP_VPS_ANDA
cd ~/backend
docker compose ps
```
Semua container (`backend` dan `db`) harus berada dalam status `Up (healthy)`.

### B. Memantau Log Aktivitas / Error
Untuk melihat aktivitas real-time FastAPI dan pemrosesan AI:
```bash
# Pantau 50 log terakhir secara langsung
docker compose logs -f backend --tail 50
```

### C. Cara Melakukan Update Kode Backend
Jika terdapat pembaruan kode di repositori GitHub:
```bash
cd ~/backend
git pull origin siap_deploy
docker compose down
docker compose up -d --build
```

### D. Cara Melakukan Update Kode Frontend
Frontend dikonfigurasi dengan *Continuous Deployment* (CI/CD) Vercel:
* Cukup lakukan `git push origin main` pada repositori frontend.
* Vercel akan otomatis melakukan proses *building* dan rilis dalam waktu ±1–2 menit tanpa downtime.

---

## 7. Prosedur Backup & Pemulihan Database

### A. Pencadangan Rutin (Backup)
Jalankan perintah berikut di VPS untuk membuat dump database MySQL:
```bash
# Format nama file dengan tanggal
BACKUP_NAME="backup_airecruit_$(date +'%Y%m%d_%H%M%S').sql"

# Eksekusi dump dari dalam container
docker compose exec -T db mysqldump -u root -p[PASSWORD_DB] airecruitpro > ~/backups/$BACKUP_NAME

# Kompresi file backup
gzip ~/backups/$BACKUP_NAME
```
*Disarankan membuat Cron Job harian untuk mengotomasi proses ini ke penyimpanan offsite (Google Drive / Cloudflare R2).*

### B. Pemulihan Database (Restore)
Jika ingin merestorasi database dari file backup:
```bash
gunzip < ~/backups/backup_airecruit_YYYYMMDD.sql.gz | docker compose exec -T db mysql -u root -p[PASSWORD_DB] airecruitpro
```

---

## 8. Panduan Pemecahan Masalah (Troubleshooting)

| Gejala Masalah | Penyebab Umum | Solusi Praktis |
| :--- | :--- | :--- |
| **Kamera/Mic Wawancara Video Tidak Terbuka** | Website diakses melalui koneksi HTTP (bukan HTTPS). | Pastikan domain sudah aktif sertifikat SSL-nya via Cloudflare / Certbot. Browser memblokir media stream pada non-HTTPS. |
| **Upload CV / Video Gagal (Error 413)** | Ukuran berkas melebihi batas request Nginx. | Tambahkan direktif `client_max_body_size 50M;` pada konfigurasi Nginx reverse proxy di VPS. |
| **Pesan Error 502 / 504 Gateway Timeout** | Container backend FastAPI mati atau restart karena kehabisan RAM. | 1. Cek log: `docker compose logs backend --tail 100`<br>2. Pastikan Virtual Memory (Swap 4GB) aktif: `swapon --show`. |
| **Email Notifikasi Lamaran Tidak Masuk** | Batas kuota Resend API habis atau domain pengirim belum diverifikasi (*unverified domain*). | Masuk ke dashboard [Resend.com](https://resend.com), pastikan status domain DKIM/SPF terverifikasi dan API Key valid. |
| **Perubahan Data Profil Belum Muncul** | Cache browser atau token kadaluarsa. | Lakukan refresh halaman atau logout dan login kembali untuk memperbarui JWT session. |

---

## 9. Struktur Repositori & Kode Program

### Repositori Backend (`backend-airecruitpro`)
```text
backend-airecruitpro/
├── app/
│   ├── core/           # Konfigurasi aplikasi, env, database engine, security
│   ├── models/         # Model tabel database SQLAlchemy
│   ├── schemas/        # Skema validasi data request/response Pydantic
│   ├── routers/        # Endpoint API (auth, jobs, applications, analysis, dll)
│   └── services/       # AI Engine (embedding_service, video_analyzer, email)
├── uploads/            # Direktori penyimpanan berkas lokal (CV & Logo)
├── Dockerfile          # Spesifikasi container backend dengan OpenCV/PyTorch
├── docker-compose.yml  # Orkestrasi multi-container (FastAPI + MySQL)
├── requirements.txt    # Dependensi pustaka Python
└── preload_models.py   # Script pemuat model AI ke dalam cache
```

### Repositori Frontend (`frontend-airecruitpro`)
```text
frontend-airecruitpro/
├── app/
│   ├── applicant/      # Halaman & fitur khusus kandidat/pelamar
│   ├── recruiter/      # Halaman & fitur khusus perusahaan/HR
│   ├── campus/         # Halaman & fitur kemitraan kampus
│   ├── admin/          # Dashboard manajemen & analitik platform
│   └── layout.tsx      # Kerangka layout utama dan navbar responsif
├── components/         # Komponen UI modular (Navbar, Drawer, Modals, Tables)
├── hooks/              # Custom React Hooks untuk data fetching & animasi
├── lib/
│   ├── api.ts          # Abstraksi koneksi Axios/Fetch ke backend
│   └── utils.ts        # Helper formatting tanggal, currency, dan status
└── public/             # Aset statis gambar, logo, dan favicon
```

---

## 10. Lembar Pengesahan Serah Terima

Dengan ditandatanganinya dokumen ini, maka:
1. Pihak Pertama telah menyelesaikan dan menyerahkan seluruh kode program, dokumentasi, serta akses infrastruktur sistem **AI Recruit Pro** sesuai dengan lingkup kerja yang disepakati.
2. Pihak Kedua telah memeriksa, menguji coba fungsi-fungsi utama platform, dan menerima hasil penyerahan proyek dalam kondisi baik dan siap digunakan.

Dibuat dan disahkan di: _______________________  
Pada tanggal: _______________________ 2026  

<br>

| Pihak Pertama (Pengembang) | Pihak Kedua (Klien / Pemilik) |
| :---: | :---: |
| <br><br><br><br> | <br><br><br><br> |
| ( __________________________ ) | ( __________________________ ) |
| *Lead Developer* | *Product Owner / Client Representative* |
