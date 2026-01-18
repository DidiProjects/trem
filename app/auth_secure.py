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

# Rate limiting em memória (para produção, usar Redis)
request_counts: dict[str, list[float]] = defaultdict(list)
failed_attempts: dict[str, list[float]] = defaultdict(list)

# Configurações de rate limiting
RATE_LIMIT_REQUESTS = 100  # requisições
RATE_LIMIT_WINDOW = 60  # segundos
MAX_FAILED_ATTEMPTS = 10  # tentativas falhas
BLOCK_DURATION = 300  # segundos de bloqueio


def _secure_compare(a: str, b: str) -> bool:
    """Comparação timing-safe para prevenir timing attacks"""
    return secrets.compare_digest(a.encode(), b.encode())


def _get_client_ip(request: Request) -> str:
    """Obtém IP real do cliente (considerando proxies)"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check_rate_limit(client_ip: str) -> None:
    """Verifica rate limiting por IP"""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    
    # Limpa requisições antigas
    request_counts[client_ip] = [
        t for t in request_counts[client_ip] if t > window_start
    ]
    
    # Verifica limite
    if len(request_counts[client_ip]) >= RATE_LIMIT_REQUESTS:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Muitas requisições. Tente novamente em alguns minutos."
        )
    
    # Registra requisição
    request_counts[client_ip].append(now)


def _check_blocked(client_ip: str) -> None:
    """Verifica se IP está bloqueado por tentativas falhas"""
    now = time.time()
    window_start = now - BLOCK_DURATION
    
    # Limpa tentativas antigas
    failed_attempts[client_ip] = [
        t for t in failed_attempts[client_ip] if t > window_start
    ]
    
    # Verifica bloqueio
    if len(failed_attempts[client_ip]) >= MAX_FAILED_ATTEMPTS:
        logger.warning(f"IP blocked due to failed attempts: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="IP temporariamente bloqueado. Tente novamente mais tarde."
        )


def _record_failed_attempt(client_ip: str) -> None:
    """Registra tentativa falha de autenticação"""
    failed_attempts[client_ip].append(time.time())
    logger.warning(f"Failed auth attempt from IP: {client_ip}")


async def verify_api_key(
    request: Request,
    api_key: str = Security(api_key_header)
) -> str:
    """
    Verifica API Key com proteções de segurança:
    1. Rate limiting por IP
    2. Bloqueio após tentativas falhas
    3. Comparação timing-safe
    4. Logging de tentativas
    """
    settings = get_settings()
    client_ip = _get_client_ip(request)
    
    # 1. Verifica se IP está bloqueado
    _check_blocked(client_ip)
    
    # 2. Verifica rate limit
    _check_rate_limit(client_ip)
    
    # 3. Verifica se API key foi fornecida
    if not api_key:
        _record_failed_attempt(client_ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key não fornecida"
        )
    
    # 4. Comparação timing-safe da API key
    if not _secure_compare(api_key, settings.API_KEY):
        _record_failed_attempt(client_ip)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key inválida"
        )
    
    # Limpa tentativas falhas após sucesso
    failed_attempts[client_ip] = []
    
    return api_key
