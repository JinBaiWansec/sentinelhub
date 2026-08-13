"""Notification fan-out.

Formats alert messages and delivers them to stored endpoints. Templates are
rendered through the Jinja sandboxed environment.
"""

import requests

from jinja2.sandbox import SandboxedEnvironment

from app.database import get_conn


_sandbox = SandboxedEnvironment()


def format_alert_message(template, context):
    """Format a message with sandboxed Jinja."""
    try:
        return _sandbox.from_string(template or "").render(**(context or {}))
    except Exception as exc:  # noqa: BLE001 - return a safe error string
        return "format error: %s" % exc


def get_preferences(user_id):
    from app.models.user import get_notification_prefs

    return get_notification_prefs(user_id)


def set_preference(user_id, channel, enabled, endpoint):
    from app.models.user import set_notification_pref

    return set_notification_pref(user_id, channel, enabled, endpoint)


def dispatch_notification(channel, endpoint, subject, body):
    """Push a rendered message to a stored endpoint.

    The endpoint is operator-configured.
    """
    if channel == "webhook":
        try:
            resp = requests.post(endpoint, json={"subject": subject, "body": body}, timeout=5)
            return {"channel": channel, "status": resp.status_code}
        except Exception as exc:  # noqa: BLE001
            return {"channel": channel, "error": str(exc)}
    if channel == "slack":
        try:
            resp = requests.post(endpoint, json={"text": "%s\n%s" % (subject, body)}, timeout=5)
            return {"channel": channel, "status": resp.status_code}
        except Exception as exc:  # noqa: BLE001
            return {"channel": channel, "error": str(exc)}
    return {"channel": channel, "status": "noop"}


def channel_catalog():
    """List the notification channels the product supports."""
    return [
        {"channel": "webhook", "label": "Webhook (generic HTTP POST)"},
        {"channel": "slack", "label": "Slack incoming webhook"},
        {"channel": "email", "label": "Email (SMTP)"},
    ]
