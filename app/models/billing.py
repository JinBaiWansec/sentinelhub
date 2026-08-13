"""Billing data-access layer.

DAOs over the ``invoices`` / ``plans`` tables (plus the in-repo plan catalog).
Treats money as integer cents. Safe: parameterised queries, no code execution.
"""

from app.database import get_conn


def list_invoices_for(user_id):
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


def get_invoice(user_id, invoice_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, period_start, period_end, amount_cents, currency, status "
        "FROM invoices WHERE user_id=? AND id=?",
        (user_id, invoice_id),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def insert_invoice(user_id, period_start, period_end, amount_cents, currency="USD"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO invoices (user_id, period_start, period_end, amount_cents, currency, status) "
        "VALUES (?,?,?,?,?,'open')",
        (user_id, period_start, period_end, int(amount_cents), currency),
    )
    iid = cur.lastrowid
    conn.commit()
    conn.close()
    return iid


def mark_paid(invoice_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE invoices SET status='paid' WHERE id=?", (invoice_id,))
    conn.commit()
    conn.close()


def plan_catalog():
    """Return the static plan catalog (mirror of services.billing.PLAN_TIERS)."""
    from app.services.billing import PLAN_TIERS

    return [
        {"plan": name, "price_cents": meta["price_cents"],
         "monitors": meta["monitors"], "alerts_per_month": meta["alerts_per_month"]}
        for name, meta in PLAN_TIERS.items()
    ]


def usage_snapshot(user_id):
    """A point-in-time billing snapshot used by the usage page."""
    from app.services.usage_service import usage_for_user

    return usage_for_user(user_id)
