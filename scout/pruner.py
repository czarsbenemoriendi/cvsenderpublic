#!/usr/bin/env python3
"""Nightly pruner — keeps the offers corpus bounded (funnel stage 4).

Rules (director-approved funnel architecture):

  a) DELETE  expired AND match_score < SHORTLIST_THRESHOLD AND
             discovered_at older than --days (default 14).
             Rows with no score yet (match_score IS NULL) are never deleted —
             the matcher runs first in the nightly pipeline.
  b) UPDATE  expired AND match_score >= SHORTLIST_THRESHOLD AND state='new'
             -> state='expired'. Kept forever (audit trail), out of the
             shortlist because the shortlist only shows alive offers.

Expired = expires_at (validThrough/expiresAt) strictly in the past. Offers
without any expiry date are never pruned by these rules.

Every deleted URL stays in seen_urls (lib/store.py) — permanent dedup:
nightly dumps never re-insert a pruned offer.

--dry-run prints what WOULD happen and touches nothing.
CLI:  python3 scout/pruner.py --db data/cvsender.db [--dry-run] [--days 14]
Stdlib only.
"""

import argparse
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "lib"))

import store  # noqa: E402  (lib/store.py)

_EXPIRED = "expires_at IS NOT NULL AND julianday(expires_at) < julianday('now')"


def run(db_path, days=14, threshold=store.SHORTLIST_THRESHOLD, dry_run=False,
        quiet=False):
    conn = store.connect(db_path)
    delete_where = (
        f"{_EXPIRED} AND match_score < ? "
        f"AND julianday(discovered_at) < julianday('now', '-' || ? || ' days')"
    )
    doomed = conn.execute(
        f"SELECT job_url, title, company FROM offers WHERE {delete_where}",
        (threshold, days),
    ).fetchall()
    expire_where = f"{_EXPIRED} AND match_score >= ? AND state = 'new'"
    to_expire = conn.execute(
        f"SELECT job_url, title FROM offers WHERE {expire_where}",
        (threshold,),
    ).fetchall()
    if not quiet:
        mode = "WOULD delete" if dry_run else "deleting"
        print(f"pruner: {mode} {len(doomed)} offers "
              f"(expired, score < {threshold}, older than {days}d)")
        for r in doomed[:10]:
            print(f"  - {r['title']} @ {r['company']}  {r['job_url']}")
        if len(doomed) > 10:
            print(f"  … and {len(doomed) - 10} more")
        mode = "WOULD expire" if dry_run else "expiring"
        print(f"pruner: {mode} {len(to_expire)} offers "
              f"(expired, score >= {threshold}, kept as state='expired')")
    if dry_run:
        conn.close()
        return {"would_delete": len(doomed), "would_expire": len(to_expire)}

    with store.write_txn(conn):
        conn.execute(f"DELETE FROM offers WHERE {delete_where}", (threshold, days))
        conn.execute(
            f"UPDATE offers SET state = 'expired' WHERE {expire_where}",
            (threshold,),
        )
    if not quiet:
        print(f"pruner: done (deleted {len(doomed)}, expired {len(to_expire)}); "
              f"seen_urls keeps their hashes — they never come back")
    return {"deleted": len(doomed), "expired": len(to_expire)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=store.DEFAULT_DB)
    ap.add_argument("--days", type=int, default=14,
                    help="min age for deletion (default 14)")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would happen, change nothing")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    run(args.db, args.days, store.SHORTLIST_THRESHOLD, args.dry_run, args.quiet)


if __name__ == "__main__":
    main()
