import json

from app.redis import redis_client


CACHE_TTL = 60
PRODUCTS_CACHE_PREFIX = "products:list:"


async def get_cached_products(cache_key: str):
    try:
        cached = await redis_client.get(cache_key)

        if cached is None:
            return None

        return json.loads(cached)

    except Exception:
        return None


async def set_cached_products(
    cache_key: str,
    products: list,
) -> None:
    try:
        await redis_client.set(
            cache_key,
            json.dumps(products),
            ex=CACHE_TTL,
        )
    except Exception:
        pass


async def invalidate_products_cache() -> None:
    try:
        keys = []

        async for key in redis_client.scan_iter(
            match=f"{PRODUCTS_CACHE_PREFIX}*"
        ):
            keys.append(key)

        if keys:
            await redis_client.delete(*keys)

    except Exception:
        pass