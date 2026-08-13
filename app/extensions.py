"""Extension initialisers.

A typical Flask service depends on a handful of extensions (ORM, task broker,
mail, cache). SentinelHub keeps these as thin stand-ins so the package layout
mirrors a production application without pulling in a broker or an ORM at
import time. The lightweight in-process worker in ``app.workers.alert_worker``
stands in for a Celery / RQ deployment.
"""


class MailExtension:
    """Placeholder for Flask-Mail; disabled until a real backend is wired."""

    def __init__(self):
        self.enabled = False

    def init_app(self, app):  # pragma: no cover - stand-in
        self.enabled = bool(app.config.get("MAIL_ENABLED"))


class CacheExtension:
    """Placeholder for a Flask-Caching backend (in-memory for the lab)."""

    def __init__(self):
        self.enabled = False
        self._store = {}

    def init_app(self, app):  # pragma: no cover - stand-in
        self.enabled = app.config.get("CACHE_ENABLED", False)


mail = MailExtension()
cache = CacheExtension()


def init_extensions(app) -> None:
    """Wire the stand-in extensions onto the application."""
    mail.init_app(app)
    cache.init_app(app)
