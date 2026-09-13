import json
import uuid

import aio_pika
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.notification import Notification
from app.metrics import notifications_created_total

EXCHANGE_NAME = "markethub.events"
QUEUE_NAME = "notifications.order-events"

EVENT_TYPES = [
    "ORDER_CREATED",
    "ORDER_STATUS_CHANGED",
]


async def handle_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    async with message.process(requeue=True):
        event = json.loads(message.body.decode())

        event_id = uuid.UUID(event["event_id"])
        event_type = event["event_type"]
        data = event["data"]

        user_id = uuid.UUID(data["user_id"])
        order_id = data["order_id"]

        if event_type == "ORDER_CREATED":
            message_text = (
                f"Заказ {order_id} создан. "
                f"Сумма: {data['total_price']}"
            )

        elif event_type == "ORDER_STATUS_CHANGED":
            message_text = (
                f"Статус заказа {order_id} изменён: "
                f"{data['status']}"
            )

        else:
            return

        async with AsyncSessionLocal() as db:
            existing = await db.execute(
                select(Notification).where(
                    Notification.event_id == event_id
                )
            )

            if existing.scalar_one_or_none() is not None:
                return

            notification = Notification(
                event_id=event_id,
                user_id=user_id,
                type=event_type,
                message=message_text,
            )

            db.add(notification)
            await db.commit()
            notifications_created_total.inc()


async def start_consumer() -> aio_pika.abc.AbstractConnection:
    connection = await aio_pika.connect_robust(
        settings.rabbitmq_url
    )

    channel = await connection.channel()

    await channel.set_qos(prefetch_count=10)

    exchange = await channel.declare_exchange(
        EXCHANGE_NAME,
        aio_pika.ExchangeType.TOPIC,
        durable=True,
    )

    queue = await channel.declare_queue(
        QUEUE_NAME,
        durable=True,
    )

    for event_type in EVENT_TYPES:
        await queue.bind(
            exchange,
            routing_key=event_type,
        )

    await queue.consume(handle_message)

    return connection