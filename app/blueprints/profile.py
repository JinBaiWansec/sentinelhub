"""Profile: email updates + account preferences."""

from flask import Blueprint, request, redirect, url_for, render_template, jsonify

from app.decorators import login_required, current_user
from app.database import record_audit
from app.models.user import (
    update_email,
    get_account_preferences,
    set_account_preferences,
)

bp = Blueprint("profile", __name__)


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile_page():
    if request.method == "POST":
        update_email(current_user()["id"], request.form.get("email", ""))
        record_audit(
            current_user()["id"],
            "profile_update",
            "user",
            current_user()["id"],
            request.form.get("timezone", "UTC"),
        )
        return redirect(url_for("profile.profile_page"))
    return render_template("profile.html", user=current_user())


@bp.route("/api/v1/profile", methods=["GET", "POST"])
@login_required
def api_profile():
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        update_email(current_user()["id"], data.get("email", ""))
        record_audit(
            current_user()["id"],
            "profile_update_api",
            "user",
            current_user()["id"],
            "",
        )
        return jsonify({"ok": True})
    return jsonify(current_user() or {})


@bp.route("/api/v1/account/preferences", methods=["GET", "PUT"])
@login_required
def api_account_preferences():
    if request.method == "PUT":
        data = request.get_json(force=True, silent=True) or {}
        set_account_preferences(
            current_user()["id"],
            data.get("display_name", ""),
            data.get("timezone", "UTC"),
            data.get("language", "en"),
        )
        return jsonify({"saved": True})
    return jsonify(get_account_preferences(current_user()["id"]))
