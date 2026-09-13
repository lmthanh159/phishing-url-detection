"""Simple in-memory rate limiting for scan endpoints."""
import time
from collections import defaultdict, deque
from typing import Deque

from fastapi import HTTPException, Request


_WINDOW_SECONDS = 60
_requests: dict[tuple[str, str], Deque[float]] = defaultdict(deque)


def _client_id(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _enforce(request: Request, bucket: str, limit: int) -> None:
    now = time.monotonic()
    key = (bucket, _client_id(request))
    hits = _requests[key]

    while hits and now - hits[0] >= _WINDOW_SECONDS:
        hits.popleft()

    if len(hits) >= limit:
        retry_after = max(1, int(_WINDOW_SECONDS - (now - hits[0])))
        raise HTTPException(
            status_code=429,
            detail="Too Many Requests",
            headers={"Retry-After": str(retry_after)},
        )

    hits.append(now)


async def rate_limit_single_scan(request: Request) -> None:
    """Limit single scans to 60 requests per minute per client."""
    _enforce(request, "single_scan", 60)


async def rate_limit_batch_scan(request: Request) -> None:
    """Limit batch scans to 10 requests per minute per client."""
    _enforce(request, "batch_scan", 10)


def clear_rate_limits() -> None:
    """Test helper for clearing in-memory counters."""
    _requests.clear()
