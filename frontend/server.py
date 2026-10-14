#!/usr/bin/env python3
"""Local dashboard for CVSender — no dependencies beyond the stdlib.

Run: python3 server.py
Then open http://127.0.0.1:8765
"""
import glob
import json
import os
import sys
from urllib.parse import parse_qs, urlsplit
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import store  # noqa: E402  (SQLite WAL store — the only funnel store)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")  # CVSender/data/
INDEX_HTML = os.path.join(BASE_DIR, "static", "index.html")
STATIC_DIR = os.path.join(BASE_DIR, "static")
STATIC_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
}
LEARNING_DIR = os.path.join(DATA_DIR, "learning")
LINKS_MD = os.path.join(DATA_DIR, "links.md")

SENT_STATUS = "Applied"

# Funnel display order: pipeline first, then the dead ends.
STATE_ORDER = ("applied", "verified", "screening", "interview", "offer",
               "blocked", "rejected", "expired")
PORT = 8765

VALID_DECISIONS = {"pending", "accepted", "postponed_future", "postponed_no_send",
                   # handled = accepted offer processed by an agent; hidden from all tabs
                   "handled"}

# Senders worth checking for application-verification links (Teamtailor
# "confirm your email" etc.). One place to edit; the panel exposes it as a
# Gmail search button (research/2026-09-09-orchestration-tooling.md §4 quick win).
GMAIL_SEARCH_SENDERS = ("teamtailor", "nofluffjobs", "theprotocol", "justjoin")
GMAIL_SEARCH_WINDOW = "newer_than:7d"

# "Brak odpowiedzi" threshold in days for the panel follow-up view
# (applications still in applied/verified/screening with no state change).
N_SILENT_DAYS = 7


def gmail_search_url():
    senders = " OR ".join(GMAIL_SEARCH_SENDERS)
    return f"https://mail.google.com/mail/u/0/#search/from:({senders}) {GMAIL_SEARCH_WINDOW}"


def find_cv_pdf():
    """Any single PDF dropped in data/ is treated as the CV to serve/attach."""
    matches = sorted(glob.glob(os.path.join(DATA_DIR, "*.pdf")))
    return matches[0] if matches else None


DB_PATH = os.path.join(DATA_DIR, "cvsender.db")
_db_conn = None


def db():
    """Lazily open the SQLite store; None when the DB is absent or empty —
    write endpoints then answer 503 (reads fall back to db_or_empty())."""
    global _db_conn
    if _db_conn is None and os.path.exists(DB_PATH):
        conn = store.connect(DB_PATH)
        if conn.execute("SELECT 1 FROM offers LIMIT 1").fetchone() or \
           conn.execute("SELECT 1 FROM applications LIMIT 1").fetchone():
            _db_conn = conn
    return _db_conn


_empty_conn = None


def db_or_empty():
    """db() for read-only views; before the first scout run (no DB yet) an
    in-memory store with the same schema, so a fresh instance renders empty
    tabs instead of 503s. Never cached as _db_conn — db() switches to the
    real file as soon as it has rows."""
    global _empty_conn
    conn = db()
    if conn is not None:
        return conn
    if _empty_conn is None:
        _empty_conn = store.connect(":memory:")
    return _empty_conn


def offer_to_legacy(r):
    """DB offer row -> the dict shape the frontend already consumes."""
    return {
        "Date": (r["discovered_at"] or "")[:10],
        "Company": r["company"] or "",
        "Position": r["title"] or "",
        "Level": r["level"] or "",
        "Match": r["match"] or "",
        "URL": r["job_url"],
        "Source": r["source"] or "",
        "Notes": r["notes"] or "",
        "Accepted": "true" if r["decision"] == "accepted" else "false",
        "Decision": r["decision"] or "pending",
    }


def application_to_legacy(r):
    return {
        "Date": (r["applied_date"] or "")[:10],
        "Company": r["company"] or "",
        "Position": r["position"] or "",
        "Level": r["level"] or "",
        "Match": r["match"] or "",
        "URL": r["job_url"] or "",
        "Source": r["source"] or "",
        "Status": r["status"] or "",
        "Method": r["method"] or "",
        "Notes": r["notes"] or "",
        "State": r["state"] or "",
        "StateChangedAt": r["state_changed_at"] or "",
    }


def list_learning_cards():
    cards = []
    if not os.path.isdir(LEARNING_DIR):
        return cards
    for fname in sorted(os.listdir(LEARNING_DIR)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(LEARNING_DIR, fname)
        try:
            with open(path, encoding="utf-8") as f:
                cards.append(json.load(f))
        except (OSError, json.JSONDecodeError):
            continue
    return cards


def list_platforms():
    """Rows of the Platforma | URL | Status | Notatki table in data/links.md."""
    platforms = []
    try:
        with open(LINKS_MD, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return platforms
    for line in lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not line.lstrip().startswith("|") or len(cells) < 3:
            continue
        if cells[0] == "Platforma" or set(cells[0]) <= set("-: "):
            continue  # header / separator row
        platforms.append({
            "name": cells[0],
            "url": cells[1],
            "status": cells[2],
            "notes": " | ".join(cells[3:]).strip(),
        })
    return platforms


# ------------------------------------------------ funnel API (lazy by design)
# The corpus is 19k+ rows: every list endpoint paginates server-side and the
# per-request limit is HARD-CAPPED — no request can ever ship the whole table.

DEFAULT_PAGE_OFFERS = 20
DEFAULT_PAGE_APPLICATIONS = 50
MAX_PAGE = 200

ORDER_BY = {
    "score": " (match_score IS NULL), match_score DESC, discovered_at DESC, id DESC",
    "recent": " discovered_at DESC, id DESC",
}

def _shortlist_where(alias=""):
    """Shortlist membership predicate; optional table-alias prefix."""
    p = f"{alias}." if alias else ""
    return (f"{p}match_score >= ? AND {p}decision = 'pending' "
            f"AND NOT ({p}expires_at IS NOT NULL "
            f"AND julianday({p}expires_at) < julianday('now'))")


SHORTLIST_WHERE = _shortlist_where()

# Content-level dedup: group membership = same non-NULL dedup_key; a row
# without a key (no title+company at scout time) is always its own group.
_DUP_URLS_SEP = "\x1f"


def _same_group(g="g", o="o"):
    return (f"(({g}.dedup_key = {o}.dedup_key AND {g}.dedup_key IS NOT NULL) "
            f"OR {g}.id = {o}.id)")


def _best_of_group():
    """Subquery: id of the best shortlist row in o's dedup group
    (max score, then freshest discovery)."""
    return (f"SELECT g.id FROM offers g WHERE {_same_group('g', 'o')} "
            f"AND {_shortlist_where('g')} "
            "ORDER BY (g.match_score IS NULL), g.match_score DESC, "
            "g.discovered_at DESC, g.id DESC LIMIT 1")


def _q1(qs, name, default=None):
    vals = qs.get(name)
    return vals[0] if vals else default


def _page(qs, default_limit):
    try:
        limit = int(_q1(qs, "limit", default_limit))
    except (TypeError, ValueError):
        limit = default_limit
    try:
        offset = int(_q1(qs, "offset", 0))
    except (TypeError, ValueError):
        offset = 0
    return max(0, min(limit, MAX_PAGE)), max(0, offset)


def _like(q, columns):
    """Case-insensitive substring filter across columns, LIKE wildcards escaped."""
    needle = "%" + q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    clause = " OR ".join(f"{c} LIKE ? ESCAPE '\\'" for c in columns)
    return f"({clause})", [needle] * len(columns)


def offer_row_json(r):
    """DB offer row -> panel JSON: legacy CSV-era keys plus funnel keys."""
    try:
        reasons = json.loads(r["match_reasons"]) if r["match_reasons"] else []
    except (TypeError, ValueError):
        reasons = []
    row = offer_to_legacy(r)
    row.update({
        "job_url": r["job_url"],
        "location": r["location"] or "",
        "salary_min": r["salary_min"],
        "salary_max": r["salary_max"],
        "salary_currency": r["salary_currency"] or "",
        "salary_period": r["salary_period"] or "",
        "expires_at": r["expires_at"] or "",
        "state": r["state"] or "new",
        "match_score": r["match_score"],
        "match_reasons": reasons,
    })
    if "dup_count" in r.keys():
        row["dup_count"] = r["dup_count"]
        row["job_urls"] = (r["dup_urls"] or "").split(_DUP_URLS_SEP)
    return row


def application_row_json(r):
    row = application_to_legacy(r)
    row["id"] = r["id"]
    return row


def _offer_filters(qs):
    """Whitelist-driven WHERE builder; None on an invalid parameter value."""
    where, args = [], []
    decision = _q1(qs, "decision")
    if decision:
        if decision not in VALID_DECISIONS:
            return None
        where.append("decision = ?")
        args.append(decision)
    min_score = _q1(qs, "min_score")
    if min_score is not None:
        try:
            where.append("match_score >= ?")
            args.append(max(0, min(100, int(min_score))))
        except (TypeError, ValueError):
            return None
    source = _q1(qs, "source")
    if source:
        where.append("source = ?")
        args.append(source)
    q = _q1(qs, "q")
    if q:
        clause, qargs = _like(q, ("company", "title", "job_url", "match", "location"))
        where.append(clause)
        args.extend(qargs)
    if _q1(qs, "remote") == "1":
        where.append("lower(location) LIKE '%remote%'")
    expiring = _q1(qs, "expiring_days")
    if expiring is not None:
        try:
            days = int(expiring)
        except (TypeError, ValueError):
            return None
        where.append(
            "julianday(expires_at) BETWEEN julianday('now') "
            "AND julianday('now', '+' || ? || ' days')"
        )
        args.append(days)
    return where, args


def query_offers(conn, qs):
    """Paginated/filtered corpus page; None when a param is invalid."""
    parsed = _offer_filters(qs)
    if parsed is None:
        return None
    where, args = parsed
    clause = (" WHERE " + " AND ".join(where)) if where else ""
    limit, offset = _page(qs, DEFAULT_PAGE_OFFERS)
    order = ORDER_BY.get(_q1(qs, "sort", "score")) or ORDER_BY["score"]
    total = conn.execute(f"SELECT COUNT(*) FROM offers{clause}", args).fetchone()[0]
    rows = conn.execute(
        f"SELECT * FROM offers{clause} ORDER BY{order} LIMIT ? OFFSET ?",
        args + [limit, offset],
    ).fetchall()
    return {"total": total, "limit": limit, "offset": offset,
            "rows": [offer_row_json(r) for r in rows]}


def query_shortlist(conn, qs):
    """The human queue: score >= threshold, pending decision, still alive —
    one card per content (dedup_key group): the group's best row (max
    score, then freshest) plus dup_count and the group's job_urls."""
    limit, offset = _page(qs, DEFAULT_PAGE_OFFERS)
    order = ORDER_BY.get(_q1(qs, "sort", "score")) or ORDER_BY["score"]
    args = (store.SHORTLIST_THRESHOLD,)
    total = conn.execute(
        f"SELECT COUNT(*) FROM offers o WHERE o.id = ({_best_of_group()})",
        args,
    ).fetchone()[0]
    rows = conn.execute(
        f"SELECT o.*, "
        f"(SELECT COUNT(*) FROM offers g WHERE {_same_group('g', 'o')} "
        f"AND {_shortlist_where('g')}) AS dup_count, "
        f"(SELECT group_concat(g.job_url, '{_DUP_URLS_SEP}') FROM offers g "
        f"WHERE {_same_group('g', 'o')} AND {_shortlist_where('g')}) AS dup_urls "
        f"FROM offers o WHERE o.id = ({_best_of_group()}) "
        f"ORDER BY{order} LIMIT ? OFFSET ?",
        args + args + args + (limit, offset),
    ).fetchall()
    return {"total": total, "limit": limit, "offset": offset,
            "rows": [offer_row_json(r) for r in rows]}


def query_applications(conn, qs):
    """Paginated applications; None when a param is invalid."""
    where, args = [], []
    state = _q1(qs, "state")
    if state:
        if state not in store.VALID_STATES:
            return None
        where.append("state = ?")
        args.append(state)
    if _q1(qs, "blocked") == "1":
        where.append("lower(status) LIKE 'blocked%'")
    q = _q1(qs, "q")
    if q:
        clause, qargs = _like(q, ("company", "position", "job_url", "notes"))
        where.append(clause)
        args.extend(qargs)
    clause = (" WHERE " + " AND ".join(where)) if where else ""
    limit, offset = _page(qs, DEFAULT_PAGE_APPLICATIONS)
    order = " id DESC" if _q1(qs, "sort") == "recent" else " id"
    total = conn.execute(
        "SELECT COUNT(*) FROM applications" + clause, args
    ).fetchone()[0]
    sent = conn.execute(
        f"SELECT COUNT(*) FROM applications WHERE state IN ({', '.join('?' * len(store.PIPELINE_STATES))})",
        store.PIPELINE_STATES,
    ).fetchone()[0]
    all_total = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    rows = conn.execute(
        "SELECT * FROM applications" + clause + f" ORDER BY{order} LIMIT ? OFFSET ?",
        args + [limit, offset],
    ).fetchall()
    return {"total": total, "sentCount": sent, "totalCount": all_total,
            "limit": limit, "offset": offset,
            "rows": [application_row_json(r) for r in rows]}




def _resolve_offer(conn, payload, index):
    """Offer row by explicit job_url (paginated UI), else by legacy index."""
    job_url = payload.get("job_url")
    if job_url:
        return store.get_offer(conn, str(job_url))
    offers = store.list_offers(conn)
    return offers[index] if 0 <= index < len(offers) else None


def panel_stats(conn):
    """Header badge counts — cheap COUNTs, never row payloads."""
    shortlist = conn.execute(
        f"SELECT COUNT(*) FROM offers o WHERE o.id = ({_best_of_group()})",
        (store.SHORTLIST_THRESHOLD,),
    ).fetchone()[0]
    corpus = conn.execute("SELECT COUNT(*) FROM offers").fetchone()[0]
    followup = conn.execute(
        """
        SELECT COUNT(*) FROM applications
        WHERE state IN ('applied','verified','screening')
          AND julianday(state_changed_at) < julianday('now', '-' || ? || ' days')
        """,
        (N_SILENT_DAYS,),
    ).fetchone()[0]
    blocked = conn.execute(
        "SELECT COUNT(*) FROM applications WHERE lower(status) LIKE 'blocked%'"
    ).fetchone()[0]
    postponed = conn.execute(
        "SELECT COUNT(*) FROM offers "
        "WHERE decision IN ('postponed_future', 'postponed_no_send')"
    ).fetchone()[0]
    apps_total = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    stages = {s: 0 for s in STATE_ORDER}
    for r in conn.execute(
        "SELECT state, COUNT(*) AS c FROM applications GROUP BY state"
    ):
        if r["state"] in stages:
            stages[r["state"]] = r["c"]
    sent = sum(stages[s] for s in store.PIPELINE_STATES)
    sources = [
        {"source": r["source"], "count": r["c"]}
        for r in conn.execute(
            "SELECT source, COUNT(*) AS c FROM offers "
            "WHERE source IS NOT NULL GROUP BY source ORDER BY c DESC"
        )
    ]
    return {"shortlist": shortlist, "corpus": corpus, "followup": followup,
            "blocked": blocked, "postponed": postponed,
            "totalCount": apps_total, "stages": stages, "sent": sent,
            "sources": sources,
            "threshold": store.SHORTLIST_THRESHOLD, "db": True}


RETRY_STATUS = "Blocked - retry queued"


def retry_applications(conn, ids):
    """Re-queue blocked applications for another agent pass. The agent's
    execution contract is the offers table with decision='accepted' (panel
    PRZYGOTOWANE tab), so a retry means: put the offer back there (deduped by
    URL, then company+title, tagged RETRY) and mark the application row
    'Blocked - retry queued' — still surfaced by every 'blocked%' filter, but
    visibly distinct. Idempotent per id."""
    retried, skipped = [], []
    today = store.utcnow()[:10]
    with store.write_txn(conn):
        for app_id in ids:
            try:
                app_id = int(app_id)
            except (TypeError, ValueError):
                skipped.append({"id": app_id, "reason": "invalid id"})
                continue
            row = conn.execute(
                "SELECT * FROM applications WHERE id = ?", (app_id,)
            ).fetchone()
            if row is None or not str(row["status"] or "").lower().startswith("blocked"):
                skipped.append({"id": app_id, "reason": "not blocked"})
                continue
            url = (row["job_url"] or "").strip()
            tag = f"RETRY of app #{app_id} queued {today}"
            hit = store.get_offer(conn, url) if url else None
            if hit is None:  # dedup fallback: company + position
                hit = conn.execute(
                    "SELECT * FROM offers WHERE company = ? AND title = ? "
                    "ORDER BY discovered_at DESC LIMIT 1",
                    ((row["company"] or "").strip(), (row["position"] or "").strip()),
                ).fetchone()
            if hit is not None:
                notes = hit["notes"] or ""
                if tag not in notes:
                    conn.execute(
                        "UPDATE offers SET notes = ? WHERE id = ?",
                        ((notes + " | " + tag).strip(" |"), hit["id"]),
                    )
                conn.execute(
                    "UPDATE offers SET decision = 'accepted' WHERE id = ?",
                    (hit["id"],),
                )
            elif url:
                store.upsert_offer(conn, {
                    "job_url": url,
                    "company": row["company"] or "",
                    "title": row["position"] or "",
                    "level": row["level"] or "",
                    "match": row["match"] or "",
                    "source": row["source"] or "",
                    "notes": f"{tag}. Blokada: {str(row['notes'] or '')[:300]}",
                    "decision": "accepted",
                })
            else:
                skipped.append({"id": app_id, "reason": "no url and no matching offer"})
                continue
            retried.append(app_id)
    if retried:
        with store.write_txn(conn):
            now = store.utcnow()
            conn.executemany(
                "UPDATE applications SET status = ?, state = ?, state_changed_at = ? "
                "WHERE id = ?",
                [(RETRY_STATUS, store.derive_state(RETRY_STATUS), now, i)
                 for i in retried],
            )
    return retried, skipped


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path, content_type):
        with open(path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        # Local dev tool: a stale cached panel after an update looks like a
        # bug, so forbid caching outright.
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        route, _, query = self.path.partition("?")
        qs = parse_qs(query)
        if route in ("/", "/index.html"):
            self._send_file(INDEX_HTML, "text/html; charset=utf-8")
        elif route == "/api/applications":
            page = query_applications(db_or_empty(), qs)
            if page is None:
                self._send_json({"error": "invalid parameter"}, status=400)
                return
            self._send_json(page)
        elif route == "/api/offers":
            page = query_offers(db_or_empty(), qs)
            if page is None:
                self._send_json({"error": "invalid parameter"}, status=400)
                return
            self._send_json(page)
        elif route == "/api/shortlist":
            self._send_json(query_shortlist(db_or_empty(), qs))
        elif route == "/api/stats":
            self._send_json(panel_stats(db_or_empty()))
        elif route == "/api/learning":
            self._send_json({"cards": list_learning_cards()})
        elif route == "/api/platforms":
            self._send_json({"platforms": list_platforms()})
        elif route == "/api/config":
            self._send_json({"gmailSearchUrl": gmail_search_url()})
        elif route == "/api/followup":
            rows = db_or_empty().execute(
                """
                SELECT id, company, position, state, status, state_changed_at, job_url
                FROM applications
                WHERE state IN ('applied','verified','screening')
                  AND julianday(state_changed_at) < julianday('now', '-' || ? || ' days')
                ORDER BY state_changed_at
                """,
                (N_SILENT_DAYS,),
            ).fetchall()
            self._send_json({
                "rows": [dict(r) for r in rows],
                "days": N_SILENT_DAYS,
                "db": True,
            })
        elif route == "/api/cv-file":
            # Served with CORS so a browser tab on another origin (e.g. an ATS
            # form with a shadow-DOM file input we can't reach via ref-based
            # tools) can fetch() this and construct a File object in-page,
            # instead of piping the PDF's bytes through the assistant's
            # context as base64.
            cv_path = find_cv_pdf()
            if cv_path is None:
                self.send_response(404)
                self.end_headers()
                return
            with open(cv_path, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header(
                "Content-Disposition",
                f'inline; filename="{os.path.basename(cv_path)}"',
            )
            self.end_headers()
            self.wfile.write(body)
        elif route.startswith("/static/"):
            name = os.path.normpath(route[len("/static/"):].split("?", 1)[0])
            fs_path = os.path.join(STATIC_DIR, name)
            ext = os.path.splitext(fs_path)[1].lower()
            if name.startswith(("..", "/")) or ext not in STATIC_TYPES or not os.path.isfile(fs_path):
                self.send_response(404)
                self.end_headers()
                return
            self._send_file(fs_path, STATIC_TYPES[ext])
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/offers/toggle":
            length = int(self.headers.get("Content-Length", 0))
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
                index = int(payload.get("index", -1))
            except (ValueError, KeyError, json.JSONDecodeError):
                self._send_json({"error": "invalid request"}, status=400)
                return
            conn = db()
            if conn is not None:
                row = _resolve_offer(conn, payload, index)
                if row is None:
                    self._send_json({"error": "unknown offer"}, status=400)
                    return
                new_accepted = row["decision"] != "accepted"
                affected = store.set_offer_decision(
                    conn, row["job_url"],
                    "accepted" if new_accepted else "pending")
                self._send_json({"index": index, "job_url": row["job_url"],
                                 "accepted": "true" if new_accepted else "false",
                                 "affected": affected})
                return
            self._send_json({"error": "sqlite store required"}, status=503)
        elif self.path == "/api/offers/decision":
            length = int(self.headers.get("Content-Length", 0))
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
                index = int(payload.get("index", -1))
                decision = str(payload["decision"])
            except (ValueError, KeyError, json.JSONDecodeError):
                self._send_json({"error": "invalid request"}, status=400)
                return
            if decision not in VALID_DECISIONS:
                self._send_json({"error": "invalid decision"}, status=400)
                return
            conn = db()
            if conn is not None:
                row = _resolve_offer(conn, payload, index)
                if row is None:
                    self._send_json({"error": "unknown offer"}, status=400)
                    return
                affected = store.set_offer_decision(conn, row["job_url"], decision)
                self._send_json({"index": index, "job_url": row["job_url"],
                                 "decision": decision, "affected": affected})
                return
            self._send_json({"error": "sqlite store required"}, status=503)
        elif self.path == "/api/applications/update":
            length = int(self.headers.get("Content-Length", 0))
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
                index = int(payload.get("index", -1))
            except (ValueError, TypeError, KeyError, json.JSONDecodeError):
                self._send_json({"error": "invalid request"}, status=400)
                return
            conn = db()
            if conn is not None:
                row = None
                try:
                    app_id = payload.get("id")
                    if app_id is not None:
                        row = conn.execute(
                            "SELECT rowid AS rid, * FROM applications WHERE id = ?",
                            (int(app_id),),
                        ).fetchone()
                except (TypeError, ValueError):
                    self._send_json({"error": "invalid id"}, status=400)
                    return
                if row is None:
                    rows = conn.execute(
                        "SELECT rowid AS rid, * FROM applications ORDER BY id"
                    ).fetchall()
                    row = rows[index] if 0 <= index < len(rows) else None
                if row is None:
                    self._send_json({"error": "unknown application"}, status=400)
                    return
                sets, args = [], []
                if "status" in payload:
                    sets.append("status = ?")
                    args.append(str(payload["status"]))
                if "notes" in payload:
                    sets.append("notes = ?")
                    args.append(str(payload["notes"]))
                if "status" in payload and "state" not in payload:
                    # Status is the ground truth; keep the funnel state in
                    # sync unless the caller moves the state explicitly.
                    sets.append("state = ?")
                    args.append(store.derive_state(payload["status"]))
                    sets.append("state_changed_at = ?")
                    args.append(store.utcnow())
                if "state" in payload:
                    new_state = str(payload["state"])
                    if new_state not in store.VALID_STATES:
                        self._send_json({"error": "invalid state"}, status=400)
                        return
                    sets.append("state = ?")
                    args.append(new_state)
                    sets.append("state_changed_at = ?")
                    args.append(store.utcnow())
                if sets:
                    with store.write_txn(conn):
                        conn.execute(
                            f"UPDATE applications SET {', '.join(sets)} WHERE rowid = ?",
                            args + [row["rid"]],
                        )
                fresh = conn.execute(
                    "SELECT state FROM applications WHERE rowid = ?", (row["rid"],)
                ).fetchone()
                self._send_json({
                    "id": row["id"],
                    "index": index,
                    "status": str(payload["status"]) if "status" in payload else (row["status"] or ""),
                    "notes": str(payload["notes"]) if "notes" in payload else (row["notes"] or ""),
                    "state": fresh["state"] if fresh else (row["state"] or ""),
                })
                return
            self._send_json({"error": "sqlite store required"}, status=503)
        elif self.path == "/api/applications/state":
            length = int(self.headers.get("Content-Length", 0))
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
                app_id = int(payload["id"])
                state = str(payload["state"])
            except (ValueError, TypeError, KeyError, json.JSONDecodeError):
                self._send_json({"error": "invalid request"}, status=400)
                return
            if state not in store.VALID_STATES:
                self._send_json({"error": "invalid state"}, status=400)
                return
            conn = db()
            if conn is None:
                self._send_json({"error": "sqlite store required"}, status=503)
                return
            if not store.set_application_state(conn, app_id, state):
                self._send_json({"error": "unknown application"}, status=400)
                return
            row = conn.execute(
                "SELECT state, state_changed_at FROM applications WHERE id = ?",
                (app_id,),
            ).fetchone()
            self._send_json({"id": app_id, "state": row["state"],
                             "state_changed_at": row["state_changed_at"]})
        elif self.path == "/api/applications/retry":
            length = int(self.headers.get("Content-Length", 0))
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
                ids = payload["ids"]
                if not isinstance(ids, list):
                    raise ValueError
            except (ValueError, KeyError, json.JSONDecodeError):
                self._send_json({"error": "invalid request"}, status=400)
                return
            conn = db()
            if conn is None:
                self._send_json({"error": "sqlite store required"}, status=503)
                return
            retried, skipped = retry_applications(conn, ids)
            self._send_json({"retried": retried, "skipped": skipped})
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def main():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"CVSender dashboard: http://127.0.0.1:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
