"""Static pages: dashboard, monitor search, incident notes."""

from flask import (
    Blueprint,
    request,
    render_template,
)

from app.decorators import login_required, current_user
from app.database import get_conn

bp = Blueprint("pages", __name__)


@bp.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    return render_template("dashboard.html", user=user)


@bp.route("/search")
@login_required
def search_page():
    # The visible search box uses a parameterised query (safe).
    q = request.args.get("q", "")
    rows = []
    if q:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, status FROM monitors WHERE name LIKE ? ORDER BY name",
            ("%" + q + "%",),
        )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
    return render_template("search.html", q=q, rows=rows)


@bp.route("/incidents/<int:incident_id>", methods=["GET", "POST"])
@login_required
def incident(incident_id):
    conn = get_conn()
    cur = conn.cursor()
    if request.method == "POST":
        body = request.form.get("comment", "")
        cur.execute(
            "INSERT INTO incidents (title, body, status) VALUES (?,?,?)",
            ("comment-%d" % incident_id, body, "open"),
        )
        conn.commit()
    cur.execute("SELECT id, title, body, status FROM incidents WHERE id=?", (incident_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        from flask import abort

        abort(404)
    # Notes are rendered as supplied (product choice: rich client notes).
    return render_template("incident.html", incident=dict(row))
