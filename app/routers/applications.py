"""
🛣️ Applications Router
Endpoint: /api/applications
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_applications():
    """Mendapatkan daftar lamaran (pelamar: lamarannya, perusahaan: semua pelamar)."""
    # TODO: Implementasi dengan database
    return {"message": "Daftar lamaran", "data": []}


@router.post("/")
async def create_application():
    """Pelamar melamar ke suatu posisi."""
    # TODO: Implementasi dengan database
    return {"message": "Lamaran berhasil dikirim (placeholder)"}


@router.get("/{application_id}")
async def get_application(application_id: str):
    """Mendapatkan detail lamaran beserta status pipeline."""
    # TODO: Implementasi dengan database
    return {"message": f"Detail lamaran {application_id}"}
