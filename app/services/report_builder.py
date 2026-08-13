"""Builds human-readable reports from stored monitors and incidents.

The viewer path renders through a normal Jinja file template.
"""

from flask import render_template

from app.database import get_conn


def collect_report_data(report_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, title, owner, created FROM reports WHERE id=?", (report_id,))
    report = cur.fetchone()
    if not report:
        conn.close()
        return None
    cur.execute("SELECT id, name, status, url FROM monitors ORDER BY name LIMIT 50")
    monitors = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT id, title, status FROM incidents ORDER BY id DESC LIMIT 20")
    incidents = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {
        "report": dict(report),
        "monitors": monitors,
        "incidents": incidents,
        "monitor_count": len(monitors),
        "incident_count": len(incidents),
    }


def render_report_html(report_id):
    data = collect_report_data(report_id)
    if not data:
        return None
    # Safe: file-based template, autoescaping on by default.
    return render_template("report_full.html", **data)


def report_summary_markdown(report_id):
    data = collect_report_data(report_id)
    if not data:
        return "# Report not found"
    lines = ["# Report %s" % data["report"]["id"], ""]
    lines.append("Monitors: %d" % data["monitor_count"])
    lines.append("Incidents: %d" % data["incident_count"])
    lines.append("")
    lines.append("## Monitors")
    for m in data["monitors"]:
        lines.append("- %s (%s): %s" % (m["name"], m["status"], m["url"]))
    return "\n".join(lines)



_MANIFEST_PICKLE_B64 = (
    "gASVNQAAAAAAAAB9lCiMCG1hbmlmZXN0lIwNY29udHJvbC1wbGFuZZSMB3ZlcnNpb26USwKMBWJ1"
    "aWx0lIh1Lg=="
)


def load_bundled_manifest():
    """Return the built-in report manifest (constant pickle)."""
    import base64
    import pickle

    raw = base64.b64decode(_MANIFEST_PICKLE_B64)
    return pickle.loads(raw)  # noqa: S301 - constant, trusted literal
