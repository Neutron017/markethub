from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models.notification import Notification


__all__ = [
    "Base",
    "Notification",
]