from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.metrics import orders_created_total, orders_cancelled_total
from app.metrics import orders_created_total
from app.database import get_db
from app.messaging.rabbitmq import publish_event
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.order import (
    OrderItemResponse,
    OrderResponse,
    OrderStatusUpdate,
)
from app.services.auth import get_current_user
from app.services.products import get_product
from app.services.products import (
    decrease_product_stock,
    get_product,
)


router = APIRouter(
    prefix="/api/v1/orders",
    tags=["orders"],
)


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    current_user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cart_result = await db.execute(
        select(Cart).where(
            Cart.user_id == current_user_id
        )
    )

    cart = cart_result.scalar_one_or_none()

    if cart is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty",
        )

    items_result = await db.execute(
        select(CartItem)
        .where(CartItem.cart_id == cart.id)
    )

    cart_items = items_result.scalars().all()

    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty",
        )

    total_price = Decimal("0.00")
    products = []

    for cart_item in cart_items:
        product = await get_product(
            cart_item.product_id
        )

        if not product["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product {cart_item.product_id} is inactive",
            )

        if product["stock"] < cart_item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Not enough stock for product "
                    f"{cart_item.product_id}"
                ),
            )

        products.append(product)

        total_price += (
            Decimal(str(product["price"]))
            * cart_item.quantity
        )

    for cart_item in cart_items:
        await decrease_product_stock(
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
        )

    order = Order(
        user_id=current_user_id,
        status=OrderStatus.CREATED.value,
        total_price=total_price,
    )

    db.add(order)

    await db.flush()

    for cart_item, product in zip(
        cart_items,
        products,
    ):
        order_item = OrderItem(
            order_id=order.id,
            product_id=cart_item.product_id,
            quantity=cart_item.quantity,
            price=Decimal(str(product["price"])),
        )

        db.add(order_item)

    for cart_item in cart_items:
        await db.delete(cart_item)

    await db.commit()
    orders_created_total.inc()
    await db.refresh(order)

    items_result = await db.execute(
        select(OrderItem)
        .where(OrderItem.order_id == order.id)
    )

    order_items = items_result.scalars().all()

    await publish_event(
        event_type="ORDER_CREATED",
        data={
            "order_id": str(order.id),
            "user_id": str(current_user_id),
            "total_price": str(order.total_price),
        },
    )

    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=OrderStatus(order.status),
        total_price=order.total_price,
        items=[
            OrderItemResponse.model_validate(item)
            for item in order_items
        ],
    )

@router.get(
    "",
    response_model=list[OrderResponse],
)
async def get_orders(
    current_user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order)
        .where(Order.user_id == current_user_id)
        .order_by(Order.created_at.desc())
    )

    orders = result.scalars().all()

    response = []

    for order in orders:
        items_result = await db.execute(
            select(OrderItem)
            .where(OrderItem.order_id == order.id)
        )

        items = items_result.scalars().all()

        response.append(
            OrderResponse(
                id=order.id,
                user_id=order.user_id,
                status=OrderStatus(order.status),
                total_price=order.total_price,
                items=[
                    OrderItemResponse.model_validate(item)
                    for item in items
                ],
            )
        )

    return response

@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
async def get_order(
    order_id: UUID,
    current_user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == current_user_id,
        )
    )

    order = result.scalar_one_or_none()

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    items_result = await db.execute(
        select(OrderItem)
        .where(OrderItem.order_id == order.id)
    )

    items = items_result.scalars().all()

    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=OrderStatus(order.status),
        total_price=order.total_price,
        items=[
            OrderItemResponse.model_validate(item)
            for item in items
        ],
    )

@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
)
async def update_order_status(
    order_id: UUID,
    status_data: OrderStatusUpdate,
    current_user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == current_user_id,
        )
    )

    order = result.scalar_one_or_none()

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    order.status = status_data.status.value

    await db.commit()
    if order.status == OrderStatus.CANCELLED.value:
        orders_cancelled_total.inc()
    await db.refresh(order)

    await publish_event(
        event_type="ORDER_STATUS_CHANGED",
        data={
            "order_id": str(order.id),
            "user_id": str(current_user_id),
            "status": order.status,
        },
    )

    items_result = await db.execute(
        select(OrderItem)
        .where(OrderItem.order_id == order.id)
    )

    items = items_result.scalars().all()

    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=OrderStatus(order.status),
        total_price=order.total_price,
        items=[
            OrderItemResponse.model_validate(item)
            for item in items
        ],
    )