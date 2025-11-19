"""
Rate Limiting Middleware

Implements token bucket rate limiting per API key to prevent abuse.
Uses in-memory storage (in production, use Redis for distributed systems).
"""

import time
from collections import defaultdict
from typing import Callable

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware


class TokenBucket:
    """Token bucket algorithm for rate limiting"""

    def __init__(self, capacity: int, refill_rate: float):
        """
        Args:
            capacity: Maximum number of tokens (requests)
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket

        Returns:
            True if tokens were consumed, False if insufficient tokens
        """
        # Refill tokens based on elapsed time
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        # Try to consume
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False

    def get_wait_time(self) -> float:
        """Get estimated wait time until next token is available"""
        if self.tokens >= 1:
            return 0.0
        return (1 - self.tokens) / self.refill_rate


class RateLimiter:
    """Rate limiter using token bucket per API key"""

    def __init__(self, default_rate_limit: int = 100):
        """
        Args:
            default_rate_limit: Default requests per minute
        """
        self.default_rate_limit = default_rate_limit
        self.buckets: dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(capacity=default_rate_limit, refill_rate=default_rate_limit / 60.0)
        )

    def check_rate_limit(self, key: str, rate_limit: int = None) -> tuple[bool, float]:
        """
        Check if request is within rate limit

        Args:
            key: Identifier (API key hash)
            rate_limit: Custom rate limit for this key

        Returns:
            (allowed, wait_time) tuple
        """
        # Get or create bucket for this key
        if key not in self.buckets and rate_limit:
            self.buckets[key] = TokenBucket(capacity=rate_limit, refill_rate=rate_limit / 60.0)

        bucket = self.buckets[key]

        # Try to consume a token
        allowed = bucket.consume()
        wait_time = bucket.get_wait_time() if not allowed else 0.0

        return allowed, wait_time

    def reset(self, key: str):
        """Reset rate limit for a key"""
        if key in self.buckets:
            del self.buckets[key]


# Global rate limiter instance
_rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Get API key from header
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            # No API key - apply strict default limit
            client_ip = request.client.host
            allowed, wait_time = _rate_limiter.check_rate_limit(f"ip:{client_ip}", rate_limit=10)
        else:
            # API key present - will be validated by auth dependency
            # For now, just check rate limit (auth happens in endpoint)
            api_key_rate = getattr(request.state, "api_key_rate_limit", 100)
            allowed, wait_time = _rate_limiter.check_rate_limit(api_key, rate_limit=api_key_rate)

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {wait_time:.1f} seconds.",
                headers={"Retry-After": str(int(wait_time) + 1)},
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(_rate_limiter.default_rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(
            int(_rate_limiter.buckets.get(api_key or f"ip:{request.client.host}", TokenBucket(100, 100/60.0)).tokens)
        )

        return response


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance"""
    return _rate_limiter
