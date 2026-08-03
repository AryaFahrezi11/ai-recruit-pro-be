"""
🔐 Security: JWT Token & Password Hashing
"""
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings

# ============================================
# Password Hashing (bcrypt)
# ============================================

def hash_password(password: str) -> str:
    """Mengenkripsi password menggunakan bcrypt."""
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Memverifikasi password dengan hash-nya."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


# ============================================
# JWT Token
# ============================================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Membuat JWT access token.

    Args:
        data: Data yang akan disimpan di token (biasanya user_id & role)
        expires_delta: Durasi token berlaku
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Memverifikasi JWT token dari header Authorization.
    Digunakan sebagai dependency di router yang butuh autentikasi.

    Contoh penggunaan:
        @router.get("/profile")
        async def get_profile(current_user: dict = Depends(verify_token)):
            user_id = current_user["sub"]
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak valid atau sudah expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception
