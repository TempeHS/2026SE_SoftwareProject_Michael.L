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
import re

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
ROLE_PATTERN = re.compile(r"^[A-Za-z0-9 \-]{1,50}$")


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
        "img-src": "'self' data: https://tile.openstreetmap.org https://*.tile.openstreetmap.org",
        "media-src": "'self'",
        "font-src": "'self'",
        "object-src": "'self'",
        "child-src": "'self'",
        "connect-src": "'self' https://nominatim.openstreetmap.org https://tile.openstreetmap.org https://*.tile.openstreetmap.org",
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

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_huddle_group_roles_group "
            "ON huddle_group_roles(group_id)"
        )

        # event close status (closed means gruop leader has finalised it)
        cols_events = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(huddle_events)").fetchall()
        }
        if "is_closed" not in cols_events:
            conn.execute(
                "ALTER TABLE huddle_events ADD COLUMN is_closed INTEGER NOT NULL DEFAULT 0"
            )
        if "closed_at" not in cols_events:
            conn.execute("ALTER TABLE huddle_events ADD COLUMN closed_at TEXT")

        # moving existing dbs created before full_name existed
        cols = {
            row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()
        }
        if "full_name" not in cols:
            conn.execute(
                "ALTER TABLE users ADD COLUMN full_name TEXT NOT NULL DEFAULT ''"
            )

        # neu huddle Groups
        conn.execute("""
            CREATE TABLE IF NOT EXISTS huddle_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                invite_code TEXT NOT NULL UNIQUE,
                created_by INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)

        # allow many memberships per user (unique pair only)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS huddle_memberships (
                user_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, group_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (group_id) REFERENCES huddle_groups(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS huddle_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                created_by INTEGER NOT NULL,
                name TEXT NOT NULL,
                location TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT,
                arrival_time TEXT,
                description TEXT,
                category TEXT,
                price_estimate REAL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES huddle_groups(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS huddle_votes (
                event_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                choice TEXT NOT NULL CHECK(choice IN ('yes','no','maybe')),
                voted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (event_id, user_id),
                FOREIGN KEY (event_id) REFERENCES huddle_events(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # event roles - assigned by group leader
        conn.execute("""
            CREATE TABLE IF NOT EXISTS huddle_event_roles (
                event_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                assigned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (event_id, user_id),
                FOREIGN KEY (event_id) REFERENCES huddle_events(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # custom roles
        conn.execute("""
            CREATE TABLE IF NOT EXISTS huddle_group_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(group_id, role),
                FOREIGN KEY (group_id) REFERENCES huddle_groups(id)
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_huddle_group_roles_group "
            "ON huddle_group_roles(group_id)"
        )

        # attendance records
        conn.execute("""
            CREATE TABLE IF NOT EXISTS huddle_attendance (
                event_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                attended INTEGER NOT NULL CHECK(attended IN (0,1)),
                marked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (event_id, user_id),
                FOREIGN KEY (event_id) REFERENCES huddle_events(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # move old schema where user_id had UNIQUE (one huddle per user) --> should technically have more for UI purposes
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='huddle_memberships'"
        ).fetchone()
        table_sql = (row["sql"] or "").upper().replace("\n", " ") if row else ""
        if "USER_ID INTEGER NOT NULL UNIQUE" in table_sql:
            conn.execute("PRAGMA foreign_keys=OFF")
            conn.execute("""
                CREATE TABLE huddle_memberships_new (
                    user_id INTEGER NOT NULL,
                    group_id INTEGER NOT NULL,
                    joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, group_id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (group_id) REFERENCES huddle_groups(id)
                )
            """)
            conn.execute("""
                INSERT OR IGNORE INTO huddle_memberships_new (user_id, group_id, joined_at)
                SELECT user_id, group_id, joined_at FROM huddle_memberships
            """)
            conn.execute("DROP TABLE huddle_memberships")
            conn.execute(
                "ALTER TABLE huddle_memberships_new RENAME TO huddle_memberships"
            )
            conn.execute("PRAGMA foreign_keys=ON")

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


INVITE_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_invite_code(length: int = 6) -> str:
    return "".join(secrets.choice(INVITE_CODE_ALPHABET) for _ in range(length))


def get_groups_for_user(user_id: int):
    with get_db_conn() as conn:
        return conn.execute(
            """
            SELECT g.*, m.joined_at
            FROM huddle_groups g
            INNER JOIN huddle_memberships m ON m.group_id = g.id
            WHERE m.user_id = ?
            ORDER BY datetime(m.joined_at) DESC, g.id DESC
            """,
            (user_id,),
        ).fetchall()


def get_user_group_by_id(user_id: int, group_id: int):
    with get_db_conn() as conn:
        return conn.execute(
            """
            SELECT g.*, m.joined_at
            FROM huddle_groups g
            INNER JOIN huddle_memberships m ON m.group_id = g.id
            WHERE m.user_id = ? AND g.id = ?
            LIMIT 1
            """,
            (user_id, group_id),
        ).fetchone()


def create_group_for_user(user_id: int, group_name: str):
    with get_db_conn() as conn:
        for _ in range(10):  # retry invite code collision edge case
            code = generate_invite_code()
            try:
                cur = conn.execute(
                    """
                    INSERT INTO huddle_groups (name, invite_code, created_by)
                    VALUES (?, ?, ?)
                    """,
                    (group_name, code, user_id),
                )
                group_id = cur.lastrowid
                conn.execute(
                    "INSERT INTO huddle_memberships (user_id, group_id) VALUES (?, ?)",
                    (user_id, group_id),
                )
                conn.commit()
                return conn.execute(
                    "SELECT * FROM huddle_groups WHERE id = ?",
                    (group_id,),
                ).fetchone()
            except sqlite3.IntegrityError:
                conn.rollback()
    return None


def join_group_by_code(user_id: int, invite_code: str):
    code = (invite_code or "").strip().upper()
    if len(code) != 6 or any(c not in INVITE_CODE_ALPHABET for c in code):
        return None, "Invalid invite code format."

    with get_db_conn() as conn:
        group = conn.execute(
            "SELECT * FROM huddle_groups WHERE invite_code = ?",
            (code,),
        ).fetchone()
        if not group:
            return None, "Invite code not found."

        already = conn.execute(
            "SELECT 1 FROM huddle_memberships WHERE user_id = ? AND group_id = ?",
            (user_id, int(group["id"])),
        ).fetchone()
        if already:
            return None, "You are already in this Huddle."

        try:
            conn.execute(
                "INSERT INTO huddle_memberships (user_id, group_id) VALUES (?, ?)",
                (user_id, int(group["id"])),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            return None, "Could not join this huddle. Please try again."

        return group, None


EVENT_CATEGORIES = [
    "Food",
    "Drinks",
    "Sports",
    "Movie",
    "Trip",
    "Party",
    "Study",
    "Gaming",
    "Outdoors",
    "Miscellaneous",
    "Other",
]

EVENT_ROLES = [
    "Organiser",
    "Driver",
    "Food",
    "Drinks",
    "Snacks",
    "Music",
    "Photographer",
    "Decorations",
    "Tickets",
    "Equipment",
]


def create_event(group_id, user_id, data):
    with get_db_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO huddle_events
                (group_id, created_by, name, location, start_date, end_date, arrival_time, description, category, price_estimate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                group_id,
                user_id,
                data["name"],
                data["location"],
                data["start_date"],
                data["end_date"],
                data["arrival_time"],
                data["description"],
                data["category"],
                data["price_estimate"],
            ),
        )
        conn.commit()
        return cur.lastrowid


# gets the events for the groups and orders them from closest to furthest
def get_events_for_group(group_id):
    with get_db_conn() as conn:
        return conn.execute(
            "SELECT * FROM huddle_events WHERE group_id = ? ORDER BY datetime(start_date) ASC",
            (group_id,),
        ).fetchall()


def get_event_in_group(event_id, group_id):
    with get_db_conn() as conn:
        return conn.execute(
            "SELECT * FROM huddle_events WHERE id = ? AND group_id = ?",
            (event_id, group_id),
        ).fetchone()


def cast_vote(event_id, user_id, choice):
    if choice not in ("yes", "no", "maybe"):
        return False
    with get_db_conn() as conn:
        conn.execute(
            """
            INSERT INTO huddle_votes (event_id, user_id, choice)
            VALUES (?, ?, ?)
            ON CONFLICT(event_id, user_id) DO UPDATE SET
                choice = excluded.choice,
                voted_at = CURRENT_TIMESTAMP
            """,
            (event_id, user_id, choice),
        )
        conn.commit()
        return True


def get_vote_tallies_for_events(event_ids, user_id):
    """Returns dict of {event_id: {'yes': n, 'no': n, 'maybe': n, 'my_vote': str|None}}"""
    if not event_ids:
        return {}
    placeholders = ",".join("?" for _ in event_ids)
    tallies = {
        eid: {"yes": 0, "no": 0, "maybe": 0, "my_vote": None} for eid in event_ids
    }
    with get_db_conn() as conn:
        rows = conn.execute(
            f"SELECT event_id, choice, COUNT(*) AS c FROM huddle_votes "
            f"WHERE event_id IN ({placeholders}) GROUP BY event_id, choice",
            event_ids,
        ).fetchall()
        for r in rows:
            tallies[r["event_id"]][r["choice"]] = r["c"]

        my_rows = conn.execute(
            f"SELECT event_id, choice FROM huddle_votes "
            f"WHERE user_id = ? AND event_id IN ({placeholders})",
            [user_id, *event_ids],
        ).fetchall()
        for r in my_rows:
            tallies[r["event_id"]]["my_vote"] = r["choice"]
    return tallies


def get_members_of_group(group_id):
    with get_db_conn() as conn:
        return conn.execute(
            """
            SELECT u.id, u.full_name, u.email, m.joined_at
            FROM users u
            INNER JOIN huddle_memberships m ON m.user_id = u.id
            WHERE m.group_id = ?
            ORDER BY u.full_name COLLATE NOCASE ASC
            """,
            (group_id,),
        ).fetchall()


def get_event_member_details(event_id, group_id):
    """For each member in the group: their vote choice, role, and attendance for this event."""
    with get_db_conn() as conn:
        return conn.execute(
            """
            SELECT u.id, u.full_name, u.email,
                   v.choice AS vote_choice,
                   r.role AS role,
                   a.attended AS attended
            FROM users u
            INNER JOIN huddle_memberships m ON m.user_id = u.id
            LEFT JOIN huddle_votes v ON v.user_id = u.id AND v.event_id = ?
            LEFT JOIN huddle_event_roles r ON r.user_id = u.id AND r.event_id = ?
            LEFT JOIN huddle_attendance a ON a.user_id = u.id AND a.event_id = ?
            WHERE m.group_id = ?
            ORDER BY u.full_name COLLATE NOCASE ASC
            """,
            (event_id, event_id, event_id, group_id),
        ).fetchall()


def assign_event_role(event_id, user_id, role):
    with get_db_conn() as conn:
        if not role:
            conn.execute(
                "DELETE FROM huddle_event_roles WHERE event_id = ? AND user_id = ?",
                (event_id, user_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO huddle_event_roles (event_id, user_id, role)
                VALUES (?, ?, ?)
                ON CONFLICT(event_id, user_id) DO UPDATE SET
                    role = excluded.role,
                    assigned_at = CURRENT_TIMESTAMP
                """,
                (event_id, user_id, role),
            )
        conn.commit()


def is_user_in_group(user_id, group_id):
    with get_db_conn() as conn:
        return (
            conn.execute(
                "SELECT 1 FROM huddle_memberships WHERE user_id = ? AND group_id = ?",
                (user_id, group_id),
            ).fetchone()
            is not None
        )


def get_group_creator_name(group):
    with get_db_conn() as conn:
        row = conn.execute(
            "SELECT full_name, email FROM users WHERE id = ?",
            (int(group["created_by"]),),
        ).fetchone()
    if not row:
        return "Unknown"
    return (row["full_name"] or "").strip() or row["email"]


def get_custom_roles_for_group(group_id):
    with get_db_conn() as conn:
        rows = conn.execute(
            "SELECT role FROM huddle_group_roles WHERE group_id = ? "
            "ORDER BY role COLLATE NOCASE ASC",
            (group_id,),
        ).fetchall()
    return [r["role"] for r in rows]


def get_merged_roles_for_group(group_id):
    custom = get_custom_roles_for_group(group_id)
    seen = set()
    merged = []
    for r in EVENT_ROLES + custom:
        key = r.lower()
        if key not in seen:
            seen.add(key)
            merged.append(r)
    return merged


def add_custom_role_for_group(group_id, role):
    with get_db_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO huddle_group_roles (group_id, role) VALUES (?, ?)",
            (group_id, role),
        )
        conn.commit()


# the members who said yes or maybe
def get_committed_members_for_event(event_id, group_id):
    with get_db_conn() as conn:
        return conn.execute(
            """
            SELECT u.id, u.full_name, u.email, v.choice AS vote_choice,
                a.attended AS attended
            FROM users u
            INNER JOIN huddle_memberships m ON m.user_id = u.id
            INNER JOIN huddle_votes v ON v.user_id = u.id AND v.event_id = ?
            LEFT JOIN huddle_attendance a ON a.user_id = u.id AND a.event_id = ?
            WHERE m.group_id = ? AND v.choice IN ('yes','maybe')
            ORDER BY u.full_name COLLATE NOCASE ASC
            """,
            (event_id, event_id, group_id),
        ).fetchall()


def close_event_and_record_attendance(event_id, group_id, attendance_map):
    """
    attendance_map: dict[int user_id -> bool attended]
    the attendance maps purpose is to only records attendance for users who actually committed (voted yes/maybe).
    Otherwise there would be "no" voters in the attendance logging but they were already never going.
    """

    committed = get_committed_members_for_event(event_id, group_id)
    committed_ids = {int(r["id"]) for r in committed}

    with get_db_conn() as conn:
        for uid, attended in attendance_map.items():
            if int(uid) not in committed_ids:
                continue
            conn.execute(
                """
                INSERT INTO huddle_attendance (event_id, user_id, attended)
                VALUES (?, ?, ?)
                ON CONFLICT(event_id, user_id) DO UPDATE SET
                    attended = excluded.attended,
                    marked_at = CURRENT_TIMESTAMP
                """,
                (event_id, int(uid), 1 if attended else 0),
            )
        conn.execute(
            "UPDATE huddle_events SET is_closed = 1, closed_at = CURRENT_TIMESTAMP "
            "WHERE id = ? AND group_id = ?",
            (event_id, group_id),
        )
        conn.commit()


def delete_event(event_id, group_id):
    with get_db_conn() as conn:
        conn.execute("DELETE FROM huddle_attendance WHERE event_id = ?", (event_id,))
        conn.execute("DELETE FROM huddle_event_roles WHERE event_id = ?", (event_id,))
        conn.execute("DELETE FROM huddle_votes WHERE event_id = ?", (event_id,))
        conn.execute(
            "DELETE FROM huddle_events WHERE id = ? AND group_id = ?",
            (event_id, group_id),
        )
        conn.commit()


def get_user_attendance_stats(user_id):
    """Returns attended_count, committed_count, and the percentage across all closed events."""
    with get_db_conn() as conn:
        row = conn.execute(
            """
            SELECT
                COALESCE(SUM(attended), 0) AS attended_count,
                COUNT(*) AS committed_count
            FROM huddle_attendance
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
    attended = int(row["attended_count"] or 0)
    committed = int(row["committed_count"] or 0)
    pct = round((attended / committed) * 100, 1) if committed > 0 else None
    return attended, committed, pct


def get_attendance_stats_for_group(group_id):
    """Returns list of {user_id, full_name, email, attended, committed, percentage}."""
    with get_db_conn() as conn:
        rows = conn.execute(
            """
            SELECT u.id, u.full_name, u.email,
                COALESCE(SUM(a.attended), 0) AS attended_count,
                COUNT(a.user_id) AS committed_count
            FROM users u
            INNER JOIN huddle_memberships m ON m.user_id = u.id
            LEFT JOIN huddle_attendance a ON a.user_id = u.id
            LEFT JOIN huddle_events e ON e.id = a.event_id AND e.group_id = ?
            WHERE m.group_id = ?
            GROUP BY u.id, u.full_name, u.email
            ORDER BY u.full_name COLLATE NOCASE ASC
            """,
            (group_id, group_id),
        ).fetchall()

    out = []
    for r in rows:
        attended = int(r["attended_count"] or 0)
        committed = int(r["committed_count"] or 0)
        pct = round((attended / committed) * 100, 1) if committed > 0 else None
        out.append(
            {
                "user_id": r["id"],
                "full_name": r["full_name"],
                "email": r["email"],
                "attended": attended,
                "committed": committed,
                "percentage": pct,
            }
        )
    return out


def get_attendance_percentages_for_group(group_id):
    with get_db_conn() as conn:
        rows = conn.execute(
            """
            SELECT u.id AS user_id,
                COUNT(a.event_id) AS committed,
                COALESCE(SUM(a.attended), 0) AS attended
            FROM users u
            INNER JOIN huddle_memberships m ON m.user_id = u.id
            LEFT JOIN huddle_attendance a
                ON a.user_id = u.id
            LEFT JOIN huddle_events e
                ON e.id = a.event_id
                AND e.group_id = ?
                AND e.is_closed = 1
            WHERE m.group_id = ?
            AND (a.event_id IS NULL OR e.id IS NOT NULL)
            GROUP BY u.id
            """,
            (group_id, group_id),
        ).fetchall()

    result = {}
    for r in rows:
        committed = int(r["committed"] or 0)
        attended = int(r["attended"] or 0)
        if committed == 0:
            result[int(r["user_id"])] = None
        else:
            result[int(r["user_id"])] = round((attended / committed) * 100)
    return result


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


@app.route("/huddle/<int:group_id>/propose", methods=["GET", "POST"])
@login_required_2fa
def propose_event(group_id):
    user_id = int(session["user_id"])
    group = get_user_group_by_id(user_id, group_id)
    if not group:
        return redirect("/your-huddle")

    error = None
    form = {}

    if request.method == "POST":
        form = {
            "name": (request.form.get("name") or "").strip(),
            "location": (request.form.get("location") or "").strip(),
            "start_date": (request.form.get("start_date") or "").strip(),
            "end_date": (request.form.get("end_date") or "").strip() or None,
            "arrival_time": (request.form.get("arrival_time") or "").strip() or None,
            "description": (request.form.get("description") or "").strip() or None,
            "category": (request.form.get("category") or "").strip() or None,
            "price_estimate": (request.form.get("price_estimate") or "").strip(),
        }

        # validate letter inputs
        if not (1 <= len(form["name"]) <= 30):
            error = "Event name must be 1–30 characters."
        elif not (1 <= len(form["location"]) <= 100):
            error = "Location must be 1–100 characters."
        elif not form["start_date"]:
            error = "Start date is required."
        elif form["description"] and len(form["description"]) > 500:
            error = "Description must be 500 characters or fewer."
        elif form["category"] and form["category"] not in EVENT_CATEGORIES:
            error = "Invalid category."

        # validate the date
        if not error:
            try:
                start_dt = datetime.fromisoformat(form["start_date"])
                if form["end_date"]:
                    end_dt = datetime.fromisoformat(form["end_date"])
                    if end_dt < start_dt:
                        error = "End date cannot be before start date."
            except ValueError:
                error = "Invalid date format."

        # validate the price
        if not error:
            if form["price_estimate"]:
                try:
                    price = float(form["price_estimate"])
                    if price < 0 or price > 100000:
                        error = "Price estimate must be between 0 and 100000."
                    else:
                        form["price_estimate"] = price
                except ValueError:
                    error = "Price estimate must be a number."
            else:
                form["price_estimate"] = None

        if not error:
            create_event(group_id, user_id, form)
            return redirect(url_for("view_huddle", group_id=group_id))

    return render_template(
        "propose_event.html",
        group=group,
        categories=EVENT_CATEGORIES,
        error=error,
        form=form,
    )


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
    user_id = int(session["user_id"])
    groups = get_groups_for_user(user_id)

    return render_template(
        "your_huddle.html",
        in_group=len(groups) > 0,
        groups=groups,
    )


@app.route("/huddle/<int:group_id>", methods=["GET"])
@login_required_2fa
def view_huddle(group_id: int):
    user_id = int(session["user_id"])
    group = get_user_group_by_id(user_id, group_id)
    if not group:
        return redirect("/your-huddle")
    events = get_events_for_group(group_id)
    tallies = get_vote_tallies_for_events([e["id"] for e in events], user_id)
    return render_template(
        "huddle_detail.html", group=group, events=events, tallies=tallies
    )


@app.route("/huddle/create", methods=["GET", "POST"])
@login_required_2fa
def create_huddle():
    user_id = int(session["user_id"])

    error = None
    if request.method == "POST":
        group_name = (request.form.get("group_name") or "").strip()
        if len(group_name) < 2 or len(group_name) > 50:
            error = "Group name must be between 2 and 50 characters."
        else:
            created = create_group_for_user(user_id, group_name)
            if created:
                return redirect("/your-huddle")
            error = "Could not create your huddle. Please try again."
    return render_template("create_huddle.html", error=error)


@app.route("/huddle/join", methods=["GET", "POST"])
@login_required_2fa
def join_huddle():
    user_id = int(session["user_id"])

    error = None
    if request.method == "POST":
        invite_code = (request.form.get("invite_code") or "").strip()
        group, error = join_group_by_code(user_id, invite_code)
        if group:
            return redirect("/your-huddle")

    return render_template("join_huddle.html", error=error)


@app.route("/huddle/<int:group_id>/event/<int:event_id>/vote", methods=["POST"])
@login_required_2fa
def vote_event(group_id, event_id):
    user_id = int(session["user_id"])
    if not is_user_in_group(user_id, group_id):
        return redirect("/your-huddle")

    event = get_event_in_group(event_id, group_id)
    if not event:
        return redirect(url_for("view_huddle", group_id=group_id))

    choice = (request.form.get("choice") or "").strip().lower()
    if choice in ("yes", "no", "maybe"):
        cast_vote(event_id, user_id, choice)

    return redirect(url_for("view_event", group_id=group_id, event_id=event_id))


@app.route("/huddle/<int:group_id>/members", methods=["GET"])
@login_required_2fa
def view_members(group_id: int):
    user_id = int(session["user_id"])
    group = get_user_group_by_id(user_id, group_id)
    if not group:
        return redirect("/your-huddle")
    members = get_members_of_group(group_id)
    return render_template("huddle_members.html", group=group, members=members)


@app.route("/huddle/<int:group_id>/event/<int:event_id>", methods=["GET"])
@login_required_2fa
def view_event(group_id: int, event_id: int):
    user_id = int(session["user_id"])
    group = get_user_group_by_id(user_id, group_id)
    if not group:
        return redirect("/your-huddle")

    event = get_event_in_group(event_id, group_id)
    if not event:
        return redirect(url_for("view_huddle", group_id=group_id))

    members = get_event_member_details(event_id, group_id)
    tallies_map = get_vote_tallies_for_events([event_id], user_id)
    tallies = tallies_map.get(
        event_id, {"yes": 0, "no": 0, "maybe": 0, "my_vote": None}
    )
    leader_name = get_group_creator_name(group)
    is_leader = int(group["created_by"]) == user_id

    custom_roles = get_custom_roles_for_group(group_id)
    roles = list(EVENT_ROLES) + [r for r in custom_roles if r not in EVENT_ROLES]

    attendance_pct = get_attendance_percentages_for_group(group_id)  # NEW

    return render_template(
        "event_detail.html",
        group=group,
        event=event,
        members=members,
        tallies=tallies,
        leader_name=leader_name,
        is_leader=is_leader,
        roles=roles,
        attendance_pct=attendance_pct,  # NEW
    )


@app.route("/huddle/<int:group_id>/event/<int:event_id>/assign_role", methods=["POST"])
@login_required_2fa
def assign_role(group_id: int, event_id: int):
    user_id = int(session["user_id"])
    group = get_user_group_by_id(user_id, group_id)
    if not group:
        return redirect("/your-huddle")

    # only the group leader can assign a role
    if int(group["created_by"]) != user_id:
        return redirect(url_for("view_event", group_id=group_id, event_id=event_id))

    event = get_event_in_group(event_id, group_id)
    if not event:
        return redirect(url_for("view_huddle", group_id=group_id))

    try:
        target_user_id = int(request.form.get("user_id") or 0)
    except ValueError:
        target_user_id = 0
    role = (request.form.get("role") or "").strip()

    if role:
        if not ROLE_PATTERN.match(role):
            return redirect(url_for("view_event", group_id=group_id, event_id=event_id))

        existing_lower = {r.lower() for r in EVENT_ROLES}
        if role.lower() not in existing_lower:
            add_custom_role_for_group(group_id, role)

    if target_user_id and is_user_in_group(target_user_id, group_id):
        assign_event_role(event_id, target_user_id, role or None)

    return redirect(url_for("view_event", group_id=group_id, event_id=event_id))


@app.route("/huddle/<int:group_id>/event/<int:event_id>/close", methods=["GET", "POST"])
@login_required_2fa
def close_event(group_id: int, event_id: int):
    user_id = int(session["user_id"])
    group = get_user_group_by_id(user_id, group_id)
    if not group:
        return redirect("/your-huddle")

    # only the group leader can close the event
    if int(group["created_by"]) != user_id:
        return redirect(url_for("view_event", group_id=group_id, event_id=event_id))

    event = get_event_in_group(event_id, group_id)
    if not event:
        return redirect(url_for("view_huddle", group_id=group_id))

    # if already closed, theres no point reopening the close form
    if int(event["is_closed"] or 0) == 1:
        return redirect(url_for("view_event", group_id=group_id, event_id=event_id))

    committed = get_committed_members_for_event(event_id, group_id)

    if request.method == "POST":
        attendance_map = {}
        for member in committed:
            uid = int(member["id"])
            # checkbox present means attended; absent means did not attend
            attended = request.form.get(f"attended_{uid}") == "on"
            attendance_map[uid] = attended

        close_event_and_record_attendance(event_id, group_id, attendance_map)
        return redirect(url_for("view_huddle", group_id=group_id))

    return render_template(
        "close_event.html",
        group=group,
        event=event,
        committed=committed,
    )


@app.route("/huddle/<int:group_id>/event/<int:event_id>/delete", methods=["POST"])
@login_required_2fa
def delete_event_route(group_id: int, event_id: int):
    user_id = int(session["user_id"])
    group = get_user_group_by_id(user_id, group_id)
    if not group:
        return redirect("/your-huddle")

    # only the group leader can delete the event
    if int(group["created_by"]) != user_id:
        return redirect(url_for("view_event", group_id=group_id, event_id=event_id))

    event = get_event_in_group(event_id, group_id)
    if not event:
        return redirect(url_for("view_huddle", group_id=group_id))

    delete_event(event_id, group_id)
    return redirect(url_for("view_huddle", group_id=group_id))


@app.route("/huddle/<int:group_id>/attendance", methods=["GET"])
@login_required_2fa
def view_attendance(group_id: int):
    user_id = int(session["user_id"])
    group = get_user_group_by_id(user_id, group_id)
    if not group:
        return redirect("/your-huddle")

    stats = get_attendance_stats_for_group(group_id)
    return render_template("attendance_stats.html", group=group, stats=stats)


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


@app.template_filter("prettydt")
def prettydt(value):
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%b %d, %Y · %I:%M %P")
    except (ValueError, TypeError):
        return value


init_auth_db()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
