"""Service layer for availability and performance metrics.

Pure computation over the metrics_samples / monitors / incidents tables. No
user-controlled strings are ever interpreted as code here, so this module is
safe to call from any request handler.
"""

from app.database import get_conn, get_metrics_samples


def uptime_percentage(monitor_id, samples=None):
    """Fraction of samples in the 'up' state, expressed as a percentage."""
    if samples is None:
        samples = get_metrics_samples(monitor_id, limit=500)
    if not samples:
        return 100.0
    up = sum(1 for s in samples if s.get("state") == "up")
    return round(100.0 * up / len(samples), 2)


def average_latency(monitor_id, samples=None):
    if samples is None:
        samples = get_metrics_samples(monitor_id, limit=500)
    if not samples:
        return None
    vals = [s["value"] for s in samples if isinstance(s.get("value"), (int, float))]
    return round(sum(vals) / len(vals), 2) if vals else None


def build_timeseries_points(monitor_id, days=7):
    """Return downsampled daily points suitable for charting."""
    samples = get_metrics_samples(monitor_id, limit=2000)
    buckets = {}
    for s in samples:
        day = (s.get("sampled_at") or "")[:10]
        if not day:
            continue
        buckets.setdefault(day, []).append(s.get("value"))
    points = []
    for day in sorted(buckets):
        vals = [v for v in buckets[day] if isinstance(v, (int, float))]
        if vals:
            points.append({"day": day, "value": round(sum(vals) / len(vals), 2)})
    return points[-days:] if days else points


def incident_resolution_rate():
    """Share of incidents that are resolved/closed, as a percentage."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM incidents")
    total = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM incidents WHERE status IN ('resolved','closed')")
    resolved = cur.fetchone()["c"]
    conn.close()
    if not total:
        return 0.0
    return round(100.0 * resolved / total, 2)


def summary_for_user(user_id):
    """Aggregate view consumed by the metrics dashboard."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name, status FROM monitors WHERE owner=?", (user_id,))
    owned = [dict(r) for r in cur.fetchall()]
    conn.close()
    monitors = []
    for m in owned:
        samples = get_metrics_samples(m["id"], limit=500)
        monitors.append({
            "id": m["id"],
            "name": m["name"],
            "status": m["status"],
            "uptime": uptime_percentage(m["id"], samples),
            "avg_latency": average_latency(m["id"], samples),
        })
    return {
        "monitor_count": len(monitors),
        "monitors": monitors,
        "incident_resolution_rate": incident_resolution_rate(),
    }
