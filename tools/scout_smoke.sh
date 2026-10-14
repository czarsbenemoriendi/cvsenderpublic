#!/usr/bin/env bash
# Scout smoke test — runs every scout stage against the LIVE endpoints into a
# THROWAWAY sqlite db (never touches data/cvsender.db).
#
# Usage:  bash tools/scout_smoke.sh
#
# Expected output shape (numbers vary with live data; from the 2026-09-09 run):
#   [1/3] JJIT sitemap -> JSON-LD
#   fetching sitemap index https://justjoin.it/sitemaps/active-jobs.xml
#   active-jobs sitemap: ~10500 urls
#   new/changed vs store: N (fetching newest 3)
#     + <title> @ <company> (<salary band>) validThrough=<iso>
#   upserted 3; JustJoin.it offers in DB: 3
#   [2/3] NFJ /api/posting dump (~145 MB, capped at 5 rows)
#   postings in dump: 5 (totalCount=~18500)
#   upserted 5; NoFluffJobs offers in DB: 5
#   [3/3] expiry pre-check on one JJIT offer
#   { "verdict": "alive", "signal": "sitemap"|"native-field", ... }
#   SMOKE PASSED
#
# Runtime: ~1-2 min (dominated by the NFJ dump download + sitemap politeness
# sleeps). Exit code 0 on success, 1 on the first failing stage.

set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
SMOKE_DB="$(mktemp -d /tmp/cvsender-smoke.XXXXXX)/smoke.db"
trap 'rm -rf "$(dirname "$SMOKE_DB")"' EXIT

echo "[1/3] JJIT sitemap -> JSON-LD"
python3 "$REPO/scout/scout.py" --db "$SMOKE_DB" --max-fetch 3

echo "[2/3] NFJ /api/posting dump (~145 MB, capped at 5 rows)"
python3 "$REPO/scout/nfj.py" --db "$SMOKE_DB" --limit 5

echo "[3/3] expiry pre-check on one JJIT offer"
JJIT_URL=$(python3 - "$SMOKE_DB" <<'EOF'
import sqlite3, sys
conn = sqlite3.connect(sys.argv[1])
row = conn.execute(
    "SELECT job_url FROM offers WHERE source='JustJoin.it' LIMIT 1").fetchone()
print(row[0] if row else "")
EOF
)
if [ -z "$JJIT_URL" ]; then
    echo "smoke: no JJIT url stored in stage 1" >&2
    exit 1
fi
python3 "$REPO/scout/expiry.py" --db "$SMOKE_DB" --no-probe "$JJIT_URL"

echo "SMOKE PASSED"
