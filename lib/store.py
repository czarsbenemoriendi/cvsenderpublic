#!/usr/bin/env python3
"""SQLite (WAL) store for CVSender — offers queue, applications log, meta.

Becomes the source of truth; the two CSVs remain a readable fallback and a
migration source (tools/migrate_csv_to_sqlite.py).

Concurrency model (research/2026-09-09-orchestration-tooling.md §3):
- journal_mode=WAL  — readers never block the writer, the writer never
  blocks readers; one writer at a time (same-host only).
- busy_timeout=5000 — a second writer waits instead of failing instantly.
- write_txn()       — every write runs inside BEGIN IMMEDIATE, so
  transactions are serialized up-front and never fail with the
  deferred-upgrade flavour of SQLITE_BUSY.
- UNIQUE(job_url)   — dedupe is a constraint, not a procedure.

State machine on applications.state:
  applied → verified → screening → interview → offer | rejected | expired
Offer lifecycle on offers.state (machine/bookkeeping column, separate from
the human decision column): new → expired/archived. Shortlisted is derived,
not stored: match_score >= SHORTLIST_THRESHOLD and decision='pending' and
a live expiry. seen_urls is the permanent dedup table — URLs pruned out of
offers never re-enter the corpus.
Stdlib only (sqlite3, contextlib, hashlib, datetime, os).
"""

import contextlib
import hashlib
import os
import re
import sqlite3
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB = os.path.join(BASE_DIR, "data", "cvsender.db")

BUSY_TIMEOUT_MS = 5000

# Funnel threshold: match_score >= SHORTLIST_THRESHOLD plus decision='pending'
# plus a live expiry defines the shortlist the human sees (scout/matcher.py).
SHORTLIST_THRESHOLD = 60

SCHEMA = """
CREATE TABLE IF NOT EXISTS offers (
    id            INTEGER PRIMARY KEY,
    job_url       TEXT NOT NULL UNIQUE,
    source        TEXT,
    title         TEXT,
    company       TEXT,
    location      TEXT,
    salary_min    REAL,
    salary_max    REAL,
    salary_currency TEXT,
    salary_period TEXT,
    posted_at     TEXT,
    expires_at    TEXT,
    status        TEXT NOT NULL DEFAULT 'new',
    decision      TEXT NOT NULL DEFAULT 'pending',
    level         TEXT,
    match         TEXT,
    notes         TEXT,
    raw_json      TEXT,
    discovered_at TEXT NOT NULL,
    applied_at    TEXT,
    expiry_check  TEXT,
    source_updated_at TEXT,
    match_score   INTEGER,
    match_reasons TEXT,
    state         TEXT NOT NULL DEFAULT 'new',
    dedup_key     TEXT
);

CREATE TABLE IF NOT EXISTS applications (
    id               INTEGER PRIMARY KEY,
    applied_date     TEXT,
    company          TEXT,
    position         TEXT,
    level            TEXT,
    match            TEXT,
    job_url          TEXT,
    source           TEXT,
    status           TEXT,
    method           TEXT,
    notes            TEXT,
    state            TEXT NOT NULL DEFAULT 'applied',
    state_changed_at TEXT
);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS seen_urls (
    url_hash   TEXT PRIMARY KEY,
    url        TEXT NOT NULL,
    first_seen TEXT NOT NULL,
    last_seen  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_offers_dedup_key ON offers(dedup_key);
"""


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def url_hash(url):
    """Stable seen_urls key — dedup survives pruner deletes and cosmetic URLs."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def dedup_key(title, company):
    """Content-level dedup key: sha256 over normalized (title|company).

    One offer is often published under many URL slugs (NoFluffJobs does
    this a lot); UNIQUE(job_url) cannot collapse those, so the queue fans
    out into identical cards. Normalization: lowercase, Polish diacritics
    folded to ASCII, punctuation stripped, whitespace collapsed. NULL when
    title or company is missing — such rows never merge.
    """
    if not title or not company:
        return None
    fold = str.maketrans({
        "ą": "a", "ć": "c", "ę": "e", "ł": "l", "ń": "n",
        "ó": "o", "ś": "s", "ź": "z", "ż": "z",
    })

    def _norm(text):
        text = text.lower().translate(fold)
        text = re.sub(r"[^\w\s]+", " ", text)
        return " ".join(text.split())

    return hashlib.sha256(
        f"{_norm(title)}|{_norm(company)}".encode("utf-8")
    ).hexdigest()


def _migrate(conn):
    """Add columns pre-existing tables lack. Must run BEFORE executescript:
    SCHEMA's CREATE INDEX statements reference the new columns, and on an
    old DB the CREATE TABLE IF NOT EXISTS is a no-op. Fresh DB: no-op."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(offers)")}
    if not cols:
        return
    for name, decl in (
        ("source_updated_at", "TEXT"),
        ("match_score", "INTEGER"),
        ("match_reasons", "TEXT"),
        ("state", "TEXT NOT NULL DEFAULT 'new'"),
        ("dedup_key", "TEXT"),
    ):
        if name not in cols:
            conn.execute(f"ALTER TABLE offers ADD COLUMN {name} {decl}")


def _backfill_dedup_keys(conn):
    """One pass computing content keys for rows created before the column
    existed. Rows without a usable title+company stay NULL — they never
    merge."""
    updates = [
        (key, r["id"])
        for r in conn.execute(
            "SELECT id, title, company FROM offers "
            "WHERE dedup_key IS NULL AND title IS NOT NULL "
            "AND company IS NOT NULL"
        )
        if (key := dedup_key(r["title"], r["company"]))
    ]
    if updates:
        with write_txn(conn):
            conn.executemany(
                "UPDATE offers SET dedup_key = ? WHERE id = ?", updates
            )


def _backfill_application_states(conn):
    """One-time pass (meta-guarded): derive the funnel state from free-text
    status for rows written before add_application/update derived it.
    Keeps state_changed_at — historical dates feed the followup query."""
    if meta_get(conn, "state_backfill_v1") == "1":
        return
    updates = [
        (state, r["id"])
        for r in conn.execute("SELECT id, status, state FROM applications")
        if (state := derive_state(r["status"])) != r["state"]
    ]
    if updates:
        with write_txn(conn):
            conn.executemany(
                "UPDATE applications SET state = ? WHERE id = ?", updates
            )
    meta_set(conn, "state_backfill_v1", "1")


def connect(db_path=DEFAULT_DB):
    """Open the store, apply WAL pragmas, ensure schema. Row access by name."""
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=BUSY_TIMEOUT_MS / 1000.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")       # persists in the file
    conn.execute("PRAGMA synchronous=NORMAL")     # WAL doc: only checkpoints fsync
    _migrate(conn)               # columns first — SCHEMA indexes may need them
    conn.executescript(SCHEMA)
    _backfill_dedup_keys(conn)
    _backfill_application_states(conn)
    return conn


@contextlib.contextmanager
def write_txn(conn):
    """BEGIN IMMEDIATE ... COMMIT / ROLLBACK. Nesting is a caller error."""
    if conn.in_transaction:
        raise RuntimeError("write_txn inside an open transaction")
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
    except BaseException:
        conn.rollback()
        raise
    else:
        conn.commit()


# ---------------------------------------------------------------- offers

OFFER_COLS = (
    "job_url", "source", "title", "company", "location", "salary_min",
    "salary_max", "salary_currency", "salary_period", "posted_at",
    "expires_at", "status", "decision", "level", "match", "notes",
    "raw_json", "discovered_at", "applied_at", "expiry_check",
    "source_updated_at", "match_score", "match_reasons", "state",
    "dedup_key",
)


def upsert_offer(conn, offer):
    present = {k: v for k, v in offer.items() if v is not None and k in OFFER_COLS}
    values = {
        "status": "new",
        "decision": "pending",
        "state": "new",
        "discovered_at": utcnow(),
        **present,
    }
    values["dedup_key"] = dedup_key(values.get("title"), values.get("company"))
    url = values["job_url"]
    h = url_hash(url)
    # Permanent dedup: every scouted URL lands in seen_urls forever. A row the
    # pruner deleted (expired + low score + old) must never re-enter the corpus
    # just because a nightly dump re-lists it — seen-but-absent means stay out.
    seen_before = conn.execute(
        "SELECT 1 FROM seen_urls WHERE url_hash = ?", (h,)
    ).fetchone()
    now = utcnow()
    conn.execute(
        "INSERT INTO seen_urls(url_hash, url, first_seen, last_seen) "
        "VALUES(?, ?, ?, ?) "
        "ON CONFLICT(url_hash) DO UPDATE SET last_seen=excluded.last_seen",
        (h, url, now, now),
    )
    if seen_before is None or conn.execute(
        "SELECT 1 FROM offers WHERE job_url = ?", (url,)
    ).fetchone():
        conn.execute(
            """
            INSERT INTO offers ({cols}) VALUES ({ph})
            ON CONFLICT(job_url) DO UPDATE SET
                source=excluded.source, title=excluded.title,
                company=excluded.company, location=excluded.location,
                salary_min=excluded.salary_min, salary_max=excluded.salary_max,
                salary_currency=excluded.salary_currency,
                salary_period=excluded.salary_period,
                posted_at=COALESCE(excluded.posted_at, offers.posted_at),
                expires_at=COALESCE(excluded.expires_at, offers.expires_at),
                level=excluded.level, match=excluded.match,
                notes=excluded.notes,
                raw_json=COALESCE(excluded.raw_json, offers.raw_json),
                expiry_check=COALESCE(excluded.expiry_check, offers.expiry_check),
                source_updated_at=COALESCE(excluded.source_updated_at, offers.source_updated_at),
                dedup_key=COALESCE(excluded.dedup_key, offers.dedup_key)
            """.format(cols=", ".join(OFFER_COLS), ph=", ".join("?" * len(OFFER_COLS))),
            [values.get(k) for k in OFFER_COLS],
        )
    return get_offer(conn, url)


def upsert_offers(conn, offers):
    """Batch upsert in one write transaction."""
    with write_txn(conn):
        for offer in offers:
            upsert_offer(conn, offer)


def get_offer(conn, job_url):
    return conn.execute("SELECT * FROM offers WHERE job_url = ?", (job_url,)).fetchone()


def list_offers(conn, decision=None, limit=None):
    sql = "SELECT * FROM offers"
    args = ()
    if decision:
        sql += " WHERE decision = ?"
        args = (decision,)
    sql += " ORDER BY discovered_at DESC"
    if limit:
        sql += f" LIMIT {int(limit)}"
    return conn.execute(sql, args).fetchall()


def set_offer_decision(conn, job_url, decision):
    """One decision per content, not per URL: applies to every row sharing
    the offer's dedup_key (multi-slug republications), so a sibling slug
    can never resurface an offer the user already decided on.
    Returns the number of rows set."""
    with write_txn(conn):
        row = conn.execute(
            "SELECT dedup_key FROM offers WHERE job_url = ?", (job_url,)
        ).fetchone()
        if row and row["dedup_key"]:
            cur = conn.execute(
                "UPDATE offers SET decision = ? WHERE dedup_key = ?",
                (decision, row["dedup_key"]),
            )
        else:
            cur = conn.execute(
                "UPDATE offers SET decision = ? WHERE job_url = ?",
                (decision, job_url),
            )
    return cur.rowcount


# ---------------------------------------------------------- applications

APP_COLS = (
    "applied_date", "company", "position", "level", "match", "job_url",
    "source", "status", "method", "notes", "state", "state_changed_at",
)

VALID_STATES = {"applied", "verified", "screening", "interview", "offer",
                 "blocked", "rejected", "expired"}

# Funnel states a candidate moves through after sending the application.
PIPELINE_STATES = ("applied", "verified", "screening", "interview", "offer")

# Free-text Status is the CSV ground truth; the funnel `state` column is
# derived from it. Longest / most specific prefixes first.
STATUS_STATE_RULES = (
    ("applied - action required", "screening"),
    ("applied", "applied"),
    ("w trakcie", "applied"),
    ("blocked", "blocked"),
    ("closed", "expired"),
    ("rejected", "rejected"),
    ("odrzucona", "rejected"),
)


def derive_state(status):
    """Map a free-text application status to its funnel state."""
    s = str(status or "").strip().lower()
    for prefix, state in STATUS_STATE_RULES:
        if s.startswith(prefix):
            return state
    return "applied"

def add_application(conn, row):
    present = {k: v for k, v in row.items() if v is not None and k in APP_COLS}
    values = {
        "state": derive_state(present.get("status")),
        "state_changed_at": present.get("applied_date") or utcnow(),
        **present,
    }
    with write_txn(conn):
        conn.execute(
            f"INSERT INTO applications ({', '.join(APP_COLS)}) VALUES ({', '.join('?' * len(APP_COLS))})",
            [values.get(k) for k in APP_COLS],
        )
    return values


def list_applications(conn, state=None):
    sql = "SELECT * FROM applications"
    args = ()
    if state:
        sql += " WHERE state = ?"
        args = (state,)
    return conn.execute(sql + " ORDER BY id", args).fetchall()

def set_application_state(conn, app_id, state):
    """Move one application to a funnel state; stamps state_changed_at."""
    with write_txn(conn):
        cur = conn.execute(
            "UPDATE applications SET state = ?, state_changed_at = ? WHERE id = ?",
            (state, utcnow(), int(app_id)),
        )
    return cur.rowcount


# ------------------------------------------------------------------ meta

def meta_set(conn, key, value):
    with write_txn(conn):
        conn.execute(
            "INSERT INTO meta(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, str(value)),
        )


def meta_get(conn, key):
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None
