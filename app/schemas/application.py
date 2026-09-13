"""
📋 Schemas untuk Applications
"""
from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    job_id: str
    catatan_pelamar: str | None = None
    cv_data: dict
