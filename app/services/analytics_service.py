"""Monitor analytics: search + listing helpers.

Search performs a free-text containment match over monitor names. User input
goes through a lightweight guard before being embedded in the query.
"""

from app.database import get_conn
from app.services.sanitize import QueryGuard


def query_monitors(query: str) -> list:
    conn = get_conn()
    cur = conn.cursor()
    sanitized_query = QueryGuard().filter(query or "")
    # Free-text containment search over monitor names.
    sql = "SELECT id, name, status FROM monitors WHERE name LIKE '%" + sanitized_query + "%' ORDER BY name"
    cur.execute(sql)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def list_monitors() -> list:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name, status, url FROM monitors ORDER BY name")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows
