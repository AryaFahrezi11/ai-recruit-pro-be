"""
🧠 AI Recruit Pro - Backend API
Entry point aplikasi FastAPI
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.services.embedding_service import EmbeddingService

# ============================================
# Lifespan: Load model AI saat server start
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Memuat model AI ke RAM saat server pertama kali dijalankan.
    Model akan tetap di RAM selama server aktif.
    """
    print("⏳ Memuat model AI...")
    app.state.embedding_service = EmbeddingService()
    print(f"✅ Model '{settings.SBERT_MODEL_NAME}' berhasil dimuat!")
    print(f"🚀 AI Recruit Pro Backend siap menerima request!")
    yield
    # Cleanup saat server mati
    print("👋 Server dimatikan. Model AI di-unload dari RAM.")


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
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Register Routers
# ============================================
from app.routers import auth, users, jobs, applications, analysis

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(applications.router, prefix="/api/applications", tags=["Applications"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["AI Analysis"])


# ============================================
# Root Endpoint
# ============================================
@app.get("/")
async def root():
    return {
        "nama": settings.APP_NAME,
        "versi": settings.APP_VERSION,
        "status": "🟢 Online",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
