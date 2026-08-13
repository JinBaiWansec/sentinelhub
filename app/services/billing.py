"""Billing and subscription accounting.

Computes usage, prorates charges, and renders invoices as plain text. All money
is handled as integer cents to avoid float drift.
"""

from datetime import date

from app.database import get_conn


PLAN_TIERS = {
    "free": {"price_cents": 0, "monitors": 3, "alerts_per_month": 100},
    "pro": {"price_cents": 2900, "monitors": 25, "alerts_per_month": 5000},
    "enterprise": {"price_cents": 9900, "monitors": 500, "alerts_per_month": 100000},
}


def plan_quota(plan):
    return PLAN_TIERS.get(plan, PLAN_TIERS["free"])


def compute_usage(user_id):
    """Count monitors and approximate alert volume for the current period."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM monitors WHERE owner=?", (user_id,))
    monitor_count = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM incidents")
    alert_count = cur.fetchone()["c"]
    conn.close()
    quota = plan_quota("free")
    return {
        "monitors_used": monitor_count,
        "monitors_quota": quota["monitors"],
        "alerts_used": alert_count,
        "alerts_quota": quota["alerts_per_month"],
    }


def prorate(amount_cents, days_elapsed, period_days=30):
    if period_days <= 0:
        return amount_cents
    return int(round(amount_cents * days_elapsed / float(period_days)))


def generate_invoice(user_id, period_start, period_end):
    """Build a line-item invoice for the given period (dict, not persisted)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT plan FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    plan = row["plan"] if row else "free"
    tier = plan_quota(plan)
    days = max(1, (period_end - period_start).days)
    line_items = [
        {
            "description": "Subscription: %s" % plan,
            "amount_cents": prorate(tier["price_cents"], days),
        },
    ]
    total = sum(li["amount_cents"] for li in line_items)
    return {
        "user_id": user_id,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "currency": "USD",
        "total_cents": total,
        "line_items": line_items,
    }


def invoice_to_text(invoice):
    """Render an invoice as a plain-text receipt (no HTML, safe)."""
    lines = []
    lines.append("SentinelHub invoice")
    lines.append("Period: %s -> %s" % (invoice["period_start"], invoice["period_end"]))
    lines.append("Currency: %s" % invoice["currency"])
    lines.append("-" * 32)
    for li in invoice["line_items"]:
        lines.append("%-24s %8.2f" % (li["description"][:24], li["amount_cents"] / 100.0))
    lines.append("-" * 32)
    lines.append("%-24s %8.2f" % ("TOTAL", invoice["total_cents"] / 100.0))
    return "\n".join(lines)


def list_invoices(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, period_start, period_end, amount_cents, currency, status "
        "FROM invoices WHERE user_id=? ORDER BY period_start DESC",
        (user_id,),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def plan_entitlements(user_id):
    """Return the current plan's quotas for the entitlements endpoint."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT plan FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    plan = row["plan"] if row else "free"
    quota = plan_quota(plan)
    return {
        "plan": plan,
        "monitors": quota["monitors"],
        "alerts_per_month": quota["alerts_per_month"],
    }
