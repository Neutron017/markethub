from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI

from app.routes import auth, users


app = FastAPI(
    title="MarketHub User Service",
    version="1.0.0",
    description="User and authentication microservice",
)

Instrumentator().instrument(app).expose(app)

app.include_router(auth.router)
app.include_router(users.router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "user-service",
    }