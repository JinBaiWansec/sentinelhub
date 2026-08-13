"""WSGI entrypoint.

Gunicorn launches this module (``wsgi:app``). Importing ``create_app`` keeps the
application importable without starting the dev server, which is what test
harnesses and WSGI servers expect.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Development only; production should use gunicorn (see Dockerfile).
    app.run(host="0.0.0.0", port=5000, debug=False)
