import time
import hashlib
import secrets
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import HTTPException, Security, Request, status
from fastapi.security import APIKeyHeader
from app.config import get_settings

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# In-memory rate limiting (for production, use Redis)
request_counts: dict[str, list[float]] = defaultdict(list)
failed_attempts: dict[str, list[float]] = defaultdict(list)

# Rate limiting settings
RATE_LIMIT_REQUESTS = 100  # requests
RATE_LIMIT_WINDOW = 60  # seconds
MAX_FAILED_ATTEMPTS = 10  # failed attempts
BLOCK_DURATION = 300  # blocking duration in seconds


def _secure_compare(a: str, b: str) -> bool:
    """Timing-safe comparison to prevent timing attacks"""
    return secrets.compare_digest(a.encode(), b.encode())


def _get_client_ip(request: Request) -> str:
    """Get real client IP (considering proxies)"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit(client_ip: str) -> None:
    """Check rate limiting by IP"""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    
    # Clean old requests
    request_counts[client_ip] = [
        t for t in request_counts[client_ip] if t > window_start
    ]
    
    # Check limit
    if len(request_counts[client_ip]) >= RATE_LIMIT_REQUESTS:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again in a few minutes."
        )
    
    # Record request
    request_counts[client_ip].append(now)


def _check_blocked(client_ip: str) -> None:
    """Check if IP is blocked due to failed attempts"""
    now = time.time()
    window_start = now - BLOCK_DURATION
    
    # Clean old attempts
    failed_attempts[client_ip] = [
        t for t in failed_attempts[client_ip] if t > window_start
    ]
    
    # Check blocking
    if len(failed_attempts[client_ip]) >= MAX_FAILED_ATTEMPTS:
        logger.warning(f"IP blocked due to failed attempts: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="IP temporarily blocked. Please try again later."
        )


def _record_failed_attempt(client_ip: str) -> None:
    """Record failed authentication attempt"""
    failed_attempts[client_ip].append(time.time())
    logger.warning(f"Failed auth attempt from IP: {client_ip}")


async def verify_api_key(
    request: Request,
    api_key: str = Security(api_key_header)
) -> str:
    """
    Verify API Key with security protections:
    1. Rate limiting by IP
    2. Blocking after failed attempts
    3. Timing-safe comparison
    4. Attempt logging
    """
    settings = get_settings()
    client_ip = _get_client_ip(request)
    
    # 1. Check if IP is blocked
    _check_blocked(client_ip)
    
    # 2. Check rate limit
    _check_rate_limit(client_ip)
    
    # 3. Check if API key was provided
    if not api_key:
        _record_failed_attempt(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key not provided"
        )
    
    # 4. Timing-safe comparison of API key
    if not _secure_compare(api_key, settings.API_KEY):
        _record_failed_attempt(client_ip)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
    
    # Clear failed attempts after success
    failed_attempts[client_ip] = []
    
    return api_key
