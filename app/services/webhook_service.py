"""Webhook delivery bookkeeping.

Tracks configured outbound webhooks and their recent delivery attempts. The
actual HTTP POST is delegated to ``app.services.notifications``.
"""

import secrets

from app.database import get_conn


def list_webhooks():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, token, channel, format_template, allow_custom_format "
        "FROM webhooks ORDER BY id"
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def create_webhook(channel, format_template, allow_custom_format=False):
    token = "wh-" + secrets.token_hex(12)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO webhooks (token, channel, format_template, allow_custom_format) "
        "VALUES (?,?,?,?)",
        (token, channel, format_template or "", int(bool(allow_custom_format))),
    )
    wid = cur.lastrowid
    conn.commit()
    conn.close()
    return {"id": wid, "token": token, "channel": channel}


def get_webhook(wid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, token, channel, format_template, allow_custom_format "
        "FROM webhooks WHERE id=?",
        (wid,),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def record_delivery(wid, status, detail):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO webhook_deliveries (webhook_id, status, detail, created_at) "
        "VALUES (?,?,?, datetime('now'))",
        (wid, status, detail or ""),
    )
    conn.commit()
    conn.close()


def recent_deliveries(wid, limit=20):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, status, detail, created_at FROM webhook_deliveries "
        "WHERE webhook_id=? ORDER BY id DESC LIMIT ?",
        (wid, limit),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
