from fastapi import FastAPI

from app.routes import categories, products


app = FastAPI(
    title="MarketHub Product Service",
    version="1.0.0",
    description="Product and category microservice",
)


app.include_router(categories.router)
app.include_router(products.router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "product-service",
    }