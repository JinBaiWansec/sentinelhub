"""Persistence layer.

Thin sqlite3 access used across the service and model layers. Kept close to
raw SQL; a production build would swap this for an ORM + migrations. The tenant
signing secret and instance id are mirrored into ``instance/app_settings.json``
alongside other deployment attributes.
"""

import os
import sqlite3
import json
import uuid

from app.config import Config

# BASE_DIR points at the project root (one level above this package) so the
# instance folder and the Jinja template folder stay where the rest of the repo
# expects them.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
REPORTS_DIR = os.path.join(INSTANCE_DIR, "reports")
ARCHIVES_DIR = os.path.join(INSTANCE_DIR, "archives")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
DB_PATH = os.path.join(INSTANCE_DIR, "app.db")
MIGRATIONS_DIR = os.path.join(BASE_DIR, "migrations")

os.makedirs(INSTANCE_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(ARCHIVES_DIR, exist_ok=True)

# Per-deployment bootstrap values.
#
# The tenant signing secret and instance id are generated dynamically on first
# boot (see init_db) and mirrored to instance/app_settings.json.
DEFAULT_INSTANCE_ID = "sh-prod-instance-fallback"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_setting(key, default=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cur.fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()


def get_instance_id():
    return get_setting("instance_id", DEFAULT_INSTANCE_ID)


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            plan TEXT,
            email TEXT,
            api_key TEXT
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS monitors (
            id INTEGER PRIMARY KEY,
            name TEXT,
            url TEXT,
            status TEXT,
            owner INTEGER
        );
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY,
            title TEXT,
            body TEXT,
            status TEXT
        );
        CREATE TABLE IF NOT EXISTS integrations (
            id INTEGER PRIMARY KEY,
            name TEXT,
            owner_id INTEGER,
            active INTEGER,
            render_mode TEXT
        );
        CREATE TABLE IF NOT EXISTS role_requests (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            requested_role TEXT,
            status TEXT,
            approver_id INTEGER
        );
        CREATE TABLE IF NOT EXISTS trial_codes (
            code TEXT PRIMARY KEY,
            claimed_by INTEGER,
            claimed INTEGER
        );
        CREATE TABLE IF NOT EXISTS webhooks (
            id INTEGER PRIMARY KEY,
            token TEXT,
            channel TEXT,
            format_template TEXT,
            allow_custom_format INTEGER
        );
        CREATE TABLE IF NOT EXISTS webhook_deliveries (
            id INTEGER PRIMARY KEY,
            webhook_id INTEGER,
            status TEXT,
            detail TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY,
            title TEXT,
            owner INTEGER,
            created TEXT
        );
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY,
            kind TEXT,
            payload TEXT,
            status TEXT,
            created TEXT
        );
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            period_start TEXT,
            period_end TEXT,
            amount_cents INTEGER,
            currency TEXT,
            status TEXT
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY,
            actor_id INTEGER,
            action TEXT,
            target_type TEXT,
            target_id INTEGER,
            detail TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS notification_preferences (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            channel TEXT,
            enabled INTEGER,
            endpoint TEXT
        );
        CREATE TABLE IF NOT EXISTS metrics_samples (
            id INTEGER PRIMARY KEY,
            monitor_id INTEGER,
            value REAL,
            state TEXT,
            sampled_at TEXT
        );
        CREATE TABLE IF NOT EXISTS monitor_thresholds (
            id INTEGER PRIMARY KEY,
            monitor_id INTEGER,
            metric TEXT,
            operator TEXT,
            threshold REAL,
            enabled INTEGER
        );
        CREATE TABLE IF NOT EXISTS account_preferences (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            display_name TEXT,
            timezone TEXT,
            language TEXT
        );
        """
    )

    # ---- per-deployment dynamic seed ---------------------------------------
    # Each fresh database gets a brand-new tenant signing secret, a unique
    # instance id, and a random enterprise trial code. These are generated ONCE
    # (the rows already exist on subsequent boots thanks to INSERT OR IGNORE),
    # so the signing key stays stable for the life of the database but is unique
    # to this deployment. An operator may pin the secret via
    # SENTINELHUB_TENANT_SECRET (e.g. for blue/green key rotation).
    tenant_secret = Config.tenant_secret_override()
    if not tenant_secret:
        existing = get_setting("tenant_signing_secret", None)
        tenant_secret = existing if existing else ("sh_secret_" + os.urandom(16).hex())

    instance_id = get_setting("instance_id", None)
    if not instance_id:
        instance_id = "inst_" + uuid.uuid4().hex[:12]
    cur.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES ('tenant_signing_secret', ?)",
        (tenant_secret,)
    )
    cur.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES ('instance_id', ?)",
        (instance_id,)
    )

    # Resolve or generate the enterprise trial code once per deployment.
    cur.execute("SELECT code FROM trial_codes LIMIT 1")
    _trial_row = cur.fetchone()
    trial_code = (
        _trial_row["code"]
        if _trial_row
        else ("ENTERPRISE-TRIAL-" + os.urandom(4).hex().upper())
    )

    app_settings_path = os.path.join(INSTANCE_DIR, "app_settings.json")
    try:
        settings_data = {}
        if os.path.exists(app_settings_path):
            with open(app_settings_path, "r", encoding="utf-8") as f:
                settings_data = json.load(f)

        settings_data["tenant_signing_secret"] = tenant_secret
        settings_data["instance_id"] = instance_id

        with open(app_settings_path, "w", encoding="utf-8") as f:
            json.dump(settings_data, f, indent=2)
    except Exception as exc:
        print(f"[!] 同步 app_settings.json 失败: {exc}")

    cur.execute(
        "INSERT OR IGNORE INTO users (id,username,password,role,plan,email,api_key) "
        "VALUES (1,'admin','admin123','admin','enterprise','admin@sentinel.local','sh-admin-9f2c7b')"
    )
    cur.execute(
        "INSERT OR IGNORE INTO users (id,username,password,role,plan,email,api_key) "
        "VALUES (2,'demo','demo123','member','free','demo@sentinel.local','sh-demo-1a2b3c')"
    )
    cur.executemany(
        "INSERT OR IGNORE INTO monitors (id,name,url,status,owner) VALUES (?,?,?,?,?)",
        [
            (1, "API Gateway", "https://api.example.com/health", "up", 1),
            (2, "Auth Service", "https://auth.example.com/ping", "degraded", 1),
            (3, "Billing DB", "https://db.example.com/status", "up", 2),
            (4, "CDN Edge", "https://cdn.example.com/health", "up", 1),
        ],
    )
    cur.execute(
        "INSERT OR IGNORE INTO integrations (id,name,owner_id,active,render_mode) "
        "VALUES (1,'PagerDuty Bridge',1,0,'modern')"
    )
    cur.execute(
        "INSERT OR IGNORE INTO trial_codes (code,claimed_by,claimed) VALUES (?,NULL,0)",
        (trial_code,),
    )
    cur.execute(
        "INSERT OR IGNORE INTO webhooks (id,token,channel,format_template,allow_custom_format) "
        "VALUES (1,'wh-public-demo','slack','Incident {{ payload.title }} was reported',0)"
    )

    # Seed a couple of historical invoices so the billing page is not empty.
    cur.execute(
        "INSERT OR IGNORE INTO invoices (id,user_id,period_start,period_end,amount_cents,currency,status) "
        "VALUES (1,1,'2026-06-01','2026-06-30',9900,'USD','paid')"
    )
    cur.execute(
        "INSERT OR IGNORE INTO invoices (id,user_id,period_start,period_end,amount_cents,currency,status) "
        "VALUES (2,2,'2026-06-01','2026-06-30',0,'USD','paid')"
    )
    cur.execute(
        "INSERT OR IGNORE INTO notification_preferences (id,user_id,channel,enabled,endpoint) "
        "VALUES (1,1,'webhook',1,'https://hooks.sentinel.local/admin')"
    )
    cur.execute(
        "INSERT OR IGNORE INTO reports (id,title,owner,created) VALUES (1,'Monthly overview',1,'2026-07-01')"
    )

    # Seed metric samples for the dashboard time-series (guarded so restarts
    # do not keep appending duplicates).
    cur.execute("SELECT COUNT(*) AS c FROM metrics_samples")
    if cur.fetchone()["c"] == 0:
        for mid in (1, 2, 3, 4):
            for day in range(1, 16):
                if mid == 2:
                    val = 92.0 - (day % 7)
                else:
                    val = 99.0 - (day % 5) * 1.5
                state = "up" if val >= 99.0 else ("degraded" if val >= 90.0 else "down")
                cur.execute(
                    "INSERT INTO metrics_samples (monitor_id, value, state, sampled_at) "
                    "VALUES (?,?,?,?)",
                    (mid, round(val, 2), state, "2026-07-%02d 00:00" % day),
                )

    # Seed default alert thresholds for the threshold-config endpoints.
    cur.execute("SELECT COUNT(*) AS c FROM monitor_thresholds")
    if cur.fetchone()["c"] == 0:
        for mid in (1, 2, 3, 4):
            cur.execute(
                "INSERT INTO monitor_thresholds (monitor_id, metric, operator, threshold, enabled) "
                "VALUES (?, 'latency_ms', '<', 200.0, 1)",
                (mid,),
            )

    conn.commit()
    conn.close()

    # Mirror secret + instance id to a config file. The values are
    # deployment-specific (see dynamic seed above) and never hard-coded in the
    # source.
    with open(os.path.join(INSTANCE_DIR, "app_settings.json"), "w") as fh:
        json.dump(
            {
                "tenant_signing_secret": tenant_secret,
                "instance_id": instance_id,
                "env": "production",
                "region": "ap-east",
            },
            fh,
        )

    # A placeholder report so the bundler has something to archive.
    with open(os.path.join(REPORTS_DIR, "latest.html"), "w") as fh:
        fh.write("<html><body>SentinelHub latest report</body></html>")


def record_audit(actor_id, action, target_type="", target_id=0, detail=""):
    """Append an entry to the administrative audit log."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO audit_log (actor_id, action, target_type, target_id, detail, created_at) "
        "VALUES (?,?,?,?,?, datetime('now'))",
        (actor_id, action, target_type, target_id, detail),
    )
    conn.commit()
    conn.close()


def get_metrics_samples(monitor_id, limit=500):
    """Return recent metric samples for a monitor, newest first."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT value, state, sampled_at FROM metrics_samples WHERE monitor_id=? "
        "ORDER BY sampled_at DESC LIMIT ?",
        (monitor_id, limit),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


if __name__ == "__main__":
    init_db()
    print("database initialized at", DB_PATH)
