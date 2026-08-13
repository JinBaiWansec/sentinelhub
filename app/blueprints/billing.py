"""Billing: trial-code redemption, invoice and usage views."""

from datetime import date

from flask import Blueprint, request, render_template, jsonify

from app.decorators import login_required, current_user
from app.database import get_conn, record_audit
from app.models.user import set_plan
from app.services.billing import (
    list_invoices,
    compute_usage,
    PLAN_TIERS,
    generate_invoice,
    invoice_to_text,
    plan_entitlements,
)

bp = Blueprint("billing", __name__)


@bp.route("/api/v1/billing/trials/redeem", methods=["POST"])
@login_required
def redeem_trial():
    data = request.get_json(force=True, silent=True) or {}
    code = data.get("code", "")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT code FROM trial_codes WHERE code=? AND claimed=0", (code,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "invalid or already claimed trial code"}), 400
    cur.execute("UPDATE users SET plan='enterprise' WHERE id=?", (current_user()["id"],))
    cur.execute(
        "UPDATE trial_codes SET claimed=0, claimed_by=? WHERE code=?",
        (current_user()["id"], code),
    )
    conn.commit()
    conn.close()
    session_plan = "enterprise"
    # Mirror into the session so downstream plan checks see the upgrade.
    from flask import session

    session["plan"] = session_plan
    record_audit(current_user()["id"], "trial_redeem", "user", current_user()["id"], code)
    return jsonify({"plan": "enterprise"})


@bp.route("/billing")
@login_required
def billing_page():
    user = current_user()
    return render_template(
        "billing.html",
        invoices=list_invoices(user["id"]),
        usage=compute_usage(user["id"]),
        tiers=PLAN_TIERS,
    )


@bp.route("/api/v1/billing/invoices")
@login_required
def api_billing_invoices():
    return jsonify(list_invoices(current_user()["id"]))


@bp.route("/api/v1/billing/usage")
@login_required
def api_billing_usage():
    return jsonify(compute_usage(current_user()["id"]))


@bp.route("/api/v1/billing/plans")
@login_required
def api_billing_plans():
    return jsonify(PLAN_TIERS)


@bp.route("/api/v1/billing/entitlements")
@login_required
def api_billing_entitlements():
    # Safe: returns the caller's own plan quotas.
    return jsonify(plan_entitlements(current_user()["id"]))


@bp.route("/api/v1/billing/preview", methods=["POST"])
@login_required
def api_billing_preview():
    data = request.get_json(force=True, silent=True) or {}
    try:
        start = date.fromisoformat(data.get("period_start", "2026-07-01"))
        end = date.fromisoformat(data.get("period_end", "2026-07-31"))
    except Exception:  # noqa: BLE001
        return jsonify({"error": "bad date"}), 400
    inv = generate_invoice(current_user()["id"], start, end)
    return jsonify({"text": invoice_to_text(inv), "invoice": inv})
