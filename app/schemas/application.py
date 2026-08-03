"""
📋 Schemas untuk Applications
"""
from pydantic import BaseModel
from datetime import datetime


class ApplicationCreate(BaseModel):
    job_id: str
    catatan_pelamar: str | None = None


class ApplicationResponse(BaseModel):
    id: str
    job_id: str
    status: str
    applied_at: datetime | None = None

    class Config:
        from_attributes = True
