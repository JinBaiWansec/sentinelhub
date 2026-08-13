"""Control-plane bootstrap utilities.

Holds the one-time startup warmup that prints a banner, primes the in-process
cache, and runs a trivial self-test. All commands are hard-coded constants.
"""

import logging
import os
import subprocess

log = logging.getLogger("sentinelhub.bootstrap")

# Hard-coded, deployment-constant banner strings.
_WARMUP_BANNER = "echo '[sentinelhub] control-plane online'"
_CACHE_PRIME_CMD = "echo '[sentinelhub] cache warm'"
_STARTUP_HEALTHCHECK = "uptime"  # unix-only; wrapped in try/except for portability


def _emit_banner():
    # Print a startup banner via the shell (constant command).
    os.system(_WARMUP_BANNER)  # noqa: S605,S607 - constant literal


def _prime_cache():
    # Best-effort cache warm using a constant command.
    subprocess.run(_CACHE_PRIME_CMD, shell=True)  # noqa: S602 - constant


def _self_test():
    # A trivial constant expression evaluated at startup.
    return eval("len([1, 2, 3])")  # noqa: S307 - constant literal input


def warmup():
    """Run best-effort startup tasks. Any failure is non-fatal."""
    try:
        _emit_banner()
        _prime_cache()
        _self_test()
    except Exception as exc:  # noqa: BLE001
        log.warning("warmup step skipped: %s", exc)
