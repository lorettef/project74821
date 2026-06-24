import time
from collections import defaultdict

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)

_AUTH_RATE_LIMIT = 100
_GENERAL_RATE_LIMIT = 300
_WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._buckets: dict[str, list[float]] = defaultdict(list)

    def _clean_window(self, key: str, now: float) -> None:
        cutoff = now - _WINDOW_SECONDS
        self._buckets[key] = [t for t in self._buckets[key] if t > cutoff]

    def _get_limit(self, path: str) -> int:
        if "/auth/" in path:
            return _AUTH_RATE_LIMIT
        return _GENERAL_RATE_LIMIT

    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
        path = request.url.path
        limit = self._get_limit(path)
        key = f"{client_ip}:{':auth' if '/auth/' in path else ':general'}"
        now = time.monotonic()

        self._clean_window(key, now)
        self._buckets[key].append(now)

        if len(self._buckets[key]) > limit:
            logger.warning(
                "rate_limit_exceeded",
                ip=client_ip,
                path=path,
                count=len(self._buckets[key]),
                limit=limit,
            )
            return Response(
                status_code=429,
                content='{"error":{"code":"RATE_LIMIT_EXCEEDED","message":"Too many requests","details":[]}}',
                media_type="application/json",
            )

        return await call_next(request)
