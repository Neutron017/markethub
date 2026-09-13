from prometheus_client import Counter

notifications_created_total = Counter(
    "notifications_created_total",
    "Total number of created notifications",
)