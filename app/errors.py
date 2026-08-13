"""Unified error envelope with content negotiation.

API clients (``/api/*``, ``Accept: application/json``, or an XHR) receive the
standard JSON shape ``{"error": ..., "message": ...}`` so automated scripts can
rely on ``response.json()["error"]`` instead of scraping Flask's default HTML
error pages. Browser navigations still receive Flask's normal HTML error pages,
so clicking around the dashboard does not show raw JSON.

This is purely a presentation concern: it changes no authorization decision and
preserves the original HTTP status code.
"""

import logging

from flask import jsonify, request, render_template_string

log = logging.getLogger("sentinelhub.errors")


_HTML_404 = """<!doctype html>
<html lang="en">
<head><title>Page not found — SentinelHub</title></head>
<body style="font-family:system-ui,sans-serif;max-width:640px;margin:4rem auto;padding:0 1rem;color:#111">
  <h1>404 — Not Found</h1>
  <p>The page you requested could not be found.</p>
  <p><a href="/dashboard">Back to dashboard</a></p>
</body>
</html>
"""

_HTML_ERROR = """<!doctype html>
<html lang="en">
<head><title>Error — SentinelHub</title></head>
<body style="font-family:system-ui,sans-serif;max-width:640px;margin:4rem auto;padding:0 1rem;color:#111">
  <h1>%(status)d — %(error)s</h1>
  <p>%(message)s</p>
  <p><a href="/dashboard">Back to dashboard</a></p>
</body>
</html>
"""


def _wants_json():
    """Return True when the client should receive a JSON error body."""
    # All API routes always speak JSON.
    if request.path.startswith("/api/"):
        return True
    # Explicit JSON preference or AJAX request.
    accept = request.headers.get("Accept", "")
    if "application/json" in accept:
        return True
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return True
    # Content-Type on the request body suggests an API client.
    ctype = request.headers.get("Content-Type", "")
    if "application/json" in ctype:
        return True
    return False


def _json_envelope(status, error, message):
    return jsonify({"error": error, "message": message}), status


def _html_error(status, error, message):
    if status == 404:
        return render_template_string(_HTML_404), status
    return render_template_string(_HTML_ERROR % {
        "status": status,
        "error": error,
        "message": message,
    }), status


def _respond(status, error, message):
    if _wants_json():
        return _json_envelope(status, error, message)
    return _html_error(status, error, message)


def register_error_handlers(app):
    """Attach content-aware error handlers to the application."""

    @app.errorhandler(400)
    def bad_request(err):
        return _respond(400, "BadRequest",
                        "The server could not understand the request.")

    @app.errorhandler(401)
    def unauthorized(err):
        return _respond(401, "Unauthorized",
                        "Authentication is required to access this resource.")

    @app.errorhandler(403)
    def forbidden(err):
        # ``abort(403, "reason")`` stores the reason on ``description``.
        msg = getattr(err, "description", None) or \
            "You do not have permission to perform this action."
        return _respond(403, "Forbidden", str(msg))

    @app.errorhandler(404)
    def not_found(err):
        return _respond(404, "NotFound",
                        "The requested resource could not be found.")

    @app.errorhandler(405)
    def method_not_allowed(err):
        return _respond(405, "MethodNotAllowed",
                        "The request method is not allowed for this resource.")

    @app.errorhandler(429)
    def too_many_requests(err):
        return _respond(429, "TooManyRequests",
                        "Rate limit exceeded. Please retry later.")

    @app.errorhandler(500)
    def internal_error(err):
        log.exception("unhandled server error")
        return _respond(500, "InternalServerError",
                        "An unexpected error occurred on the server.")

    @app.errorhandler(Exception)
    def unhandled_exception(err):
        # Catch-all for non-HTTP exceptions; keeps the wire format consistent.
        log.exception("unhandled exception")
        return _respond(500, "InternalServerError",
                        "An unexpected error occurred on the server.")
