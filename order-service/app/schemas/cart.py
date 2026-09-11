from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CartItemCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(gt=0)


class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    quantity: int
    price: Decimal


class CartResponse(BaseModel):
    id: UUID
    user_id: UUID
    items: list[CartItemResponse]

class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)