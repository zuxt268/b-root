"""
Rate limiting service for preventing brute force attacks and API abuse.
Uses pyrate-limiter library with Redis backend for distributed rate limiting.
"""

import os
import hashlib
from typing import Optional, Tuple
from functools import wraps

from flask import request, jsonify, abort, current_app
from pyrate_limiter import Duration, Rate, Limiter, RedisBucket

from service.redis_client import get_redis


class RateLimiterService:
    """Rate limiting service with Redis backend for scalability."""

    def __init__(self):
        self.redis_client = get_redis()

        # Rate limiting configurations from environment variables
        self.login_rate_limit = int(os.getenv("LOGIN_RATE_LIMIT", "5"))  # 5 attempts
        self.login_window = int(os.getenv("LOGIN_RATE_WINDOW", "900"))  # 15 minutes

        self.api_rate_limit = int(os.getenv("API_RATE_LIMIT", "100"))  # 100 requests
        self.api_window = int(os.getenv("API_RATE_WINDOW", "3600"))  # 1 hour

        self.registration_rate_limit = int(
            os.getenv("REGISTRATION_RATE_LIMIT", "3")  # 3 attempts
        )
        self.registration_window = int(
            os.getenv("REGISTRATION_RATE_WINDOW", "3600")  # 1 hour
        )

        # Create rate limiters
        self._create_limiters()

    def _create_limiters(self):
        """Create rate limiters with Redis backend."""
        try:
            # Login rate limiter (per IP)
            self.login_limiter = Limiter(
                Rate(self.login_rate_limit, Duration.SECOND * self.login_window),
                bucket_class=RedisBucket,
                bucket_kwargs={"redis_pool": self.redis_client.connection_pool}
            )

            # API rate limiter (per IP)
            self.api_limiter = Limiter(
                Rate(self.api_rate_limit, Duration.SECOND * self.api_window),
                bucket_class=RedisBucket,
                bucket_kwargs={"redis_pool": self.redis_client.connection_pool}
            )

            # Registration rate limiter (per IP)
            self.registration_limiter = Limiter(
                Rate(
                    self.registration_rate_limit,
                    Duration.SECOND * self.registration_window
                ),
                bucket_class=RedisBucket,
                bucket_kwargs={"redis_pool": self.redis_client.connection_pool}
            )

        except Exception as e:
            current_app.logger.error(f"Failed to initialize rate limiters: {e}")
            # Fallback to in-memory limiter
            self._create_memory_limiters()

    def _create_memory_limiters(self):
        """Fallback to in-memory rate limiters if Redis is unavailable."""
        from pyrate_limiter import InMemoryBucket

        self.login_limiter = Limiter(
            Rate(self.login_rate_limit, Duration.SECOND * self.login_window),
            bucket_class=InMemoryBucket
        )

        self.api_limiter = Limiter(
            Rate(self.api_rate_limit, Duration.SECOND * self.api_window),
            bucket_class=InMemoryBucket
        )

        self.registration_limiter = Limiter(
            Rate(
                self.registration_rate_limit,
                Duration.SECOND * self.registration_window
            ),
            bucket_class=InMemoryBucket
        )

    def get_client_identifier(self) -> str:
        """Get unique client identifier for rate limiting."""
        # Get IP address (consider X-Forwarded-For in trusted proxy environments)
        client_ip = self._get_client_ip()

        # For authenticated requests, also consider user ID if available
        user_id = (
            getattr(request, 'user_id', None) or
            request.headers.get('X-User-ID', '')
        )

        # Create unique identifier
        identifier = f"{client_ip}:{user_id}" if user_id else client_ip

        # Hash to ensure consistent length and privacy
        return hashlib.sha256(identifier.encode()).hexdigest()[:16]

    def _get_client_ip(self) -> str:
        """Get client IP address, considering proxy headers."""
        # Check for forwarded headers (only if in trusted proxy environment)
        trusted_proxies = os.getenv("TRUSTED_PROXIES", "").split(",")

        if trusted_proxies and request.remote_addr in trusted_proxies:
            # Trust X-Forwarded-For header
            forwarded_for = request.headers.get('X-Forwarded-For')
            if forwarded_for:
                return forwarded_for.split(',')[0].strip()

        return request.remote_addr or '127.0.0.1'

    def is_rate_limited(self, limiter_type: str) -> Tuple[bool, Optional[int]]:
        """
        Check if request should be rate limited.

        Args:
            limiter_type: Type of rate limiter ('login', 'api', 'registration')

        Returns:
            Tuple of (is_limited, retry_after_seconds)
        """
        identifier = self.get_client_identifier()

        try:
            if limiter_type == 'login':
                limiter = self.login_limiter
            elif limiter_type == 'api':
                limiter = self.api_limiter
            elif limiter_type == 'registration':
                limiter = self.registration_limiter
            else:
                raise ValueError(f"Unknown limiter type: {limiter_type}")

            # Try to acquire a token
            item = limiter.try_acquire(identifier)

            if item is None:
                # Rate limited - calculate retry after
                bucket = limiter.bucket_factory(identifier)
                retry_after = bucket.leak()
                return True, int(retry_after) if retry_after else self.login_window

            return False, None

        except Exception as e:
            current_app.logger.error(f"Rate limiter error: {e}")
            # On error, allow the request (fail open)
            return False, None

    def record_failed_attempt(self, identifier: str, attempt_type: str):
        """Record a failed attempt for additional security tracking."""
        try:
            key = f"failed_attempts:{attempt_type}:{identifier}"
            self.redis_client.incr(key)
            self.redis_client.expire(key, 3600)  # 1 hour expiry
        except Exception as e:
            current_app.logger.error(f"Failed to record attempt: {e}")

    def get_failed_attempts(self, identifier: str, attempt_type: str) -> int:
        """Get number of failed attempts for identifier."""
        try:
            key = f"failed_attempts:{attempt_type}:{identifier}"
            count = self.redis_client.get(key)
            return int(count) if count else 0
        except Exception as e:
            current_app.logger.error(f"Failed to get attempt count: {e}")
            return 0


# Global rate limiter instance - initialized lazily
rate_limiter = None


def get_rate_limiter():
    """Get or create the global rate limiter instance."""
    global rate_limiter
    if rate_limiter is None:
        rate_limiter = RateLimiterService()
    return rate_limiter


def rate_limit(limiter_type: str = 'api'):
    """
    Decorator for rate limiting endpoints.

    Args:
        limiter_type: Type of rate limiter ('login', 'api', 'registration')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            limiter = get_rate_limiter()
            is_limited, retry_after = limiter.is_rate_limited(limiter_type)

            if is_limited:
                # Log rate limit violation
                client_id = limiter.get_client_identifier()
                current_app.logger.warning(
                    f"Rate limit exceeded for {limiter_type}: {client_id}, "
                    f"retry after {retry_after}s"
                )

                # Return appropriate response
                accept_header = request.headers.get('Accept', '')
                if request.is_json or 'application/json' in accept_header:
                    response = jsonify({
                        'error': 'Rate limit exceeded',
                        'message': (
                            f'Too many {limiter_type} requests. '
                            'Please try again later.'
                        ),
                        'retry_after': retry_after
                    })
                    response.status_code = 429
                    if retry_after:
                        response.headers['Retry-After'] = str(retry_after)
                    return response
                else:
                    # For web requests, abort with 429
                    abort(429)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def check_brute_force_protection(identifier: str, max_attempts: int = 10) -> bool:
    """
    Additional brute force protection check.

    Args:
        identifier: Client identifier
        max_attempts: Maximum failed attempts allowed

    Returns:
        True if client should be blocked
    """
    limiter = get_rate_limiter()
    failed_count = limiter.get_failed_attempts(identifier, 'login')
    return failed_count >= max_attempts
