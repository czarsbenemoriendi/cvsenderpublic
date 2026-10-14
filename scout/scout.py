#!/usr/bin/env python3
"""JustJoin.it browserless scout — sitemap diff + JSON-LD fetcher.

Path (robots.txt-published, research/2026-09-09-data-access.md §1):
  1. GET https://justjoin.it/sitemaps/active-jobs.xml (a sitemap index;
     part files redirect to public.justjoin.com — redirects are followed).
  2. Diff the (url, lastmod) set against offers already in SQLite
     (source_updated_at holds the lastmod we ingested).
  3. Fetch only new/changed offer pages, newest lastmod first, capped per
     run (--max-fetch). Parse the schema.org JobPosting JSON-LD every page
     embeds and upsert it (validThrough gives expiry for free).

Never touches justjoin.it/api/* (robots-disallowed, and 503s anyway).

Usage:
    python3 scout/scout.py [--db data/cvsender.db] [--max-fetch 200] [--full] [--quiet]
Stdlib only.
"""
import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urlparse
from html import unescape as _html_unescape

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "lib"))

import fetch  # noqa: E402  (scout/fetch.py)
import store  # noqa: E402  (lib/store.py)

SITEMAP_INDEX = "https://justjoin.it/sitemaps/active-jobs.xml"
SOURCE = "JustJoin.it"


# ------------------------------------------------------------- sitemaps

def _namespace(tag):
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag

SITEMAP_INDEX = "https://justjoin.it/sitemaps/active-jobs.xml"
EXPIRED_INDEX = "https://justjoin.it/sitemaps/expired-jobs.xml"

def fetch_sitemap_urls(url, pace):
    """Return {url: lastmod} for one sitemap; recurses into sitemap indexes."""
    pace.wait()
    xml_text = fetch.get_text(url)
    root = ET.fromstring(xml_text.encode())
    kind = _namespace(root.tag)
    if kind == "sitemapindex":
        out = {}
        for sm in root:
            if _namespace(sm.tag) != "sitemap":
                continue
            for child in sm:
                if _namespace(child.tag) == "loc":
                    out.update(fetch_sitemap_urls(child.text.strip(), pace))
        return out
    urls = {}
    for sm in root:
        if _namespace(sm.tag) != "url":
            continue
        loc = lastmod = None
        for child in sm:
            name = _namespace(child.tag)
            if name == "loc":
                loc = child.text.strip() if child.text else None
            elif name == "lastmod":
                lastmod = child.text.strip() if child.text else None
        if loc:
            urls[loc] = lastmod
    return urls


# ------------------------------------------------------------- JSON-LD

class _LDParser(HTMLParser):
    """Collect the contents of <script type="application/ld+json"> blocks."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.chunks = []
        self._in_ld = False

    def handle_starttag(self, tag, attrs):
        if tag == "script" and any(
            k == "type" and v and "ld+json" in v for k, v in attrs
        ):
            self._in_ld = True

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_ld = False

    def handle_data(self, data):
        if self._in_ld and data.strip():
            self.chunks.append(data)


def extract_jobposting(html):
    """Return the first schema.org JobPosting dict found in the page, or None."""
    parser = _LDParser()
    parser.feed(html)
    for chunk in parser.chunks:
        try:
            data = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        candidates = data if isinstance(data, list) else [data]
        for node in candidates:
            if isinstance(node, dict):
                graph = node.get("@graph")
                pool = list(graph) if isinstance(graph, list) else [node]
                for item in pool:
                    if isinstance(item, dict) and "JobPosting" in str(
                        item.get("@type", "")
                    ):
                        return item
    return None


def offer_from_jobposting(jp, job_url, lastmod):
    org = jp.get("hiringOrganization") or {}
    salary = jp.get("baseSalary") or {}
    value = salary.get("value") or {}
    url_path = urlparse(job_url).path
    remote = bool(re.search(r"-remote-", url_path))
    cities = ", ".join(
        sorted({p["address"]["addressLocality"] for p in jp.get("jobLocation", [])
                if isinstance(p, dict) and isinstance(p.get("address"), dict)
                and p["address"].get("addressLocality")})
    ) or ("Remote" if remote else None)
    return {
        "job_url": job_url,
        "source": SOURCE,
        "title": _html_unescape(jp.get("title") or "") or None,
        "company": _html_unescape(org.get("name") or "") or None,
        "location": cities,
        "salary_min": value.get("minValue"),
        "salary_max": value.get("maxValue"),
        "salary_currency": salary.get("currency"),
        "salary_period": value.get("unitText"),
        "posted_at": jp.get("datePosted"),
        "expires_at": jp.get("validThrough"),
        "source_updated_at": lastmod,
        "raw_json": json.dumps(jp, ensure_ascii=False),
    }


def fetch_offer(job_url, lastmod, pace):
    """Fetch one offer page and return its offer dict, or None."""
    pace.wait()
    try:
        html = fetch.get_text(job_url)
    except Exception as e:  # noqa: BLE001 — one bad page must not kill the run
        print(f"  ! fetch failed {job_url}: {e}", file=sys.stderr)
        return None
    jp = extract_jobposting(html)
    if jp is None:
        return None
    return offer_from_jobposting(jp, job_url, lastmod)


# ------------------------------------------------------------------ run

def run(db_path, max_fetch=200, full=False, quiet=False):
    conn = store.connect(db_path)
    pace = fetch.Pace()

    if not quiet:
        print(f"fetching sitemap index {SITEMAP_INDEX}")
    sitemap = fetch_sitemap_urls(SITEMAP_INDEX, pace)
    if not quiet:
        print(f"active-jobs sitemap: {len(sitemap)} urls")

    known = {
        r["job_url"]: r["source_updated_at"]
        for r in conn.execute(
            "SELECT job_url, source_updated_at FROM offers WHERE source = ?",
            (SOURCE,),
        )
    }
    todo = [
        (u, m) for u, m in sitemap.items()
        if u not in known or (m and known.get(u) != m)
    ]
    todo.sort(key=lambda um: um[1] or "", reverse=True)  # newest lastmod first
    backlog = len(todo)
    if not full:
        todo = todo[:max_fetch]
    if not quiet:
        print(f"new/changed vs store: {backlog} (fetching newest "
              f"{'all' if full else max_fetch})")

    upserted = 0
    batch = []
    for u, m in todo:
        offer = fetch_offer(u, m, pace)
        if offer:
            batch.append(offer)
            upserted += 1
            if not quiet:
                sal = f"{offer['salary_min'] or '?'}-{offer['salary_max'] or '?'} {offer['salary_currency'] or ''}/{offer['salary_period'] or '?'}"
                print(f"  + {offer['title']} @ {offer['company']} ({sal}) validThrough={offer['expires_at']}")
        if len(batch) >= 50:
            store.upsert_offers(conn, batch)
            batch = []
    if batch:
        store.upsert_offers(conn, batch)
    total = conn.execute(
        "SELECT COUNT(*) FROM offers WHERE source = ?", (SOURCE,)
    ).fetchone()[0]
    conn.close()
    if not quiet:
        print(f"upserted {upserted}; {SOURCE} offers in DB: {total}")
    return {"sitemap": len(sitemap), "fetched": upserted, "total": total}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=store.DEFAULT_DB)
    ap.add_argument("--max-fetch", type=int, default=200)
    ap.add_argument("--full", action="store_true",
                    help="fetch every new/changed offer (first run can take ~2h at 0.75s/req)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    run(args.db, args.max_fetch, args.full, args.quiet)


if __name__ == "__main__":
    main()
