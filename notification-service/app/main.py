from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.messaging.consumer import start_consumer
from app.routes import notifications


@asynccontextmanager
async def lifespan(app: FastAPI):
    rabbitmq_connection = await start_consumer()

    try:
        yield
    finally:
        await rabbitmq_connection.close()


app = FastAPI(
    title="MarketHub Notification Service",
    version="1.0.0",
    description="Notification microservice",
    lifespan=lifespan,
)

app.include_router(notifications.router)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "notification-service",
    }