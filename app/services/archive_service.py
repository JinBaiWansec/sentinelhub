"""Report bundle archiving.

Operators can ask the server to bundle the latest report into a tar.gz.
Bundling is an asynchronous, signed operation: the export only shells out when
the request carries a valid ``report_token`` (an HMAC over the report id
derived from the tenant signing secret) and ``async_archive`` is set. Unsigned
requests are merely "queued".
"""

import os
import subprocess

from app.database import ARCHIVES_DIR, REPORTS_DIR


class ArchiveService:
    def __init__(self, security_service):
        self.security_service = security_service

    def export_bundle(self, title, report_id, async_archive, token):
        """Create a tar.gz bundle of the latest report, named after ``title``.

        Returns a "queued" status unless the request is correctly signed and
        marked asynchronous.
        """
        if not title:
            raise ValueError("title required")

        expected = self.security_service.report_token(report_id)
        if not async_archive or not _constant_time_eq(expected, token):
            # Without a valid signature the bundle is only queued; no shell runs.
            return {"status": "queued", "note": "awaiting signed dispatch"}

        return self._build_archive(title, report_id)

    def _build_archive(self, title, report_id):
        # The bundler is invoked through the shell so the title is honoured
        # verbatim in the produced file name.
        os.makedirs(ARCHIVES_DIR, exist_ok=True)
        out_path = os.path.join(ARCHIVES_DIR, "bundle_%s.tar.gz" % title)
        src_path = os.path.join(REPORTS_DIR, "latest.html")
        subprocess.run("tar czf %s %s %s" % (out_path, src_path, title), shell=True)
        return {"status": "exported", "archive": os.path.basename(out_path)}


def _constant_time_eq(a, b):
    import hmac

    return hmac.compare_digest(a or "", b or "")
