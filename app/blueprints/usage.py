"""Usage & metering endpoints (all safe)."""

from flask import Blueprint, request, jsonify

from app.decorators import login_required, current_user
from app.services import usage_service

bp = Blueprint("usage", __name__)


@bp.route("/api/v1/usage/summary")
@login_required
def usage_summary():
    return jsonify(usage_service.usage_for_user(current_user()["id"]))


@bp.route("/api/v1/usage/daily")
@login_required
def usage_daily():
    days = request.args.get("days", default=14, type=int)
    if days < 1 or days > 90:
        return jsonify({"error": "days must be between 1 and 90"}), 400
    return jsonify(usage_service.daily_active_monitors(days))


@bp.route("/api/v1/usage/platform")
@login_required
def usage_platform():
    # Operator/admins use this for the instance overview; safe read-only.
    return jsonify(usage_service.platform_totals())
