#!/usr/bin/env python3
"""Expiry / dead-offer pre-check — run before EVERY apply.

Implements the 5-signal check from research/2026-09-09-data-access.md §9:

  1. native expiry field   NFJ expiresAt/status, JJIT validThrough,
                           Pracuj expirationDate  -> expired
  2. sitemap membership    JJIT: url absent from active-jobs.xml but
                           present in expired-jobs.xml  -> expired;
                           present in active  -> alive (positive signal)
  3. offer-page probe      HTTP 404/410 on the offer url -> expired
  4. age heuristic         posted/renewed older than ~14d -> 'stale'
                           (soft signal — boards auto-renew; deprioritize)
  5. cached verdict        offers.expiry_check keeps
                           {verdict, signal, reason, checked_at};
                           fresh caches (<CACHE_H) short-circuit

Verdicts: 'alive' | 'expired' | 'stale' | 'unknown'.

Apply-flow entry points:
    check_url(conn, job_url) -> verdict dict (uses cache, fetches missing native expiry)
    is_expired(conn, job_url) -> bool
Stdlib only.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "lib"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fetch  # noqa: E402  (scout/fetch.py)
import store  # noqa: E402  (lib/store.py)

CACHE_H = 24
MAX_AGE_DAYS = 14

_expired_cache = None  # lazy url sets from JJIT sitemaps (per process)
_active_cache = None




def _parse_dt(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:  # NFJ detail sends naive timestamps (UTC implied)
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


# Detail statuses that mean the posting is down. "NEW" is our own store
# default (ingest marker), never an NFJ publish status — must not trip this.
DEAD_NFJ_STATUSES = {"ARCHIVED", "CLOSED", "EXPIRED", "UNPUBLISHED"}


def _sitemap_sets():
    """(active_urls, expired_urls) lazily fetched — JJIT signal 2."""
    global _active_cache, _expired_cache
    import scout as jjit
    if _active_cache is None or _expired_cache is None:
        pace = fetch.Pace()
        if _active_cache is None:
            _active_cache = set(jjit.fetch_sitemap_urls(jjit.SITEMAP_INDEX, pace))
        if _expired_cache is None:
            _expired_cache = set(jjit.fetch_sitemap_urls(jjit.EXPIRED_INDEX, pace))
    return _active_cache, _expired_cache


def _signal_native(conn, offer, now):
    """Signal 1: stored native expiry (JJIT validThrough, NFJ detail, Pracuj)."""
    exp = _parse_dt(offer["expires_at"])
    if exp and exp < now:
        return {"verdict": "expired", "signal": "native-field",
                "reason": f"expires_at {offer['expires_at']} < now"}
    if exp:
        return {"verdict": "alive", "signal": "native-field",
                "reason": f"expires_at {offer['expires_at']} in the future"}
    if offer["source"] == "NoFluffJobs" and status in DEAD_NFJ_STATUSES:
        return {"verdict": "expired", "signal": "nfj-status",
                "reason": f"detail status={offer['status']}"}
    if offer["source"] == "NoFluffJobs" and not offer["expires_at"]:
        # shortlist context: the detail endpoint is the expiry oracle — one call
        import nfj
        refreshed = nfj.refresh_expiry(conn, offer["job_url"])
        if refreshed is not None:
            return _signal_native(conn, dict(refreshed), now)
    return None


def _signal_sitemap(offer):
    """Signal 2: JJIT active/expired sitemap membership."""
    if offer["source"] != "JustJoin.it":
        return None
    active, expired = _sitemap_sets()
    if offer["job_url"] in expired and offer["job_url"] not in active:
        return {"verdict": "expired", "signal": "sitemap",
                "reason": "in expired-jobs.xml, absent from active-jobs.xml"}
    if offer["job_url"] in active:
        return {"verdict": "alive", "signal": "sitemap",
                "reason": "present in active-jobs.xml"}
    return None


def _signal_probe(offer):
    """Signal 3: cheap status probe of the offer page itself."""
    code = fetch.probe_status(offer["job_url"])
    if code in (404, 410):
        return {"verdict": "expired", "signal": "http-probe",
                "reason": f"offer page returned {code}"}
    if code is None:
        return {"verdict": "unknown", "signal": "http-probe",
                "reason": "network-level failure"}
    return None


def _signal_age(offer, now):
    """Signal 4: soft staleness — boards auto-renew, so this never means 'expired'."""
    for field in ("source_updated_at", "posted_at", "discovered_at"):
        dt = _parse_dt(offer[field])
        if dt:
            if now - dt > timedelta(days=MAX_AGE_DAYS):
                return {"verdict": "stale", "signal": "age",
                        "reason": f"{field} {offer[field]} older than {MAX_AGE_DAYS}d"}
            return None
    return None


def _cached(offer, now):
    """Signal 5: fresh cached verdict short-circuits everything else."""
    try:
        cached = json.loads(offer["expiry_check"] or "null")
    except json.JSONDecodeError:
        cached = None
    if not isinstance(cached, dict):
        return None
    checked = _parse_dt(cached.get("checked_at"))
    if checked and now - checked < timedelta(hours=CACHE_H):
        out = dict(cached)
        out["signal"] = "cache:" + str(cached.get("signal"))
        return out
    return None


def check_offer(conn, offer, probe=True):
    """Run the signal ladder over one offer row (sqlite3.Row or dict).

    probe=False skips the HTTP probe (e.g. bulk scans of the whole queue)."""
    now = datetime.now(timezone.utc)
    row = dict(offer)

    cached = _cached(row, now)
    if cached:
        return cached

    verdict = (
        _signal_native(conn, row, now)
        or _signal_sitemap(row)
        or (_signal_probe(row) if probe else None)
        or _signal_age(row, now)
        or {"verdict": "alive", "signal": "default",
            "reason": "no expiry signal fired"}
    )
    verdict = dict(verdict)
    verdict["checked_at"] = now.isoformat(timespec="seconds")
    store.upsert_offers(conn, [{
        "job_url": row["job_url"],
        "source": row.get("source"),
        "expiry_check": json.dumps(verdict, ensure_ascii=False),
    }])
    return verdict


def check_url(conn, job_url, probe=True):
    offer = store.get_offer(conn, job_url)
    if offer is None:
        return {"verdict": "unknown", "signal": "store",
                "reason": "url not in store",
                "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    return check_offer(conn, offer, probe=probe)


def is_expired(conn, job_url, probe=True):
    return check_url(conn, job_url, probe=probe)["verdict"] == "expired"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=store.DEFAULT_DB)
    ap.add_argument("url", help="offer url to pre-check")
    ap.add_argument("--no-probe", action="store_true")
    args = ap.parse_args()
    conn = store.connect(args.db)
    print(json.dumps(check_url(conn, args.url, probe=not args.no_probe), indent=2))


if __name__ == "__main__":
    main()
