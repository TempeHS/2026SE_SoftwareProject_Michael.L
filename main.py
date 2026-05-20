from flask import Flask
from flask import redirect
from flask import render_template
from flask import request
from flask import jsonify
from flask import url_for
from flask import session
from dotenv import load_dotenv
from datetime import timedelta
from datetime import datetime
from functools import wraps
import requests
from flask_wtf import CSRFProtect
from flask_csp.csp import csp_header
import logging
import secrets
import base64
import os
import qrcode
import pyotp
from urllib.parse import urlparse
import sqlite3
from io import BytesIO
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "data", "database.db")
AUTH_DB = os.environ.get("AUTH_DB", DEFAULT_DB_PATH)

if not os.path.isabs(AUTH_DB):
    AUTH_DB = os.path.join(BASE_DIR, AUTH_DB)

os.makedirs(os.path.dirname(AUTH_DB), exist_ok=True)

app_log = logging.getLogger(__name__)
logging.basicConfig(
    filename="security_log.log",
    encoding="utf-8",
    level=logging.DEBUG,
    format="%(asctime)s %(message)s",
)

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
if not app.config["SECRET_KEY"]:
    raise RuntimeError("SECRET_KEY environment variable is not set")

app.config["JSON_SORT_KEYS"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") == "production"
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["WTF_CSRF_TIME_LIMIT"] = 3600
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

csrf = CSRFProtect(app)


# Redirect index.html to domain root for consistent UX
@app.route("/index", methods=["GET"])
@app.route("/index.htm", methods=["GET"])
@app.route("/index.asp", methods=["GET"])
@app.route("/index.php", methods=["GET"])
@app.route("/index.html", methods=["GET"])
def root():
    return redirect("/", 302)


@app.route("/", methods=["POST", "GET"])
@csp_header(
    {
        # Server Side CSP is consistent with meta CSP in layout.html
        "base-uri": "'self'",
        "default-src": "'self'",
        "style-src": "'self'",
        "script-src": "'self'",
        "img-src": "'self' data:",
        "media-src": "'self'",
        "font-src": "'self'",
        "object-src": "'self'",
        "child-src": "'self'",
        "connect-src": "'self'",
        "worker-src": "'self'",
        "report-uri": "/csp_report",
        "frame-ancestors": "'none'",
        "form-action": "'self'",
        "frame-src": "'none'",
    }
)
def index():
    is_logged_in = "user_id" in session and session.get("2fa_verified", False)

    dashboard_updates = []
    if is_logged_in:
        dashboard_updates = [
            {"message": "New invite from Alex", "time": "2m ago"},
            {"message": "Sam accepted your event", "time": "10m ago"},
        ]

    return render_template(
        "index.html",
        dashboard_updates=dashboard_updates,
        is_logged_in=is_logged_in,
    )


def get_db_conn():
    conn = sqlite3.connect(AUTH_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_auth_db():
    with get_db_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                totp_secret TEXT
            )
        """)

        # Migration for existing dbs created before full_name existed
        cols = {
            row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()
        }
        if "full_name" not in cols:
            conn.execute(
                "ALTER TABLE users ADD COLUMN full_name TEXT NOT NULL DEFAULT ''"
            )

        conn.commit()


def get_user_by_email(email: str):
    with get_db_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def get_user_by_id(user_id: int):
    with get_db_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def create_user(email: str, password: str, full_name: str) -> bool:
    password_hash = generate_password_hash(password)
    try:
        with get_db_conn() as conn:
            conn.execute(
                "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
                (full_name.strip(), email.strip().lower(), password_hash),
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def verify_user(email: str, password: str):
    user = get_user_by_email(email)
    if not user:
        return None

    stored = user["password_hash"] or ""

    if stored.startswith("pbkdf2:") or stored.startswith("scrypt:"):
        return user if check_password_hash(stored, password) else None

    if stored == password:
        new_hash = generate_password_hash(password)
        with get_db_conn() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (new_hash, int(user["id"])),
            )
            conn.commit()
        return get_user_by_id(int(user["id"]))

    return None


def ensure_totp_secret(user_id: int):
    user = get_user_by_id(user_id)
    if user and user["totp_secret"]:
        return user["totp_secret"]

    secret = pyotp.random_base32()
    with get_db_conn() as conn:
        conn.execute("UPDATE users SET totp_secret = ? WHERE id = ?", (secret, user_id))
        conn.commit()
    return secret


def make_qr_code_base64(otp_uri: str) -> str:
    qr = qrcode.QRCode(version=1, box_size=8, border=4)
    qr.add_data(otp_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    stream = BytesIO()
    img.save(stream, format="PNG")
    return base64.b64encode(stream.getvalue()).decode("utf-8")


def is_safe_next(next_url: str) -> bool:
    if not next_url:
        return False
    parsed = urlparse(next_url)
    return parsed.scheme == "" and parsed.netloc == "" and next_url.startswith("/")


def login_required_2fa(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            next_path = request.path or "/"
            if not is_safe_next(next_path):
                next_path = "/"
            return redirect(f"/login.html?next={next_path}")
        if not session.get("2fa_verified", False):
            return redirect("/2fa.html")
        return f(*args, **kwargs)

    return decorated


@app.route("/privacy.html", methods=["GET"])
def privacy():
    return render_template("privacy.html")


@app.route("/secure-form")
def secure_form():
    return render_template("secure-form.html")


@app.route("/account.html", methods=["GET"])
@login_required_2fa
def account():
    return render_template("account.html")


@app.route("/help.html", methods=["GET"])
def help_page():
    return render_template("help.html")


@app.route("/your-huddle")
@login_required_2fa
def your_huddle():
    group_activity = [
        {
            "user": "Alex",
            "action": "shared a new plan for Friday night.",
            "time": "5m ago",
        },
        {"user": "Mia", "action": "joined the hiking huddle.", "time": "20m ago"},
        {"user": "Arnav", "action": "commented: I have no money", "time": "always"},
        {
            "user": "Jordan",
            "action": "commented: “I can bring snacks.”",
            "time": "1h ago",
        },
    ]
    return render_template("your_huddle.html", group_activity=group_activity)


@app.route("/signup.html", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        ok = create_user(email=email, password=password, full_name=full_name)
        if not ok:
            return render_template("signup.html", is_done=False, dupe=True)

        user = get_user_by_email(email)

        # Stage identity for 2FA verification (do not fully log in yet)
        session["pending_user_id"] = int(user["id"])
        session["pending_user_email"] = user["email"]
        session["pending_user_name"] = user["full_name"]
        session["2fa_verified"] = False
        session.permanent = True

        # Correct endpoint name
        return redirect(url_for("two_factor_auth"))

    return render_template("signup.html", is_done=False, dupe=False, error=None)


@app.route("/login.html", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        next_url = (request.form.get("next_url") or "").strip()
        if is_safe_next(next_url):
            session["next_url"] = next_url

        user = verify_user(email, password)
        if user:
            session["pending_user_id"] = int(user["id"])
            session["pending_user_email"] = user["email"]
            session["pending_user_name"] = (user["full_name"] or "").strip() or user[
                "email"
            ]
            session["2fa_verified"] = False
            session["SID"] = secrets.token_urlsafe(32)
            session.permanent = False
            return redirect("/2fa.html")

        return render_template("login.html", error="Invalid Email or Password")

    next_url = (request.args.get("next") or "").strip()
    if is_safe_next(next_url):
        session["next_url"] = next_url

    return render_template("login.html", next_url=session.get("next_url", ""))


@app.route("/2fa.html", methods=["GET", "POST"])
def two_factor_auth():
    pending_user_id = session.get("pending_user_id")
    pending_user_email = session.get("pending_user_email")
    pending_user_name = session.get("pending_user_name")

    if not pending_user_id or not pending_user_email:
        return redirect("/login.html")

    secret = ensure_totp_secret(int(pending_user_id))
    totp = pyotp.TOTP(secret)
    otp_uri = totp.provisioning_uri(name=pending_user_email, issuer_name="Huddle")
    qr_code_b64 = make_qr_code_base64(otp_uri)

    if request.method == "POST":
        otp_input = (request.form.get("otp") or "").strip()
        if totp.verify(otp_input, valid_window=1):
            session["user_id"] = int(pending_user_id)
            session["user_email"] = pending_user_email
            session["user_name"] = pending_user_name or pending_user_email
            session["2fa_verified"] = True
            next_url = session.pop("next_url", "/")
            session.pop("pending_user_id", None)
            session.pop("pending_user_email", None)
            session.pop("pending_user_name", None)
            return redirect(next_url if is_safe_next(next_url) else "/")

        return render_template(
            "2fa.html", qr_code=qr_code_b64, error="Invalid code. Please try again"
        )

    return render_template("2fa.html", qr_code=qr_code_b64)


@app.route("/logout.html", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect("/login.html")


# Endpoint for logging CSP violations
@app.route("/csp_report", methods=["POST"])
@csrf.exempt
def csp_report():
    app.logger.critical(request.data.decode())
    return "done"


init_auth_db()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
