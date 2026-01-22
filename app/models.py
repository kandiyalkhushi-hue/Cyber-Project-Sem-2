from datetime import datetime
from app import db

# -----------------------------
# USERS
# -----------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    attendance_records = db.relationship("Attendance", backref="user", lazy=True, cascade="all, delete-orphan")
    leave_requests = db.relationship("LeaveRequest", backref="user", lazy=True, cascade="all, delete-orphan")

# -----------------------------
# ATTENDANCE
# -----------------------------
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False)  # Present
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

# -----------------------------
# LEAVE REQUESTS
# -----------------------------
class LeaveRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="Pending")  # Pending/Approved/Rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# -----------------------------
# ADMIN
# -----------------------------
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, default="Admin")
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# -----------------------------
# APP SETTINGS (CAPTCHA TOGGLES)
# -----------------------------
class AppSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    captcha_text = db.Column(db.Boolean, default=True)
    captcha_math = db.Column(db.Boolean, default=True)
    captcha_emoji = db.Column(db.Boolean, default=False)  # placeholder for future
    captcha_audio = db.Column(db.Boolean, default=False)  # placeholder for future
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
