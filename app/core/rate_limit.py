import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.time()
        bucket = self._buckets[key]
        while bucket and bucket[0] <= now - window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True


rate_limiter = InMemoryRateLimiter()


async def enforce_rate_limit(request: Request, call_next):
    path = request.url.path
    client_host = request.client.host if request.client else "unknown"
    sensitive_prefixes = ("/api/v1/auth/login", "/api/v1/auth/refresh", "/api/v1/webhooks/")
    if path.startswith(sensitive_prefixes):
        allowed = rate_limiter.check(f"{client_host}:{path}", limit=10, window_seconds=60)
        if not allowed:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
    return await call_next(request)
