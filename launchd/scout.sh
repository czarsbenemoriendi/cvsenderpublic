#!/bin/bash
# CVSender nightly scout wrapper for launchd.
#
# launchd runs binaries directly — no shell profile, minimal PATH — so this
# wrapper self-locates the repo, pins the interpreter, and tolerates the
# scrubbed environment (`env -i`). Logs go to data/logs/ (created on demand).
#
# Manual test outside launchd (env hygiene dry-run):
#   /usr/bin/env -i HOME="$HOME" PATH=/usr/bin:/bin:/usr/sbin:/sbin \
#       "$PWD/launchd/scout.sh"

# Repo root = parent of this script's directory (no machine-specific paths).
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Interpreter: CVSENDER_PYTHON wins, then the Python.org framework build,
# then whatever python3 is on PATH (launchd's minimal PATH included).
PY="${CVSENDER_PYTHON:-/Library/Frameworks/Python.framework/Versions/3.14/bin/python3}"
[ -x "$PY" ] || PY="$(command -v python3)"

LOGDIR="$REPO/data/logs"
DB="$REPO/data/cvsender.db"

mkdir -p "$LOGDIR"

# One scout at a time (atomic mkdir lock; launchd normally coalesces
# overlapping fires of the same label, but a wake-from-sleep re-fire can
# still race a long stalled run — this is belt and suspenders).
LOCKDIR="$LOGDIR/scout.lock"
if ! mkdir "$LOCKDIR" 2>/dev/null; then
    echo "$(date -u +%FT%TZ) another scout run is active, exiting" >&2
    exit 0
fi
trap 'rmdir "$LOCKDIR" 2>/dev/null' EXIT
echo "$(date -u +%FT%TZ) scout run starting (db=$DB)"

# Stage 1: JustJoin.it sitemap scout (new/changed offers into the corpus).
"$PY" "$REPO/scout/scout.py" --db "$DB" \
    || echo "$(date -u +%FT%TZ) jjit scout failed (non-fatal)" >&2

# Stage 2: NoFluffJobs dump (the nightly 1-request budget).
"$PY" "$REPO/scout/nfj.py" --db "$DB" \
    || echo "$(date -u +%FT%TZ) nfj dump failed (non-fatal)" >&2

# Stage 2.5: foreign remote-job feeds (Jobicy/Remotive/Himalayas/Working Nomads).
"$PY" "$REPO/scout/feeds.py" --db "$DB" \
    || echo "$(date -u +%FT%TZ) foreign feeds failed (non-fatal)" >&2

# Stage 3: incremental CV matcher (scores new/updated offers against the CV).
# Fresh install: matcher seeds the empty DB from the nightly dumps itself.
"$PY" "$REPO/scout/matcher.py" --db "$DB"

# Stage 4: nightly pruner (delete stale low-scorers, expire kept high-scorers).
"$PY" "$REPO/scout/pruner.py" --db "$DB"

# Stage 5 (optional): ATS watchlist poll (only if user configured companies).
if [ -f "$REPO/data/watchlist.json" ]; then
    "$PY" "$REPO/scout/ats.py" --db "$DB" || echo "$(date -u +%FT%TZ) ats poll failed (non-fatal)" >&2
fi

echo "$(date -u +%FT%TZ) scout run finished"
# macOS notification with the fresh-queue size (best effort, never fails the run).
NEW=$("$PY" - "$DB" <<'EOF'
import sqlite3, sys
try:
    conn = sqlite3.connect(sys.argv[1])
    n = conn.execute(
        "SELECT COUNT(*) FROM offers WHERE decision='pending' "
        "AND discovered_at >= date('now','-1 day')").fetchone()[0]
    print(n)
except Exception:
    print(0)
EOF
) || NEW=0
osascript -e "display notification \"CVSender scout: ${NEW} nowych ofert w kolejce\" with title \"CVSender\" sound name \"Glass\"" >/dev/null 2>&1 || true
