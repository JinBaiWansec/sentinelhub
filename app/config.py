"""Application configuration.

Settings are loaded from environment variables with sensible in-repo defaults.
The Flask session signing key is kept separate from the tenant signing secret.
"""

import os


# Name of the environment variable that may carry the per-deployment Flask
# session key. When absent, ``create_app`` generates a fresh random key at boot.
SESSION_SECRET_ENV = "SENTINELHUB_SESSION_SECRET"

# The tenant signing secret environment override (otherwise the DB default is
# used). Kept separate from the session key on purpose.
TENANT_SECRET_ENV = "SENTINELHUB_TENANT_SECRET"


class Config:
    """Base configuration object consumed by the application factory."""

    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True

    @staticmethod
    def session_secret() -> str:
        """Return the Flask session key, or ``None`` to force a random key."""
        return os.environ.get(SESSION_SECRET_ENV)

    @staticmethod
    def tenant_secret_override() -> "str | None":
        return os.environ.get(TENANT_SECRET_ENV)


def load_config(app) -> None:
    """Apply the resolved configuration onto a Flask app instance."""
    app.config["SESSION_SECRET_ENV"] = SESSION_SECRET_ENV
    app.config["TENANT_SECRET_ENV"] = TENANT_SECRET_ENV
    if os.environ.get("SENTINELHUB_DEBUG"):
        app.config["DEBUG"] = True
