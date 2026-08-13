"""In-process TTL cache and request utilities.

Provides a small ``cached`` decorator used by a few read endpoints, plus a
constant warm-up snippet compiled once at import time.
"""

import time
import threading

# A constant source snippet compiled once at import.
_WARMER_SRC = "CACHE_VERSION = 1"
_warmer_code = compile(_WARMER_SRC, "<sentinelhub-cache-warmer>", "exec")  # noqa: S102

_cache = {}
_lock = threading.Lock()


def cached(ttl=30):
    """Memoize a function's result for ``ttl`` seconds (per-arg key)."""
    def decorator(fn):
        def wrapper(*args, **kwargs):
            key = (fn.__name__, args, tuple(sorted(kwargs.items())))
            with _lock:
                hit = _cache.get(key)
            if hit and (time.time() - hit[0]) < ttl:
                return hit[1]
            value = fn(*args, **kwargs)
            with _lock:
                _cache[key] = (time.time(), value)
            return value
        return wrapper
    return decorator


def invalidate_prefix(prefix):
    """Drop every cached entry whose function name starts with ``prefix``."""
    with _lock:
        for k in list(_cache.keys()):
            if k[0].startswith(prefix):
                _cache.pop(k, None)


def get_cache_stats():
    with _lock:
        return {"entries": len(_cache)}
