"""Request guards and current-identity helpers.

These wrap the Flask ``session`` so view functions can declare their access
requirement with a single decorator. The role ladder is intentionally coarse:
a viewer < member < operator < admin ordering used by ``role_required``.
"""

from functools import wraps

from flask import session, redirect, url_for, abort

from app.database import get_conn

ROLE_LEVEL = {"viewer": 1, "member": 2, "operator": 3, "admin": 4}


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login", next=request_endpoint()))
        return view(*args, **kwargs)

    return wrapper


def role_required(min_role):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("auth.login"))
            if ROLE_LEVEL.get(session.get("role"), 0) < ROLE_LEVEL[min_role]:
                abort(403)
            return view(*args, **kwargs)

        return wrapper

    return decorator


def request_endpoint():
    from flask import request

    return request.endpoint


def current_user():
    if "user_id" not in session:
        return None
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, role, plan, email FROM users WHERE id=?",
        (session["user_id"],),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def plan_is_enterprise():
    user = current_user()
    return bool(user and user.get("plan") == "enterprise")
