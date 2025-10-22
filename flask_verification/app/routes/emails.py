from flask import Blueprint, request, jsonify
from ..extensions import db
from ..models import Email
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

bp = Blueprint("emails", __name__, url_prefix="/emails")

@bp.post("/create")
def create_email():
    data = request.get_json(silent=True) or {}
    required_fields = ("email_id", "user", "body")
    missing = [k for k in required_fields if k not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
    email_id = str(data["email_id"])
    existing_id = db.session.execute(select(Email.id).filter_by(email_id=email_id)).scalar_one_or_none()
    if existing_id is not None:
        return jsonify({"message": "Email is duplicate", "id": existing_id}), 409
    e = Email(
        email_id=data["email_id"],
        user=data["user"],
        subject=data.get("subject"),
        body=data.get("body"),
        state=data.get("state", "pending"),
    )
    db.session.add(e)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Error occured"}), 409
    return jsonify({"id": e.id}), 201

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
