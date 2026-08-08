"""
🧠 AI Recruit Pro - Backend API
Entry point aplikasi FastAPI
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.services.embedding_service import EmbeddingService
from app.core.database import engine, Base
from app.models import *  # Memastikan semua model ter-load sebelum create_all

# ============================================
# Lifespan: Load model AI & Init DB saat server start
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Memuat model AI ke RAM dan inisialisasi database.
    """
    # 1. Inisialisasi Database
    print("[INFO] Membuat tabel database (jika belum ada)...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] Database siap!")

    # 2. Load Model AI
    print("[INFO] Memuat model AI...")
    app.state.embedding_service = EmbeddingService()
    print(f"[OK] Model '{settings.SBERT_MODEL_NAME}' berhasil dimuat!")
    print(f"[OK] AI Recruit Pro Backend siap menerima request!")
    yield
    # Cleanup saat server mati
    print("[INFO] Server dimatikan. Model AI di-unload dari RAM.")


# ============================================
# Inisialisasi FastAPI App
# ============================================
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend API untuk platform rekrutmen berbasis AI",
    lifespan=lifespan,
)

# ============================================
# CORS Middleware (agar frontend bisa akses API)
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Static Files (untuk upload dokumen)
# ============================================
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ============================================
# Register Routers
# ============================================
from app.routers import auth, users, jobs, applications, analysis, saved_jobs, admin, perusahaan

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(applications.router, prefix="/api/applications", tags=["Applications"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["AI Analysis"])
app.include_router(saved_jobs.router, prefix="/api/saved-jobs", tags=["Saved Jobs"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin Developer"])
app.include_router(perusahaan.router, prefix="/api/perusahaan", tags=["Perusahaan"])


# ============================================
# Root Endpoint
# ============================================
@app.get("/")
async def root():
    return {
        "nama": settings.APP_NAME,
        "versi": settings.APP_VERSION,
        "status": "Online",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
