from prometheus_client import Counter

cache_hits_total = Counter(
    "cache_hits_total",
    "Total number of Redis cache hits",
)

cache_misses_total = Counter(
    "cache_misses_total",
    "Total number of Redis cache misses",
)