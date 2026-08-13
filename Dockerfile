FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Create a low-privilege runtime user. The application process (gunicorn) runs
# as this user, NOT as root. The flag file is owned by root and world-readable
# (mode 644) so a successful RCE -- which executes as sentineluser -- can read
# it via the achieved shell (`cat /flag.txt`). This mirrors the standard
# OSWE / CTF goal: get code execution, then read the flag.
RUN useradd --create-home --shell /usr/sbin/nologin sentineluser \
    && chown -R sentineluser:sentineluser /app

# Flag creation + privilege drop happen in the entrypoint.
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENV FLASK_RUN_PORT=5000
EXPOSE 5000

# Single worker is intentional: the lab uses an in-process alert queue, so a
# pre-fork model would split the queue across processes. Inject the Flask
# session key at runtime via SENTINELHUB_SESSION_SECRET for stable sessions.
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
