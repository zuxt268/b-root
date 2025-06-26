# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask-based SaaS application that automatically syncs Instagram content to WordPress blogs. The system integrates with Facebook/Instagram Graph API, WordPress REST API, Stripe for payments, and various third-party services (OpenAI, SendGrid, Slack).

## Development Commands

**Running the Application:**
```bash
# Local development
python app.py

# Production with Gunicorn
gunicorn --bind 0.0.0.0:8000 wsgi:app

# Health check endpoint
curl http://localhost:5000/flask-health-check
```

**Code Quality:**
```bash
# Linting
flake8 .

# Type checking  
mypy .

# Code formatting
black .
```

**Testing:**
```bash
# Run tests (pytest is available)
pytest

# Run specific test file
pytest test_filename.py
```

## Architecture Overview

**Clean Architecture Pattern:**
- **Blueprints** (`blueprint/`): HTTP request/response handling, routing
- **Services** (`service/`): Business logic orchestration, external API integration
- **Repositories** (`repository/`): Data persistence layer with Unit of Work pattern
- **Domain** (`domain/`): Core business entities, validation, error handling

**Key Architectural Components:**

**Unit of Work Pattern** (`repository/unit_of_work.py`):
- Manages database transactions and connection pooling
- MySQL connection with PyMySQL driver
- Automatic rollback on exceptions
- Pool size: 5, max overflow: 10, pool recycle: 3600s

**Service Layer Integration:**
- **Meta Service**: Facebook/Instagram Graph API integration
- **WordPress Services**: Factory pattern for different WordPress configurations
- **OpenAI Service**: Customer support and content processing
- **Stripe Integration**: Subscription management via `wordpress_service_stripe.py`

**Authentication & Authorization:**
- Session-based auth for customers and admin users
- HMAC-based API authentication for external integrations
- Redis-based token management for email verification

**Database Schema:**
- `customers`: User accounts, Instagram tokens, WordPress URLs, payment info
- `admin_users`: Administrative access
- `posts`: Synchronized content tracking
- Instagram token status enum: NOT_CONNECTED(0), CONNECTED(1), EXPIRED(2)

**Environment Configuration:**
- Database: `DATABASE_USER`, `DATABASE_PASSWORD`, `DATABASE_HOST`, `DATABASE_SCHEME`
- Redis connection managed via Flask `g` object
- `.env` file loaded via python-dotenv

**Error Handling:**
- Global exception handler with Slack notifications
- Stack trace logging with client IP tracking
- Custom error templates and 404 handling

**Key Business Logic:**
- Instagram content filtering by customer start_date
- Duplicate post prevention via media_id tracking
- Batch processing for content synchronization
- WordPress publishing with permalink tracking

## Development Notes

**Adding New Features:**
- Follow the Service -> Repository -> Domain pattern
- Use Unit of Work for database operations
- Add appropriate error handling with Slack notifications
- Implement proper validation in domain objects

**Database Operations:**
- Always use Unit of Work context manager
- Commit explicitly after successful operations
- Repository pattern abstracts SQLAlchemy models

**External API Integration:**
- Rate limiting implemented via pyrate-limiter
- Proper error handling for API failures
- Token refresh logic for Instagram/Facebook APIs

**Security Considerations:**
- Password hashing via scrypt (Werkzeug)
- CSRF protection via Flask-WTF
- Session security with 365-day lifetime
- HMAC signature validation for API endpoints