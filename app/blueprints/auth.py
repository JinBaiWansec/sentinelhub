"""Authentication: public status, login, registration, logout."""

from flask import (
    Blueprint,
    request,
    redirect,
    url_for,
    session,
    render_template,
    jsonify,
)

from app.services.analytics_service import list_monitors
from app.models.user import authenticate, create

bp = Blueprint("auth", __name__)


@bp.route("/")
@bp.route("/status")
def index():
    return render_template("index.html", monitors=list_monitors())


@bp.route("/api/public/status")
def public_status_api():
    return jsonify(list_monitors())


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = authenticate(username, password)
        if user:
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["plan"] = user["plan"]
            # Preserve the requested return path after login.
            nxt = request.form.get("next")
            if nxt:
                return redirect(nxt)
            return redirect(url_for("pages.dashboard"))
        return render_template("login.html", error="invalid credentials")
    return render_template("login.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email", "")
        if not username or not password:
            return render_template("register.html", error="username and password required")
        uid = create(username, password, email)
        if uid is None:
            return render_template("register.html", error="username taken")
        session["user_id"] = uid
        session["role"] = "member"
        session["plan"] = "free"
        return redirect(url_for("pages.dashboard"))
    return render_template("register.html")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.index"))
