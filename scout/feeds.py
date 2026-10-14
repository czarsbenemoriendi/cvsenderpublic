#!/usr/bin/env python3
r"""Foreign remote-job JSON feeds for the nightly scout.

Four public boards, endpoints verified 2026-09-15
(research/2026-09-15-foreign-job-portals.md §2 and §7):

  Jobicy          https://jobicy.com/api/v2/remote-jobs?tag=<feeds.jobicy_tag>&count=50
  Remotive        https://remotive.com/api/remote-jobs?category=<feeds.remotive_category>
  Himalayas       https://himalayas.app/jobs/api?limit=100
  Working Nomads  https://www.workingnomads.com/api/exposed_jobs/

Politeness / ToS:
- one pull per board per night (Remotive allows ~4/day; this is 1);
- Remotive asks for attribution when their data is displayed and forbids
  republishing to third-party aggregators — the panel shows the source
  name on every row, and these rows must not be re-exported elsewhere;
- sequential fetches with the shared fetch.Pace throttle.

Inclusion rule (research §6) — a posting is stored only when BOTH:
  title    matches any of feeds.include_title from the search profile
           (data/search_profile.json, lib/profile.py — written by SETUP.md)
  location ~ /(remote|worldwide|europe|poland|emea|\beu\b)/i
Everything else from these boards is skipped so the corpus stays a
job-search corpus instead of a feed mirror. Widen feeds.include_title in the
profile to expand. Empty include_title (or no jobicy_tag) skips the
filter-dependent part instead of mirroring whole feeds.

CLI:  python3 scout/feeds.py [--db data/cvsender.db] [--quiet]
Stdlib only.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from urllib.parse import quote

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "lib"))

import fetch  # noqa: E402  (scout/fetch.py)
import profile as search_profile  # noqa: E402  (lib/profile.py)
import store  # noqa: E402  (lib/store.py)

INCLUDE_LOC = re.compile(r"(remote|worldwide|europe|poland|polska|emea|\beu\b)", re.I)
PACE_BETWEEN_FEEDS_S = 2.0


def _iso(epoch_seconds):
    if not epoch_seconds:
        return None
    return datetime.fromtimestamp(int(epoch_seconds), tz=timezone.utc).isoformat(timespec="seconds")


def _included(title, location, include_title):
    """Inclusion rule: profile-matching title AND remote/EU-ish location."""
    return bool(include_title.search(title or "")) and bool(INCLUDE_LOC.search(location or ""))


def offer_jobicy(j):
    return {
        "job_url": j.get("url"),
        "source": "Jobicy",
        "title": j.get("jobTitle"),
        "company": j.get("companyName"),
        "location": j.get("jobGeo"),
        "posted_at": j.get("pubDate"),
        "level": j.get("jobLevel") or None,
    }


def offer_remotive(j):
    return {
        "job_url": j.get("url"),
        "source": "Remotive",
        "title": j.get("title"),
        "company": j.get("company_name"),
        "location": j.get("candidate_required_location"),
        "posted_at": j.get("publication_date"),
    }


def offer_himalayas(j):
    locs = ", ".join(j.get("locationRestrictions") or []) or None
    seniority = j.get("seniority")
    if isinstance(seniority, (list, tuple)):
        seniority = ", ".join(str(s) for s in seniority)
    return {
        "job_url": j.get("applicationLink"),
        "source": "Himalayas",
        "title": j.get("title"),
        "company": j.get("companyName"),
        "location": locs,
        "salary_min": j.get("minSalary"),
        "salary_max": j.get("maxSalary"),
        "salary_currency": j.get("currency"),
        "salary_period": j.get("salaryPeriod"),
        "posted_at": _iso(j.get("pubDate")),
        "expires_at": _iso(j.get("expiryDate")),
        "level": seniority or None,
    }


def offer_working_nomads(j):
    return {
        "job_url": j.get("url"),
        "source": "Working Nomads",
        "title": j.get("title"),
        "company": j.get("company_name"),
        "location": j.get("location"),
        "posted_at": j.get("pub_date"),
    }


def build_feeds(feeds_cfg):
    """(source name, endpoint, per-item mapper, jobs key — None for a bare list).
    Endpoints that need a profile tag/category are dropped when it is unset."""
    feeds = []
    if feeds_cfg.get("jobicy_tag"):
        feeds.append(("Jobicy", "https://jobicy.com/api/v2/remote-jobs?tag="
                      f"{quote(feeds_cfg['jobicy_tag'])}&count=50", offer_jobicy, "jobs"))
    if feeds_cfg.get("remotive_category"):
        feeds.append(("Remotive", "https://remotive.com/api/remote-jobs?category="
                      f"{quote(feeds_cfg['remotive_category'])}", offer_remotive, "jobs"))
    feeds.append(("Himalayas", "https://himalayas.app/jobs/api?limit=100", offer_himalayas, "jobs"))
    feeds.append(("Working Nomads", "https://www.workingnomads.com/api/exposed_jobs/",
                  offer_working_nomads, None))
    return feeds


def run(db_path, quiet=False):
    feeds_cfg = search_profile.load()["feeds"]
    include_title = search_profile.compile_terms(feeds_cfg["include_title"])
    if include_title is None:
        print("feeds: profile has no feeds.include_title — skipping foreign feeds "
              "(run SETUP.md to create data/search_profile.json)", flush=True)
        return []
    if not search_profile.is_personal() and not quiet:
        print("feeds: WARNING — no data/search_profile.json, filtering with the "
              "EXAMPLE profile (run SETUP.md)", file=sys.stderr)
    conn = store.connect(db_path)
    pace = fetch.Pace(PACE_BETWEEN_FEEDS_S)
    stats = []
    for source, endpoint, mapper, jobs_key in build_feeds(feeds_cfg):
        pace.wait()
        try:
            data = fetch.get_json(endpoint)
        except Exception as e:  # one dead feed must not kill the others
            print(f"{source}: FETCH FAILED ({e})" + ("" if quiet else ""), flush=True)
            stats.append({"source": source, "fetched": 0, "kept": 0, "error": str(e)[:120]})
            continue
        items = data.get(jobs_key) if jobs_key else data
        if isinstance(items, dict):
            items = list(items.values())
        offers, skipped = [], 0
        for j in items or []:
            o = mapper(j)
            if not o.get("job_url") or not o.get("title"):
                skipped += 1
                continue
            if not _included(o["title"], o.get("location") or "", include_title):
                skipped += 1
                continue
            offers.append(o)
        store.upsert_offers(conn, offers)
        total = conn.execute(
            "SELECT COUNT(*) FROM offers WHERE source = ?", (source,)
        ).fetchone()[0]
        if not quiet:
            print(f"{source}: fetched {len(items or [])}, kept {len(offers)} "
                  f"(skipped {skipped} by filter); {source} offers in DB: {total}",
                  flush=True)
        stats.append({"source": source, "fetched": len(items or []),
                      "kept": len(offers), "total": total})
    conn.close()
    return stats


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=os.path.join(REPO_ROOT, "data", "cvsender.db"))
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    run(args.db, args.quiet)


if __name__ == "__main__":
    main()
