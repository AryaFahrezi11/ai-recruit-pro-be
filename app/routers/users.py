"""
🛣️ Users Router
Endpoint: GET /api/users/profile, PUT /api/users/profile
"""
from fastapi import APIRouter, Depends
from app.core.security import verify_token

router = APIRouter()


@router.get("/profile")
async def get_profile(current_user: dict = Depends(verify_token)):
    """
    Mendapatkan profil user yang sedang login.
    """
    # TODO: Implementasi dengan database
    return {
        "user_id": current_user.get("sub"),
        "role": current_user.get("role"),
        "message": "Endpoint profil - akan diimplementasi setelah database siap"
    }


@router.put("/profile")
async def update_profile(current_user: dict = Depends(verify_token)):
    """
    Mengupdate profil user yang sedang login.
    """
    # TODO: Implementasi dengan database
    return {"message": "Profil berhasil diupdate (placeholder)"}
