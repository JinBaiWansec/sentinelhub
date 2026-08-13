"""Team: role requests, approvals, and member roster."""

from flask import Blueprint, request, session, jsonify

from app.decorators import login_required, role_required, current_user
from app.database import get_conn, record_audit
from app.models.user import (
    create_role_request,
    get_role_request,
    approve_role_request,
)

bp = Blueprint("team", __name__)


@bp.route("/api/v1/team/role-requests", methods=["POST"])
@login_required
def create_role_request_view():
    data = request.get_json(force=True, silent=True) or {}
    requested_role = data.get("requested_role", "operator")
    if requested_role not in ("operator", "admin"):
        return jsonify({"error": "invalid role"}), 400
    rid = create_role_request(current_user()["id"], requested_role)
    return jsonify({"id": rid, "status": "pending"})


@bp.route("/api/v1/team/role-requests/<int:rid>/approve", methods=["POST"])
@login_required
def approve_role_request_view(rid):
    data = request.get_json(force=True, silent=True) or {}

    approver_id = data.get("approver_id", current_user()["id"])
    req = get_role_request(rid)
    if not req or req["status"] != "pending":
        return jsonify({"error": "request not pending"}), 400
    result = approve_role_request(rid, approver_id)
    if result and result["user_id"] == current_user()["id"]:
        session["role"] = result["requested_role"]
    record_audit(
        current_user()["id"],
        "role_approve",
        "role_request",
        rid,
        result["requested_role"] if result else "unknown",
    )
    return jsonify({"approved": True, "role": result["requested_role"] if result else None})


@bp.route("/api/v1/team/members")
@role_required("operator")
def list_members():

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, username, role, plan FROM users ORDER BY id")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows)
