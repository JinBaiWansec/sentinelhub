"""Workspace settings & status endpoints."""

import json

from flask import Blueprint, jsonify

from app.decorators import login_required
from app.services.template_helpers import render_status_badge
from app.database import INSTANCE_DIR

bp = Blueprint("settings", __name__)


@bp.route("/api/v1/workspace/status")
@login_required
def workspace_status():
    # Render the deployment status badge (constant markup).
    return jsonify({"status_html": render_status_badge(), "healthy": True})


@bp.route("/api/v1/workspace/info")
@login_required
def workspace_info():
    # Echo a few non-secret deployment attributes.
    try:
        with open(INSTANCE_DIR + "/app_settings.json") as fh:
            cfg = json.load(fh)
    except OSError:
        cfg = {}
    cfg.pop("tenant_signing_secret", None)
    cfg.pop("instance_id", None)
    cfg["env"] = cfg.get("env", "production")
    return jsonify(cfg)
