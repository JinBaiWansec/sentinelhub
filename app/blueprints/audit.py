"""Audit log read endpoint (operator-only, safe)."""

from flask import Blueprint, jsonify

from app.decorators import role_required
from app.models.user import list_audit

bp = Blueprint("audit", __name__)


@bp.route("/api/v1/audit/log")
@role_required("operator")
def api_audit_log():
    return jsonify(list_audit())
