"""Feature-flag endpoints (safe)."""

from flask import Blueprint, jsonify

from app.decorators import login_required, current_user
from app.services import feature_flags as ff

bp = Blueprint("feature_flags", __name__)


@bp.route("/api/v1/feature-flags")
@login_required
def my_flags():
    plan = current_user().get("plan", "free")
    return jsonify({"plan": plan, "flags": ff.evaluate_flags(plan)})


@bp.route("/api/v1/feature-flags/catalog")
@login_required
def flags_catalog():
    return jsonify(ff.catalog())
