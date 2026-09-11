from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.redis import close_redis
from app.routes import categories, products, reviews


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()


app = FastAPI(
    title="MarketHub Product Service",
    version="1.0.0",
    description="Product and category microservice",
    lifespan=lifespan,
)

app.include_router(categories.router)
app.include_router(products.router)
app.include_router(reviews.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "product-service"}