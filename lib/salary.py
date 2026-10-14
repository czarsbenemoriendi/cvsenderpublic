#!/usr/bin/env python3
"""Salary-answer resolver for CVSender — what number to type into a form.

Policy lives in data/salary_policy.json (personal, gitignored; template:
data/salary_policy.example.json, tracked):

    {
      "default_net_pln": 14000,      // your default monthly net answer
      "band_strategy": "midpoint",   // how to use the offer's own band
      "hourly_divisor": 160,         // monthly net -> your hourly equivalent
      "overrides": {                 // longest job_url substring wins
        "some-company-slug": 15000
      }
    }

Rules encoded (SKILL.md hard rule 6):
- offer band in PLN/month  -> midpoint of the band ("midpoint" strategy)
- offer band in PLN/hour   -> your hourly equivalent (default/divisor),
  UNLESS the offer's hourly floor is higher -> use the offer's floor
- override substring match -> that value (PLN/month; converted for hourly
  forms via hourly_divisor)
- no band, no override     -> default_net_pln
- non-PLN currency         -> manual (never invent an FX rate)

CLI:  python3 lib/salary.py <job_url> [salary_min] [salary_max] [currency] [period]
API:  resolve(offer_dict) -> {"value", "unit", "source", "note"}
Stdlib only.
"""

import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLICY_PATH = os.path.join(BASE_DIR, "data", "salary_policy.json")
EXAMPLE_POLICY_PATH = os.path.join(BASE_DIR, "data", "salary_policy.example.json")

DEFAULTS = {
    "default_net_pln": 14000,
    "band_strategy": "midpoint",
    "hourly_divisor": 160,
    "overrides": {},
}

# A band midpoint this far above the default is suspicious (auto-renewed
# seniority inflation, different role level) — flag for human review instead
# of silently typing a big number (rule 6: "never inflate").
MIDPOINT_REVIEW_RATIO = 1.5


def load_policy():
    path = POLICY_PATH if os.path.exists(POLICY_PATH) else EXAMPLE_POLICY_PATH
    with open(path, encoding="utf-8") as f:
        policy = json.load(f)
    merged = dict(DEFAULTS)
    merged.update(policy)
    return merged


def resolve(offer):
    """offer: dict with job_url, salary_min/max, salary_currency, salary_period
    (store.offers shape; CSV-ish names are tolerated). Returns a decision dict."""
    policy = load_policy()
    default = policy["default_net_pln"]
    divisor = policy["hourly_divisor"] or 160
    job_url = str(offer.get("job_url") or offer.get("URL") or "")
    lo = offer.get("salary_min")
    hi = offer.get("salary_max")
    currency = (offer.get("salary_currency") or "PLN" or "").upper()
    period = (offer.get("salary_period") or "Month" or "").capitalize()

    if currency != "PLN":
        return {"value": None, "unit": currency, "source": "manual",
                "note": f"non-PLN currency ({currency}) — never invent an FX "
                        f"rate; use the user's stated policy for this currency"}

    # overrides: longest matching substring wins
    override_value = None
    for needle, value in (policy.get("overrides") or {}).items():
        if needle and needle in job_url and (override_value is None or len(needle) > override_value[1]):
            override_value = (value, len(needle))

    if period == "Hour":
        own_hourly = round(default / divisor, 1)
        if override_value is not None:
            return {"value": round(override_value[0] / divisor, 1),
                    "unit": "PLN/hour", "source": "override",
                    "note": f"override {override_value[0]} PLN/month / {divisor}h"}
        floor = _num(lo)
        if floor and own_hourly and floor > own_hourly:
            return {"value": floor, "unit": "PLN/hour", "source": "offer-floor",
                    "note": f"offer floor {floor} > own hourly {own_hourly} (rule 6)"}
        return {"value": own_hourly, "unit": "PLN/hour", "source": "default",
                "note": f"default {default}/month / {divisor}h"}

    # monthly form
    if override_value is not None:
        return {"value": override_value[0], "unit": "PLN/month",
                "source": "override", "note": "job_url override"}
    if _num(lo) and _num(hi) and policy["band_strategy"] == "midpoint":
        mid = round((_num(lo) + _num(hi)) / 2)
        if mid > default * MIDPOINT_REVIEW_RATIO:
            return {"value": mid, "unit": "PLN/month",
                    "source": "offer-midpoint",
                    "note": f"REVIEW: midpoint {mid} >> default {default} — "
                            f"confirm role level before submitting"}
        return {"value": mid, "unit": "PLN/month", "source": "offer-midpoint",
                "note": f"midpoint of {lo}-{hi}"}
    return {"value": default, "unit": "PLN/month", "source": "default",
            "note": "no band/override — policy default"}


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    offer = {
        "job_url": sys.argv[1],
        "salary_min": sys.argv[2] if len(sys.argv) > 2 else None,
        "salary_max": sys.argv[3] if len(sys.argv) > 3 else None,
        "salary_currency": sys.argv[4] if len(sys.argv) > 4 else None,
        "salary_period": sys.argv[5] if len(sys.argv) > 5 else None,
    }
    print(json.dumps(resolve(offer), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
