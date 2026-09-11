from uuid import UUID

import httpx
from fastapi import HTTPException, status

from app.config import settings


async def get_product(product_id: UUID) -> dict:
    url = f"{settings.product_service_url}/api/v1/products/{product_id}"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Product Service is unavailable",
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Product Service returned an error",
        )

    return response.json()


async def decrease_product_stock(
    product_id: UUID,
    quantity: int,
) -> dict:
    url = (
        f"{settings.product_service_url}"
        f"/api/v1/products/{product_id}/stock"
    )

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.patch(
                url,
                json={
                    "quantity": -quantity,
                },
                headers={
                    "X-Internal-Token": settings.internal_service_token,
                },
            )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Product Service is unavailable",
        )

    if response.status_code == 400:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough product stock",
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to update product stock",
        )

    return response.json()