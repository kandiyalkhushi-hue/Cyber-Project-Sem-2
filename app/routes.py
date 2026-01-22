# app/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app.models import db, User, Attendance, LeaveRequest, AppSetting
from app import bcrypt
import random, string, os, time

main = Blueprint("main", __name__)

# ---------------- CAPTCHA BUILDERS -----------------

def create_text_captcha():
    text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return {"type": "text", "question": None, "text": text, "answer": text.lower()}

def create_math_captcha():
    a, b = random.randint(1, 9), random.randint(1, 9)
    q = f"{a} + {b}"
    return {"type": "math", "question": q, "text": None, "answer": str(a + b)}

def create_emoji_captcha():
    """
    Shows a grid of emojis and asks: 'How many of <target> are there?'
    User answer is a number as string.
    """
    pool = ["🐱","🐶","🐼","🦊","🐵","🐸","🐷","🐨","🐯","🦁","🐔","🐰"]
    target = random.choice(pool)
    grid = [random.choice(pool) for _ in range(16)]
    answer = str(sum(1 for e in grid if e == target))
    return {
        "type": "emoji",
        "emoji_grid": grid,     # list of 16
        "emoji_target": target, # the one to count
        "answer": answer
    }

def create_audio_captcha():
    """
    Generates a 5-digit code and saves a spoken MP3/WAV to static/audio/.
    Returns audio_url for <audio> tag and the correct answer.
    """
    try:
        import pyttsx3
    except Exception:
        # If pyttsx3 missing at runtime, fall back to text captcha
        return create_text_captcha()

    code = ''.join(random.choices("23456789", k=5))  # avoid 0/1 confusion
    # paths
    audio_dir = os.path.join(current_app.static_folder, "audio")
    os.makedirs(audio_dir, exist_ok=True)
    fname = f"cap_{int(time.time()*1000)}_{random.randint(1000,9999)}.mp3"
    abs_path = os.path.join(audio_dir, fname)
    rel_url = f"/static/audio/{fname}"

    # TTS
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)
        engine.setProperty('volume', 1.0)
        # Add some spacing when spoken: "2  3  7  8  4"
        spoken = "  ".join(list(code))
        engine.save_to_file(f"Please type the digits: {spoken}", abs_path)
        engine.runAndWait()
    except Exception:
        # If TTS fails on the machine, fallback to text captcha
        return create_text_captcha()

    return {
        "type": "audio",
        "audio_url": rel_url,
        "answer": code
    }

def generate_captcha():
    """
    Chooses captcha type according to AppSetting toggles.
    If table empty, create defaults.
    """
    s = AppSetting.query.first()
    if not s:
        s = AppSetting(captcha_text=True, captcha_math=True, captcha_emoji=False, captcha_audio=False)
        db.session.add(s); db.session.commit()

    available = []
    if s.captcha_text:  available.append("text")
    if s.captcha_math:  available.append("math")
    if s.captcha_emoji: available.append("emoji")
    if s.captcha_audio: available.append("audio")

    if not available:
        available = ["text"]

    choice = random.choice(available)
    if choice == "text":  return create_text_captcha()
    if choice == "math":  return create_math_captcha()
    if choice == "emoji": return create_emoji_captcha()
    if choice == "audio": return create_audio_captcha()
    return create_text_captcha()

# ---------------- ROUTES -----------------

@main.route("/")
def home():
    return render_template("base.html")

@main.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name","").strip()
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        user_answer = request.form.get("captcha_answer","").lower().strip()
        correct = request.form.get("captcha_correct","").lower().strip()

        form_data = {"name": name, "email": email}

        if user_answer != correct:
            flash("Invalid captcha!", "danger")
            return render_template("signup.html", captcha=generate_captcha(), form_data=form_data)

        if not name or not email or not password:
            flash("Please fill all fields.", "danger")
            return render_template("signup.html", captcha=generate_captcha(), form_data=form_data)

        if User.query.filter_by(email=email).first():
            flash("Email already registered!", "danger")
            return render_template("signup.html", captcha=generate_captcha(), form_data=form_data)

        pw = bcrypt.generate_password_hash(password).decode("utf-8")
        db.session.add(User(name=name, email=email, password_hash=pw))
        db.session.commit()
        flash("Signup successful! Please login.", "success")
        return redirect(url_for("main.login"))

    return render_template("signup.html", captcha=generate_captcha(), form_data={})

@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        user_answer = request.form.get("captcha_answer","").lower().strip()
        correct = request.form.get("captcha_correct","").lower().strip()

        if user_answer != correct:
            flash("Invalid captcha!", "danger")
            return render_template("login.html", captcha=generate_captcha())

        user = User.query.filter_by(email=email).first()
        if not user or not bcrypt.check_password_hash(user.password_hash, password):
            flash("Invalid email or password.", "danger")
            return render_template("login.html", captcha=generate_captcha())

        session["user_id"] = user.id
        flash("Login successful!", "success")
        return redirect(url_for("main.attendance"))

    return render_template("login.html", captcha=generate_captcha())

@main.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out.", "success")
    return redirect(url_for("main.home"))

@main.route("/attendance", methods=["GET","POST"])
def attendance():
    if "user_id" not in session:
        return redirect(url_for("main.login"))

    if request.method == "POST":
        attendance_val = request.form.get("attendance")
        user_answer = request.form.get("captcha_answer","").lower().strip()
        correct = request.form.get("captcha_correct","").lower().strip()

        if user_answer != correct:
            flash("Invalid captcha!", "danger")
            return render_template("attendance.html", captcha=generate_captcha())

        if attendance_val != "Present":
            flash("Invalid option.", "danger")
            return render_template("attendance.html", captcha=generate_captcha())

        db.session.add(Attendance(user_id=session["user_id"], status="Present"))
        db.session.commit()
        flash("Attendance marked successfully!", "success")

    return render_template("attendance.html", captcha=generate_captcha())

@main.route("/apply-leave", methods=["POST"])
def apply_leave():
    if "user_id" not in session:
        return redirect(url_for("main.login"))
    reason = request.form.get("reason","").strip()
    if not reason:
        flash("Please enter a reason.", "danger")
        return redirect(url_for("main.attendance"))
    db.session.add(LeaveRequest(user_id=session["user_id"], reason=reason, status="Pending"))
    db.session.commit()
    flash("Leave request submitted!", "success")
    return redirect(url_for("main.attendance"))
