import re
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional

class AdminUserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    role: str
    name: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Kata sandi minimal 8 karakter")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Kata sandi harus mengandung minimal satu huruf kapital")
        if not re.search(r"[a-z]", v):
            raise ValueError("Kata sandi harus mengandung minimal satu huruf kecil")
        if not re.search(r"\d", v):
            raise ValueError("Kata sandi harus mengandung minimal satu angka")
        if not re.search(r"[@$!%*?&#^_\-]", v):
            raise ValueError("Kata sandi harus mengandung minimal satu karakter spesial (@$!%*?&#^_-)")
        return v

class AdminUserUpdateRequest(BaseModel):
    email: EmailStr
    role: str
    name: str
