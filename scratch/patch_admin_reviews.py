import os

path = 'c:/ai-recruit-pro-be/app/routers/admin.py'

with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

new_code = """

# ============================================
# PLATFORM REVIEWS ENDPOINTS (ADMIN)
# ============================================
@router.get("/reviews")
async def admin_get_reviews(
    search: Optional[str] = None,
    rating: Optional[int] = None,
    category: Optional[str] = None,
    current_user: dict = Depends(verify_admin),
    db: AsyncSession = Depends(get_db)
):
    from app.models.review import PlatformReview
    from sqlalchemy import select, or_, desc
    
    query = select(PlatformReview).order_by(desc(PlatformReview.created_at))
    
    if rating:
        query = query.where(PlatformReview.rating == rating)
        
    if category and category.strip():
        query = query.where(PlatformReview.category.ilike(f"%{category.strip()}%"))
        
    if search and search.strip():
        kw_clean = search.strip()
        query = query.where(
            or_(
                PlatformReview.name.ilike(f"%{kw_clean}%"),
                PlatformReview.comment.ilike(f"%{kw_clean}%"),
                PlatformReview.category.ilike(f"%{kw_clean}%"),
                PlatformReview.role.ilike(f"%{kw_clean}%")
            )
        )
        
    res = await db.execute(query)
    reviews = res.scalars().all()
    return reviews


@router.delete("/reviews/{review_id}")
async def admin_delete_review(
    review_id: str,
    current_user: dict = Depends(verify_admin),
    db: AsyncSession = Depends(get_db)
):
    from app.models.review import PlatformReview
    from sqlalchemy import select
    
    res = await db.execute(select(PlatformReview).where(PlatformReview.id == review_id))
    review = res.scalars().first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Ulasan tidak ditemukan")
        
    await db.delete(review)
    await db.commit()
    return {"message": "Ulasan berhasil dihapus"}
"""

if 'admin_get_reviews' not in content:
    content += new_code
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added admin review endpoints to admin.py")
else:
    print("admin_get_reviews already exists in admin.py")
