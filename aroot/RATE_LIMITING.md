# Rate Limiting Implementation

## Overview

This application implements comprehensive rate limiting to protect against brute force attacks, API abuse, and denial of service attempts using the `pyrate-limiter` library with Redis backend.

## Rate Limiting Rules

### 1. Login Endpoints (`/login`, `/admin/login`)
- **Limit**: 5 attempts per 15 minutes (900 seconds)
- **Scope**: Per IP address
- **Brute Force Protection**: Account locked after 10 failed attempts
- **Purpose**: Prevent password brute force attacks

### 2. Registration Endpoints (`/register`, `/send_verification_email`)
- **Limit**: 3 attempts per 1 hour (3600 seconds)
- **Scope**: Per IP address
- **Purpose**: Prevent spam registrations and abuse

### 3. API Endpoints (`/api/*`)
- **Limit**: 100 requests per 1 hour (3600 seconds)
- **Scope**: Per IP address
- **Purpose**: Prevent API abuse and DoS attacks

## Configuration

Rate limiting is configured via environment variables in `.env`:

```bash
# Login rate limiting
LOGIN_RATE_LIMIT=5          # Max attempts
LOGIN_RATE_WINDOW=900       # Time window in seconds (15 minutes)

# API rate limiting
API_RATE_LIMIT=100          # Max requests
API_RATE_WINDOW=3600        # Time window in seconds (1 hour)

# Registration rate limiting
REGISTRATION_RATE_LIMIT=3   # Max attempts
REGISTRATION_RATE_WINDOW=3600 # Time window in seconds (1 hour)
```

## Backend Storage

### Redis Backend (Recommended)
- **Distributed**: Works across multiple application instances
- **Persistent**: Rate limit data survives application restarts
- **Performance**: High-performance Redis operations

### In-Memory Fallback
- **Local**: Single application instance only
- **Temporary**: Data lost on application restart
- **Automatic**: Falls back if Redis is unavailable

## Client Identification

Rate limiting uses a combination of factors for client identification:

1. **IP Address**: Primary identifier
2. **Trusted Proxy Support**: Handles X-Forwarded-For headers safely
3. **User ID**: Additional identifier for authenticated requests
4. **Hashing**: Identifiers are hashed for privacy and consistency

## Security Features

### Brute Force Protection
- **Failed Attempt Tracking**: Records failed login attempts
- **Account Locking**: Temporary lockout after 10 failed attempts
- **Secure Fallback**: System fails open on errors (allows requests)

### Trusted Proxy Handling
- **Environment Variable**: `TRUSTED_PROXIES` configuration
- **Header Validation**: Only trusts X-Forwarded-For from trusted sources
- **Spoofing Prevention**: Ignores headers from untrusted sources

## Error Responses

### HTTP 429 (Too Many Requests)
- **JSON APIs**: Returns structured error with retry information
- **Web Requests**: Renders error page with user-friendly message
- **Headers**: Includes `Retry-After` header when possible

### Example JSON Response
```json
{
  "error": "Rate limit exceeded",
  "message": "Too many login requests. Please try again later.",
  "retry_after": 300
}
```

## Monitoring and Logging

### Application Logs
- **Rate Limit Violations**: Logged with client identifier and retry time
- **Failed Attempts**: Tracked separately for security analysis
- **System Errors**: Rate limiter failures logged for debugging

### Redis Keys
- **Rate Limits**: `pyrate_limiter:*` keys
- **Failed Attempts**: `failed_attempts:*` keys
- **TTL**: Automatic expiration based on time windows

## Deployment Considerations

### Production Settings
1. **Reduce Limits**: Consider stricter limits for production
2. **Monitor Usage**: Track legitimate user patterns
3. **Adjust Windows**: Fine-tune time windows based on usage patterns

### Security Best Practices
1. **Monitor Logs**: Watch for rate limit violations
2. **Alert Setup**: Configure alerts for excessive rate limiting
3. **IP Whitelist**: Consider whitelisting known good IPs
4. **Load Balancer**: Ensure proper IP forwarding configuration

## Testing Rate Limits

### Manual Testing
```bash
# Test login rate limiting
for i in {1..6}; do
  curl -X POST http://localhost:5000/login \
    -d "email=test@example.com&password=wrong" \
    -H "Content-Type: application/x-www-form-urlencoded"
done
```

### Monitoring Commands
```bash
# Check Redis rate limit keys
redis-cli KEYS "pyrate_limiter:*"

# Check failed attempt counters
redis-cli KEYS "failed_attempts:*"

# Get specific counter value
redis-cli GET "failed_attempts:login:abc123"
```

## Troubleshooting

### Common Issues
1. **Redis Connection**: Check Redis server availability
2. **High False Positives**: Adjust rate limits or time windows
3. **Proxy Configuration**: Verify TRUSTED_PROXIES setting
4. **Performance**: Monitor Redis performance under load

### Debug Mode
Set application logging to DEBUG level to see detailed rate limiting information:

```python
import logging
logging.getLogger('rate_limiter').setLevel(logging.DEBUG)
```

## Future Enhancements

1. **Dynamic Limits**: Adjust limits based on user behavior
2. **Geographic Filtering**: Different limits by geographic region
3. **Machine Learning**: Detect anomalous patterns
4. **Dashboard**: Web interface for monitoring and management