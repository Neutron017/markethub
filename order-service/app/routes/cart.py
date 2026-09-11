from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.cart import Cart, CartItem
from app.schemas.cart import (
    CartItemCreate,
    CartItemResponse,
    CartItemUpdate,
    CartResponse,
)
from app.services.auth import get_current_user
from app.services.products import get_product


router = APIRouter(
    prefix="/api/v1/cart",
    tags=["cart"],
)


async def get_or_create_cart(
    user_id: UUID,
    db: AsyncSession,
) -> Cart:
    result = await db.execute(
        select(Cart).where(Cart.user_id == user_id)
    )

    cart = result.scalar_one_or_none()

    if cart is None:
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.flush()

    return cart


@router.get(
    "",
    response_model=CartResponse,
)
async def get_cart(
    current_user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cart = await get_or_create_cart(
        current_user_id,
        db,
    )

    result = await db.execute(
        select(CartItem)
        .where(CartItem.cart_id == cart.id)
        .order_by(CartItem.id)
    )

    items = result.scalars().all()

    await db.commit()

    return CartResponse(
        id=cart.id,
        user_id=cart.user_id,
        items=[
            CartItemResponse.model_validate(item)
            for item in items
        ],
    )


@router.post(
    "/items",
    response_model=CartItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_to_cart(
    item_data: CartItemCreate,
    current_user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product = await get_product(item_data.product_id)

    if not product["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product is inactive",
        )

    if product["stock"] < item_data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough product stock",
        )

    cart = await get_or_create_cart(
        current_user_id,
        db,
    )

    result = await db.execute(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == item_data.product_id,
        )
    )

    existing_item = result.scalar_one_or_none()

    if existing_item:
        new_quantity = existing_item.quantity + item_data.quantity

        if product["stock"] < new_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough product stock",
            )

        existing_item.quantity = new_quantity
        existing_item.price = product["price"]

        await db.commit()
        await db.refresh(existing_item)

        return existing_item

    new_item = CartItem(
        cart_id=cart.id,
        product_id=item_data.product_id,
        quantity=item_data.quantity,
        price=product["price"],
    )

    db.add(new_item)

    await db.commit()
    await db.refresh(new_item)

    return new_item


@router.patch(
    "/items/{item_id}",
    response_model=CartItemResponse,
)
async def update_cart_item(
    item_id: UUID,
    item_data: CartItemUpdate,
    current_user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CartItem)
        .join(Cart)
        .where(
            CartItem.id == item_id,
            Cart.user_id == current_user_id,
        )
    )

    item = result.scalar_one_or_none()

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found",
        )

    product = await get_product(item.product_id)

    if product["stock"] < item_data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough product stock",
        )

    item.quantity = item_data.quantity
    item.price = product["price"]

    await db.commit()
    await db.refresh(item)

    return item


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_cart_item(
    item_id: UUID,
    current_user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CartItem)
        .join(Cart)
        .where(
            CartItem.id == item_id,
            Cart.user_id == current_user_id,
        )
    )

    item = result.scalar_one_or_none()

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found",
        )

    await db.delete(item)
    await db.commit()


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def clear_cart(
    current_user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Cart).where(Cart.user_id == current_user_id)
    )

    cart = result.scalar_one_or_none()

    if cart is None:
        return

    result = await db.execute(
        select(CartItem).where(CartItem.cart_id == cart.id)
    )

    items = result.scalars().all()

    for item in items:
        await db.delete(item)

    await db.commit()