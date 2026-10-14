#!/usr/bin/env python3
"""ATS watchlist scout — poll public board APIs of target companies.

All six endpoints are published-for-consumption (green board in
research/2026-09-09-data-access.md §6); no keys, no scraping. Rows land in
the shared SQLite offers table with source = "ats-<vendor>", so the queue,
the panel and the expiry pre-check treat them like any other offer.
UNIQUE(job_url) dedupes across vendors automatically.

Watchlist: data/watchlist.json (personal, gitignored; template:
data/watchlist.example.json, tracked). Each company carries any subset of:

    greenhouse      boards-api.greenhouse.io/v1/boards/{slug}/jobs
    lever           api.lever.co/v0/postings/{slug}?mode=json
    workable        apply.workable.com/api/v1/widget/accounts/{slug}?details=true
    smartrecruiters api.smartrecruiters.com/v1/companies/{id}/postings
    ashby           api.ashbyhq.com/posting-api/job-board/{org}
    teamtailor      careers.{host}/jobs.json      (host, not slug)

Usage:
    python3 scout/ats.py [--db data/cvsender.db] [--company GitLab] [--quiet]
Stdlib only.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "lib"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import fetch  # noqa: E402  (scout/fetch.py)
import store  # noqa: E402  (lib/store.py)

WATCHLIST_PATH = os.path.join(REPO_ROOT, "data", "watchlist.json")
WATCHLIST_EXAMPLE = os.path.join(REPO_ROOT, "data", "watchlist.example.json")

# per-board page caps — a first sync of a huge board must not run forever
MAX_JOBS_PER_BOARD = 500


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------- fetchers
# Each fetcher: slug -> list of normalized offer dicts (store.offers shape,
# minus company/discovered_at which the caller fills in).

def fetch_greenhouse(slug, company):
    data = fetch.get_json(
        f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=false")
    out = []
    for j in (data.get("jobs") or [])[:MAX_JOBS_PER_BOARD]:
        out.append({
            "job_url": j["absolute_url"],
            "source": "ats-greenhouse",
            "title": j.get("title"),
            "company": company,
            "location": (j.get("location") or {}).get("name"),
            "posted_at": j.get("updated_at") or j.get("first_published"),
        })
    return out


def fetch_lever(slug, company):
    data = fetch.get_json(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    out = []
    for j in data[:MAX_JOBS_PER_BOARD]:
        created = j.get("createdAt")
        posted = None
        if created:
            posted = datetime.fromtimestamp(
                created / 1000, tz=timezone.utc).isoformat(timespec="seconds")
        out.append({
            "job_url": j.get("hostedUrl"),
            "source": "ats-lever",
            "title": j.get("text"),
            "company": company,
            "location": (j.get("categories") or {}).get("location"),
            "posted_at": posted,
        })
    return out


def fetch_workable(slug, company):
    data = fetch.get_json(
        f"https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true")
    out = []
    for j in (data.get("jobs") or [])[:MAX_JOBS_PER_BOARD]:
        loc = j.get("location") or {}
        city = ", ".join(str(loc.get(k)) for k in ("city", "country") if loc.get(k))
        out.append({
            "job_url": j.get("url") or j.get("shortlink"),
            "source": "ats-workable",
            "title": j.get("title"),
            "company": company,
            "location": city or None,
            "posted_at": j.get("published_on"),
        })
    return out


def fetch_smartrecruiters(slug, company):
    data = fetch.get_json(
        f"https://api.smartrecruiters.com/v1/companies/{slug}/postings")
    out = []
    for j in (data.get("content") or [])[:MAX_JOBS_PER_BOARD]:
        ref = j.get("ref") or ""
        loc = j.get("location") or {}
        city = ", ".join(str(loc.get(k)) for k in ("city", "country") if loc.get(k))
        out.append({
            "job_url": f"https://jobs.smartrecruiters.com{ref}" if ref else None,
            "source": "ats-smartrecruiters",
            "title": j.get("name"),
            "company": company,
            "location": city or None,
            "posted_at": j.get("releasedDate"),
        })
    return [o for o in out if o["job_url"]]


def fetch_ashby(slug, company):
    data = fetch.get_json(
        f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
    out = []
    for j in (data.get("jobs") or [])[:MAX_JOBS_PER_BOARD]:
        if j.get("isClosed"):
            continue
        out.append({
            "job_url": j.get("jobUrl"),
            "source": "ats-ashby",
            "title": j.get("title"),
            "company": company,
            "location": j.get("location"),
            "posted_at": j.get("publishedAt"),
        })
    return [o for o in out if o["job_url"]]


def fetch_teamtailor(host, company):
    data = fetch.get_json(f"https://careers.{host}/jobs.json")
    out = []
    for j in (data.get("items") or [])[:MAX_JOBS_PER_BOARD]:
        out.append({
            "job_url": j.get("url"),
            "source": "ats-teamtailor",
            "title": j.get("title"),
            "company": company,
            "posted_at": j.get("date_published"),
        })
    return [o for o in out if o["job_url"]]


FETCHERS = {
    "greenhouse": ("greenhouse", fetch_greenhouse),
    "lever": ("lever", fetch_lever),
    "workable": ("workable", fetch_workable),
    "smartrecruiters": ("smartrecruiters", fetch_smartrecruiters),
    "ashby": ("ashby", fetch_ashby),
    "teamtailor": ("teamtailor", fetch_teamtailor),
}


def load_watchlist(path=WATCHLIST_PATH):
    if not os.path.exists(path):
        path = WATCHLIST_EXAMPLE
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("companies") or []


def run(db_path, only_company=None, quiet=False):
    conn = store.connect(db_path)
    pace = fetch.Pace()
    total_new = 0
    for entry in load_watchlist():
        company = entry.get("name") or "?"
        if only_company and company.lower() != only_company.lower():
            continue
        for vendor, (slug_key, fn) in FETCHERS.items():
            slug = entry.get(slug_key)
            if not slug:
                continue
            try:
                offers = fn(slug, company)
            except Exception as e:  # noqa: BLE001 — one dead board must not kill the run
                if not quiet:
                    print(f"  ! {company}/{vendor}: {e}", file=sys.stderr)
                continue
            for o in offers:
                o.setdefault("discovered_at", store.utcnow())
            store.upsert_offers(conn, offers)
            total_new += len(offers)
            if not quiet:
                print(f"  {company} [{vendor}] {slug}: {len(offers)} postings")
            pace.wait()
    total = conn.execute("SELECT COUNT(*) FROM offers").fetchone()[0]
    conn.close()
    if not quiet:
        print(f"watchlist sync done: {total_new} postings upserted; offers in DB: {total}")
    return total_new


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=store.DEFAULT_DB)
    ap.add_argument("--company", default=None, help="sync a single company")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    run(args.db, args.company, args.quiet)


if __name__ == "__main__":
    main()
