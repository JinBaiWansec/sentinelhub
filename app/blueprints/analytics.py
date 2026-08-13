"""Analytics: monitor search and advanced expression filter."""

import ast

from flask import Blueprint, request, jsonify

from app.decorators import login_required
from app.services.analytics_service import query_monitors

bp = Blueprint("analytics", __name__)


@bp.route("/api/v1/analytics/monitors/search")
@login_required
def api_analytics_search():
    q = request.args.get("q", "")
    return jsonify(query_monitors(q))


@bp.route("/api/v1/analytics/monitors/advanced", methods=["POST"])
@login_required
def api_analytics_advanced():
    data = request.get_json(force=True, silent=True) or {}
    expression = data.get("expression", "")
    try:
        # Safe: only literals are accepted by ast.literal_eval.
        result = ast.literal_eval(expression)
    except Exception as exc:  # noqa: BLE001
        result = "eval error: %s" % exc
    return jsonify({"result": result})
