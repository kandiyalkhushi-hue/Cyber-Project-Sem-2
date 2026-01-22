from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import db, User, Attendance, LeaveRequest, Admin, AppSetting
from app import bcrypt
from sqlalchemy import desc
from app.routes import generate_captcha   # ✅ Import captcha generator

# ✅ FIXED — removed template_folder
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ---------------------------------------------------
# Helper: Check if admin is logged in
# ---------------------------------------------------
def require_admin():
    return "admin_id" in session


# ---------------------------------------------------
# ✅ ADMIN LOGIN (with CAPTCHA)
# ---------------------------------------------------
@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    captcha = generate_captcha()

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user_answer = request.form.get("captcha_answer", "").lower()
        correct_answer = request.form.get("captcha_correct", "").lower()

        # Captcha validation
        if user_answer != correct_answer:
            flash("Invalid captcha!", "danger")
            return render_template("admin_login.html", captcha=generate_captcha())

        admin = Admin.query.filter_by(email=email).first()

        if not admin or not bcrypt.check_password_hash(admin.password_hash, password):
            flash("Invalid admin credentials.", "danger")
            return render_template("admin_login.html", captcha=generate_captcha())

        session["admin_id"] = admin.id
        flash("Welcome, Admin!", "success")
        return redirect(url_for("admin.dashboard"))

    return render_template("admin_login.html", captcha=captcha)


# ---------------------------------------------------
# ✅ LOGOUT
# ---------------------------------------------------
@admin_bp.route("/logout")
def logout():
    session.pop("admin_id", None)
    flash("Admin logged out successfully.", "success")
    return redirect(url_for("admin.login"))


# ---------------------------------------------------
# ✅ ADMIN DASHBOARD
# ---------------------------------------------------
@admin_bp.route("/")
def dashboard():
    if not require_admin():
        return redirect(url_for("admin.login"))

    users_count = User.query.count()
    attendance_count = Attendance.query.count()
    pending_leaves = LeaveRequest.query.filter_by(status="Pending").count()

    return render_template("admin_dashboard.html",
                           users_count=users_count,
                           attendance_count=attendance_count,
                           pending_leaves=pending_leaves)


# ---------------------------------------------------
# ✅ STUDENT LIST
# ---------------------------------------------------
@admin_bp.route("/students")
def students():
    if not require_admin():
        return redirect(url_for("admin.login"))

    students = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin_students.html", students=students)


@admin_bp.route("/students/<int:user_id>/delete", methods=["POST"])
def delete_student(user_id):
    if not require_admin():
        return redirect(url_for("admin.login"))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()

    flash("Student deleted successfully.", "success")
    return redirect(url_for("admin.students"))


# ---------------------------------------------------
# ✅ ATTENDANCE LOGS
# ---------------------------------------------------
@admin_bp.route("/attendance")
def attendance():
    if not require_admin():
        return redirect(url_for("admin.login"))

    logs = Attendance.query.order_by(desc(Attendance.timestamp)).limit(200).all()
    return render_template("admin_attendance.html", logs=logs)


# ---------------------------------------------------
# ✅ LEAVE REQUESTS
# ---------------------------------------------------
@admin_bp.route("/leaves")
def leaves():
    if not require_admin():
        return redirect(url_for("admin.login"))

    leaves = LeaveRequest.query.order_by(desc(LeaveRequest.created_at)).all()
    return render_template("admin_leaves.html", leaves=leaves)


@admin_bp.route("/leaves/<int:leave_id>/approve", methods=["POST"])
def approve_leave(leave_id):
    if not require_admin():
        return redirect(url_for("admin.login"))

    lr = LeaveRequest.query.get_or_404(leave_id)
    lr.status = "Approved"
    db.session.commit()

    flash("Leave approved.", "success")
    return redirect(url_for("admin.leaves"))


@admin_bp.route("/leaves/<int:leave_id>/reject", methods=["POST"])
def reject_leave(leave_id):
    if not require_admin():
        return redirect(url_for("admin.login"))

    lr = LeaveRequest.query.get_or_404(leave_id)
    lr.status = "Rejected"
    db.session.commit()

    flash("Leave rejected.", "warning")
    return redirect(url_for("admin.leaves"))


# ---------------------------------------------------
# ✅ CAPTCHA SETTINGS PAGE
# ---------------------------------------------------
@admin_bp.route("/settings", methods=["GET", "POST"])
def settings():
    if not require_admin():
        return redirect(url_for("admin.login"))

    s = AppSetting.query.first()

    # Create default settings row if missing
    if not s:
        s = AppSetting()
        db.session.add(s)
        db.session.commit()

    if request.method == "POST":
        s.captcha_text = bool(request.form.get("captcha_text"))
        s.captcha_math = bool(request.form.get("captcha_math"))
        s.captcha_emoji = bool(request.form.get("captcha_emoji"))
        s.captcha_audio = bool(request.form.get("captcha_audio"))

        db.session.commit()
        flash("Settings updated successfully.", "success")
        return redirect(url_for("admin.settings"))

    return render_template("admin_settings.html", s=s)
