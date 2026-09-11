import json
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.internal_auth import verify_internal_token
from app.services.auth import get_current_user
from app.database import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductStockUpdate, ProductResponse, ProductUpdate
from app.services.cache import PRODUCTS_CACHE_PREFIX, get_cached_products, invalidate_products_cache, set_cached_products

router = APIRouter(
    prefix="/api/v1/products",
    tags=["Products"],
)


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    data: ProductCreate,
    current_user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product = Product(
        seller_id=current_user_id,
        category_id=data.category_id,
        name=data.name,
        description=data.description,
        price=data.price,
        stock=data.stock,
    )

    db.add(product)

    await db.commit()
    await db.refresh(product)

    await invalidate_products_cache()

    return product


@router.get(
    "",
    response_model=list[ProductResponse],
)
async def get_products(
    category_id: UUID | None = None,
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    search: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    cache_key = (
        f"{PRODUCTS_CACHE_PREFIX}"
        f"page={page}:"
        f"limit={limit}:"
        f"category={category_id}:"
        f"min_price={min_price}:"
        f"max_price={max_price}:"
        f"search={search}"
    )

    cached_products = await get_cached_products(cache_key)

    if cached_products is not None:
        return cached_products

    query = select(Product).where(
        Product.is_active.is_(True)
    )

    if category_id:
        query = query.where(
            Product.category_id == category_id
        )

    if min_price is not None:
        query = query.where(
            Product.price >= min_price
        )

    if max_price is not None:
        query = query.where(
            Product.price <= max_price
        )

    if search:
        query = query.where(
            Product.name.ilike(f"%{search}%")
        )

    offset = (page - 1) * limit

    query = (
        query
        .order_by(Product.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(query)

    products = result.scalars().all()

    response = [
        ProductResponse.model_validate(product).model_dump(mode="json")
        for product in products
    ]

    await set_cached_products(
        cache_key,
        response,
    )

    return response

@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Product).where(
            Product.id == product_id,
            Product.is_active.is_(True),
        )
    )

    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return product


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
)
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    current_user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Product).where(
            Product.id == product_id
        )
    )

    product = result.scalar_one_or_none()

    if product.seller_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only modify your own products",
        )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)

    await invalidate_products_cache()

    return product

@router.patch(
    "/{product_id}/stock",
    response_model=ProductResponse,
)
async def update_product_stock(
    product_id: UUID,
    stock_data: ProductStockUpdate,
    _: None = Depends(verify_internal_token),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )

    product = result.scalar_one_or_none()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    new_stock = product.stock + stock_data.quantity

    if new_stock < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough stock",
        )

    product.stock = new_stock

    await db.commit()
    await db.refresh(product)

    await invalidate_products_cache()

    return product

@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_product(
    product_id: UUID,
    current_user_id: UUID = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Product).where(
            Product.id == product_id
        )
    )

    product = result.scalar_one_or_none()

    if product.seller_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only modify your own products",
        )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    product.is_active = False

    await db.commit()

    await invalidate_products_cache()

    return

