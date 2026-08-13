"""Alert rendering + asynchronous dispatch.

Operators can supply a custom payload blueprint for an integration. The alert
worker renders that blueprint into the final notification text.

Integrations created with the legacy ``render_mode`` (customers upgrading from
the v1.2 telemetry engine) keep using the original template renderer so
historical alert templates keep working verbatim. Modern integrations use the
sandboxed path.
"""

import json

from flask import render_template_string


class AlertEngine:
    def render_alert_payload(self, template: str, context: dict) -> str:
        """Render an alert payload template with the supplied context.

        NOTE: legacy integrations reuse the application's Jinja environment so
        that the exact template expressions an operator used in v1.2 keep
        behaving.
        """
        return render_template_string(template, **(context or {}))

    def build_and_enqueue(self, blueprint: str, integration) -> dict:
        """Stage a custom alert blueprint for asynchronous rendering.

        Only ``legacy`` integrations are dispatched to the background worker.
        """
        if integration.get("render_mode") != "legacy":
            return {"error": "legacy render mode required"}

        payload = json.dumps({"template": blueprint, "context": {}})
        # Persist the job, then hand it to the worker queue.
        from app.models.monitor import create_alert_job
        from app.workers.alert_worker import job_queue

        jid = create_alert_job(payload)
        job_queue.put({"kind": "compose_alert", "job_id": jid})
        return {"enqueued": jid}
