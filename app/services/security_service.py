"""Cryptographic primitives for snapshot / report / dispatch integrity.

All signatures use only the Python standard library (``hmac`` / ``hashlib``).
The per-instance snapshot key is derived as::

    K = HMAC_SHA256(tenant_secret, instance_id)

so a snapshot exported from one deployment cannot be restored into another.
"""

import hmac
import hashlib

from app.database import get_setting, get_instance_id


class SecurityService:
    """Centralises key derivation and signature verification."""

    def __init__(self, secret=None, instance_id=None):
        # Resolved lazily from settings so the service can be constructed at
        # import time without touching the database.
        self._secret = secret
        self._instance_id = instance_id

    @property
    def secret(self):
        return self._secret if self._secret is not None else (get_setting("tenant_signing_secret") or "")

    @property
    def instance_id(self):
        return self._instance_id if self._instance_id is not None else get_instance_id()

    # -- low level ----------------------------------------------------------

    @staticmethod
    def _hmac(key: bytes, blob: bytes) -> str:
        return hmac.new(key, blob, hashlib.sha256).hexdigest()

    # -- snapshot signing ---------------------------------------------------

    def derive_instance_key(self) -> bytes:
        """Per-instance key: HMAC_SHA256(tenant_secret, instance_id)."""
        return hmac.new(
            self.secret.encode(),
            self.instance_id.encode(),
            hashlib.sha256,
        ).digest()

    def sign_blob(self, raw: bytes) -> str:
        key = self.derive_instance_key()
        return self._hmac(key, raw)

    def verify_snapshot_signature(self, raw: bytes, signature: str) -> bool:
        """Constant-time compare of the per-instance HMAC over the raw blob."""
        if not signature:
            return False
        expected = self.sign_blob(raw)
        return hmac.compare_digest(expected, signature)

    # -- report bundle token ------------------------------------------------

    def report_token(self, report_id) -> str:
        return hmac.new(
            self.secret.encode(),
            str(report_id).encode(),
            hashlib.sha256,
        ).hexdigest()

    # -- internal dispatch queue signature ----------------------------------

    def dispatch_signature(self, job_id) -> str:
        return hmac.new(
            self.secret.encode(),
            str(job_id).encode(),
            hashlib.sha256,
        ).hexdigest()
