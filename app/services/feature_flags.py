"""Feature-flag evaluation.

Some product capabilities are gated by plan tier. This module maps a flag to the
minimum plan required and evaluates it against the caller's current plan. Pure
data + comparison; safe.
"""

from app.services.billing import PLAN_TIERS

# flag -> minimum plan required to see it
FLAG_REQUIREMENTS = {
    "advanced_analytics": "pro",
    "sso_saml": "enterprise",
    "audit_export": "enterprise",
    "custom_webhook_templates": "pro",
    "multi_region": "enterprise",
    "beta_dashboards": "free",
}


_PLAN_ORDER = {"free": 0, "pro": 1, "enterprise": 2}


def flag_enabled(flag, plan):
    required = FLAG_REQUIREMENTS.get(flag)
    if required is None:
        return False
    return _PLAN_ORDER.get(plan, 0) >= _PLAN_ORDER.get(required, 0)


def evaluate_flags(plan):
    return {
        flag: flag_enabled(flag, plan)
        for flag in FLAG_REQUIREMENTS
    }


def catalog():
    return [
        {"flag": f, "min_plan": r, "description": _describe(f)}
        for f, r in FLAG_REQUIREMENTS.items()
    ]


def _describe(flag):
    return {
        "advanced_analytics": "Custom dashboards and metric roll-ups",
        "sso_saml": "SAML 2.0 single sign-on for your IdP",
        "audit_export": "Export the administrative audit log",
        "custom_webhook_templates": "Bring your own webhook message template",
        "multi_region": "Replicate monitors across regions",
        "beta_dashboards": "Early access to experimental widgets",
    }.get(flag, "")
