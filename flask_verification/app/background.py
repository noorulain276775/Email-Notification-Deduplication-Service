import atexit
import queue
import threading
import uuid
from typing import Dict, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .extensions import db
from .models import Email


class EmailVerificationService:
    """Background processor that verifies and stores incoming email payloads."""

    def __init__(self, app=None):
        self.app = None
        self._queue: "queue.Queue[Optional[tuple[str, dict]]]" = queue.Queue()
        self._results: Dict[str, Dict] = {}
        self._results_lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker: Optional[threading.Thread] = None
        self._atexit_registered = False
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Bind the service to a Flask app and start the worker."""
        if "email_verification_service" in app.extensions:
            return app.extensions["email_verification_service"]

        self.app = app
        app.extensions["email_verification_service"] = self

        if not self._atexit_registered:
            atexit.register(self.stop)
            self._atexit_registered = True

        self.start()
        return self

    def start(self):
        if self._worker and self._worker.is_alive():
            return

        self._stop_event.clear()
        self._worker = threading.Thread(
            target=self._run,
            name="email-verification-worker",
            daemon=True,
        )
        self._worker.start()

    def stop(self):
        if not self._worker:
            return

        self._stop_event.set()
        self._queue.put(None)
        self._worker.join(timeout=5)
        self._worker = None

    def enqueue(self, payload: dict) -> str:
        job_id = str(uuid.uuid4())
        with self._results_lock:
            self._results[job_id] = {"status": "queued", "http_status": 202}
        self._queue.put((job_id, payload))
        return job_id

    def get_result(self, job_id: str) -> Optional[Dict]:
        with self._results_lock:
            result = self._results.get(job_id)
            return dict(result) if result is not None else None

    def _run(self):
        while not self._stop_event.is_set():
            item = self._queue.get()
            if item is None:
                self._queue.task_done()
                break

            job_id, payload = item

            with self._results_lock:
                self._results[job_id] = {"status": "processing", "http_status": 202}

            result = self._process_payload(payload)

            with self._results_lock:
                self._results[job_id] = result

            self._queue.task_done()

        # Drain remaining sentinel values if present
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
            finally:
                self._queue.task_done()

    def _process_payload(self, payload: dict) -> Dict:
        with self.app.app_context():
            missing = [k for k in ("email_id", "user", "body") if not payload.get(k)]
            if missing:
                self.app.logger.warning(
                    "Rejecting email payload missing fields: %s", ", ".join(missing)
                )
                return {
                    "status": "failed",
                    "message": f"Missing required fields: {', '.join(missing)}",
                    "http_status": 400,
                }

            email_id = str(payload["email_id"])

            try:
                existing_id = db.session.execute(
                    select(Email.id).filter_by(email_id=email_id)
                ).scalar_one_or_none()
                if existing_id is not None:
                    return {
                        "status": "duplicate",
                        "message": "Email already stored",
                        "email_db_id": existing_id,
                        "http_status": 409,
                    }

                email = Email(
                    email_id=email_id,
                    user=payload["user"],
                    subject=payload.get("subject"),
                    body=payload.get("body"),
                    state=payload.get("state", "pending"),
                )
                db.session.add(email)
                db.session.commit()

                return {
                    "status": "completed",
                    "message": "Email stored",
                    "email_db_id": email.id,
                    "http_status": 201,
                }

            except IntegrityError:
                db.session.rollback()
                existing_id = db.session.execute(
                    select(Email.id).filter_by(email_id=email_id)
                ).scalar_one_or_none()
                return {
                    "status": "duplicate",
                    "message": "Email already stored",
                    "email_db_id": existing_id,
                    "http_status": 409,
                }
            except Exception:
                db.session.rollback()
                self.app.logger.exception("Unexpected error verifying email payload.")
                return {
                    "status": "error",
                    "message": "Internal verification error",
                    "http_status": 500,
                }
