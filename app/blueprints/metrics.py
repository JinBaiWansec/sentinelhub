"""Metrics dashboards and chart endpoints (all safe)."""

from flask import Blueprint, request, render_template, jsonify

from app.decorators import login_required, current_user
from app.services.metrics import summary_for_user, build_timeseries_points, uptime_percentage

bp = Blueprint("metrics", __name__)


@bp.route("/metrics/dashboard")
@login_required
def metrics_dashboard():
    return render_template(
        "metrics_dashboard.html",
        summary=summary_for_user(current_user()["id"]),
    )


@bp.route("/api/v1/metrics/summary")
@login_required
def api_metrics_summary():
    return jsonify(summary_for_user(current_user()["id"]))


@bp.route("/api/v1/metrics/timeseries")
@login_required
def api_metrics_timeseries():
    monitor_id = request.args.get("monitor_id", type=int)
    days = request.args.get("days", default=7, type=int)
    if not monitor_id:
        return jsonify({"error": "monitor_id required"}), 400
    return jsonify({"points": build_timeseries_points(monitor_id, days)})


@bp.route("/api/v1/metrics/top")
@login_required
def api_metrics_top():
    # Safe: ranking of owned monitors by uptime for the dashboard widget.
    summary = summary_for_user(current_user()["id"])
    ranked = sorted(
        summary.get("monitors", []),
        key=lambda m: m.get("uptime", 0),
        reverse=True,
    )
    return jsonify(ranked[:10])
