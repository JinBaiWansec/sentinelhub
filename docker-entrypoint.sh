#!/bin/sh
# SentinelHub container entrypoint.
#
# Responsibilities:
#   1. Provision /flag.txt (the CTF flag) owned by root, world-readable (644).
#      Per OSWE / CTF convention the flag is at a well-known path; the app runs
#      as the low-privilege sentineluser, so it must be read through achieved
#      RCE, not through the web UI.
#   2. Drop privileges from root to sentineluser and launch the single-worker
#      gunicorn server.
set -e

if [ ! -f /flag.txt ]; then
    if [ -n "$CTF_FLAG" ]; then
        FLAG_VALUE="$CTF_FLAG"
    else
        # Fresh random flag per container when none is supplied.
        FLAG_VALUE="FLAG{$(head -c 16 /dev/urandom | base64 | tr -d '/+=')}"
    fi
    echo "$FLAG_VALUE" > /flag.txt
    chown root:root /flag.txt
    chmod 644 /flag.txt
    echo "[entrypoint] flag written to /flag.txt"
fi

# Ensure the runtime user can write the sqlite db / instance dir.
chown -R sentineluser:sentineluser /app/instance 2>/dev/null || true

echo "[entrypoint] starting gunicorn as sentineluser"
exec runuser -u sentineluser -- \
    gunicorn -w 1 -b 0.0.0.0:5000 wsgi:app
