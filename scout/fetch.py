"""Shared HTTP helpers for the CVSender scout — stdlib urllib only.

Politeness contract (research/2026-09-09-data-access.md §8):
- honest User-Agent, sequential requests, ~0.5-1 s sleep between fetches
- 1 request/night cadence for crawler-disallowed surfaces (NFJ /api/)
- never touch JJIT /api/*; sitemaps and public offer pages only
"""

import json
import os
import ssl
import time
import urllib.error
import urllib.request

USER_AGENT = "cvsender-scout/1.0 (personal job search)"
TIMEOUT_S = 30
POLITE_SLEEP_S = 0.75


def _ssl_context():
    """macOS python.org framework builds ship no CA bundle; fall back to the
    system cert file (and certifi when present). Verify-first, never disable."""
    candidates = []
    try:
        import certifi  # optional; not a project dependency

        candidates.append(certifi.where())
    except ImportError:
        pass
    candidates.append("/etc/ssl/cert.pem")
    for cafile in candidates:
        if os.path.exists(cafile):
            try:
                return ssl.create_default_context(cafile=cafile)
            except ssl.SSLError:
                continue
    return ssl.create_default_context()


_CTX = _ssl_context()


def _request(url, method="GET", headers=None, data=None):
    req = urllib.request.Request(url, method=method, data=data)
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Accept", "application/json, text/xml, text/html;q=0.8")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    return urllib.request.urlopen(req, timeout=TIMEOUT_S, context=_CTX)


def get_text(url, headers=None):
    """GET -> decoded body. Raises urllib.error.HTTPError on 4xx/5xx."""
    with _request(url, headers=headers) as resp:
        return resp.read().decode("utf-8", errors="replace")


def get_json(url, headers=None):
    return json.loads(get_text(url, headers=headers))


def probe_status(url):
    """Status-code probe for the expiry check: 200/403/404/410/... .

    Never raises for HTTP error codes — the code IS the answer.
    Returns None only on network-level failure (DNS, timeout)."""
    try:
        with _request(url) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except (urllib.error.URLError, OSError, TimeoutError):
        return None


class Pace:
    """Sequential-fetch throttle: sleep before each request after the first."""

    def __init__(self, seconds=POLITE_SLEEP_S):
        self.seconds = seconds
        self._last = None

    def wait(self):
        if self._last is not None:
            delta = time.monotonic() - self._last
            if delta < self.seconds:
                time.sleep(self.seconds - delta)
        self._last = time.monotonic()
