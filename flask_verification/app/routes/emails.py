from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("emails", __name__, url_prefix="/emails")


def _get_service():
    service = current_app.extensions.get("email_verification_service")
    if service is None:
        current_app.logger.error("Email verification service not configured.")
        return None
    service.start()
    return service


@bp.post("/create")
def create_email():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid or missing JSON payload"}), 400

    service = _get_service()
    if service is None:
        return jsonify({"error": "Verification service unavailable"}), 503

    job_id = service.enqueue(data)
    return jsonify({"job_id": job_id, "status": "queued"}), 202


@bp.get("/status/<job_id>")
def email_status(job_id):
    service = _get_service()
    if service is None:
        return jsonify({"error": "Verification service unavailable"}), 503

    result = service.get_result(job_id)
    if result is None:
        return jsonify({"error": "Unknown job id"}), 404

    payload = dict(result)
    payload["job_id"] = job_id
    status_code = payload.pop("http_status", 200)
    return jsonify(payload), status_code

# @bp.get("")
# def list_emails():
#     rows = Email.query.order_by(Email.id.desc()).all()
#     return jsonify([
#         {
#             "id": r.id,
#             "email_id": r.email_id,
#             "user": r.user,
#             "subject": r.subject,
#             "state": r.state,
#             "created_at": r.created_at.isoformat(),
#         } for r in rows
#     ])
