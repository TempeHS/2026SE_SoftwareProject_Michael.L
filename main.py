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

AUTH_DB = os.environ.get("AUTH_DB", "database.db")

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
    return render_template("/index.html")


def get_db_conn():
    conn = sqlite3.connect(AUTH_DB)
    conn.row_factory = sqlite3.Row
    return conn


def get_user_by_email(email: str):
    with get_db_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def get_user_by_id(user_id: int):
    with get_db_conn() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def create_user(email: str, password: str) -> bool:
    password_hash = generate_password_hash(password)
    try:
        with get_db_conn() as conn:
            conn.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash),
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def verify_user(email: str, password: str):
    user = get_user_by_email(email)
    if not user:
        return None
    return user if check_password_hash(user["password_hash"], password) else None


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
            return redirect(f"/login.html?next={request.path}")
        if not session.get("2fa_verified", False):
            return redirect("/2fa.html")
        return f(*args, **kwargs)

    return decorated


@app.route("/privacy.html", methods=["GET"])
def privacy():
    return render_template("privacy.html")


@app.route("/signup.html", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        if not email or not password:
            return render_template("signup.html", error="Missing fields")

        if len(password) < 8:
            return render_template(
                "signup.html", error="Password must be at least 8 characters"
            )

        if create_user(email, password):
            return render_template("login.html", is_done=True)

        return render_template("signup.html", dupe=True)

    return render_template("signup.html")


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
            session.clear()
            session["pending_user_id"] = int(user["id"])
            session["pending_user_email"] = user["email"]
            if is_safe_next(next_url):
                session["next_url"] = next_url
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

    if not pending_user_id or not pending_user_email:
        return redirect("/login.html")

    secret = ensure_totp_secret(int(pending_user_id))
    totp = pyotp.TOTP(secret)
    otp_uri = totp.provisioning_uri(
        name=pending_user_email, issuer_name="WCA Predictor"
    )
    qr_code_b64 = make_qr_code_base64(otp_uri)

    if request.method == "POST":
        otp_input = (request.form.get("otp") or "").strip()
        if totp.verify(otp_input, valid_window=1):
            session["user_id"] = int(pending_user_id)
            session["user_email"] = pending_user_email
            session["2fa_verified"] = True
            next_url = session.pop("next_url", "/")
            session.pop("pending_user_id", None)
            session.pop("pending_user_email", None)
            return redirect(next_url if is_safe_next(next_url) else "/")

        return render_template(
            "2fa.html", qr_code=qr_code_b64, error="Invalid code. Please try again"
        )

    return render_template("2fa.html", qr_code=qr_code_b64)


@app.route("/logout.html", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect("/")


# Endpoint for logging CSP violations
@app.route("/csp_report", methods=["POST"])
@csrf.exempt
def csp_report():
    app.logger.critical(request.data.decode())
    return "done"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
