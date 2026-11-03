import os
import functools
from fastapi import Request
from starlette.requests import Request as StarletteRequest
from slowapi import Limiter

def get_client_ip(request: Request) -> str:
    """Extract real client IP safely, taking reverse proxies into account when explicitly enabled."""
    trusted_proxy = os.getenv("TRUSTED_PROXY", "false").lower() in ["true", "1", "yes"]
    if trusted_proxy:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Client IP is the first IP in the X-Forwarded-For chain
            return forwarded_for.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
    return request.client.host if request.client and request.client.host else "127.0.0.1"

rate_limit_enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() in ["true", "1", "yes"]
default_limit = os.getenv("DEFAULT_RATE_LIMIT", "120/minute")

limiter = Limiter(
    key_func=get_client_ip,
    default_limits=[default_limit] if rate_limit_enabled else [],
    enabled=rate_limit_enabled
)

def safe_rate_limit(limit_string: str):
    """
    Decorator that applies slowapi rate limiting for FastAPI HTTP requests,
    while cleanly delegating to the underlying function if invoked directly
    as a Python function in automated unit tests without an HTTP Request context.
    """
    slowapi_decorator = limiter.limit(limit_string)

    def decorator(func):
        wrapped = slowapi_decorator(func)

        @functools.wraps(func)
        def sync_inner(*args, **kwargs):
            has_request = any(isinstance(a, StarletteRequest) for a in args) or isinstance(kwargs.get("request"), StarletteRequest)
            if not has_request:
                # Direct Python call in unit/logic test without FastAPI ASGI request wrapper
                return func(*args, **kwargs)
            return wrapped(*args, **kwargs)

        return sync_inner

    return decorator
