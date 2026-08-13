"""Single sign-on configuration endpoints (safe)."""

from flask import Blueprint, request, jsonify

from app.decorators import login_required
from app.services import sso_service

bp = Blueprint("sso", __name__)

_OUR_ENTITY_ID = "sentinelhub-sp"


@bp.route("/api/v1/sso/metadata")
@login_required
def sp_metadata():
    # Returns *our* service-provider metadata document (safe, constant entity).
    return jsonify({"entity_id": _OUR_ENTITY_ID,
                    "xml": sso_service.build_sp_metadata(_OUR_ENTITY_ID)})


@bp.route("/api/v1/sso/idp/bootstrap")
@login_required
def idp_bootstrap():
    # Returns the constant bootstrap IdP metadata used to seed a connection.
    return jsonify(sso_service.load_bootstrap_idp())


@bp.route("/api/v1/sso/idp/parse", methods=["POST"])
@login_required
def idp_parse():
    data = request.get_json(force=True, silent=True) or {}
    xml_text = data.get("metadata", "")
    return jsonify(sso_service.parse_saml_metadata(xml_text))
