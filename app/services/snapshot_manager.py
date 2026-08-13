"""Tenant snapshot import.

Operators export tenant state (monitors, thresholds, dashboards) as a portable
snapshot and later re-import it on another instance. To stop a snapshot from
one deployment being restored into another, every snapshot carries a
per-instance HMAC signature derived from the tenant signing secret.
"""

import base64
import pickle


class InvalidSignatureError(Exception):
    """Raised when a snapshot fails its integrity check."""


class TenantSnapshotManager:
    def __init__(self, security_service):
        self.security_service = security_service

    def import_tenant_snapshot(self, encoded_blob, signature):
        """Public entry used by the admin snapshot endpoint.

        Pipeline: decode -> verify signature -> rebuild application state.
        """
        # Layer 1: decode and basic format validation.
        raw_bytes = self._decode_payload(encoded_blob)

        # Layer 2: verify the per-instance HMAC signature. Without a valid
        # signature the blob is rejected before any state is touched.
        if not self.security_service.verify_snapshot_signature(raw_bytes, signature):
            raise InvalidSignatureError("Snapshot integrity check failed")

        # Layer 3: apply the (now trusted) snapshot object to the database.
        return self._apply_snapshot_object(raw_bytes)

    def _decode_payload(self, encoded_blob):
        """Base64-decode the tenant snapshot envelope."""
        if not encoded_blob:
            raise InvalidSignatureError("empty snapshot")
        try:
            return base64.b64decode(encoded_blob)
        except Exception as exc:  # noqa: BLE001 - surface a clean error
            raise InvalidSignatureError("invalid snapshot encoding") from exc

    def _apply_snapshot_object(self, raw_bytes):
        # Rehydrate the snapshot payload and rebuild the corresponding rows.
        unserialized_data = pickle.loads(raw_bytes)
        return self._rebuild_database_state(unserialized_data)

    def _rebuild_database_state(self, data):
        # In a full deployment this would upsert monitors / thresholds / etc.
        if isinstance(data, dict):
            return {"restored": True, "keys": list(data.keys())}
        return {"restored": True}
