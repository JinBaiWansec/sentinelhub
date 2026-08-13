"""Static template helpers.

Renders fixed, deployment-constant HTML fragments for the status page. The
template string is a hard-coded constant.
"""

from flask import render_template_string

# Constant badge markup rendered on the status page.
_STATUS_BADGE_HTML = (
    "<span class='pill pill-ok'>All systems operational</span>"
)


def render_status_badge():
    # Render the constant status badge template.
    return render_template_string(_STATUS_BADGE_HTML)  # noqa: S701 - constant
