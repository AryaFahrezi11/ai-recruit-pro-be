"""
🔐 Security: JWT Token & Password Hashing
"""
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings

# ============================================
# Password Hashing (bcrypt)
# ============================================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Mengenkripsi password menggunakan bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Memverifikasi password dengan hash-nya."""
    return pwd_context.verify(plain_password, hashed_password)


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
