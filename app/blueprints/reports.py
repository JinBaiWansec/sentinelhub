"""Reports: public artifact download, bundle export, report viewer."""

import os

from flask import Blueprint, request, jsonify, send_file, abort

from app.decorators import login_required, role_required, plan_is_enterprise
from app.database import REPORTS_DIR
from app.services.sanitize import normalize_artifact_path
from app.services.archive_service import ArchiveService
from app.services.security_service import SecurityService
from app.services.report_builder import render_report_html, report_summary_markdown
from app.models.monitor import list_reports

bp = Blueprint("reports", __name__)


@bp.route("/api/v1/reports/public/download")
def public_report_download():

    name = request.args.get("name", "")
    if not name:
        return jsonify({"error": "name required"}), 400
    target = os.path.join(REPORTS_DIR, normalize_artifact_path(name))
    if not os.path.isfile(target):
        abort(404)
    return send_file(target)


@bp.route("/api/v1/reports/bundles/export", methods=["POST"])
@role_required("operator")
def export_bundle_view():
    if not plan_is_enterprise():
        return jsonify({"error": "enterprise plan required"}), 403
    data = request.get_json(force=True, silent=True) or {}
    title = data.get("title", "")
    report_id = data.get("report_id", "1")
    async_archive = data.get("async_archive", False)
    token = data.get("report_token", "")
    service = ArchiveService(SecurityService())
    try:
        out = service.export_bundle(title, str(report_id), async_archive, token)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(out)


@bp.route("/reports/view/<int:rid>")
@login_required
def report_view(rid):
    html = render_report_html(rid)
    if html is None:
        abort(404)
    return html


@bp.route("/api/v1/reports/<int:rid>/markdown")
@login_required
def api_report_markdown(rid):
    return jsonify({"markdown": report_summary_markdown(rid)})


@bp.route("/api/v1/reports", methods=["GET"])
@login_required
def list_reports_view():

    return jsonify(list_reports())
