"""Integrations: creation, render-mode toggle, alert sync, connectivity probe."""

from flask import Blueprint, request, jsonify, abort

from app.decorators import login_required, role_required, current_user, plan_is_enterprise
from app.models.monitor import (
    get_integration,
    create_integration,
    update_integration,
    list_integrations,
)
from app.services.alert_engine import AlertEngine
from app.services.fetch_remote import synchronize_external_source

bp = Blueprint("integrations", __name__)


@bp.route("/api/v1/integrations", methods=["POST"])
@role_required("operator")
def create_integration_view():
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name", "Unnamed integration")
    iid = create_integration(name, current_user()["id"])
    return jsonify({"id": iid, "render_mode": "modern"})


@bp.route("/api/v1/integrations", methods=["GET"])
@role_required("operator")
def list_integrations_view():

    return jsonify(list_integrations(owner_id=current_user()["id"]))


@bp.route("/api/v1/integrations/<int:iid>", methods=["PATCH"])
@role_required("operator")
def patch_integration_view(iid):
    data = request.get_json(force=True, silent=True) or {}
    integ = get_integration(iid)
    if not integ or integ["owner_id"] != current_user()["id"]:
        abort(403)

    if "render_mode" in data:
        update_integration(iid, render_mode=data["render_mode"])
    if "active" in data:
        update_integration(iid, active=data["active"])
    return jsonify({"updated": True})


@bp.route("/api/v1/integrations/<int:iid>/sync", methods=["POST"])
@role_required("operator")
def integration_sync_view(iid):
    if not plan_is_enterprise():
        return jsonify({"error": "enterprise plan required for alert sync"}), 403
    data = request.get_json(force=True, silent=True) or {}
    blueprint = data.get("custom_payload_blueprint", "")
    integ = get_integration(iid)
    if not integ or integ["owner_id"] != current_user()["id"]:
        abort(403)

    if integ["render_mode"] != "legacy":
        return jsonify({"error": "legacy render mode required"}), 400
    # Hand the blueprint to the alert engine, which decides whether to dispatch
    # it to the worker (legacy only).
    engine = AlertEngine()
    return jsonify(engine.build_and_enqueue(blueprint, integ))


@bp.route("/api/v1/integrations/<int:iid>/probe", methods=["POST"])
@login_required
def integration_probe_view(iid):

    data = request.get_json(force=True, silent=True) or {}
    url = data.get("url", "")
    if not url:
        return jsonify({"error": "url required"}), 400
    try:
        resp = synchronize_external_source(url)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    try:
        return jsonify({"status": resp.status_code, "body": resp.text[:2000]})
    except Exception:  # noqa: BLE001
        return jsonify({"status": getattr(resp, "status_code", 200)})
