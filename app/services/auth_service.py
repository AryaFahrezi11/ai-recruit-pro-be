"""
🔐 Auth Service (Placeholder)
Logika bisnis untuk autentikasi.
Akan diimplementasi setelah database siap.
"""
from app.core.security import hash_password, verify_password, create_access_token


class AuthService:
    """
    Service untuk autentikasi user.
    """

    async def register(self, email: str, password: str, role: str) -> dict:
        """Mendaftarkan user baru."""
        # TODO: Implementasi dengan database
        hashed = hash_password(password)
        token = create_access_token(data={"sub": "user-id", "role": role})
        return {
            "access_token": token,
            "token_type": "bearer",
            "role": role,
            "user_id": "user-id-placeholder"
        }

    async def login(self, email: str, password: str) -> dict:
        """Login user."""
        # TODO: Implementasi dengan database
        token = create_access_token(data={"sub": "user-id", "role": "pelamar"})
        return {
            "access_token": token,
            "token_type": "bearer",
            "role": "pelamar",
            "user_id": "user-id-placeholder"
        }
