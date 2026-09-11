from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.order import OrderStatus


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    quantity: int
    price: Decimal

class OrderCreate(BaseModel):
    pass

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    status: OrderStatus
    total_price: Decimal
    items: list[OrderItemResponse]


class OrderStatusUpdate(BaseModel):
    status: OrderStatus