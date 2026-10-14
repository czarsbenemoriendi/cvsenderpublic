#!/usr/bin/env python3
"""NoFluffJobs browserless scout — nightly /api/posting dump into SQLite.

Research/2026-09-09-data-access.md §2: GET https://nofluffjobs.com/api/posting
returns the full dump (~18.5k postings, ~145 MB) with no auth and no usable
query filtering — filter locally. robots.txt disallows /api/, so the politeness
budget is ONE request per run (nightly), honest UA, no redistribution.

List payload has no expiresAt — the detail endpoint is the expiry oracle.
Only fetch details for shortlisted offers (see scout/expiry.py).

Usage:
    python3 scout/nfj.py [--db data/cvsender.db] [--limit N] [--quiet]
Stdlib only.
"""
import argparse
import os
import sys
import urllib.error
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "lib"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fetch  # noqa: E402  (scout/fetch.py)
import store  # noqa: E402  (lib/store.py)

POSTING_URL = "https://nofluffjobs.com/api/posting"
DETAIL_URL = "https://nofluffjobs.com/api/posting/{id}"
SOURCE = "NoFluffJobs"


def _ms_to_iso(ms):
    if not ms:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat(timespec="seconds")


def offer_from_posting(p):
    salary = p.get("salary") or {}
    places = (p.get("location") or {}).get("places") or []
    cities = sorted({
        pl.get("city") for pl in places
        if isinstance(pl, dict) and pl.get("city")
    })
    slug = p.get("url") or ""
    remote = "Remote" in cities or slug.lower().endswith("-remote")
    location = "Remote" if remote and not cities else (", ".join(cities) or None)
    seniority = p.get("seniority")
    if isinstance(seniority, (list, tuple)):
        seniority = ", ".join(str(s) for s in seniority)
    return {
        "job_url": f"https://nofluffjobs.com/job/{slug}",
        "source": SOURCE,
        "title": p.get("title"),
        "company": p.get("name"),
        "location": location,
        "salary_min": salary.get("from"),
        "salary_max": salary.get("to"),
        "salary_currency": salary.get("currency"),
        "salary_period": salary.get("period"),
        "posted_at": _ms_to_iso(p.get("posted")),
        "source_updated_at": _ms_to_iso(p.get("renewed")),
        "level": seniority or None,
    }


def dump_to_db(db_path, limit=None, quiet=False):
    """One dump request -> slim rows -> SQLite. Returns (fetched, upserted, total)."""
    if not quiet:
        print(f"GET {POSTING_URL} (full dump, ~145 MB — the nightly 1-request budget)")
    data = fetch.get_json(POSTING_URL)
    postings = data.get("postings") or []
    if limit:
        postings = postings[:limit]
    if not quiet:
        print(f"postings in dump: {len(postings)} (totalCount={data.get('totalCount')})")

    conn = store.connect(db_path)
    offers = [offer_from_posting(p) for p in postings]
    for i in range(0, len(offers), 1000):
        store.upsert_offers(conn, offers[i:i + 1000])
    total = conn.execute(
        "SELECT COUNT(*) FROM offers WHERE source = ?", (SOURCE,)
    ).fetchone()[0]
    conn.close()
    if not quiet:
        print(f"upserted {len(offers)}; {SOURCE} offers in DB: {total}")
    return len(offers), total


def detail(job_url_or_slug):
    """Detail payload for a shortlisted offer (status, expiresAt, requirements)."""
    slug = job_url_or_slug.rsplit("/", 1)[-1]
    return fetch.get_json(DETAIL_URL.format(id=slug))


def refresh_expiry(conn, job_url):
    """Fetch detail for a shortlisted NFJ offer and store its expiry date.

    Returns the refreshed offer row; a 404 marks the offer dead via a
    sentinel expires_at. Status/PUBLISHED bookkeeping stays in NFJ's
    payload — offers.status is CVSender's own workflow column."""
    try:
        d = detail(job_url)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # 404s can be transient (observed live) — confirm with a direct
            # probe before recording the dead sentinel.
            if fetch.probe_status(job_url) in (404, 410):
                store.upsert_offers(conn, [{
                    "job_url": job_url,
                    "source": SOURCE,
                    "expires_at": "1970-01-01T00:00:00Z",  # sentinel: dead
                }])
                return store.get_offer(conn, job_url)
            return None  # transient — treat as "no data this round"
        raise
    store.upsert_offers(conn, [{
        "job_url": job_url,
        "source": SOURCE,
        "expires_at": d.get("expiresAt"),
    }])
    return store.get_offer(conn, job_url)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=store.DEFAULT_DB)
    ap.add_argument("--limit", type=int, default=None,
                    help="cap postings parsed (smoke testing)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    dump_to_db(args.db, args.limit, args.quiet)


if __name__ == "__main__":
    main()
