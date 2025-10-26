# Email Notification Deduplication Service

This repository contains a minimal email-notification pipeline composed of two Dockerised components:

- `flask_verification`: a Flask API that accepts email requests, enqueues them for background verification, deduplicates by `email_id`, and persists the results in a relational database.
- `email_generator`: a simple producer that emits random email payloads and polls the verification API to demonstrate the asynchronous workflow.

## Features

- **Asynchronous verification**: the HTTP endpoint returns immediately with a job identifier while a background worker validates, deduplicates, and stores the email.
- **Deduplication**: `email_id` is enforced as unique; duplicates are reported through the job status API.
- **Pluggable storage**: defaults to SQLite for local development but honours the `DATABASE_URL` environment variable.
- **Sample producer**: the generator service exercises both the happy path and several error cases (missing fields, duplicates).

## Quick start

The easiest way to run the demo stack is via Docker Compose.

```bash
docker-compose up --build
```

This starts:

1. `flask_verification` on <http://localhost:5000>
2. `email_generator`, which continually posts sample payloads and prints job/status responses to stdout

Stop the stack with `Ctrl+C`. Docker volume data (SQLite database) lives inside the `flask_verification` container and is discarded when the container is removed.

### Running without Docker

If you prefer to run the services manually:

1. Create and activate a virtual environment.
2. Install dependencies for the API:
   ```bash
   pip install -r flask_verification/requirements.txt
   ```
3. Start the Flask API:
   ```bash
   cd flask_verification
   flask --app wsgi run --host 0.0.0.0 --port 5000
   ```
4. In a separate shell, install the generator dependencies and run it:
   ```bash
   pip install -r email_generator/requirements.txt
   python email_generator/generator.py
   ```

## API

All endpoints live under the `/emails` prefix.

### `POST /emails/create`

Queues a new email verification job.

**Request body**

```json
{
  "email_id": "12345",
  "user": "recipient@example.com",
  "subject": "Your invoice",
  "body": "Invoice content...",
  "state": "pending"
}
```

- `email_id`, `user`, and `body` are validated during background processing.
- Additional fields are stored if present.

**Response**

```json
{
  "job_id": "f1d31c5a-a116-4fa5-93b3-5ec86d8a793a",
  "status": "queued"
}
```

Status code: `202 Accepted`

### `GET /emails/status/<job_id>`

Returns the latest information for a previously submitted job.

Possible response bodies:

```json
{ "job_id": "...", "status": "processing" }
{ "job_id": "...", "status": "completed", "email_db_id": 7, "message": "Email stored" }
{ "job_id": "...", "status": "duplicate", "email_db_id": 3, "message": "Email already stored" }
{ "job_id": "...", "status": "failed", "message": "Missing required fields: body" }
{ "job_id": "...", "status": "error", "message": "Internal verification error" }
```

Status codes mirror the underlying outcome:

- `202 Accepted` – queued or processing
- `201 Created` – stored successfully
- `409 Conflict` – duplicate `email_id`
- `400 Bad Request` – validation failure
- `500 Internal Server Error` – unexpected error during verification
- `404 Not Found` – unknown `job_id`

## Background processing flow

1. The HTTP request enqueues the payload and returns a `job_id`.
2. A dedicated worker thread consumes queued jobs, operating inside the Flask application context.
3. Each payload is validated for required fields, checked for duplicates, and written to the database when valid.
4. Verification results are stored in-memory and exposed through the status endpoint. The generator service uses the same endpoint to display live outcomes.

## Configuration

| Variable | Service | Description | Default |
| --- | --- | --- | --- |
| `DATABASE_URL` | `flask_verification` | SQLAlchemy database URL | `sqlite:///../emails.db` |
| `VERIFY_URL` | `email_generator` | URL for the create endpoint | `http://flask_verification:5000/emails/create` |
| `STATUS_URL_TEMPLATE` | `email_generator` | Optional format string for the status endpoint (`{job_id}` placeholder required) | derived from `VERIFY_URL` |
| `GEN_INTERVAL` | `email_generator` | Seconds to wait between requests | `5` |

## Repository layout

- `flask_verification/app/background.py` – background queue and worker implementation
- `flask_verification/app/routes/emails.py` – HTTP routes for enqueueing and status lookup
- `flask_verification/app/models.py` – SQLAlchemy model used for persisted emails
- `email_generator/generator.py` – sample producer driving the workflow
