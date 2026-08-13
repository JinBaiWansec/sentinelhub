"""SentinelHub application factory.

A self-hosted observability & alerting platform. The app is assembled through a
factory so it can be imported without side effects (tests, WSGI servers) and so
the Flask session signing key can be set once, at boot, from an environment
override or a fresh random value.
"""

import os

from flask import Flask

from app.database import INSTANCE_DIR, TEMPLATES_DIR
from app.config import load_config, Config
from app.extensions import init_extensions
from app.errors import register_error_handlers
from app.workers.alert_worker import start_worker
from app.services.bootstrap import warmup

from app.blueprints.auth import bp as auth_bp
from app.blueprints.pages import bp as pages_bp
from app.blueprints.analytics import bp as analytics_bp
from app.blueprints.billing import bp as billing_bp
from app.blueprints.team import bp as team_bp
from app.blueprints.integrations import bp as integrations_bp
from app.blueprints.reports import bp as reports_bp
from app.blueprints.admin import bp as admin_bp
from app.blueprints.metrics import bp as metrics_bp
from app.blueprints.notifications import bp as notifications_bp
from app.blueprints.profile import bp as profile_bp
from app.blueprints.audit import bp as audit_bp
from app.blueprints.dispatch import bp as dispatch_bp
from app.blueprints.monitor import bp as monitor_bp
from app.blueprints.webhooks import bp as webhooks_bp
from app.blueprints.usage import bp as usage_bp
from app.blueprints.sso import bp as sso_bp
from app.blueprints.feature_flags import bp as feature_flags_bp
from app.blueprints.settings import bp as settings_bp


def create_app() -> Flask:
    """Build and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder=TEMPLATES_DIR,
        instance_path=INSTANCE_DIR,
        instance_relative_config=True,
    )

    # Flask session signing key is separate from ``tenant_signing_secret``.
    # Inject it at deploy time via SENTINELHUB_SESSION_SECRET; otherwise a
    # fresh random key is generated per boot.
    app.secret_key = Config.session_secret() or os.urandom(32).hex()
    app.config["SECRET_KEY"] = app.secret_key

    load_config(app)
    init_extensions(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(team_bp)
    app.register_blueprint(integrations_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(dispatch_bp)
    app.register_blueprint(monitor_bp)
    app.register_blueprint(webhooks_bp)
    app.register_blueprint(usage_bp)
    app.register_blueprint(sso_bp)
    app.register_blueprint(feature_flags_bp)
    app.register_blueprint(settings_bp)

    # Unified JSON error envelope (400/403/404/405/500/...) for API clients.
    register_error_handlers(app)

    # Idempotent schema + seed bootstrap. The seed is generated dynamically per
    # database.
    from app.database import init_db

    init_db()

    # Best-effort startup warmup (banner / cache prime / self-test).
    warmup()

    # Start the background alert worker (stand-in for a Celery / RQ deployment).
    start_worker(app)

    return app
