from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.product import Product
from app.models.review import Review
from app.schemas.product import ReviewCreate, ReviewResponse
from app.services.auth import get_current_user


router = APIRouter(
    prefix="/api/v1/products/{product_id}/reviews",
    tags=["reviews"],
)


@router.post(
    "",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    product_id: UUID,
    review: ReviewCreate,
    current_user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.is_active.is_(True),
        )
    )

    product = result.scalar_one_or_none()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    new_review = Review(
        product_id=product_id,
        user_id=current_user_id,
        rating=review.rating,
        comment=review.comment,
    )

    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)

    return new_review


@router.get(
    "",
    response_model=list[ReviewResponse],
)
async def get_reviews(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Review)
        .where(Review.product_id == product_id)
        .order_by(Review.created_at.desc())
    )

    return result.scalars().all()