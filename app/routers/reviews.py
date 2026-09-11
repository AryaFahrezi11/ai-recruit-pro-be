from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from typing import List, Optional
from pydantic import BaseModel
import datetime

from app.core.database import get_db
from app.core.security import verify_token
from app.models.review import PlatformReview
from app.models.user import User, PelamarProfile, PerusahaanProfile

router = APIRouter(prefix="/reviews", tags=["Reviews"])

class ReviewCreate(BaseModel):
    rating: int
    role: Optional[str] = None
    category: Optional[str] = None
    comment: Optional[str] = None
    context_event: Optional[str] = None
    is_anonymous: bool = False

class ReviewResponse(BaseModel):
    id: str
    name: Optional[str] = None
    role: Optional[str] = None
    rating: int
    category: Optional[str] = None
    comment: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

@router.post("/", response_model=ReviewResponse)
async def submit_review(
    review_data: ReviewCreate,
    current_user_data: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    user_id = current_user_data.get("sub")
    role = current_user_data.get("role")

    name = "User"
    role_desc = review_data.role if review_data.role else "Pelamar Kerja"

    if role == "pelamar":
        res = await db.execute(select(PelamarProfile).where(PelamarProfile.user_id == user_id))
        prof = res.scalars().first()
        if prof:
            name = prof.nama_lengkap
            if not review_data.role and prof.judul_posisi:
                role_desc = prof.judul_posisi
    elif role == "perusahaan":
        res = await db.execute(select(PerusahaanProfile).where(PerusahaanProfile.user_id == user_id))
        prof = res.scalars().first()
        if prof:
            name = prof.nama_perusahaan
            role_desc = "Perusahaan / HR"

    # Avoid duplicate review for the same event
    if review_data.context_event:
        existing = await db.execute(
            select(PlatformReview).where(
                PlatformReview.user_id == user_id,
                PlatformReview.context_event == review_data.context_event
            )
        )
        if existing.scalars().first():
            raise HTTPException(status_code=400, detail="Anda sudah memberikan ulasan untuk tahap ini.")

    new_review = PlatformReview(
        user_id=user_id,
        name=name,
        role=role_desc,
        rating=review_data.rating,
        category=review_data.category,
        comment=review_data.comment,
        context_event=review_data.context_event,
        is_anonymous=review_data.is_anonymous
    )
    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)
    return new_review

@router.get("/me/status")
async def check_review_status(
    context_event: str,
    current_user_data: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    user_id = current_user_data.get("sub")
    existing = await db.execute(
        select(PlatformReview).where(
            PlatformReview.user_id == user_id,
            PlatformReview.context_event == context_event
        )
    )
    has_reviewed = existing.scalars().first() is not None
    return {"has_reviewed": has_reviewed}

@router.get("/public", response_model=List[ReviewResponse])
async def get_public_reviews(db: AsyncSession = Depends(get_db)):
    # Get 3 newest 5-star reviews
    result = await db.execute(
        select(PlatformReview)
        .where(PlatformReview.rating == 5, PlatformReview.comment != "", PlatformReview.comment.isnot(None))
        .order_by(desc(PlatformReview.created_at))
        .limit(3)
    )
    reviews = result.scalars().all()
    
    for r in reviews:
        if r.is_anonymous and r.name:
            parts = r.name.split()
            masked_parts = []
            for part in parts:
                if len(part) <= 2:
                    masked_parts.append(part[0] + "*" * (len(part) - 1))
                else:
                    masked_parts.append(part[0] + "*" * (len(part) - 2) + part[-1])
            r.name = " ".join(masked_parts)

    return reviews
