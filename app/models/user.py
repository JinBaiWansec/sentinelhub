"""User data-access layer.

Thin DAO over the ``users`` / ``role_requests`` / ``notification_preferences`` /
``account_preferences`` / ``audit_log`` tables. These helpers are safe: they
never interpret caller input as code and they never short-circuit authorisation
(which lives in the blueprints / decorators). Business rules (such as who may
approve a role request) intentionally live in the view layer so the DAO stays
dumb.
"""

import sqlite3

from app.database import get_conn


def get_by_id(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, role, plan, email, api_key FROM users WHERE id=?",
        (uid,),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def authenticate(username, password):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, role, plan, email FROM users WHERE username=? AND password=?",
        (username, password),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def create(username, password, email="", role="member", plan="free"):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password, role, plan, email) VALUES (?,?,?,?,?)",
            (username, password, role, plan, email),
        )
        uid = cur.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return None
    conn.close()
    return uid


def set_role(uid, role):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET role=? WHERE id=?", (role, uid))
    conn.commit()
    conn.close()


def set_plan(uid, plan):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET plan=? WHERE id=?", (plan, uid))
    conn.commit()
    conn.close()


def update_email(uid, email):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET email=? WHERE id=?", (email, uid))
    conn.commit()
    conn.close()


# -- Role requests -----------------------------------------------------------


def create_role_request(uid, requested_role):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO role_requests (user_id, requested_role, status, approver_id) "
        "VALUES (?,?,?,?)",
        (uid, requested_role, "pending", None),
    )
    rid = cur.lastrowid
    conn.commit()
    conn.close()
    return rid


def get_role_request(rid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, user_id, requested_role, status, approver_id FROM role_requests WHERE id=?",
        (rid,),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def approve_role_request(rid, approver_id):
    """Mark a request approved and apply the requested role to its owner."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, user_id, requested_role, status FROM role_requests WHERE id=?",
        (rid,),
    )
    req = cur.fetchone()
    if not req:
        conn.close()
        return None
    cur.execute(
        "UPDATE role_requests SET status='approved', approver_id=? WHERE id=?",
        (approver_id, rid),
    )
    cur.execute(
        "UPDATE users SET role=? WHERE id=?",
        (req["requested_role"], req["user_id"]),
    )
    conn.commit()
    conn.close()
    return {"user_id": req["user_id"], "requested_role": req["requested_role"]}


# -- Notification preferences -------------------------------------------------


def get_notification_prefs(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, channel, enabled, endpoint FROM notification_preferences WHERE user_id=?",
        (uid,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def set_notification_pref(uid, channel, enabled, endpoint):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO notification_preferences (user_id, channel, enabled, endpoint) "
        "VALUES (?,?,?,?)",
        (uid, channel, int(bool(enabled)), endpoint or ""),
    )
    conn.commit()
    conn.close()
    return {"saved": True, "channel": channel}


# -- Account preferences (safe noise) ----------------------------------------


def get_account_preferences(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT display_name, timezone, language FROM account_preferences WHERE user_id=?",
        (uid,),
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {"display_name": "", "timezone": "UTC", "language": "en"}


def set_account_preferences(uid, display_name, timezone, language):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO account_preferences (user_id, display_name, timezone, language) "
        "VALUES (?,?,?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET "
        "display_name=excluded.display_name, timezone=excluded.timezone, language=excluded.language",
        (uid, display_name or "", timezone or "UTC", language or "en"),
    )
    conn.commit()
    conn.close()
    return {"saved": True}


# -- Audit log ----------------------------------------------------------------


def list_audit(limit=100):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, actor_id, action, target_type, target_id, detail, created_at "
        "FROM audit_log ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
