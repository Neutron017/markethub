from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse
from app.services.auth import get_current_user


router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["notifications"],
)


@router.get(
    "",
    response_model=list[NotificationResponse],
)
async def get_notifications(
    current_user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user_id)
        .order_by(Notification.created_at.desc())
    )

    return result.scalars().all()


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
async def mark_as_read(
    notification_id: UUID,
    current_user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user_id,
        )
    )

    notification = result.scalar_one_or_none()

    if notification is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )

    notification.is_read = True

    await db.commit()
    await db.refresh(notification)

    return notification