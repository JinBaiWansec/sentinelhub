"""Internal dispatch queue (loopback + signature)."""

from flask import Blueprint, request, jsonify, abort

import hmac

from app.workers.alert_worker import job_queue, JOB_RESULTS
from app.services.security_service import SecurityService

bp = Blueprint("dispatch", __name__)


@bp.route("/api/internal/dispatch/queue", methods=["POST"])
def internal_dispatch():
    if request.remote_addr not in ("127.0.0.1", "::1", "::ffff:127.0.0.1"):
        abort(403)
    data = request.get_json(force=True, silent=True) or {}
    job_id = data.get("job_id")
    sig = data.get("signature", "")
    if not hmac.compare_digest(SecurityService().dispatch_signature(job_id), sig or ""):
        abort(403)
    job_queue.put({"kind": "compose_alert", "job_id": job_id})
    return jsonify({"queued": True})


@bp.route("/api/internal/dispatch/output", methods=["GET"])
def internal_dispatch_output():
    if request.remote_addr not in ("127.0.0.1", "::1", "::ffff:127.0.0.1"):
        abort(403)
    return jsonify(JOB_RESULTS)
