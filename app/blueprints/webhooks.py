"""Webhook configuration endpoints (all safe)."""

from flask import Blueprint, request, jsonify

from app.decorators import login_required, current_user
from app.services import webhook_service
from app.services.notifications import dispatch_notification
from app.utils.validators import is_nonempty

bp = Blueprint("webhooks", __name__)


@bp.route("/api/v1/webhooks")
@login_required
def list_webhooks():
    return jsonify(webhook_service.list_webhooks())


@bp.route("/api/v1/webhooks/<int:wid>")
@login_required
def get_webhook(wid):
    wh = webhook_service.get_webhook(wid)
    if not wh:
        return jsonify({"error": "webhook not found"}), 404
    return jsonify(wh)


@bp.route("/api/v1/webhooks", methods=["POST"])
@login_required
def create_webhook():
    data = request.get_json(force=True, silent=True) or {}
    ok, msg = is_nonempty(data.get("channel"), "channel")
    if not ok:
        return jsonify({"error": msg}), 400
    created = webhook_service.create_webhook(
        data["channel"],
        data.get("format_template", ""),
        bool(data.get("allow_custom_format", False)),
    )
    return jsonify(created), 201


@bp.route("/api/v1/webhooks/<int:wid>/test", methods=["POST"])
@login_required
def test_webhook(wid):
    wh = webhook_service.get_webhook(wid)
    if not wh:
        return jsonify({"error": "webhook not found"}), 404
    # Fire a delivery against the operator-configured endpoint.
    result = dispatch_notification(
        wh["channel"],
        "https://hooks.sentinel.local/%s" % wh["token"],
        "SentinelHub webhook test",
        "This is a test delivery from SentinelHub.",
    )
    webhook_service.record_delivery(wid, str(result.get("status")), str(result))
    return jsonify({"delivered": True, "result": result})


@bp.route("/api/v1/webhooks/<int:wid>/deliveries")
@login_required
def webhook_deliveries(wid):
    return jsonify(webhook_service.recent_deliveries(wid))
