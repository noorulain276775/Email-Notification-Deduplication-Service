from datetime import datetime
from .extensions import db

class Email(db.Model):
    __tablename__ = "emails"
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.String(64), unique=True, nullable=False)
    user = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(255))
    body = db.Column(db.Text)
    state = db.Column(db.String(32), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
