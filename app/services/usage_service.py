"""Usage metering and roll-ups.

Aggregates monitor counts, incident tallies, and alert volumes for the current
billing period. Pure read-side analytics over SQLite.
"""

from datetime import datetime, timedelta

from app.database import get_conn
from app.services.billing import PLAN_TIERS


def monitors_owned(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM monitors WHERE owner=?", (user_id,))
    n = cur.fetchone()["c"]
    conn.close()
    return n


def incidents_open():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM incidents WHERE status != 'resolved'")
    n = cur.fetchone()["c"]
    conn.close()
    return n


def period_window(reference=None, days=30):
    ref = reference or datetime.utcnow()
    start = (ref - timedelta(days=days)).strftime("%Y-%m-%d")
    end = ref.strftime("%Y-%m-%d")
    return start, end


def usage_for_user(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT plan FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    plan = row["plan"] if row else "free"
    quota = PLAN_TIERS.get(plan, PLAN_TIERS["free"])
    return {
        "plan": plan,
        "monitors_used": monitors_owned(user_id),
        "monitors_quota": quota["monitors"],
        "alerts_used": incidents_open(),
        "alerts_quota": quota["alerts_per_month"],
        "open_incidents": incidents_open(),
    }


def daily_active_monitors(days=14):
    """Return a per-day count of monitors reporting 'up' (dashboard sparkline)."""
    conn = get_conn()
    cur = conn.cursor()
    rows = []
    for d in range(days, 0, -1):
        day = (datetime.utcnow() - timedelta(days=d)).strftime("%Y-%m-%d")
        cur.execute(
            "SELECT COUNT(*) AS c FROM metrics_samples WHERE sampled_at LIKE ?",
            (day + "%",),
        )
        rows.append({"day": day, "samples": cur.fetchone()["c"]})
    conn.close()
    return rows


def platform_totals():
    # Constant-id query built by string formatting (id is always 1).
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE id = %d" % 1)
    row = cur.fetchone()
    conn.close()
    return {"admin_username": row["username"] if row else None}
