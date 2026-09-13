import json
import uuid
from datetime import datetime, timezone

import aio_pika

from app.config import settings
from app.metrics import rabbitmq_events_total

EXCHANGE_NAME = "markethub.events"


async def publish_event(
    event_type: str,
    data: dict,
) -> None:
    connection = await aio_pika.connect_robust(
        settings.rabbitmq_url,
    )

    try:
        channel = await connection.channel()

        exchange = await channel.declare_exchange(
            EXCHANGE_NAME,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }

        message = aio_pika.Message(
            body=json.dumps(event).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        await exchange.publish(
            message,
            routing_key=event_type,
        )

        rabbitmq_events_total.inc()

    finally:
        await connection.close()