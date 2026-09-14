import os
import uuid
import mimetypes
import logging
from typing import Optional
from fastapi import HTTPException
from app.core.config import settings

# Boto3 client untuk Cloudflare R2 Object Storage
logger = logging.getLogger(__name__)

def is_r2_configured() -> bool:
    """Cek apakah kredensial Cloudflare R2 sudah lengkap di konfigurasi."""
    return bool(
        settings.R2_ACCOUNT_ID and 
        settings.R2_ACCESS_KEY_ID and 
        settings.R2_SECRET_ACCESS_KEY and
        settings.R2_BUCKET_NAME
    )

def is_cloudinary_configured() -> bool:
    """Cek apakah kredensial Cloudinary sudah lengkap."""
    return bool(
        settings.CLOUDINARY_CLOUD_NAME and 
        settings.CLOUDINARY_API_KEY and 
        settings.CLOUDINARY_API_SECRET
    )

def get_r2_client():
    """Menginisialisasi boto3 S3 client yang terhubung ke Cloudflare R2."""
    import boto3
    from botocore.config import Config

    raw_id = settings.R2_ACCOUNT_ID.strip()
    if raw_id.startswith("http://") or raw_id.startswith("https://"):
        endpoint_url = raw_id.rstrip("/")
    elif ".r2.cloudflarestorage.com" in raw_id:
        endpoint_url = f"https://{raw_id}".rstrip("/")
    else:
        endpoint_url = f"https://{raw_id}.r2.cloudflarestorage.com"

    return boto3.client(
        service_name="s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID.strip(),
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY.strip(),
        region_name="auto",
        config=Config(signature_version="s3v4")
    )

def upload_video_file(local_path: str, original_filename: str) -> str:
    """
    Mengunggah video wawancara dengan urutan prioritas:
    1. Cloudflare R2 (Penyimpanan utama: Gratis Egress / Bebas Kuota Download)
    2. Cloudinary (Cadangan / Fallback)
    """
    # 1. Coba Cloudflare R2
    if is_r2_configured():
        try:
            client = get_r2_client()
            clean_name = os.path.basename(original_filename).replace(" ", "_")
            file_key = f"interviews/{uuid.uuid4().hex[:12]}_{clean_name}"
            
            content_type, _ = mimetypes.guess_type(local_path)
            if not content_type:
                content_type = "video/mp4"

            logger.info(f"Mengunggah file ke Cloudflare R2 ({settings.R2_BUCKET_NAME}/{file_key})...")
            client.upload_file(
                local_path,
                settings.R2_BUCKET_NAME,
                file_key,
                ExtraArgs={"ContentType": content_type}
            )

            # Susun Public URL
            if settings.R2_PUBLIC_URL:
                public_base = settings.R2_PUBLIC_URL.rstrip("/")
                return f"{public_base}/{file_key}"
            else:
                # Fallback ke direct r2 endpoint jika public url belum diset
                return f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com/{settings.R2_BUCKET_NAME}/{file_key}"
        except Exception as e:
            logger.error(f"Gagal mengunggah ke Cloudflare R2: {e}")
            if not is_cloudinary_configured():
                raise HTTPException(status_code=500, detail=f"Gagal upload video ke Cloudflare R2: {str(e)}")

    # 2. Coba Cloudinary sebagai Fallback
    if is_cloudinary_configured():
        try:
            import cloudinary.uploader
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET
            )
            upload_result = cloudinary.uploader.upload(
                local_path, 
                resource_type="video",
                folder="ai_recruit_interviews"
            )
            return upload_result.get("secure_url")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Gagal mengunggah video ke Cloudinary: {str(e)}")

    raise HTTPException(
        status_code=500, 
        detail="Penyimpanan media belum dikonfigurasi. Harap isi kredensial Cloudflare R2 atau Cloudinary di file .env."
    )


def download_video_file_to_local(video_url: str, local_path: str):
    """
    Mengunduh video wawancara ke disk lokal untuk dianalisis oleh AI.
    Jika video berada di Cloudflare R2, proses unduh dilakukan langsung via S3 Client (boto3)
    sehingga 100% bypass DNS Telkomsel/Internet Baik dan tidak akan error SSL mismatch.
    """
    # 1. Jika URL berasal dari Cloudflare R2
    if is_r2_configured() and ("r2.dev" in video_url or "cloudflarestorage.com" in video_url):
        try:
            if "/interviews/" in video_url:
                file_key = "interviews/" + video_url.split("/interviews/")[-1].split("?")[0]
            else:
                file_key = video_url.split("/")[-1].split("?")[0]

            logger.info(f"Mengunduh langsung dari bucket Cloudflare R2 via S3: {file_key}")
            client = get_r2_client()
            client.download_file(settings.R2_BUCKET_NAME, file_key, local_path)
            return
        except Exception as e:
            logger.warning(f"Gagal download via S3 Client: {e}, mencoba fallback HTTP...")

    # 2. Fallback HTTP untuk Cloudinary atau sumber lainnya
    import urllib.request
    import ssl
    import shutil

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(
        video_url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    )
    with urllib.request.urlopen(req, context=ctx) as response, open(local_path, "wb") as out_file:
        shutil.copyfileobj(response, out_file)


def get_video_playback_url(video_url: str, expires_in: int = 86400) -> str:
    """
    Menghasilkan URL playback video yang aman.
    Jika file tersimpan di R2, menghasilkan URL presigned resmi dari cloudflarestorage.com
    yang tidak diblokir oleh Telkomsel / Internet Baik.
    """
    if not video_url:
        return ""
    
    if is_r2_configured() and ("r2.dev" in video_url or "cloudflarestorage.com" in video_url):
        try:
            if "/interviews/" in video_url:
                file_key = "interviews/" + video_url.split("/interviews/")[-1].split("?")[0]
            else:
                file_key = video_url.split("/")[-1].split("?")[0]

            client = get_r2_client()
            return client.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.R2_BUCKET_NAME, "Key": file_key},
                ExpiresIn=expires_in
            )
        except Exception as e:
            logger.warning(f"Gagal membuat presigned URL: {e}")

    return video_url

