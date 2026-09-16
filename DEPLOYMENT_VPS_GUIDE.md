# 🚀 Panduan Deployment VPS (RAM 4GB, 2 CPU) - AI Recruit Pro

Panduan ini disusun khusus agar backend FastAPI (beserta model AI: YOLOv8, SBERT, Faster-Whisper, MediaPipe) dan database **MySQL** dapat berjalan stabil tanpa crash/OOM (Out of Memory) pada VPS dengan spesifikasi **RAM 4GB & 2 vCPU**.

---

## ⚠️ Langkah 1: Buat 4GB Swap File di Ubuntu VPS (Wajib!)

VPS dengan RAM 4GB membutuhkan virtual RAM tambahan (Swap) agar saat pemrosesan video atau transkripsi Whisper terjadi lonjakan memori, server tidak *freeze* atau me-reboot sendiri.

Jalankan perintah ini melalui terminal SSH VPS:

```bash
# 1. Buat file swap sebesar 4GB
sudo fallocate -l 4G /swapfile

# 2. Atur permission file swap
sudo chmod 600 /swapfile

# 3. Format file sebagai swap space
sudo mkswap /swapfile

# 4. Aktifkan swap
sudo swapon /swapfile

# 5. Pasang permanen agar aktif saat VPS restart
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 6. Cek apakah swap sudah aktif (harus muncul swap ~4GB)
free -h
```

---

## 📦 Langkah 2: Install Docker & Docker Compose di VPS

Jika VPS belum terpasang Docker:

```bash
# Update repository
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

# Install Docker & Docker Compose plugin
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Pasang permission ke user saat ini
sudo usermod -aG docker $USER
```

---

## ⚙️ Langkah 3: Siapkan Proyek & File Environment

1. Clone atau copy folder `backend-airecruitpro` ke VPS:
   ```bash
   cd /var/www/backend-airecruitpro  # atau folder pilihan Anda
   ```

2. Buat file `.env` di direktori backend:
   ```bash
   nano .env
   ```
   Isi contoh konfigurasi:
   ```env
   # MySQL Configuration
   MYSQL_ROOT_PASSWORD=PasswordRootAman123!
   MYSQL_DATABASE=airecruitpro
   MYSQL_USER=airecruit_user
   MYSQL_PASSWORD=PasswordUserAman123!

   # App Secret
   SECRET_KEY=kombinasi_rahasia_dan_panjang_acak_min_32_karakter
   FRONTEND_URL=https://app.domainanda.com

   # Cloudflare R2 Storage (Opsional jika simpan file di cloud)
   R2_ACCOUNT_ID=
   R2_ACCESS_KEY_ID=
   R2_SECRET_ACCESS_KEY=
   R2_BUCKET_NAME=airecruitpro
   R2_PUBLIC_URL=
   ```

---

## 🚢 Langkah 4: Build & Jalankan Container

Jalankan perintah berikut:

```bash
# Jalankan container (Docker akan otomatis mengunduh dependency dan preload model AI)
docker compose up -d --build
```

> **Apa yang terjadi saat proses build?**
> 1. Menginstall PyTorch versi CPU khusus (hanya ~180MB, bukan 2.5GB).
> 2. Menginstall library sistem (FFmpeg, OpenCV Headless, MediaPipe, Tesseract OCR).
> 3. Menjalankan `preload_models.py` yang otomatis mengunduh dan mem-validasi:
>    - Model SBERT (`paraphrase-multilingual-MiniLM-L12-v2`) ke HuggingFace cache.
>    - Model Faster-Whisper (`tiny` int8).
>    - Model `yolov8n-pose.pt` dan `face_landmarker.task`.
> 4. Mengonfigurasi MySQL dengan batas RAM 128MB InnoDB Buffer Pool agar hemat memori.

---

## 🔍 Langkah 5: Memeriksa Status & Log

```bash
# Cek apakah kedua container (backend & db) sedang berjalan
docker compose ps

# Melihat log proses backend secara live
docker compose logs -f backend

# Melihat log database MySQL
docker compose logs -f db

# Cek penggunaan RAM real-time
docker stats
```

---

## 🛡️ Rangkuman Optimasi RAM 4GB:

| Komponen | Alokasi Normal Default | Alokasi Dioptimasi di Setup Ini |
| :--- | :--- | :--- |
| **MySQL 8.0** | 1.2 GB - 2.0 GB | **~250 MB - 350 MB** (`innodb-buffer-pool-size=128M`) |
| **PyTorch Wheel** | ~2.5 GB (CUDA build) | **~180 MB** (CPU build) |
| **Uvicorn Worker** | Multi-worker (4x RAM) | **1 Worker** (Single process asynchronous) |
| **SBERT + Whisper** | Download saat runtime (hang) | **Preloaded saat build** |
| **Safety Net** | Tanpa Swap (Crash OOM) | **4GB Swap File** |
