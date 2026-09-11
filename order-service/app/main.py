from fastapi import FastAPI

from app.routes import cart, orders


app = FastAPI(
    title="MarketHub Order Service",
    version="1.0.0",
    description="Order and cart microservice",
)


app.include_router(cart.router)
app.include_router(orders.router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "order-service",
    }