from pydantic import BaseModel, EmailStr
from typing import Optional

class AdminUserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    role: str
    name: str

class AdminUserUpdateRequest(BaseModel):
    email: EmailStr
    role: str
    name: str
