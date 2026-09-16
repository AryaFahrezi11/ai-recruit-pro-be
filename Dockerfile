# Menggunakan Python 3.11 Slim yang stabil untuk PyTorch, MediaPipe, dan OpenCV
FROM python:3.11-slim

# Menghindari interaksi manual & optimasi buffering python
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install dependency tingkat OS (C/C++ libraries) untuk MediaPipe, OpenCV, FFmpeg, dan OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    libegl1 \
    libgles2 \
    libglib2.0-0 \
    tesseract-ocr \
    tesseract-ocr-ind \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Upgrade pip ke versi terbaru
RUN pip install --no-cache-dir --upgrade pip

# Salin daftar dependency
COPY requirements.txt .

# 1. Install PyTorch CPU-only build lebih dulu (Hanya ~180MB, menghemat >2GB dibanding versi CUDA)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 2. Install seluruh dependency aplikasi
RUN pip install --no-cache-dir -r requirements.txt

# Salin file proyek backend dan model yang sudah ada
COPY . .

# Expose port FastAPI
EXPOSE 8000

# Jalankan preload model saat container start, lalu jalankan Uvicorn (hemat space build image)
CMD ["sh", "-c", "python preload_models.py && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"]
