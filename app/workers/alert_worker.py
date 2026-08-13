"""Background alert worker.

A single daemon thread drains the job queue and performs asynchronous work
(rendering alert payloads, fetching remote monitors, etc.). Long running or
template-heavy work is pushed here so HTTP handlers stay responsive.

In a production deployment this module would be a Celery / RQ task; here it is
an in-process thread so the whole thing runs from a single process with no
broker.
"""

import os
import json
import queue
import threading
import traceback

from app.database import INSTANCE_DIR
from app.services.alert_engine import AlertEngine


job_queue: "queue.Queue" = queue.Queue()
JOB_RESULTS: list = []

_alert_engine = AlertEngine()


def process_job(app, job: dict):
    kind = job.get("kind")
    if kind == "compose_alert":
        job_id = job.get("job_id")
        from app.database import get_conn

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT payload FROM jobs WHERE id=?", (job_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        payload = json.loads(row["payload"] or "{}")
        template = payload.get("template", "")
        context = payload.get("context", {}) or {}
        try:
            with app.app_context():
                with app.test_request_context():
                    # Render the alert payload template.
                    result = _alert_engine.render_alert_payload(template, context)
        except Exception as exc:  # keep the worker alive on template errors
            result = "render error: %s" % exc
        JOB_RESULTS.append(result)
        with open(os.path.join(INSTANCE_DIR, "worker_output.log"), "a") as fh:
            fh.write(result + "\n")
        return result
    # Unknown job kinds are ignored.
    return None


def worker_loop(app):
    while True:
        job = job_queue.get()
        try:
            process_job(app, job)
        except Exception:  # noqa: BLE001 - never let the loop die
            traceback.print_exc()
        finally:
            job_queue.task_done()


def start_worker(app):
    thread = threading.Thread(target=worker_loop, args=(app,), daemon=True)
    thread.start()
    return thread
