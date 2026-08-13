"""Notifications: preferences, safe preview, channel catalog, webhook test."""

from flask import Blueprint, request, render_template, jsonify

from app.decorators import login_required, current_user
from app.database import record_audit
from app.services.notifications import (
    get_preferences,
    set_preference,
    format_alert_message,
    dispatch_notification,
    channel_catalog,
)
from app.models.user import get_notification_prefs

bp = Blueprint("notifications", __name__)


@bp.route("/notifications")
@login_required
def notifications_page():
    return render_template(
        "notifications.html",
        prefs=get_preferences(current_user()["id"]),
    )


@bp.route("/api/v1/notifications/preferences", methods=["GET", "POST"])
@login_required
def api_notifications_prefs():
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        out = set_preference(
            current_user()["id"],
            data.get("channel", "webhook"),
            data.get("enabled", True),
            data.get("endpoint", ""),
        )
        record_audit(
            current_user()["id"],
            "notification_pref_update",
            "notification",
            0,
            data.get("channel", ""),
        )
        return jsonify(out)
    return jsonify(get_preferences(current_user()["id"]))


@bp.route("/api/v1/notifications/preview", methods=["POST"])
@login_required
def api_notifications_preview():
    # Rendered through the sandboxed formatter in the notifications service.
    data = request.get_json(force=True, silent=True) or {}
    rendered = format_alert_message(data.get("template", ""), data.get("context") or {})
    return jsonify({"preview": rendered})


@bp.route("/api/v1/notifications/channels")
@login_required
def api_notifications_channels():
    # Safe: list the channels the product supports.
    return jsonify(channel_catalog())


@bp.route("/api/v1/notifications/webhook/test", methods=["POST"])
@login_required
def api_notifications_webhook_test():
    # Safe: fires a test alert to the caller's *stored* webhook endpoint (not an
    # arbitrary user-supplied URL), so it is not an SSRF surface.
    prefs = get_notification_prefs(current_user()["id"])
    endpoint = None
    for p in prefs:
        if p.get("channel") == "webhook" and p.get("enabled"):
            endpoint = p.get("endpoint")
            break
    if not endpoint:
        return jsonify({"error": "no enabled webhook configured"}), 400
    result = dispatch_notification(
        "webhook",
        endpoint,
        "SentinelHub test",
        "This is a test notification from SentinelHub.",
    )
    return jsonify(result)
