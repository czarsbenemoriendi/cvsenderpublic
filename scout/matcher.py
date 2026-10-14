#!/usr/bin/env python3
"""Incremental CV matcher — scores offers 0-100 against the search profile.

Funnel stage between the scouts and the pruner: reads the offers corpus,
writes offers.match_score + offers.match_reasons (JSON array of
{"rule", "delta"}). The shortlist the human sees is DERIVED, not stored:
match_score >= store.SHORTLIST_THRESHOLD (60) AND decision='pending' AND
offer not expired.

Scoring heuristics (deterministic, no network, documented in
SESSION_STATUS.md). Role/stack rules are NOT hardcoded — they come from the
search profile (data/search_profile.json, written by SETUP.md from the
onboarding questionnaire + CV; schema in lib/profile.py):

  ±N   each profile "scoring" rule whose terms hit its "where" text
       (title / musthave = title + first 200 chars of requirements /
       text = title + notes + JSON-LD description)
  +N   location.remote_bonus — "remote" in title or location
  +N   location.eu_remote_bonus — Europe/Poland/EMEA/worldwide/EU-country
       region in title or location (stacks with the remote rule)
  +10  salary band midpoint >= default_net_pln PLN/month (hourly bands x
       hourly_divisor from lib/salary.py policy; non-PLN never scores)
  -N   location.onsite_penalty — on-site in a profile-listed city when
       remote is not stated
  -100 expired (expires_at in the past)

Total clamped to 0-100. Each reason carries a human "label" the panel shows.
After editing the profile, rescore with --full.

Incremental cursor: meta.last_matched_at. A row is (re)scored when it is
new or updated since the cursor (COALESCE(source_updated_at, discovered_at)
> cursor) or was never scored (match_score IS NULL). --full ignores the
cursor and rescores everything (19k rows in seconds). The cursor advances
only after a successful scoring commit, so an interrupted run self-heals.

CLI:  python3 scout/matcher.py --db data/cvsender.db [--full]
      python3 scout/matcher.py --try "Senior DevOps Engineer" [--location "Remote, Poland"]
          [--salary 18000-24000] [--description "..."]
          — score one hypothetical offer and print the breakdown (no DB);
          SETUP.md uses it to show the user how their profile scores offers.
Stdlib only.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "lib"))

import profile as search_profile  # noqa: E402  (lib/profile.py)
import salary  # noqa: E402  (lib/salary.py — policy + band parsing)
import store  # noqa: E402  (lib/store.py)

CURSOR_KEY = "last_matched_at"

RULE_REMOTE = "remote"
RULE_EU_REMOTE = "location-eu-remote"
RULE_SALARY = "salary-midpoint"
RULE_ONSITE = "onsite-city"
RULE_EXPIRED = "expired"
_EU_REMOTE_LOCATION = re.compile(
    r"\b(europe|european union|poland|polska|emea|worldwide|anywhere|\beu\b"
    r"|germany|netherlands|france|spain|portugal|italy|austria|belgium"
    r"|denmark|sweden|norway|finland|ireland|czech\w*|hungary|bulgaria"
    r"|romania|croatia|slovenia|slovakia|estonia|latvia|lithuania"
    r"|luxembourg|malta|cyprus)\b", re.I)
_HTML_TAGS = re.compile(r"<[^>]+>")


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _expired(expires_at):
    if not expires_at:
        return False
    try:
        exp = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
    except ValueError:
        return False  # malformed date never deletes/score-kills by itself
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    return exp < datetime.now(timezone.utc)


def _description(raw_json):
    """Requirements/description text from the stored JSON-LD (JJIT), if any."""
    if not raw_json:
        return ""
    try:
        data = json.loads(raw_json)
    except (TypeError, ValueError):
        return ""
    desc = data.get("description") if isinstance(data, dict) else None
    if not isinstance(desc, str):
        return ""
    return _HTML_TAGS.sub(" ", desc)


def compile_profile(profile):
    """Precompile profile rules once per run: (rules, onsite_cities_re, location)."""
    rules = []
    for rule in profile["scoring"]:
        pattern = search_profile.compile_terms(rule["terms"])
        if pattern is not None and rule["delta"]:
            rules.append(dict(rule, pattern=pattern))
    location = profile["location"]
    cities = search_profile.compile_terms(location.get("onsite_penalty_cities"))
    return {"rules": rules, "cities": cities, "location": location}


def score_offer(offer, policy, compiled):
    """Return (score 0-100, reasons list). Deterministic pure function."""
    title = offer["title"] or ""
    location = (offer["location"] or "").lower()
    notes = offer["match"] or ""
    desc = _description(offer["raw_json"])
    loc_cfg = compiled["location"]
    reasons = []

    haystacks = {
        "title": title,
        # Must-have context heuristic: title or first 200 chars of requirements.
        "musthave": " ".join((title, desc[:200] or notes[:200])),
        "text": " ".join((title, notes, desc)),
    }
    for rule in compiled["rules"]:
        if rule["pattern"].search(haystacks[rule["where"]]):
            reasons.append({"rule": rule["id"], "label": rule["label"], "delta": rule["delta"]})

    # Foreign boards encode region/remote in the title ("Senior Engineer |
    # Remote - Europe | TS/Vue"), so both signals scan title + location.
    region_haystack = " ".join((title, location)).lower()
    remote = "remote" in region_haystack
    if remote and loc_cfg["remote_bonus"]:
        reasons.append({"rule": RULE_REMOTE, "label": "Zdalnie",
                        "delta": loc_cfg["remote_bonus"]})

    # EU-remote: a Europe/Poland/worldwide hiring region opens the role to a
    # Poland-based contractor even when the literal word "remote" is absent.
    if loc_cfg["eu_remote_bonus"] and _EU_REMOTE_LOCATION.search(region_haystack):
        reasons.append({"rule": RULE_EU_REMOTE, "label": "Region EU/PL",
                        "delta": loc_cfg["eu_remote_bonus"]})

    # Salary band midpoint in PLN/month (salary.py policy: hourly x divisor).
    lo, hi = _num(offer["salary_min"]), _num(offer["salary_max"])
    currency = (offer["salary_currency"] or "PLN").upper()
    period = (offer["salary_period"] or "Month").capitalize()
    if currency == "PLN" and (lo is not None or hi is not None):
        mid = ((lo if lo is not None else hi) + (hi if hi is not None else lo)) / 2
        if period == "Hour":
            mid *= policy["hourly_divisor"] or 160
        if period in ("Month", "Hour") and mid >= policy["default_net_pln"]:
            reasons.append({"rule": RULE_SALARY,
                            "label": f"Stawka ≥ {policy['default_net_pln'] / 1000:g}k",
                            "delta": 10})

    if (not remote and loc_cfg["onsite_penalty"] and compiled["cities"] is not None
            and compiled["cities"].search(location)):
        reasons.append({"rule": RULE_ONSITE, "label": "Stacjonarnie (miasto spoza preferencji)",
                        "delta": loc_cfg["onsite_penalty"]})

    if _expired(offer["expires_at"]):
        reasons.append({"rule": RULE_EXPIRED, "label": "Wygasła", "delta": -100})

    total = max(0, min(100, sum(r["delta"] for r in reasons)))
    return total, reasons


def run(db_path, full=False, quiet=False):
    conn = store.connect(db_path)
    policy = salary.load_policy()
    compiled = compile_profile(search_profile.load())
    if not search_profile.is_personal() and not quiet:
        print("matcher: WARNING — no data/search_profile.json, scoring with the "
              "EXAMPLE profile (run SETUP.md)", file=sys.stderr)
    cursor = store.meta_get(conn, CURSOR_KEY)

    if full or not cursor:
        where = ""
        args = ()
    else:
        where = ("WHERE COALESCE(source_updated_at, discovered_at) > ? "
                 "OR match_score IS NULL")
        args = (cursor,)

    rows = conn.execute(
        f"""
        SELECT job_url, title, location, salary_min, salary_max,
               salary_currency, salary_period, expires_at, match, raw_json
        FROM offers {where}
        """,
        args,
    ).fetchall()

    updates = []
    for r in rows:
        score, reasons = score_offer(dict(r), policy, compiled)
        updates.append((score, json.dumps(reasons, ensure_ascii=False), r["job_url"]))

    with store.write_txn(conn):
        conn.executemany(
            "UPDATE offers SET match_score = ?, match_reasons = ? WHERE job_url = ?",
            updates,
        )
        # inline meta_set — write_txn must not nest
        conn.execute(
            "INSERT INTO meta(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (CURSOR_KEY, store.utcnow()),
        )

    shortlist = conn.execute(
        """
        SELECT COUNT(*) FROM offers
        WHERE match_score >= ? AND decision = 'pending'
          AND NOT (expires_at IS NOT NULL AND julianday(expires_at) < julianday('now'))
        """,
        (store.SHORTLIST_THRESHOLD,),
    ).fetchone()[0]
    conn.close()

    if not quiet:
        print(f"matcher: cursor was {cursor or 'none'}; "
              f"processed {len(rows)}, scored {len(updates)}; "
              f"shortlist (score >= {store.SHORTLIST_THRESHOLD}, pending, alive): "
              f"{shortlist}")
    return {"processed": len(rows), "scored": len(updates), "shortlist": shortlist}


def try_offer(title, location="", salary_band=None, description=""):
    """Score one hypothetical offer against the current profile; print why."""
    lo = hi = None
    if salary_band:
        parts = [p.strip().replace(" ", "") for p in salary_band.split("-")]
        lo = float(parts[0])
        hi = float(parts[-1])
    offer = {
        "title": title, "location": location, "match": "",
        "raw_json": json.dumps({"description": description}) if description else None,
        "salary_min": lo, "salary_max": hi, "salary_currency": "PLN",
        "salary_period": "Month", "expires_at": None,
    }
    profile = search_profile.load()
    score, reasons = score_offer(offer, salary.load_policy(), compile_profile(profile))
    source = "" if search_profile.is_personal() else "  [EXAMPLE profile]"
    verdict = "KOLEJKA" if score >= store.SHORTLIST_THRESHOLD else "poza kolejką"
    print(f"{score:>3} pkt  {verdict} (próg {store.SHORTLIST_THRESHOLD})  — "
          f"{title} | {location or 'brak lokalizacji'}{source}")
    for r in reasons:
        print(f"       {r['delta']:+4d}  {r['label']}")
    return score, reasons


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=store.DEFAULT_DB)
    ap.add_argument("--full", action="store_true",
                    help="rescore every row, ignoring the incremental cursor")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--try", dest="try_title", metavar="TITLE",
                    help="score one hypothetical offer title and print the breakdown")
    ap.add_argument("--location", default="")
    ap.add_argument("--salary", metavar="MIN-MAX", help="PLN/month band, e.g. 18000-24000")
    ap.add_argument("--description", default="")
    args = ap.parse_args()
    if args.try_title:
        try_offer(args.try_title, args.location, args.salary, args.description)
        return
    run(args.db, args.full, args.quiet)


if __name__ == "__main__":
    main()
