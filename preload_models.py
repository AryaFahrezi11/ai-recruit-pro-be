"""
====================================================================
AI Recruit Pro - Preload AI Models Script
====================================================================
Script ini bertugas mengunduh dan memvalidasi semua model AI lokal
sebelum aplikasi berjalan (dijalankan saat Docker build atau setup VPS).
Dengan script ini:
1. Model tidak perlu di-download berulang kali saat request pertama.
2. Server FastAPI langsung siap pakai seketika saat container aktif.
3. Menghindari request timeout karena proses unduh model saat runtime.
====================================================================
"""
import os
import sys
import urllib.request
from ultralytics import YOLO
from faster_whisper import WhisperModel
from sentence_transformers import SentenceTransformer


def preload_all_models():
    print("==================================================")
    print("🚀 MEMULAI PROSES PRELOAD SEMUA MODEL AI...")
    print("==================================================")

    # 1. MediaPipe Face Landmarker (.task)
    face_model_file = "face_landmarker.task"
    print(f"\n[1/4] Memeriksa {face_model_file}...")
    if not os.path.exists(face_model_file):
        url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
        print(f"      Mengunduh model dari: {url}")
        urllib.request.urlretrieve(url, face_model_file)
        print("      ✓ Berhasil mengunduh face_landmarker.task!")
    else:
        print("      ✓ face_landmarker.task sudah tersedia.")

    # 2. YOLOv8 Pose Model (.pt)
    yolo_model_file = "yolov8n-pose.pt"
    print(f"\n[2/4] Memeriksa & memuat {yolo_model_file}...")
    try:
        # Ultralytics akan otomatis mendownload ke working dir jika belum ada
        YOLO(yolo_model_file)
        print("      ✓ YOLOv8n-pose siap digunakan!")
    except Exception as e:
        print(f"      ❌ Gagal memuat YOLOv8: {e}")
        sys.exit(1)

    # 3. SBERT Multilingual Model (HuggingFace Cache)
    sbert_name = "paraphrase-multilingual-MiniLM-L12-v2"
    print(f"\n[3/4] Mengunduh/memverifikasi SBERT model: {sbert_name}...")
    try:
        SentenceTransformer(sbert_name)
        print(f"      ✓ SBERT model '{sbert_name}' tersimpan di cache lokal!")
    except Exception as e:
        print(f"      ❌ Gagal memuat SBERT: {e}")
        sys.exit(1)

    # 4. Faster-Whisper Model Tiny int8 (HuggingFace Cache)
    whisper_size = "tiny"
    print(f"\n[4/4] Mengunduh/memverifikasi Faster-Whisper: {whisper_size} (int8 CPU)...")
    try:
        WhisperModel(whisper_size, device="cpu", compute_type="int8")
        print(f"      ✓ Faster-Whisper '{whisper_size}' tersimpan di cache lokal!")
    except Exception as e:
        print(f"      ❌ Gagal memuat Faster-Whisper: {e}")
        sys.exit(1)

    print("\n==================================================")
    print("🎉 SEMUA MODEL AI BERHASIL DIUNDUH & SIAP DIGUNAKAN!")
    print("==================================================")


if __name__ == "__main__":
    preload_all_models()
