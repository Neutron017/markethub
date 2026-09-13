from prometheus_client import Counter

orders_created_total = Counter(
    "orders_created_total",
    "Total number of created orders",
)

orders_cancelled_total = Counter(
    "orders_cancelled_total",
    "Total number of cancelled orders",
)

rabbitmq_events_total = Counter(
    "rabbitmq_events_total",
    "Total number of published RabbitMQ events",
)