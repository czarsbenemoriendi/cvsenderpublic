#!/usr/bin/env python3
"""Search-profile loader for CVSender — WHO we are searching for.

The profile lives in data/search_profile.json (personal, gitignored;
template: data/search_profile.example.json, tracked). SETUP.md writes it
from the onboarding questionnaire + CV; the matcher (scoring), the foreign
feeds (inclusion filter) and the cvskill workflow (search keywords) read it
instead of carrying one person's stack hardcoded in the code.

    {
      "role": "DevOps Engineer",
      "search_keywords": ["devops", "sre", "kubernetes"],   // skill + links.md
      "scoring": [                                           // matcher rules
        {"id": "core-role", "label": "DevOps/SRE",
         "terms": ["devops", "sre"], "where": "title", "delta": 25},
        {"id": "unwanted-stack", "label": "Java/.NET",
         "terms": ["java", ".net"], "where": "musthave", "delta": -30}
      ],
      "location": {
        "remote_bonus": 20,            // "remote" in title/location
        "eu_remote_bonus": 20,         // Europe/Poland/worldwide region
        "onsite_penalty": -20,         // on-site in a listed city, no remote
        "onsite_penalty_cities": ["warszawa", "kraków"]
      },
      "feeds": {
        "include_title": ["devops", "sre", "platform"],  // keep-if-title-matches
        "jobicy_tag": "devops",
        "remotive_category": "devops"
      }
    }

Rule "where" values (what text a term is searched in):
  title     — offer title only
  musthave  — title + first 200 chars of the requirements text
  text      — title + matcher notes + full JSON-LD description

Terms are matched case-insensitively on word boundaries; a term may also be
a regex when prefixed with "re:" (e.g. "re:full.?stack").

API:  load() -> dict (merged with DEFAULTS), compile_terms(terms) -> re.Pattern
CLI:  python3 lib/profile.py   (prints the effective profile and its source)
Stdlib only.
"""

import json
import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE_PATH = os.path.join(BASE_DIR, "data", "search_profile.json")
EXAMPLE_PROFILE_PATH = os.path.join(BASE_DIR, "data", "search_profile.example.json")

WHERE_VALUES = ("title", "musthave", "text")

DEFAULT_LOCATION = {
    "remote_bonus": 20,
    "eu_remote_bonus": 20,
    "onsite_penalty": -20,
    "onsite_penalty_cities": [],
}

DEFAULT_FEEDS = {
    "include_title": [],
    "jobicy_tag": None,
    "remotive_category": "software-dev",
}


def profile_path():
    """Path actually used: the personal profile, else the tracked example."""
    return PROFILE_PATH if os.path.exists(PROFILE_PATH) else EXAMPLE_PROFILE_PATH


def is_personal():
    return os.path.exists(PROFILE_PATH)


def load():
    with open(profile_path(), encoding="utf-8") as f:
        raw = json.load(f)
    profile = {
        "role": raw.get("role") or "",
        "search_keywords": list(raw.get("search_keywords") or []),
        "scoring": [],
        "location": dict(DEFAULT_LOCATION, **(raw.get("location") or {})),
        "feeds": dict(DEFAULT_FEEDS, **(raw.get("feeds") or {})),
    }
    for i, rule in enumerate(raw.get("scoring") or []):
        terms = [t for t in (rule.get("terms") or []) if t]
        where = rule.get("where") or "title"
        if not terms:
            continue
        if where not in WHERE_VALUES:
            raise ValueError(f"scoring[{i}].where must be one of {WHERE_VALUES}, got {where!r}")
        profile["scoring"].append({
            "id": rule.get("id") or f"rule-{i}",
            "label": rule.get("label") or ", ".join(terms[:3]),
            "terms": terms,
            "where": where,
            "delta": int(rule.get("delta") or 0),
        })
    return profile


def _term_pattern(term):
    if term.startswith("re:"):
        return term[3:]
    escaped = re.escape(term)
    # \b only works next to word chars; ".net" / "c++" need lookarounds instead.
    left = r"\b" if term[0].isalnum() else r"(?<!\w)"
    right = r"\b" if term[-1].isalnum() else r"(?!\w)"
    return f"{left}{escaped}{right}"


def compile_terms(terms):
    """One case-insensitive alternation for a list of terms; None if empty."""
    terms = [t for t in terms or [] if t]
    if not terms:
        return None
    return re.compile("|".join(f"(?:{_term_pattern(t)})" for t in terms), re.I)


def main():
    profile = load()
    source = "personal" if is_personal() else "EXAMPLE (run SETUP.md to create data/search_profile.json)"
    print(f"# profile source: {source} — {profile_path()}")
    print(json.dumps(profile, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
