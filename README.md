# Email Notification Deduplication Service

A robust webhook-based service designed to handle transactional email notifications with built-in deduplication, retry mechanisms, and failure handling.

## Overview

This service ensures reliable delivery of transactional emails (invoices, password resets, etc.) while preventing duplicate sends through a webhook-based architecture. It handles concurrent requests, implements retry mechanisms, and maintains idempotency in email delivery.

## Key Features

- **Webhook Integration**: Handles incoming email notification webhooks
- **Deduplication**: Prevents duplicate email sends using unique constraints
- **Retry Mechanism**: Implements exponential backoff for failed sends
- **Concurrent Processing**: Safely handles multiple simultaneous webhook requests
- **Background Processing**: Uses worker queues for asynchronous email sending
- **Monitoring**: Tracks statistics for sent, pending, and failed emails
- **Dead Letter Queue**: Logs permanently failed email attempts

## Getting Started

### Prerequisites

- Python 3.8+
- Redis (for distributed locking)
- SQL Database

### Installation

1. Clone the repository:
```bash
git clone https://github.com/noorulain276775/Email-Notification-Deduplication-Service.git
cd Email-Notification-Deduplication-Service
```

2. Set up a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Running Docker Image:
```bash
docker build -t fastapi-email-dedupe ./fastapi_app
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Configuration

Key configuration options in `.env`:

```ini
DATABASE_URL=postgresql://user:pass@localhost/dbname
REDIS_URL=redis://localhost:6379
RETRY_DELAY_SECONDS=5
MAX_RETRY_ATTEMPTS=3
```

## API Documentation

### Webhook Endpoint

```http
POST /webhook/email
Content-Type: application/json

{
  "email_id": "unique_id",
  "user": "recipient@example.com",
  "subject": "Your Invoice",
  "body": "Invoice content..."
}
```

### Status Endpoint

```http
GET /stats
```
Returns counts of pending, sent, and failed emails.

## Architecture

The service implements:
- Webhook handler for receiving email events
- Background worker system using queues
- Idempotency through database constraints
- Retry mechanism with exponential backoff
- Redis-based distributed locking
- Comprehensive logging and monitoring

## Testing

Run the test suite:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest --cov=src tests/
```

## Monitoring

Access service statistics at `/stats` endpoint for:
- Total emails received
- Successfully sent emails
- Failed attempts
- Current pending queue size

## Author

Noor Ul ain Ibrahim - [@noorulain276775](https://github.com/noorulain276775)