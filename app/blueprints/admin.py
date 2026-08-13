"""Administration console: snapshot restore, template preview, state restore."""

import json

from flask import Blueprint, request, jsonify, abort, render_template

from jinja2.sandbox import SandboxedEnvironment

from app.decorators import login_required, role_required
from app.services.snapshot_manager import TenantSnapshotManager, InvalidSignatureError
from app.services.security_service import SecurityService

bp = Blueprint("admin", __name__)


@bp.route("/administration")
@role_required("admin")
def console():
    return render_template("admin.html")


@bp.route("/api/v1/administration/templates/preview", methods=["POST"])
@role_required("operator")
def template_preview():

    data = request.get_json(force=True, silent=True) or {}
    env = SandboxedEnvironment()
    try:
        rendered = env.from_string(data.get("template", "")).render(**(data.get("context") or {}))
    except Exception as exc:  # noqa: BLE001
        rendered = "sandbox error: %s" % exc
    return jsonify({"preview": rendered})


@bp.route("/api/v1/administration/snapshots/restore", methods=["POST"])
@role_required("admin")
def restore_snapshot_view():
    data = request.get_json(force=True, silent=True) or {}
    manager = TenantSnapshotManager(SecurityService())
    try:
        result = manager.import_tenant_snapshot(
            data.get("snapshot"),
            data.get("signature"),
        )
    except InvalidSignatureError:
        abort(403, "invalid snapshot signature")
    return jsonify(result)


@bp.route("/api/v1/state/restore", methods=["POST"])
@login_required
def state_restore():

    data = request.get_json(force=True, silent=True) or {}
    state = data.get("state", "")
    try:
        raw = json.loads(state)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": "invalid state: %s" % exc}), 400
    return jsonify({"restored": raw})
