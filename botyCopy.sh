#!/usr/bin/env bash
# ตั้งค่าโปรเจกต์แอปหางาน/จ้างงาน (Flask + SQLite) อัตโนมัติ
# ใช้งาน: bash setup_freelance_app.sh
# เปลี่ยนพอร์ตตอนรันแอปได้ด้วยตัวแปรแวดล้อม PORT เช่น: PORT=8080 python app.py
set -e

PROJECT_DIR="$HOME/freelance_app"
echo "==> สร้างโฟลเดอร์โปรเจกต์ที่ $PROJECT_DIR"
mkdir -p "$PROJECT_DIR/templates" "$PROJECT_DIR/static/css" "$PROJECT_DIR/static/uploads/profile" "$PROJECT_DIR/static/uploads/chat"
cd "$PROJECT_DIR"

echo "==> เขียนไฟล์ app.py"
cat > app.py << 'EOF'
import os
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, g
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from db import get_db, init_db, get_app_name

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(__file__)
UPLOAD_PROFILE = os.path.join(BASE_DIR, "static", "uploads", "profile")
UPLOAD_CHAT = os.path.join(BASE_DIR, "static", "uploads", "chat")
ALLOWED_IMAGE = {"png", "jpg", "jpeg", "gif", "webp"}
ALLOWED_VIDEO = {"mp4", "mov", "webm"}

# Admin login (as requested by the app owner)
ADMIN_USERNAME = "3894"
ADMIN_PASSWORD = "148222"

app = Flask(__name__)
app.secret_key = "change-this-secret-key-in-production"
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB uploads

os.makedirs(UPLOAD_PROFILE, exist_ok=True)
os.makedirs(UPLOAD_CHAT, exist_ok=True)


def allowed_file(filename, allowed_set):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_set


# ---------------------------------------------------------------------------
# Context / helpers
# ---------------------------------------------------------------------------
@app.context_processor
def inject_globals():
    return {
        "app_name": get_app_name(),
        "current_user": get_current_user(),
        "unread_notif_count": get_unread_notif_count(),
    }


def get_current_user():
    if "user_id" not in session:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    conn.close()
    return user


def get_unread_notif_count():
    if "user_id" not in session:
        return 0
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) as c FROM notifications WHERE user_id = ? AND is_read = 0",
        (session["user_id"],),
    ).fetchone()
    conn.close()
    return row["c"]


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# Auth: signup / login / logout
# ---------------------------------------------------------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        day = request.form.get("birth_day", "").strip()
        month = request.form.get("birth_month", "").strip()
        year = request.form.get("birth_year", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        errors = []
        if not all([first_name, last_name, email, phone, day, month, year, password, confirm]):
            errors.append("กรุณากรอกข้อมูลให้ครบทุกช่อง")
        if password != confirm:
            errors.append("รหัสผ่านและการยืนยันรหัสผ่านไม่ตรงกัน")
        if len(password) < 6:
            errors.append("รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร")

        conn = get_db()
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            errors.append("อีเมลนี้ถูกใช้สมัครแล้ว")

        if errors:
            conn.close()
            for e in errors:
                flash(e, "error")
            return render_template("signup.html", form=request.form)

        password_hash = generate_password_hash(password)
        cur = conn.execute(
            """INSERT INTO users
               (first_name, last_name, email, phone, birth_day, birth_month, birth_year, password_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (first_name, last_name, email, phone, day, month, year, password_hash),
        )
        conn.commit()
        user_id = cur.lastrowid
        conn.close()

        session["user_id"] = user_id
        session["just_signed_up"] = True
        return redirect(url_for("home"))

    return render_template("signup.html", form={})


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            return redirect(url_for("home"))
        flash("อีเมลหรือรหัสผ่านไม่ถูกต้อง", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------
@app.route("/")
@login_required
def home():
    show_welcome = session.pop("just_signed_up", False)
    return render_template("home.html", show_welcome=show_welcome)


# ---------------------------------------------------------------------------
# Find job (หางาน)
# ---------------------------------------------------------------------------
@app.route("/find-job")
@login_required
def find_job():
    conn = get_db()
    categories = conn.execute("SELECT * FROM job_categories ORDER BY name").fetchall()
    conn.close()
    return render_template("find_job.html", categories=categories, active_tab="find_job")


@app.route("/find-job/<int:category_id>")
@login_required
def find_job_category(category_id):
    conn = get_db()
    category = conn.execute("SELECT * FROM job_categories WHERE id = ?", (category_id,)).fetchone()
    jobs = conn.execute(
        """SELECT job_posts.*, users.first_name, users.last_name
           FROM job_posts JOIN users ON job_posts.employer_id = users.id
           WHERE category_id = ? AND status = 'open'
           ORDER BY job_posts.created_at DESC""",
        (category_id,),
    ).fetchall()
    conn.close()
    return render_template("job_list.html", category=category, jobs=jobs, active_tab="find_job")


@app.route("/job/<int:job_id>")
@login_required
def job_detail(job_id):
    conn = get_db()
    job = conn.execute(
        """SELECT job_posts.*, users.first_name, users.last_name, users.id as employer_user_id
           FROM job_posts JOIN users ON job_posts.employer_id = users.id
           WHERE job_posts.id = ?""",
        (job_id,),
    ).fetchone()
    conn.close()
    return render_template("job_detail.html", job=job, active_tab="find_job")


@app.route("/job/<int:job_id>/accept", methods=["POST"])
@login_required
def accept_job(job_id):
    conn = get_db()
    job = conn.execute("SELECT * FROM job_posts WHERE id = ?", (job_id,)).fetchone()
    if not job:
        conn.close()
        return redirect(url_for("find_job"))

    room = conn.execute(
        "SELECT * FROM chat_rooms WHERE job_post_id = ? AND seeker_id = ?",
        (job_id, session["user_id"]),
    ).fetchone()

    if not room:
        cur = conn.execute(
            "INSERT INTO chat_rooms (job_post_id, employer_id, seeker_id) VALUES (?, ?, ?)",
            (job_id, job["employer_id"], session["user_id"]),
        )
        room_id = cur.lastrowid
        conn.execute(
            "INSERT INTO chat_messages (room_id, sender_id, msg_type, content) VALUES (?, ?, 'system', ?)",
            (room_id, session["user_id"], "เริ่มการสนทนาเกี่ยวกับงาน: " + job["title"]),
        )
        conn.commit()
    else:
        room_id = room["id"]
    conn.close()
    return redirect(url_for("chat_room", room_id=room_id))


# ---------------------------------------------------------------------------
# Hire job (จ้างงาน)
# ---------------------------------------------------------------------------
@app.route("/hire-job", methods=["GET", "POST"])
@login_required
def hire_job():
    conn = get_db()
    categories = conn.execute("SELECT * FROM job_categories ORDER BY name").fetchall()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category_id = request.form.get("category_id")
        pay_amount = request.form.get("pay_amount", "0")
        contact_tiktok = request.form.get("contact_tiktok", "").strip()
        contact_phone = request.form.get("contact_phone", "").strip()
        contact_facebook = request.form.get("contact_facebook", "").strip()
        details = request.form.get("details", "").strip()

        if not title or not category_id:
            flash("กรุณากรอกชื่องานและเลือกประเภทงาน", "error")
            conn.close()
            return render_template("hire_job.html", categories=categories, form=request.form, active_tab="hire_job")

        cur = conn.execute(
            """INSERT INTO job_posts
               (employer_id, title, category_id, pay_amount, contact_tiktok, contact_phone, contact_facebook, details)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (session["user_id"], title, category_id, pay_amount or 0,
             contact_tiktok, contact_phone, contact_facebook, details),
        )
        job_id = cur.lastrowid

        # Notify friends (job seekers who have friended this employer)
        friends = conn.execute(
            "SELECT friend_id FROM friends WHERE user_id = ?", (session["user_id"],)
        ).fetchall()
        for f in friends:
            conn.execute(
                "INSERT INTO notifications (user_id, message, job_post_id) VALUES (?, ?, ?)",
                (f["friend_id"], f'เพื่อนของคุณประกาศหาคนทำงานใหม่: "{title}"', job_id),
            )

        conn.commit()
        conn.close()
        flash("ประกาศงานสำเร็จ", "success")
        return redirect(url_for("hire_job"))

    my_jobs = conn.execute(
        "SELECT job_posts.*, job_categories.name as category_name FROM job_posts "
        "JOIN job_categories ON job_posts.category_id = job_categories.id "
        "WHERE employer_id = ? ORDER BY job_posts.created_at DESC",
        (session["user_id"],),
    ).fetchall()
    conn.close()
    return render_template("hire_job.html", categories=categories, form={}, my_jobs=my_jobs, active_tab="hire_job")


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------
@app.route("/chat")
@login_required
def chat_list():
    conn = get_db()
    uid = session["user_id"]
    rooms = conn.execute(
        """SELECT chat_rooms.*, job_posts.title as job_title,
               emp.first_name as emp_first, emp.last_name as emp_last,
               seek.first_name as seek_first, seek.last_name as seek_last
           FROM chat_rooms
           JOIN job_posts ON chat_rooms.job_post_id = job_posts.id
           JOIN users emp ON chat_rooms.employer_id = emp.id
           JOIN users seek ON chat_rooms.seeker_id = seek.id
           WHERE chat_rooms.employer_id = ? OR chat_rooms.seeker_id = ?
           ORDER BY chat_rooms.id DESC""",
        (uid, uid),
    ).fetchall()
    conn.close()
    return render_template("chat_list.html", rooms=rooms, uid=uid, active_tab="chat")


@app.route("/chat/<int:room_id>", methods=["GET", "POST"])
@login_required
def chat_room(room_id):
    conn = get_db()
    uid = session["user_id"]
    room = conn.execute(
        """SELECT chat_rooms.*, job_posts.title as job_title, job_posts.status as job_status
           FROM chat_rooms JOIN job_posts ON chat_rooms.job_post_id = job_posts.id
           WHERE chat_rooms.id = ?""",
        (room_id,),
    ).fetchone()

    if not room or uid not in (room["employer_id"], room["seeker_id"]):
        conn.close()
        return redirect(url_for("chat_list"))

    other_id = room["seeker_id"] if uid == room["employer_id"] else room["employer_id"]
    other_user = conn.execute("SELECT * FROM users WHERE id = ?", (other_id,)).fetchone()
    is_employer = uid == room["employer_id"]

    if request.method == "POST":
        msg_type = request.form.get("msg_type", "text")
        if msg_type == "text":
            content = request.form.get("content", "").strip()
            if content:
                conn.execute(
                    "INSERT INTO chat_messages (room_id, sender_id, msg_type, content) VALUES (?, ?, 'text', ?)",
                    (room_id, uid, content),
                )
                conn.commit()
        else:
            file = request.files.get("media_file")
            if file and file.filename:
                is_img = allowed_file(file.filename, ALLOWED_IMAGE)
                is_vid = allowed_file(file.filename, ALLOWED_VIDEO)
                if is_img or is_vid:
                    filename = secure_filename(f"{room_id}_{datetime.now().timestamp()}_{file.filename}")
                    file.save(os.path.join(UPLOAD_CHAT, filename))
                    conn.execute(
                        "INSERT INTO chat_messages (room_id, sender_id, msg_type, content) VALUES (?, ?, ?, ?)",
                        (room_id, uid, "image" if is_img else "video", filename),
                    )
                    conn.commit()
                else:
                    flash("รองรับเฉพาะไฟล์รูปภาพหรือวิดีโอ", "error")
        conn.close()
        return redirect(url_for("chat_room", room_id=room_id))

    messages = conn.execute(
        "SELECT * FROM chat_messages WHERE room_id = ? ORDER BY id ASC", (room_id,)
    ).fetchall()

    payment = conn.execute(
        "SELECT * FROM payment_requests WHERE room_id = ? ORDER BY id DESC LIMIT 1", (room_id,)
    ).fetchone()

    is_friend = conn.execute(
        "SELECT 1 FROM friends WHERE user_id = ? AND friend_id = ?", (uid, other_id)
    ).fetchone() is not None

    conn.close()
    return render_template(
        "chat_room.html",
        room=room, other_user=other_user, messages=messages,
        is_employer=is_employer, payment=payment, is_friend=is_friend, uid=uid,
        active_tab="chat",
    )


@app.route("/chat/<int:room_id>/add-friend", methods=["POST"])
@login_required
def add_friend(room_id):
    conn = get_db()
    uid = session["user_id"]
    room = conn.execute("SELECT * FROM chat_rooms WHERE id = ?", (room_id,)).fetchone()
    if room:
        other_id = room["seeker_id"] if uid == room["employer_id"] else room["employer_id"]
        conn.execute("INSERT OR IGNORE INTO friends (user_id, friend_id) VALUES (?, ?)", (uid, other_id))
        conn.execute("INSERT OR IGNORE INTO friends (user_id, friend_id) VALUES (?, ?)", (other_id, uid))
        conn.commit()
    conn.close()
    return redirect(url_for("chat_room", room_id=room_id))


@app.route("/chat/<int:room_id>/request-payment", methods=["POST"])
@login_required
def request_payment(room_id):
    # Employer initiates "end job" -> asks seeker for bank details
    conn = get_db()
    room = conn.execute("SELECT * FROM chat_rooms WHERE id = ?", (room_id,)).fetchone()
    if room and session["user_id"] == room["employer_id"]:
        conn.execute(
            "INSERT INTO payment_requests (room_id, status) VALUES (?, 'awaiting_bank_info')", (room_id,)
        )
        conn.execute(
            "INSERT INTO chat_messages (room_id, sender_id, msg_type, content) VALUES (?, ?, 'system', ?)",
            (room_id, session["user_id"], "ผู้จ้างงานต้องการจบงาน กรุณาส่งเลขบัญชี/พร้อมเพย์เพื่อรับเงิน"),
        )
        conn.commit()
    conn.close()
    return redirect(url_for("chat_room", room_id=room_id))


@app.route("/chat/<int:room_id>/submit-bank-info", methods=["POST"])
@login_required
def submit_bank_info(room_id):
    bank_info = request.form.get("bank_info", "").strip()
    conn = get_db()
    room = conn.execute("SELECT * FROM chat_rooms WHERE id = ?", (room_id,)).fetchone()
    if room and session["user_id"] == room["seeker_id"] and bank_info:
        conn.execute(
            "UPDATE payment_requests SET bank_info = ?, status = 'awaiting_payment' "
            "WHERE room_id = ? AND status = 'awaiting_bank_info'",
            (bank_info, room_id),
        )
        conn.execute(
            "INSERT INTO chat_messages (room_id, sender_id, msg_type, content) VALUES (?, ?, 'system', ?)",
            (room_id, session["user_id"], f"ส่งข้อมูลบัญชีสำหรับรับเงินแล้ว: {bank_info}"),
        )
        conn.commit()
    conn.close()
    return redirect(url_for("chat_room", room_id=room_id))


@app.route("/chat/<int:room_id>/mark-paid", methods=["POST"])
@login_required
def mark_paid(room_id):
    conn = get_db()
    room = conn.execute("SELECT * FROM chat_rooms WHERE id = ?", (room_id,)).fetchone()
    if room and session["user_id"] == room["employer_id"]:
        conn.execute(
            "UPDATE payment_requests SET status = 'paid' WHERE room_id = ? AND status = 'awaiting_payment'",
            (room_id,),
        )
        conn.execute(
            "INSERT INTO chat_messages (room_id, sender_id, msg_type, content) VALUES (?, ?, 'system', ?)",
            (room_id, session["user_id"], "ผู้จ้างงานแจ้งว่าโอนเงินแล้ว รอผู้รับงานยืนยัน"),
        )
        conn.commit()
    conn.close()
    return redirect(url_for("chat_room", room_id=room_id))


@app.route("/chat/<int:room_id>/confirm-payment", methods=["POST"])
@login_required
def confirm_payment(room_id):
    conn = get_db()
    room = conn.execute("SELECT * FROM chat_rooms WHERE id = ?", (room_id,)).fetchone()
    if room and session["user_id"] == room["seeker_id"]:
        conn.execute(
            "UPDATE payment_requests SET status = 'confirmed' WHERE room_id = ? AND status = 'paid'",
            (room_id,),
        )
        conn.execute("UPDATE job_posts SET status = 'completed' WHERE id = ?", (room["job_post_id"],))
        conn.execute("UPDATE chat_rooms SET status = 'completed' WHERE id = ?", (room_id,))
        conn.execute(
            "INSERT INTO chat_messages (room_id, sender_id, msg_type, content) VALUES (?, ?, 'system', ?)",
            (room_id, session["user_id"], "ผู้รับงานยืนยันได้รับเงินแล้ว งานเสร็จสมบูรณ์"),
        )
        conn.commit()
    conn.close()
    return redirect(url_for("chat_room", room_id=room_id))


@app.route("/chat/<int:room_id>/reject-payment", methods=["POST"])
@login_required
def reject_payment(room_id):
    conn = get_db()
    room = conn.execute("SELECT * FROM chat_rooms WHERE id = ?", (room_id,)).fetchone()
    if room and session["user_id"] == room["seeker_id"]:
        conn.execute(
            "UPDATE payment_requests SET status = 'rejected' WHERE room_id = ? AND status = 'paid'",
            (room_id,),
        )
        conn.execute(
            "INSERT INTO chat_messages (room_id, sender_id, msg_type, content) VALUES (?, ?, 'system', ?)",
            (room_id, session["user_id"], "ผู้รับงานแจ้งว่ายังไม่ได้รับเงิน ยังไม่สามารถจบงานได้"),
        )
        conn.commit()
    conn.close()
    return redirect(url_for("chat_room", room_id=room_id))


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------
@app.route("/notifications")
@login_required
def notifications():
    conn = get_db()
    uid = session["user_id"]
    notifs = conn.execute(
        "SELECT * FROM notifications WHERE user_id = ? ORDER BY id DESC", (uid,)
    ).fetchall()
    conn.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (uid,))
    conn.commit()
    conn.close()
    return render_template("notifications.html", notifs=notifs, active_tab="notifications")


@app.route("/notifications/<int:notif_id>/accept", methods=["POST"])
@login_required
def accept_notification(notif_id):
    conn = get_db()
    notif = conn.execute("SELECT * FROM notifications WHERE id = ?", (notif_id,)).fetchone()
    conn.close()
    if notif and notif["job_post_id"]:
        return accept_job(notif["job_post_id"])
    return redirect(url_for("notifications"))


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------
@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", active_tab="profile")


@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    conn = get_db()
    uid = session["user_id"]
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()

        dup = conn.execute("SELECT id FROM users WHERE email = ? AND id != ?", (email, uid)).fetchone()
        if dup:
            flash("อีเมลนี้ถูกใช้แล้ว", "error")
        else:
            conn.execute(
                "UPDATE users SET first_name=?, last_name=?, email=?, phone=? WHERE id=?",
                (first_name, last_name, email, phone, uid),
            )
            conn.commit()
            flash("บันทึกข้อมูลสำเร็จ", "success")
        conn.close()
        return redirect(url_for("profile"))
    user = conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
    conn.close()
    return render_template("edit_profile.html", user=user, active_tab="profile")


@app.route("/profile/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old_password = request.form.get("old_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()

        if not check_password_hash(user["password_hash"], old_password):
            flash("รหัสผ่านปัจจุบันไม่ถูกต้อง", "error")
        elif new_password != confirm_password:
            flash("รหัสผ่านใหม่และการยืนยันไม่ตรงกัน", "error")
        elif len(new_password) < 6:
            flash("รหัสผ่านใหม่ต้องมีอย่างน้อย 6 ตัวอักษร", "error")
        else:
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (generate_password_hash(new_password), session["user_id"]),
            )
            conn.commit()
            flash("เปลี่ยนรหัสผ่านสำเร็จ", "success")
            conn.close()
            return redirect(url_for("profile"))
        conn.close()
    return render_template("change_password.html", active_tab="profile")


@app.route("/profile/change-picture", methods=["GET", "POST"])
@login_required
def change_picture():
    if request.method == "POST":
        file = request.files.get("picture")
        if file and file.filename and allowed_file(file.filename, ALLOWED_IMAGE):
            filename = secure_filename(f"{session['user_id']}_{datetime.now().timestamp()}_{file.filename}")
            file.save(os.path.join(UPLOAD_PROFILE, filename))
            conn = get_db()
            conn.execute("UPDATE users SET profile_pic = ? WHERE id = ?", (filename, session["user_id"]))
            conn.commit()
            conn.close()
            flash("เปลี่ยนรูปโปรไฟล์สำเร็จ", "success")
        else:
            flash("กรุณาเลือกไฟล์รูปภาพ", "error")
        return redirect(url_for("profile"))
    return render_template("change_picture.html", active_tab="profile")


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["is_admin"] = True
            return redirect(url_for("admin_dashboard"))
        flash("ชื่อผู้ใช้หรือรหัสผ่าน admin ไม่ถูกต้อง", "error")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin_login"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    conn = get_db()
    stats = {
        "users": conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"],
        "jobs": conn.execute("SELECT COUNT(*) c FROM job_posts").fetchone()["c"],
        "categories": conn.execute("SELECT COUNT(*) c FROM job_categories").fetchone()["c"],
    }
    conn.close()
    return render_template("admin_dashboard.html", stats=stats)


@app.route("/admin/app-settings", methods=["GET", "POST"])
@admin_required
def admin_app_settings():
    conn = get_db()
    if request.method == "POST":
        new_name = request.form.get("app_name", "").strip()
        if new_name:
            conn.execute("UPDATE app_settings SET app_name = ? WHERE id = 1", (new_name,))
            conn.commit()
            flash("อัพเดทชื่อแอปสำเร็จ ระบบจะเปลี่ยนชื่อในทุกหน้าโดยอัตโนมัติ", "success")
    name = get_app_name()
    conn.close()
    return render_template("admin_app_settings.html", app_name=name)


@app.route("/admin/categories", methods=["GET", "POST"])
@admin_required
def admin_categories():
    conn = get_db()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if name:
            try:
                conn.execute("INSERT INTO job_categories (name) VALUES (?)", (name,))
                conn.commit()
                flash("เพิ่มหัวข้องานสำเร็จ อัพเดททุกจุดที่เกี่ยวข้องแล้ว", "success")
            except Exception:
                flash("มีหัวข้องานนี้อยู่แล้ว", "error")
    categories = conn.execute("SELECT * FROM job_categories ORDER BY name").fetchall()
    conn.close()
    return render_template("admin_categories.html", categories=categories)


@app.route("/admin/categories/<int:cat_id>/delete", methods=["POST"])
@admin_required
def admin_delete_category(cat_id):
    conn = get_db()
    conn.execute("DELETE FROM job_categories WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_categories"))


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    app.run(debug=True, host=host, port=port)
EOF

echo "==> เขียนไฟล์ db.py"
cat > db.py << 'EOF'
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "freelance.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS app_settings (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        app_name TEXT NOT NULL DEFAULT 'JobConnect'
    );

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL,
        birth_day INTEGER,
        birth_month INTEGER,
        birth_year INTEGER,
        password_hash TEXT NOT NULL,
        profile_pic TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS job_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS job_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employer_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        category_id INTEGER NOT NULL,
        pay_amount REAL,
        contact_tiktok TEXT DEFAULT '',
        contact_phone TEXT DEFAULT '',
        contact_facebook TEXT DEFAULT '',
        details TEXT DEFAULT '',
        status TEXT DEFAULT 'open',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employer_id) REFERENCES users(id),
        FOREIGN KEY (category_id) REFERENCES job_categories(id)
    );

    CREATE TABLE IF NOT EXISTS chat_rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_post_id INTEGER NOT NULL,
        employer_id INTEGER NOT NULL,
        seeker_id INTEGER NOT NULL,
        status TEXT DEFAULT 'active',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_post_id) REFERENCES job_posts(id)
    );

    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_id INTEGER NOT NULL,
        sender_id INTEGER NOT NULL,
        msg_type TEXT DEFAULT 'text',
        content TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (room_id) REFERENCES chat_rooms(id)
    );

    CREATE TABLE IF NOT EXISTS payment_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_id INTEGER NOT NULL,
        bank_info TEXT DEFAULT '',
        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (room_id) REFERENCES chat_rooms(id)
    );

    CREATE TABLE IF NOT EXISTS friends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        friend_id INTEGER NOT NULL,
        UNIQUE(user_id, friend_id)
    );

    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        job_post_id INTEGER,
        is_read INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    c.execute("INSERT OR IGNORE INTO app_settings (id, app_name) VALUES (1, 'JobConnect')")

    default_categories = [
        "วาดรูป",
        "เขียนโค้ด",
        "แปลภาษา",
        "ตัดต่อวิดีโอ",
        "เขียนบทความ/คอนเทนต์",
        "กราฟิกดีไซน์",
        "ออกแบบโลโก้",
        "ถ่ายภาพ",
        "ตัดต่อเสียง/พากย์เสียง",
        "แต่งเพลง/ทำดนตรี",
        "ยิงแอด/การตลาดออนไลน์",
        "ดูแลเพจ/โซเชียลมีเดีย",
        "คีย์ข้อมูล",
        "ทำบัญชี",
        "ติวเตอร์/สอนพิเศษ",
        "ออกแบบเว็บไซต์",
        "ทำแอนิเมชัน/Motion Graphic",
        "ถอดเทป/พิมพ์งาน",
        "รีวิวสินค้า",
        "นายแบบ/นางแบบ",
        "ดูแลระบบไอที",
        "เขียนแผนธุรกิจ",
        "ทำสไลด์/พรีเซนเทชัน",
        "แปลซับไตเติ้ล",
        "ตอบแชทลูกค้า",
        "ผู้ช่วยส่วนตัวออนไลน์",
        "รีทัชภาพ/ตกแต่งภาพ",
        "ทำโมเดล 3D",
    ]
    for name in default_categories:
        c.execute("INSERT OR IGNORE INTO job_categories (name) VALUES (?)", (name,))

    conn.commit()
    conn.close()


def get_app_name():
    conn = get_db()
    row = conn.execute("SELECT app_name FROM app_settings WHERE id = 1").fetchone()
    conn.close()
    return row["app_name"] if row else "JobConnect"
EOF

echo "==> เขียนไฟล์ static/css/style.css"
cat > static/css/style.css << 'EOF'
:root {
  --primary: #1565c0;
  --primary-dark: #0d47a1;
  --primary-light: #e3f2fd;
  --accent: #42a5f5;
  --white: #ffffff;
  --gray-bg: #f4f8fd;
  --text: #10243e;
  --text-muted: #64748b;
  --danger: #e53935;
  --success: #2e7d32;
  --radius: 16px;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: "Segoe UI", "Noto Sans Thai", Tahoma, sans-serif;
  background: var(--gray-bg);
  color: var(--text);
}

.app-shell {
  max-width: 420px;
  margin: 0 auto;
  min-height: 100vh;
  background: var(--white);
  display: flex;
  flex-direction: column;
  position: relative;
  box-shadow: 0 0 24px rgba(21, 101, 192, 0.08);
}

.topbar {
  background: linear-gradient(135deg, var(--primary), var(--accent));
  color: var(--white);
  padding: 18px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 10;
}

.topbar h1 {
  font-size: 19px;
  margin: 0;
  font-weight: 700;
}

.topbar a { color: var(--white); text-decoration: none; font-size: 14px; }

.content {
  flex: 1;
  padding: 18px;
  padding-bottom: 90px;
}

.auth-wrap {
  max-width: 420px;
  margin: 0 auto;
  min-height: 100vh;
  background: var(--white);
  padding: 32px 24px;
}

.auth-logo {
  text-align: center;
  margin-bottom: 24px;
}
.auth-logo .emoji { font-size: 46px; }
.auth-logo h2 { color: var(--primary-dark); margin: 6px 0 0; }

.field {
  margin-bottom: 14px;
}
.field label {
  display: block;
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 5px;
  font-weight: 600;
}
.field input, .field select, .field textarea {
  width: 100%;
  padding: 12px 14px;
  border: 1.5px solid #cfe0f7;
  border-radius: 10px;
  font-size: 15px;
  background: var(--gray-bg);
  color: var(--text);
}
.field input:focus, .field select:focus, .field textarea:focus {
  outline: none;
  border-color: var(--primary);
  background: var(--white);
}
.row3 { display: flex; gap: 8px; }
.row3 .field { flex: 1; }

.btn {
  display: inline-block;
  width: 100%;
  padding: 13px;
  border: none;
  border-radius: 10px;
  background: var(--primary);
  color: var(--white);
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  text-align: center;
  text-decoration: none;
}
.btn:hover { background: var(--primary-dark); }
.btn.secondary { background: var(--white); color: var(--primary); border: 1.5px solid var(--primary); }
.btn.danger { background: var(--danger); }
.btn.small { width: auto; padding: 8px 16px; font-size: 13px; }
.btn.block-outline { background: var(--white); color: var(--primary-dark); border: 1.5px dashed var(--primary); }

.link-row { text-align: center; margin-top: 16px; font-size: 14px; color: var(--text-muted); }
.link-row a { color: var(--primary); font-weight: 700; text-decoration: none; }

.flash { padding: 10px 14px; border-radius: 10px; margin-bottom: 12px; font-size: 14px; }
.flash.error { background: #fde8e8; color: var(--danger); }
.flash.success { background: #e6f4ea; color: var(--success); }

.welcome-card {
  background: linear-gradient(135deg, var(--primary), var(--accent));
  color: var(--white);
  border-radius: var(--radius);
  padding: 22px;
  margin-bottom: 18px;
  display: flex;
  gap: 14px;
  align-items: center;
}
.welcome-card .char { font-size: 42px; }
.welcome-card h3 { margin: 0 0 4px; }
.welcome-card p { margin: 0; font-size: 13px; opacity: 0.9; }

.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.tile {
  background: var(--primary-light);
  border-radius: var(--radius);
  padding: 18px 14px;
  text-align: center;
  text-decoration: none;
  color: var(--primary-dark);
  font-weight: 700;
  border: 1px solid #d5e7fb;
}
.tile .icon { font-size: 30px; display: block; margin-bottom: 8px; }

.card {
  background: var(--white);
  border: 1px solid #e3edf9;
  border-radius: var(--radius);
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(16, 36, 62, 0.04);
}
.card h4 { margin: 0 0 6px; color: var(--primary-dark); }
.card .meta { font-size: 12px; color: var(--text-muted); margin-bottom: 8px; }
.badge {
  display: inline-block;
  background: var(--primary-light);
  color: var(--primary-dark);
  font-size: 11px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 20px;
}
.badge.status-open { background: #e6f4ea; color: var(--success); }
.badge.status-completed { background: #eeeeee; color: #666; }

.bottom-nav {
  position: sticky;
  bottom: 0;
  display: flex;
  background: var(--white);
  border-top: 1px solid #e3edf9;
  padding: 8px 4px;
  z-index: 20;
}
.bottom-nav a {
  flex: 1;
  text-align: center;
  text-decoration: none;
  color: var(--text-muted);
  font-size: 11px;
  padding: 6px 0;
  position: relative;
}
.bottom-nav a.active { color: var(--primary); font-weight: 700; }
.bottom-nav a .nav-icon { display: block; font-size: 20px; margin-bottom: 2px; }
.nav-dot {
  position: absolute;
  top: 2px;
  right: 22%;
  background: var(--danger);
  color: white;
  font-size: 9px;
  border-radius: 10px;
  padding: 1px 5px;
}

.chat-bubble-wrap { display: flex; margin-bottom: 10px; }
.chat-bubble-wrap.mine { justify-content: flex-end; }
.chat-bubble {
  max-width: 75%;
  padding: 10px 14px;
  border-radius: 16px;
  font-size: 14px;
  background: var(--primary-light);
  color: var(--text);
}
.chat-bubble-wrap.mine .chat-bubble { background: var(--primary); color: var(--white); }
.chat-bubble.system {
  background: #fff7e0;
  color: #8a6d00;
  font-size: 12px;
  margin: 0 auto 10px;
  text-align: center;
  max-width: 90%;
}
.chat-bubble img, .chat-bubble video { max-width: 100%; border-radius: 10px; margin-top: 4px; }

.chat-input-bar {
  display: flex;
  gap: 8px;
  padding: 10px;
  border-top: 1px solid #e3edf9;
  background: var(--white);
  position: sticky;
  bottom: 60px;
}
.chat-input-bar input[type=text] {
  flex: 1;
  padding: 10px 14px;
  border-radius: 20px;
  border: 1.5px solid #cfe0f7;
  background: var(--gray-bg);
}
.chat-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: var(--primary-light);
  border-bottom: 1px solid #d5e7fb;
}
.avatar {
  width: 40px; height: 40px; border-radius: 50%;
  background: var(--primary); color: white;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 16px; overflow: hidden; flex-shrink: 0;
}
.avatar img { width: 100%; height: 100%; object-fit: cover; }

.menu-dots { position: relative; margin-left: auto; }
.menu-dots > span { cursor: pointer; font-size: 20px; padding: 4px 8px; color: var(--primary-dark); }
.menu-dropdown {
  display: none;
  position: absolute;
  right: 0;
  top: 28px;
  background: white;
  border: 1px solid #e3edf9;
  border-radius: 10px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  min-width: 170px;
  z-index: 30;
}
.menu-dropdown.show { display: block; }
.menu-dropdown form, .menu-dropdown a {
  display: block; width: 100%; text-align: left; background: none; border: none;
  padding: 10px 14px; font-size: 13px; color: var(--text); text-decoration: none; cursor: pointer;
}
.menu-dropdown form button { all: unset; width: 100%; cursor: pointer; font-size: 13px; }
.menu-dropdown form:hover, .menu-dropdown a:hover { background: var(--gray-bg); }

.section-title { font-size: 15px; font-weight: 700; margin: 18px 0 10px; color: var(--primary-dark); }
.empty-state { text-align: center; color: var(--text-muted); padding: 40px 10px; font-size: 14px; }
.notif-item { display: flex; gap: 10px; align-items: flex-start; }
.notif-item .icon { font-size: 22px; }
.file-upload-label {
  display: block; border: 2px dashed #cfe0f7; border-radius: var(--radius);
  padding: 26px; text-align: center; color: var(--text-muted); cursor: pointer;
}
.profile-header { text-align: center; padding: 10px 0 20px; }
.profile-header .avatar { width: 84px; height: 84px; font-size: 30px; margin: 0 auto 10px; }
.list-menu a, .list-menu button {
  display: flex; justify-content: space-between; align-items: center;
  width: 100%; padding: 14px 16px; background: white; border: none;
  border-bottom: 1px solid #eef3fa; text-decoration: none; color: var(--text);
  font-size: 14px; cursor: pointer; text-align: left;
}
.list-menu a:last-child, .list-menu button:last-child { border-bottom: none; }
.pay-tag { color: var(--primary-dark); font-weight: 700; }
EOF

echo "==> เขียนไฟล์ templates/admin_app_settings.html"
cat > templates/admin_app_settings.html << 'EOF'
<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>จัดการหน้าแอป - Admin</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
  <div class="app-shell">
    <div class="topbar">
      <h1>🏷️ จัดการหน้าแอป</h1>
      <a href="{{ url_for('admin_dashboard') }}">‹ กลับ</a>
    </div>
    <div class="content">
      {% with messages = get_flashed_messages(with_categories=true) %}
        {% for category, message in messages %}
          <div class="flash {{ category }}">{{ message }}</div>
        {% endfor %}
      {% endwith %}

      <p style="font-size:13px;color:var(--text-muted);">
        เปลี่ยนชื่อแอปที่นี่ เมื่อกดอัพเดท ชื่อแอปจะเปลี่ยนพร้อมกันทุกหน้าของแอปโดยอัตโนมัติ
      </p>
      <form method="POST">
        <div class="field">
          <label>ชื่อแอป</label>
          <input type="text" name="app_name" value="{{ app_name }}" required>
        </div>
        <button type="submit" class="btn">อัพเดทชื่อแอป</button>
      </form>
    </div>
  </div>
</body>
</html>
EOF

echo "==> เขียนไฟล์ templates/admin_categories.html"
cat > templates/admin_categories.html << 'EOF'
<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>จัดการประเภทงาน - Admin</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
  <div class="app-shell">
    <div class="topbar">
      <h1>📂 จัดการประเภทงาน</h1>
      <a href="{{ url_for('admin_dashboard') }}">‹ กลับ</a>
    </div>
    <div class="content">
      {% with messages = get_flashed_messages(with_categories=true) %}
        {% for category, message in messages %}
          <div class="flash {{ category }}">{{ message }}</div>
        {% endfor %}
      {% endwith %}

      <p style="font-size:13px;color:var(--text-muted);">
        เพิ่มหัวข้องานใหม่ที่นี่ เมื่อเพิ่มแล้วจะปรากฏในหน้า "หางาน" และ "จ้างงาน" ของผู้ใช้ทุกคนทันที
      </p>
      <form method="POST" style="display:flex;gap:8px;margin-bottom:18px;">
        <input type="text" name="name" placeholder="ชื่อประเภทงานใหม่" required style="flex:1;padding:12px;border-radius:10px;border:1.5px solid #cfe0f7;">
        <button type="submit" class="btn small">เพิ่ม</button>
      </form>

      <div class="card list-menu" style="padding:0;">
        {% for cat in categories %}
        <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 16px;border-bottom:1px solid #eef3fa;">
          <span>{{ cat['name'] }}</span>
          <form method="POST" action="{{ url_for('admin_delete_category', cat_id=cat['id']) }}" onsubmit="return confirm('ลบประเภทงานนี้?');">
            <button type="submit" style="background:none;border:none;color:var(--danger);cursor:pointer;">ลบ</button>
          </form>
        </div>
        {% endfor %}
      </div>
    </div>
  </div>
</body>
</html>
EOF

echo "==> เขียนไฟล์ templates/admin_dashboard.html"
cat > templates/admin_dashboard.html << 'EOF'
<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Admin Dashboard - {{ app_name }}</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
  <div class="app-shell">
    <div class="topbar">
      <h1>🛠️ ระบบ Admin</h1>
      <a href="{{ url_for('admin_logout') }}">ออกจากระบบ</a>
    </div>
    <div class="content">
      <div class="grid-2" style="margin-bottom:16px;">
        <div class="card" style="text-align:center;"><div style="font-size:22px;font-weight:700;color:var(--primary-dark);">{{ stats.users }}</div><div class="meta">ผู้ใช้ทั้งหมด</div></div>
        <div class="card" style="text-align:center;"><div style="font-size:22px;font-weight:700;color:var(--primary-dark);">{{ stats.jobs }}</div><div class="meta">งานทั้งหมด</div></div>
      </div>

      <div class="card list-menu" style="padding:0;">
        <a href="{{ url_for('admin_app_settings') }}">🏷️ จัดการหน้าแอป (ชื่อแอป) <span>›</span></a>
        <a href="{{ url_for('admin_categories') }}">📂 จัดการประเภทงาน <span>›</span></a>
      </div>
    </div>
  </div>
</body>
</html>
EOF

echo "==> เขียนไฟล์ templates/admin_login.html"
cat > templates/admin_login.html << 'EOF'
<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Admin Login - {{ app_name }}</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
  <div class="auth-wrap">
    <div class="auth-logo">
      <div class="emoji">🛠️</div>
      <h2>เข้าสู่ระบบ Admin</h2>
    </div>

    {% with messages = get_flashed_messages(with_categories=true) %}
      {% for category, message in messages %}
        <div class="flash {{ category }}">{{ message }}</div>
      {% endfor %}
    {% endwith %}

    <form method="POST">
      <div class="field">
        <label>ชื่อผู้ใช้ Admin</label>
        <input type="text" name="username" required>
      </div>
      <div class="field">
        <label>รหัสผ่าน</label>
        <input type="password" name="password" required>
      </div>
      <button type="submit" class="btn">เข้าสู่ระบบ</button>
    </form>

    <div class="link-row">
      <a href="{{ url_for('login') }}">กลับหน้าเข้าสู่ระบบผู้ใช้</a>
    </div>
  </div>
</body>
</html>
EOF

echo "==> เขียนไฟล์ templates/base.html"
cat > templates/base.html << 'EOF'
<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
  <title>{{ app_name }}</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
  <div class="app-shell">
    <div class="topbar">
      <h1>{% if current_user %}<a href="{{ url_for('home') }}" style="color:inherit;text-decoration:none;">{{ app_name }}</a>{% else %}{{ app_name }}{% endif %}</h1>
      {% block topbar_right %}{% endblock %}
    </div>

    <div class="content">
      {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
          {% for category, message in messages %}
            <div class="flash {{ category }}">{{ message }}</div>
          {% endfor %}
        {% endif %}
      {% endwith %}

      {% block content %}{% endblock %}
    </div>

    {% if current_user %}
    <nav class="bottom-nav">
      <a href="{{ url_for('find_job') }}" class="{{ 'active' if active_tab == 'find_job' else '' }}">
        <span class="nav-icon">🔍</span>หางาน
      </a>
      <a href="{{ url_for('hire_job') }}" class="{{ 'active' if active_tab == 'hire_job' else '' }}">
        <span class="nav-icon">📢</span>จ้างงาน
      </a>
      <a href="{{ url_for('chat_list') }}" class="{{ 'active' if active_tab == 'chat' else '' }}">
        <span class="nav-icon">💬</span>แชท
      </a>
      <a href="{{ url_for('notifications') }}" class="{{ 'active' if active_tab == 'notifications' else '' }}">
        <span class="nav-icon">🔔</span>แจ้งเตือน
        {% if unread_notif_count and unread_notif_count > 0 %}
          <span class="nav-dot">{{ unread_notif_count }}</span>
        {% endif %}
      </a>
      <a href="{{ url_for('profile') }}" class="{{ 'active' if active_tab == 'profile' else '' }}">
        <span class="nav-icon">👤</span>โปรไฟล์
      </a>
    </nav>
    {% endif %}
  </div>
</body>
</html>
EOF

echo "==> เขียนไฟล์ templates/change_password.html"
cat > templates/change_password.html << 'EOF'
{% extends "base.html" %}
{% block content %}
<div class="section-title">เปลี่ยนรหัสผ่าน</div>

<form method="POST">
  <div class="field">
    <label>รหัสผ่านปัจจุบัน</label>
    <input type="password" name="old_password" required>
  </div>
  <div class="field">
    <label>รหัสผ่านใหม่</label>
    <input type="password" name="new_password" required minlength="6">
  </div>
  <div class="field">
    <label>ยืนยันรหัสผ่านใหม่</label>
    <input type="password" name="confirm_password" required minlength="6">
  </div>
  <button type="submit" class="btn">เปลี่ยนรหัสผ่าน</button>
</form>
{% endblock %}
EOF

echo "==> เขียนไฟล์ templates/change_picture.html"
cat > templates/change_picture.html << 'EOF'
{% extends "base.html" %}
{% block content %}
<div class="section-title">เปลี่ยนรูปโปรไฟล์</div>

<form method="POST" enctype="multipart/form-data">
  <label class="file-upload-label">
    📷 แตะเพื่อเลือกรูปภาพจากคลังรูปภาพ
    <input type="file" name="picture" accept="image/*" style="display:block;margin-top:10px;">
  </label>
  <button type="submit" class="btn" style="margin-top:14px;">อัปโหลดรูปโปรไฟล์</button>
</form>
{% endblock %}
EOF

echo "==> เขียนไฟล์ templates/chat_list.html"
cat > templates/chat_list.html << 'EOF'
{% extends "base.html" %}
{% block content %}
<div class="section-title">แชททั้งหมด</div>

{% if rooms %}
  {% for room in rooms %}
    {% set other_name = room['seek_first'] ~ ' ' ~ room['seek_last'] if uid == room['employer_id'] else room['emp_first'] ~ ' ' ~ room['emp_last'] %}
    <a href="{{ url_for('chat_room', room_id=room['id']) }}" style="text-decoration:none;color:inherit;">
      <div class="card" style="display:flex;align-items:center;gap:12px;">
        <div class="avatar">{{ other_name[0] }}</div>
        <div>
          <h4 style="margin:0;">{{ other_name }}</h4>
          <div class="meta" style="margin:2px 0 0;">งาน: {{ room['job_title'] }}</div>
        </div>
      </div>
    </a>
  {% endfor %}
{% else %}
  <div class="empty-state">ยังไม่มีการสนทนา ลองไปหางาน หรือรับงานที่สนใจดูนะ</div>
{% endif %}

{% endblock %}
EOF

echo "==> เขียนไฟล์ templates/chat_room.html"
cat > templates/chat_room.html << 'EOF'
{% extends "base.html" %}
{% block content %}
<div style="margin:-18px -18px 12px;">
  <div class="chat-header">
    <a href="{{ url_for('chat_list') }}" style="color:var(--primary-dark);text-decoration:none;">&larr;</a>
    <div class="avatar">
      {% if other_user['profile_pic'] %}
        <img src="{{ url_for('static', filename='uploads/profile/' + other_user['profile_pic']) }}">
      {% else %}{{ other_user['first_name'][0] }}{% endif %}
    </div>
    <div>
      <strong>{{ other_user['first_name'] }} {{ other_user['last_name'] }}</strong>
      <div class="meta">งาน: {{ room['job_title'] }}</div>
    </div>

    <div class="menu-dots" id="menuDots">
      <span onclick="document.getElementById('menuDropdown').classList.toggle('show')">⋮</span>
      <div class="menu-dropdown" id="menuDropdown">
        {% if not is_friend %}
        <form method="POST" action="{{ url_for('add_friend', room_id=room['id']) }}">
          <button type="submit">➕ เพิ่มเพื่อน</button>
        </form>
        {% else %}
        <a style="opacity:0.6;">✅ เป็นเพื่อนแล้ว</a>
        {% endif %}

        {% if is_employer and room['job_status'] not in ['completed'] and not payment %}
        <form method="POST" action="{{ url_for('request_payment', room_id=room['id']) }}">
          <button type="submit">🏁 จบงาน</button>
        </form>
        {% endif %}
      </div>
    </div>
  </div>
</div>

{% if payment and payment['status'] != 'confirmed' %}
<div class="card" style="border-color:#ffd479;background:#fffaf0;">
  {% if payment['status'] == 'awaiting_bank_info' and not is_employer %}
    <strong>ผู้จ้างงานต้องการจบงาน</strong>
    <p style="font-size:13px;">กรุณาส่งเลขบัญชี / พร้อมเพย์ เพื่อรับเงิน</p>
    <form method="POST" action="{{ url_for('submit_bank_info', room_id=room['id']) }}">
      <div class="field"><input type="text" name="bank_info" placeholder="เลขบัญชี / พร้อมเพย์" required></div>
      <button type="submit" class="btn small">ส่งข้อมูลบัญชี</button>
    </form>
  {% elif payment['status'] == 'awaiting_bank_info' and is_employer %}
    <p style="font-size:13px;">รอผู้รับงานส่งข้อมูลบัญชีเพื่อรับเงิน...</p>
  {% elif payment['status'] == 'awaiting_payment' and is_employer %}
    <p style="font-size:13px;">บัญชีสำหรับโอนเงิน: <strong>{{ payment['bank_info'] }}</strong></p>
    <form method="POST" action="{{ url_for('mark_paid', room_id=room['id']) }}">
      <button type="submit" class="btn small">✅ แจ้งว่าโอนเงินแล้ว</button>
    </form>
  {% elif payment['status'] == 'awaiting_payment' and not is_employer %}
    <p style="font-size:13px;">รอผู้จ้างงานโอนเงินตามบัญชีที่ส่งไป...</p>
  {% elif payment['status'] == 'paid' and not is_employer %}
    <p style="font-size:13px;">ผู้จ้างงานแจ้งว่าโอนเงินแล้ว กรุณาตรวจสอบและยืนยัน</p>
    <div style="display:flex;gap:8px;">
      <form method="POST" action="{{ url_for('confirm_payment', room_id=room['id']) }}" style="flex:1;">
        <button type="submit" class="btn small" style="width:100%;">✅ ยืนยันได้รับเงินแล้ว</button>
      </form>
      <form method="POST" action="{{ url_for('reject_payment', room_id=room['id']) }}" style="flex:1;">
        <button type="submit" class="btn small danger" style="width:100%;">❌ ยังไม่ได้รับเงิน</button>
      </form>
    </div>
  {% elif payment['status'] == 'paid' and is_employer %}
    <p style="font-size:13px;">รอผู้รับงานยืนยันการรับเงิน...</p>
  {% elif payment['status'] == 'rejected' %}
    <p style="font-size:13px;color:var(--danger);">ผู้รับงานแจ้งว่ายังไม่ได้รับเงิน กรุณาตรวจสอบการโอนอีกครั้ง</p>
    {% if is_employer %}
    <form method="POST" action="{{ url_for('mark_paid', room_id=room['id']) }}">
      <button type="submit" class="btn small">แจ้งว่าโอนเงินแล้วอีกครั้ง</button>
    </form>
    {% endif %}
  {% endif %}
</div>
{% elif payment and payment['status'] == 'confirmed' %}
<div class="card" style="border-color:#b6e3c1;background:#f2fbf4;text-align:center;">
  <strong style="color:var(--success);">🎉 งานนี้เสร็จสมบูรณ์แล้ว</strong>
</div>
{% endif %}

<div>
  {% for m in messages %}
    {% if m['msg_type'] == 'system' %}
      <div class="chat-bubble system">{{ m['content'] }}</div>
    {% else %}
      <div class="chat-bubble-wrap {{ 'mine' if m['sender_id'] == uid else '' }}">
        <div class="chat-bubble">
          {% if m['msg_type'] == 'text' %}
            {{ m['content'] }}
          {% elif m['msg_type'] == 'image' %}
            <img src="{{ url_for('static', filename='uploads/chat/' + m['content']) }}">
          {% elif m['msg_type'] == 'video' %}
            <video controls src="{{ url_for('static', filename='uploads/chat/' + m['content']) }}"></video>
          {% endif %}
        </div>
      </div>
    {% endif %}
  {% endfor %}
</div>

{% if room['status'] != 'completed' %}
<form method="POST" class="chat-input-bar" style="margin:0 -18px;">
  <input type="hidden" name="msg_type" value="text">
  <input type="text" name="content" placeholder="พิมพ์ข้อความ...">
  <button type="submit" class="btn small">ส่ง</button>
</form>
<form method="POST" enctype="multipart/form-data" style="display:flex;gap:8px;margin:8px -18px 0;padding:0 10px;">
  <input type="hidden" name="msg_type" value="media">
  <input type="file" name="media_file" accept="image/*,video/*" style="flex:1;font-size:12px;">
  <button type="submit" class="btn small secondary">📎 ส่งไฟล์</button>
</form>
{% endif %}

<script>
document.addEventListener('click', function(e) {
  var dots = document.getElementById('menuDots');
  var dropdown = document.getElementById('menuDropdown');
  if (dots && !dots.contains(e.target)) {
    dropdown.classList.remove('show');
  }
});
</script>

{% endblock %}
EOF

echo "==> เขียนไฟล์ templates/edit_profile.html"
cat > templates/edit_profile.html << 'EOF'
{% extends "base.html" %}
{% block content %}
<div class="section-title">แก้ไขข้อมูลส่วนตัว</div>

<form method="POST">
  <div class="field">
    <label>ชื่อ</label>
    <input type="text" name="first_name" value="{{ user['first_name'] }}" required>
  </div>
  <div class="field">
    <label>นามสกุล</label>
    <input type="text" name="last_name" value="{{ user['last_name'] }}" required>
  </div>
  <div class="field">
    <label>อีเมล</label>
    <input type="email" name="email" value="{{ user['email'] }}" required>
  </div>
  <div class="field">
    <label>เบอร์โทร</label>
    <input type="tel" name="phone" value="{{ user['phone'] }}" required>
  </div>
  <button type="submit" class="btn">บันทึกการเปลี่ยนแปลง</button>
</form>
{% endblock %}
EOF

echo "==> เขียนไฟล์ templates/find_job.html"
cat > templates/find_job.html << 'EOF'
{% extends "base.html" %}
{% block content %}
<div class="section-title">เลือกประเภทงานที่ต้องการหา</div>

{% if categories %}
<div class="grid-2">
  {% for cat in categories %}
  <a class="tile" href="{{ url_for('find_job_category', category_id=cat['id']) }}">
    <span class="icon">🏷️</span>{{ cat['name'] }}
  </a>
  {% endfor %}
</div>
{% else %}
<div class="empty-state">ยังไม่มีประเภทงานในระบบ</div>
{% endif %}

{% endblock %}
EOF

echo "==> เขียนไฟล์ templates/hire_job.html"
cat > templates/hire_job.html << 'EOF'
{% extends "base.html" %}
{% block content %}
<div class="section-title">ประกาศจ้างงานใหม่</div>

<form method="POST">
  <div class="field">
    <label>1. ชื่องาน</label>
    <input type="text" name="title" value="{{ form.get('title','') }}" required>
  </div>
  <div class="field">
    <label>2. ประเภทงาน</label>
    <select name="category_id" required>
      <option value="">-- เลือกประเภทงาน --</option>
      {% for cat in categories %}
      <option value="{{ cat['id'] }}" {{ 'selected' if form.get('category_id')|string == cat['id']|string else '' }}>{{ cat['name'] }}</option>
      {% endfor %}
    </select>
  </div>
  <div class="field">
    <label>3. ค่าตอบแทน (บาท)</label>
    <input type="number" step="0.01" name="pay_amount" value="{{ form.get('pay_amount','') }}">
  </div>

  <div class="field">
    <label>4. ช่องทางการติดต่อ</label>
  </div>
  <div class="field">
    <label style="font-weight:400;">4.1 TikTok (ลิงก์)</label>
    <input type="text" name="contact_tiktok" value="{{ form.get('contact_tiktok','') }}" placeholder="https://tiktok.com/@...">
  </div>
  <div class="field">
    <label style="font-weight:400;">4.2 เบอร์โทรศัพท์</label>
    <input type="tel" name="contact_phone" value="{{ form.get('contact_phone','') }}">
  </div>
  <div class="field">
    <label style="font-weight:400;">4.3 Facebook (ลิงก์โปรไฟล์)</label>
    <input type="text" name="contact_facebook" value="{{ form.get('contact_facebook','') }}" placeholder="https://facebook.com/...">
  </div>

  <div class="field">
    <label>5. รายละเอียดงาน</label>
    <textarea name="details" rows="4" placeholder="เช่น ให้ไปรับอาหารหน่อยนะ, สร้างดิสคอร์ดให้หน่อยนะ">{{ form.get('details','') }}</textarea>
  </div>

  <button type="submit" class="btn">📢 ประกาศงาน</button>
</form>

{% if my_jobs %}
<div class="section-title">งานที่ฉันประกาศไว้</div>
{% for job in my_jobs %}
<div class="card">
  <span class="badge status-{{ job['status'] }}">{{ 'เปิดรับ' if job['status']=='open' else job['status'] }}</span>
  <h4>{{ job['title'] }}</h4>
  <div class="meta">{{ job['category_name'] }}{% if job['pay_amount'] %} · {{ job['pay_amount']|round(2) }} บาท{% endif %}</div>
</div>
{% endfor %}
{% endif %}

{% endblock %}
EOF

echo "==> เขียนไฟล์ templates/home.html"
cat > templates/home.html << 'EOF'
{% extends "base.html" %}
{% block content %}

{% if show_welcome %}
<div class="welcome-card">
  <div class="char">👋</div>
  <div>
    <h3>สวัสดี {{ current_user['first_name'] }}!</h3>
    <p>ยินดีต้อนรับสู่ {{ app_name }} เริ่มต้นหางาน หรือประกาศจ้างงานได้เลย</p>
  </div>
</div>
{% else %}
<div class="welcome-card">
  <div class="char">😊</div>
  <div>
    <h3>สวัสดี {{ current_user['first_name'] }}</h3>
    <p>วันนี้อยากหางาน หรือจะประกาศจ้างงานดี?</p>
  </div>
</div>
{% endif %}

<div class="section-title">เมนูหลัก</div>
<div class="grid-2">
  <a class="tile" href="{{ url_for('find_job') }}">
    <span class="icon">🔍</span>หางาน
  </a>
  <a class="tile" href="{{ url_for('hire_job') }}">
    <span class="icon">📢</span>จ้างงาน
  </a>
  <a class="tile" href="{{ url_for('chat_list') }}">
    <span class="icon">💬</span>แชทของฉัน
  </a>
  <a class="tile" href="{{ url_for('notifications') }}">
    <span class="icon">🔔</span>การแจ้งเตือน
  </a>
</div>

{% endblock %}
EOF

echo "==> เขียนไฟล์ templates/job_detail.html"
cat > templates/job_detail.html << 'EOF'
{% extends "base.html" %}
{% block content %}

{% if job %}
<div class="card">
  <span class="badge status-{{ job['status'] }}">{{ 'เปิดรับ' if job['status']=='open' else job['status'] }}</span>
  <h4>{{ job['title'] }}</h4>
  <div class="meta">ประกาศโดย {{ job['first_name'] }} {{ job['last_name'] }}</div>
  {% if job['pay_amount'] %}<div class="pay-tag">💰 ค่าตอบแทน {{ job['pay_amount']|round(2) }} บาท</div>{% endif %}

  <div class="section-title">รายละเอียดงาน</div>
  <p style="font-size:14px;">{{ job['details'] or '-' }}</p>

  <div class="section-title">ช่องทางติดต่อ</div>
  {% if job['contact_tiktok'] %}<p>🎵 TikTok: {{ job['contact_tiktok'] }}</p>{% endif %}
  {% if job['contact_phone'] %}<p>📞 เบอร์โทร: {{ job['contact_phone'] }}</p>{% endif %}
  {% if job['contact_facebook'] %}<p>📘 Facebook: {{ job['contact_facebook'] }}</p>{% endif %}

  {% if job['employer_user_id'] != current_user['id'] %}
  <form method="POST" action="{{ url_for('accept_job', job_id=job['id']) }}">
    <button type="submit" class="btn" style="margin-top:14px;">✅ รับงานนี้ (เข้าสู่แชท)</button>
  </form>
  {% endif %}
</div>
{% else %}
<div class="empty-state">ไม่พบงานนี้</div>
{% endif %}

{% endblock %}
EOF

echo "==> เขียนไฟล์ templates/job_list.html"
cat > templates/job_list.html << 'EOF'
{% extends "base.html" %}
{% block content %}
<a href="{{ url_for('find_job') }}" style="font-size:13px;color:var(--text-muted);text-decoration:none;">&larr; กลับ</a>
<div class="section-title">งาน: {{ category['name'] }}</div>

{% if jobs %}
  {% for job in jobs %}
  <div class="card">
    <span class="badge status-open">เปิดรับ</span>
    <h4>{{ job['title'] }}</h4>
    <div class="meta">โดย {{ job['first_name'] }} {{ job['last_name'] }}</div>
    {% if job['pay_amount'] %}<div class="pay-tag">💰 {{ job['pay_amount']|round(2) }} บาท</div>{% endif %}
    <a class="btn small" style="margin-top:10px;" href="{{ url_for('job_detail', job_id=job['id']) }}">ดูรายละเอียด</a>
  </div>
  {% endfor %}
{% else %}
  <div class="empty-state">ยังไม่มีงานในหมวดนี้</div>
{% endif %}

{% endblock %}
EOF

echo "==> เขียนไฟล์ templates/login.html"
cat > templates/login.html << 'EOF'
<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>เข้าสู่ระบบ - {{ app_name }}</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
  <div class="auth-wrap">
    <div class="auth-logo">
      <div class="emoji">💼</div>
      <h2>{{ app_name }}</h2>
    </div>

    {% with messages = get_flashed_messages(with_categories=true) %}
      {% for category, message in messages %}
        <div class="flash {{ category }}">{{ message }}</div>
      {% endfor %}
    {% endwith %}

    <form method="POST">
      <div class="field">
        <label>อีเมล</label>
        <input type="email" name="email" required>
      </div>
      <div class="field">
        <label>รหัสผ่าน</label>
        <input type="password" name="password" required>
      </div>
      <button type="submit" class="btn">เข้าสู่ระบบ</button>
    </form>

    <div class="link-row">
      ยังไม่มีบัญชี? <a href="{{ url_for('signup') }}">สมัครสมาชิก</a>
    </div>
    <div class="link-row" style="margin-top:24px;">
      <a href="{{ url_for('admin_login') }}">เข้าสู่ระบบ Admin</a>
    </div>
  </div>
</body>
</html>
EOF

echo "==> เขียนไฟล์ templates/notifications.html"
cat > templates/notifications.html << 'EOF'
{% extends "base.html" %}
{% block content %}
<div class="section-title">การแจ้งเตือน</div>

{% if notifs %}
  {% for n in notifs %}
  <div class="card">
    <div class="notif-item">
      <div class="icon">🔔</div>
      <div style="flex:1;">
        <p style="margin:0 0 8px;font-size:14px;">{{ n['message'] }}</p>
        {% if n['job_post_id'] %}
        <form method="POST" action="{{ url_for('accept_notification', notif_id=n['id']) }}">
          <button type="submit" class="btn small">✅ รับงานนี้</button>
        </form>
        {% endif %}
      </div>
    </div>
  </div>
  {% endfor %}
{% else %}
  <div class="empty-state">ยังไม่มีการแจ้งเตือน</div>
{% endif %}

{% endblock %}
EOF

echo "==> เขียนไฟล์ templates/profile.html"
cat > templates/profile.html << 'EOF'
{% extends "base.html" %}
{% block content %}

<div class="profile-header">
  <div class="avatar">
    {% if current_user['profile_pic'] %}
      <img src="{{ url_for('static', filename='uploads/profile/' + current_user['profile_pic']) }}">
    {% else %}{{ current_user['first_name'][0] }}{% endif %}
  </div>
  <h3 style="margin:0;">{{ current_user['first_name'] }} {{ current_user['last_name'] }}</h3>
  <div class="meta">{{ current_user['email'] }}</div>
</div>

<div class="card list-menu" style="padding:0;">
  <a href="{{ url_for('edit_profile') }}">✏️ แก้ไขข้อมูลส่วนตัว <span>›</span></a>
  <a href="{{ url_for('change_password') }}">🔒 เปลี่ยนรหัสผ่าน <span>›</span></a>
  <a href="{{ url_for('change_picture') }}">🖼️ เปลี่ยนรูปโปรไฟล์ <span>›</span></a>
  <a href="{{ url_for('logout') }}" style="color:var(--danger);">🚪 ออกจากระบบ <span>›</span></a>
</div>

{% endblock %}
EOF

echo "==> เขียนไฟล์ templates/signup.html"
cat > templates/signup.html << 'EOF'
<!DOCTYPE html>
<html lang="th">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>สมัครสมาชิก - {{ app_name }}</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
  <div class="auth-wrap">
    <div class="auth-logo">
      <div class="emoji">🧑‍💼</div>
      <h2>สมัครสมาชิก {{ app_name }}</h2>
    </div>

    {% with messages = get_flashed_messages(with_categories=true) %}
      {% for category, message in messages %}
        <div class="flash {{ category }}">{{ message }}</div>
      {% endfor %}
    {% endwith %}

    <form method="POST">
      <div class="field">
        <label>ชื่อ</label>
        <input type="text" name="first_name" value="{{ form.get('first_name','') }}" required>
      </div>
      <div class="field">
        <label>นามสกุล</label>
        <input type="text" name="last_name" value="{{ form.get('last_name','') }}" required>
      </div>
      <div class="field">
        <label>อีเมล</label>
        <input type="email" name="email" value="{{ form.get('email','') }}" required>
      </div>
      <div class="field">
        <label>เบอร์โทร</label>
        <input type="tel" name="phone" value="{{ form.get('phone','') }}" required>
      </div>

      <div class="field">
        <label>วันเกิด / เดือน / ปี</label>
        <div class="row3">
          <input type="number" name="birth_day" placeholder="วัน" min="1" max="31" value="{{ form.get('birth_day','') }}" required>
          <input type="number" name="birth_month" placeholder="เดือน" min="1" max="12" value="{{ form.get('birth_month','') }}" required>
          <input type="number" name="birth_year" placeholder="ปี (พ.ศ./ค.ศ.)" value="{{ form.get('birth_year','') }}" required>
        </div>
      </div>

      <div class="field">
        <label>รหัสผ่าน</label>
        <input type="password" name="password" required minlength="6">
      </div>
      <div class="field">
        <label>ยืนยันรหัสผ่าน</label>
        <input type="password" name="confirm_password" required minlength="6">
      </div>

      <button type="submit" class="btn">สมัครสมาชิก</button>
    </form>

    <div class="link-row">
      มีบัญชีอยู่แล้ว? <a href="{{ url_for('login') }}">เข้าสู่ระบบ</a>
    </div>
  </div>
</body>
</html>
EOF

echo "==> ติดตั้ง Flask"
pip install --quiet flask 2>/dev/null || pip install --quiet --break-system-packages flask

echo ""
echo "ติดตั้งเสร็จแล้ว! โปรเจกต์อยู่ที่ $PROJECT_DIR"
echo "รันแอปด้วยคำสั่ง (พอร์ตเริ่มต้น 5000):"
echo "  cd $PROJECT_DIR && python app.py"
echo ""
echo "ต้องการเปลี่ยนพอร์ต ใช้ตัวแปรแวดล้อม PORT เช่น:"
echo "  cd $PROJECT_DIR && PORT=8080 python app.py"
echo ""
echo "Admin: http://<host>:<port>/admin/login  (username: 3894 / password: 148222)"
