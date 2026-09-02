"""
⚙️ Konfigurasi Aplikasi
Membaca environment variables dari file .env
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- App ---
    APP_NAME: str = "AI Recruit Pro"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # --- Database (SQLite untuk development) ---
    DATABASE_URL: str = "sqlite+aiosqlite:///./airecruitpro.db"

    # --- JWT Auth ---
    SECRET_KEY: str = "ganti-dengan-secret-key-yang-panjang-dan-random"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- AI Model ---
    SBERT_MODEL_NAME: str = "paraphrase-multilingual-MiniLM-L12-v2"
    CV_THRESHOLD_DEFAULT: float = 40.0
    INTERVIEW_THRESHOLD_DEFAULT: float = 40.0

    # --- CORS ---
    FRONTEND_URL: str = "http://localhost:3000"

    # --- Cloudinary ---
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # --- Supabase ---
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
