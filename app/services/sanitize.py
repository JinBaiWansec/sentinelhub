"""Input normalisation helpers used across SentinelHub."""


class QueryGuard:
    """Lightweight guard applied to free-text search inputs.

    The blocklist is applied once, in order, with a single ``.replace`` per
    token.
    """

    BLOCKLIST = ["UNION", "SELECT", "INSERT", "UPDATE", "DELETE",
                 "DROP", "--", "#", "/*", "*/"]

    def filter(self, value: str) -> str:
        out = value or ""
        for token in self.BLOCKLIST:
            out = out.replace(token, "")
        return out


def normalize_artifact_path(name: str) -> str:
    """Strip common traversal sequences from the supplied name."""
    if not name:
        return ""
    cleaned = name.replace("../", "")
    cleaned = cleaned.replace("..\\", "")
    return cleaned
