"""Input validators used across view layers.

These helpers centralise the boring checks (email shape, URL scheme, plan
names, threshold operators) so every blueprint validates the same way. They
return ``(ok, message)`` tuples rather than raising, which keeps the call sites
readable. None of them interpret input as code.
"""

import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
URL_RE = re.compile(r"^https?://", re.IGNORECASE)

VALID_PLANS = ("free", "pro", "enterprise")
VALID_ROLES = ("viewer", "member", "operator", "admin")
VALID_OPERATORS = ("<", "<=", ">", ">=", "==")
VALID_TIMEZONES = (
    "UTC", "America/New_York", "America/Los_Angeles",
    "Europe/London", "Europe/Berlin", "Asia/Tokyo", "Asia/Shanghai",
)
VALID_LANGUAGES = ("en", "es", "de", "fr", "zh", "ja")


def is_nonempty(value, field="value", min_len=1, max_len=256):
    if value is None:
        return False, "%s is required" % field
    text = str(value).strip()
    if len(text) < min_len:
        return False, "%s is too short" % field
    if len(text) > max_len:
        return False, "%s is too long" % field
    return True, ""


def is_email(value, field="email"):
    if not value:
        return False, "%s is required" % field
    if not EMAIL_RE.match(str(value)):
        return False, "%s is not a valid address" % field
    return True, ""


def is_safe_url(value, field="url"):
    if not value:
        return False, "%s is required" % field
    if not URL_RE.match(str(value)):
        return False, "%s must start with http:// or https://" % field
    return True, ""


def is_plan(value, field="plan"):
    if value not in VALID_PLANS:
        return False, "%s must be one of %s" % (field, ", ".join(VALID_PLANS))
    return True, ""


def is_role(value, field="role"):
    if value not in VALID_ROLES:
        return False, "%s must be one of %s" % (field, ", ".join(VALID_ROLES))
    return True, ""


def is_operator(value, field="operator"):
    if value not in VALID_OPERATORS:
        return False, "%s must be one of %s" % (field, ", ".join(VALID_OPERATORS))
    return True, ""


def is_timezone(value, field="timezone"):
    if value not in VALID_TIMEZONES:
        return False, "%s is not a supported timezone" % field
    return True, ""


def is_language(value, field="language"):
    if value not in VALID_LANGUAGES:
        return False, "%s is not a supported language" % field
    return True, ""


def validate_monitor_payload(data):
    """Validate a monitor create/update payload; return (ok, errors dict)."""
    errors = {}
    ok, msg = is_nonempty(data.get("name"), "name")
    if not ok:
        errors["name"] = msg
    ok, msg = is_safe_url(data.get("url"), "url")
    if not ok:
        errors["url"] = msg
    return (len(errors) == 0, errors)


def validate_threshold_payload(data):
    """Validate an alert-threshold payload; return (ok, errors dict)."""
    errors = {}
    ok, msg = is_nonempty(data.get("metric"), "metric")
    if not ok:
        errors["metric"] = msg
    ok, msg = is_operator(data.get("operator"), "operator")
    if not ok:
        errors["operator"] = msg
    try:
        float(data.get("threshold", 0))
    except (TypeError, ValueError):
        errors["threshold"] = "threshold must be numeric"
    return (len(errors) == 0, errors)
