from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import time
from app.core.database import get_db
from app.models.setting import SystemSetting

router = APIRouter()

_config_cache = None
_config_cache_time = 0
CONFIG_CACHE_TTL = 30  # detik

def invalidate_config_cache():
    global _config_cache, _config_cache_time
    _config_cache = None
    _config_cache_time = 0

@router.get("/public")
async def get_public_config(db: AsyncSession = Depends(get_db)):
    global _config_cache, _config_cache_time
    now = time.time()
    if _config_cache is not None and (now - _config_cache_time) < CONFIG_CACHE_TTL:
        return _config_cache

    keys = ["maintenance_mode", "seo_title", "seo_description", "admin_email", "smtp_from", "smtp_user", "support_whatsapp", "lokasi_kantor_pusat"]
    result = await db.execute(select(SystemSetting).where(SystemSetting.key.in_(keys)))
    settings = result.scalars().all()
    
    config = {
        "maintenance_mode": False,
        "seo_title": "AI Recruit Pro",
        "seo_description": "Platform Rekrutmen Cerdas Berbasis AI",
        "admin_email": ""
    }
    
    parsed = {}
    for s in settings:
        try:
            val = json.loads(s.value)
        except:
            val = s.value
        parsed[s.key] = val
        
        if s.key == "maintenance_mode":
            config["maintenance_mode"] = val == True or str(val).lower() == "true"
        elif s.key in ["seo_title", "seo_description"]:
            config[s.key] = val

    # Ambil email admin terdaftar dari system_settings
    admin_email = parsed.get("admin_email") or parsed.get("smtp_from") or parsed.get("smtp_user") or ""
    config["admin_email"] = admin_email
    config["support_whatsapp"] = parsed.get("support_whatsapp") or ""
    config["lokasi_kantor_pusat"] = parsed.get("lokasi_kantor_pusat") or ""
            
    _config_cache = config
    _config_cache_time = now
    return config

