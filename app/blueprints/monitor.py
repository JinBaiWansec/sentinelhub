"""Monitor thresholds + dashboard widgets."""

from flask import Blueprint, request, jsonify

from app.decorators import login_required, current_user
from app.models.monitor import (
    get_monitor_thresholds,
    set_monitor_threshold,
    acknowledge_monitor,
)
from app.services.metrics import summary_for_user, incident_resolution_rate

bp = Blueprint("monitor", __name__)


@bp.route("/api/v1/monitors/thresholds", methods=["GET", "PUT"])
@login_required
def monitor_thresholds():
    if request.method == "PUT":
        data = request.get_json(force=True, silent=True) or {}
        mid = data.get("monitor_id")
        if not mid:
            return jsonify({"error": "monitor_id required"}), 400
        tid = set_monitor_threshold(
            mid,
            data.get("metric", "latency_ms"),
            data.get("operator", "<"),
            data.get("threshold", 200.0),
            data.get("enabled", True),
        )
        return jsonify({"id": tid, "saved": True})
    monitor_id = request.args.get("monitor_id", type=int)
    if not monitor_id:
        return jsonify({"error": "monitor_id required"}), 400
    return jsonify(get_monitor_thresholds(monitor_id))


@bp.route("/api/v1/monitors/<int:monitor_id>/ack", methods=["POST"])
@login_required
def acknowledge(monitor_id):
    # Safe: operator acknowledgement of a monitor alert.
    return jsonify(acknowledge_monitor(monitor_id))


@bp.route("/api/v1/dashboard/widgets")
@login_required
def dashboard_widgets():
    # Safe: aggregate widgets for the operator dashboard.
    summary = summary_for_user(current_user()["id"])
    return jsonify({
        "monitor_count": summary.get("monitor_count"),
        "monitors": summary.get("monitors"),
        "incident_resolution_rate": incident_resolution_rate(),
    })
