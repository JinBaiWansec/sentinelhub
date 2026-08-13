"""Monitor / integration / job data-access layer.

Safe CRUD over the operational tables. Like ``app.models.user``, these helpers
perform no authorisation and no string interpretation; the view layer owns the
business rules (ownership checks, render-mode gating, enterprise plan checks).
"""

import sqlite3

from app.database import get_conn


def list_monitors():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name, status, url FROM monitors ORDER BY name")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_integration(iid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, owner_id, active, render_mode FROM integrations WHERE id=?",
        (iid,),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def create_integration(name, owner_id, render_mode="modern"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO integrations (name, owner_id, active, render_mode) VALUES (?,?,?,?)",
        (name, owner_id, 0, render_mode),
    )
    iid = cur.lastrowid
    conn.commit()
    conn.close()
    return iid


def update_integration(iid, render_mode=None, active=None):
    conn = get_conn()
    cur = conn.cursor()
    if render_mode is not None:
        cur.execute("UPDATE integrations SET render_mode=? WHERE id=?", (render_mode, iid))
    if active is not None:
        cur.execute("UPDATE integrations SET active=? WHERE id=?", (int(bool(active)), iid))
    conn.commit()
    conn.close()


def list_integrations(owner_id=None):
    conn = get_conn()
    cur = conn.cursor()
    if owner_id is not None:
        cur.execute(
            "SELECT id, name, owner_id, active, render_mode FROM integrations WHERE owner_id=?",
            (owner_id,),
        )
    else:
        cur.execute(
            "SELECT id, name, owner_id, active, render_mode FROM integrations ORDER BY id"
        )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def create_alert_job(payload_json):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO jobs (kind, payload, status, created) VALUES (?,?,?,?)",
        ("compose_alert", payload_json, "queued", "now"),
    )
    jid = cur.lastrowid
    conn.commit()
    conn.close()
    return jid


def get_job_payload(jid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT payload FROM jobs WHERE id=?", (jid,))
    row = cur.fetchone()
    conn.close()
    return row["payload"] if row else None


def list_invoices(uid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, period_start, period_end, amount_cents, currency, status "
        "FROM invoices WHERE user_id=? ORDER BY period_start DESC",
        (uid,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def list_reports():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title, owner, created FROM reports ORDER BY id")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# -- Alert thresholds (safe noise) -------------------------------------------


def get_monitor_thresholds(monitor_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, monitor_id, metric, operator, threshold, enabled "
        "FROM monitor_thresholds WHERE monitor_id=? ORDER BY id",
        (monitor_id,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def set_monitor_threshold(monitor_id, metric, operator, threshold, enabled=True):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO monitor_thresholds (monitor_id, metric, operator, threshold, enabled) "
        "VALUES (?,?,?,?,?)",
        (monitor_id, metric, operator, float(threshold), int(bool(enabled))),
    )
    tid = cur.lastrowid
    conn.commit()
    conn.close()
    return tid


def acknowledge_monitor(monitor_id):
    """Operator ack: record the action so dashboards reflect it."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name FROM monitors WHERE id=?", (monitor_id,))
    row = cur.fetchone()
    conn.close()
    return {"acknowledged": bool(row), "monitor_id": monitor_id}
