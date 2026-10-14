# CVSender: Orchestration & Tooling Research (daily scouting, storage, email verification, outcome tracking)

**Research date: 2026-09-09.** Facts verified against primary sources (official docs, GitHub repos fetched via API, vendor pages) on this date unless marked `[INFERENCE]`. Stars/counts are as returned by the GitHub API on this date.

**Context.** CVSender = python-stdlib panel (`frontend/server.py`, port 8765) + two CSV data files (applications log, offer queue) + Playwright/CDP driving the user's real Chrome + multi-agent orchestration (director spawns worker CLI sessions). Pain points: manual scouting with no cadence (4 offers lost to expiry), CSV write races between concurrent agents, manual Teamtailor email-verification clicks, no outcome tracking beyond a Status column.

---

## 0. TL;DR — top recommendations

1. **Schedule the scout with a launchd LaunchAgent** (`StartCalendarInterval`); it re-fires on wake-from-sleep, unlike cron — this alone fixes the "no daily cadence" pain with ~2h of work and zero daemons. (§2)
2. **Migrate the two CSVs to one SQLite DB in WAL mode** with `busy_timeout` + `BEGIN IMMEDIATE`; WAL gives concurrent readers + single serialized writer, which is exactly the 2-4-writer scale here. CommandJobs proves the pattern (SQLite + numbered migrations) for this exact domain. (§3)
3. **Short term**, put an `fcntl.flock` shim around CSV writes (1-2h) to stop the races before the migration lands. (§3.4)
4. **Email verification: IMAP + app password beats Gmail API** for 1-2 mails/week — the API path hits Google's 7-day refresh-token expiry for apps in "Testing" status unless you publish the app; IMAP with an app password is ~2h and durable. Quick win first: a panel button that opens the right Gmail search. (§4)
5. **Track outcomes as a tiny state machine** (`applied → verified → screening → interview → offer/rejected/expired`) with `status_changed_at`; derive a follow-up list from "N days silence". (§5)
6. **LinkedIn "my items" (saved/applied) data is reachable** from a logged-in session via the internal `voyagerSearchDashClusters` GraphQL (`cardType: APPLIED`) — usable with the existing CDP session for reconciliation; no official API. Treat as fragile/ToS-sensitive. (§5.3)
7. **Borrow from OSS**: AIHawk's persistent-profile + seeded-identity browser setup, JobSpy's `hours_old` incremental-scout parameter, CommandJobs' SQLite+migrations+`json_extract` matching, EasyApplyJobsBot's YAML answer/blacklist config. (§1)

---

## 1. What active OSS job-search/auto-apply agents do (Q1)

| Project | Stars | License | Last activity signal | Stack |
|---|---|---|---|---|
| feder-cr/**AIHawk** (`Jobs_Applier_AI_Agent_AIHawk`) | 30,327 (4,647 forks) | MIT (releases after 2026-09-02; older AGPL-3.0) | Very active — README/license updated days before research date [FACT] | Python, Playwright-based stealth browser agent, MCP server |
| speedyapply/**JobSpy** (`cullenwatson/JobSpy`) | 4,252 (840 forks) | MIT | Active, on PyPI as `python-jobspy` [FACT] | Python scraper library: LinkedIn, Indeed, Glassdoor, Google, ZipRecruiter, Bayt, Naukri → pandas/CSV |
| browser-use/**workflow-use** | 4,165 (345 forks) | AGPL-3.0 | Early-stage, self-declared "not production" [FACT] | Python + Chrome extension recorder; deterministic workflows with AI fallback |
| nicobrenner/**commandjobs** | 168 (16 forks) | Apache-2.0 | Building-in-public, 2025 updates in README [FACT] | Python TUI: HN Who's-Hiring + Workday scrapers → SQLite → GPT matching |
| GabeGiro/**EasyApplyJobsBot** (fork of wodsuz) | 28 (11 forks) | MIT | Small/stale-ish; 44 open issues [INFERENCE] | Python/Selenium LinkedIn Easy Apply, Docker headless/VNC |
| mdkim/**LinkedInJobsAssistant** | 0 | MIT | Small personal tool [FACT] | Chrome MV3 extension exporting LinkedIn saved jobs to CSV/Excel |

`srexi/jobbot` → **HTTP 404** on GitHub [FACT, checked 2026-09-09]; no public project by that name — the user's tentative pointer is dead.

### What each does better, and what CVSender should borrow

- **AIHawk** — pivoted from LinkedIn auto-apply (TechCrunch's "2,843 applications" bot) into a general stealth browser agent embeddable into coding agents over MCP (`claude mcp add stealth -- uvx aihawk`). Borrowables: (a) `--profile-dir` persistent browser profile so logins/cookies survive restarts; (b) `--seed` fixed browser-identity seeding for stable fingerprints; (c) `.env` > flag precedence with values never printed; (d) a docs discipline around *agent retry loops & rate limits* and *when agents get blocked* (dedicated wiki/docs pages); (e) its stated ethical line: "do not submit anything a human has not read" — matches CVSender's review-before-apply gate. https://github.com/feder-cr/Jobs_Applier_AI_Agent_AIHawk
- **JobSpy** — the scouting primitive CVSender lacks: one normalized `JobPost` schema across boards, scraped concurrently, with an `hours_old` filter (incremental scouting: only what appeared since last run), `results_wanted`, `offset`, proxy round-robin. Honest operational notes worth copying into CVSender docs: "Indeed is the best scraper currently with no rate limiting"; "LinkedIn … usually rate limits around the 10th page with one IP. Proxies are a must"; HTTP 429 handling = wait between scrapes / change IP. Caveat it documents: LinkedIn `easy_apply` filter "no longer works". Borrow: `hours_old`-style incremental fetch + a stable per-board fetcher interface + rate-limit notes. https://github.com/cullenwatson/JobSpy
- **CommandJobs** — architecturally the closest cousin (local-first, human-review-in-the-loop): scrapes into **SQLite with numbered, idempotent migrations** (`000…007`, incl. `unique_applications_job_id`, `add_applied_date`, `application_notes`); AI matching writes a **JSON verdict into a column**, then matching is plain SQL: `json_extract(gi.answer, '$.fit_for_resume') = 'Yes'`. Borrow: SQLite+migrations for queue/applications; JSON-verdict column for AI match results; unique job_id constraint = dedupe at the schema level. https://github.com/nicobrenner/commandjobs
- **EasyApplyJobsBot** — small but operationally mature ideas: screening-question answers in a **YAML config** (`additionalQuestions.yaml`), **company/title blacklists**, randomized inter-action sleeps ("time breaks … to prevent threshold"), an explicit **"couldn't apply, here are the links" report**, and a self-imposed "don't exceed ~200 applies/day" guideline. Borrow: YAML answer/blacklist config; the failure report; pacing. https://github.com/GabeGiro/EasyApplyJobsBot
- **LinkedInJobsAssistant** — proof that LinkedIn's `my-items/saved-jobs` pages paginate cleanly and export to CSV; its **selector fallback chains** (per-URL-format fallbacks) and MutationObserver debouncing are directly applicable to CVSender's board scrapers. https://github.com/mdkim/LinkedInJobsAssistant
- **workflow-use** — see §6; included here because it exists *specifically* to make browser agents reliable ("born out of customer demand to make Browser Use more reliable and deterministic"). https://github.com/browser-use/workflow-use

What they all do **worse** than CVSender: none combine human-acceptance gating + a local panel + multi-agent orchestration; AIHawk's history shows the spammy full-auto mode draws press and platform heat [INFERENCE, cf. Verge/404 Media coverage linked from its README].

---

## 2. Daily cadence on macOS without a daemon (Q2)

### Facts

- Apple's official guidance: "The preferred way to add a timed job is to use `launchd`. Each `launchd` job is described by a separate file", configured with a `StartCalendarInterval` dict. https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html [FACT]
- Sleep/off behavior (same page): if the Mac is **asleep** at the scheduled time, a `StartCalendarInterval` job **runs when the computer wakes**; if it is **off**, it runs "at the next designated time". **cron jobs are simply lost** while asleep/off. For a laptop this is the deciding argument. [FACT]
- launchd runs the binary directly — no shell, minimal `PATH` (`/usr/bin:/bin:/usr/sbin:/sbin`); use a wrapper script + absolute venv paths, `StandardOutPath`/`StandardErrorPath` (directory must pre-exist), `EnvironmentVariables`, `WorkingDirectory` keys; `launchctl load`, `launchctl list`, `launchctl print gui/$(id -u)/<label>`, `launchctl start <label>` for manual test-fire; missed days fire **once**, not per-missed-day [FACT for the behaviors documented there]. Known-good full example (plist + wrapper + `env -i` dry test): https://devops.sarmento.org/en/posts/scheduling-tasks-on-macos-with-launchd-no-cron-no-workarounds/ [FACT that the example exists as described; the article is secondary but consistent with Apple's doc]
- `StartCalendarInterval` also accepts an **array of dicts** for multiple daily times (man `launchd.plist(5)`): https://keith.github.io/xcode-man-pages/launchd.plist.5.html [FACT]
- Notifications from shell: Apple's own Mac Automation Scripting Guide documents `display notification "text" with title "…" subtitle "…" sound name "…"`. https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/DisplayNotifications.html [FACT]

### Concrete pieces for CVSender

`~/Library/LaunchAgents/pl.cvsender.scout.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>pl.cvsender.scout</string>
  <key>ProgramArguments</key>
  <array><string>~/bin/cvsender-scout.sh</string></array>
  <key>StartCalendarInterval</key>
  <array>
    <dict><key>Hour</key><integer>8</integer><key>Minute</key><integer>7</integer></dict>
    <dict><key>Hour</key><integer>17</integer><key>Minute</key><integer>42</integer></dict>
  </array>
  <key>WorkingDirectory</key><string>~/Repositories/cvsenderpublic</string>
  <key>StandardOutPath</key><string>~/.local/log/cvsender-scout.out.log</string>
  <key>StandardErrorPath</key><string>~/.local/log/cvsender-scout.err.log</string>
</dict>
</plist>
```

Wrapper (absolute paths; no shell-session assumptions; `env -i` test before loading):

```bash
#!/bin/bash
cd ~/Repositories/cvsenderpublic || exit 1
# headless scout: no human review here — queue only, notify at the end
agent -p "/cvskill scout --all-keywords --queue-only" \
  >> ~/.local/log/cvsender-scout.out.log 2>&1
new=$(python3 tools/queue_stats.py --new-today)
osascript -e "display notification \"${new} new offers queued\" with title \"CVSender\" sound name \"Glass\""
```

Install/verify: `launchctl load ~/Library/LaunchAgents/pl.cvsender.scout.plist && launchctl list | grep cvsender && launchctl start pl.cvsender.scout`. Result collection = file drop (SQLite queue, §3) + the log files + the notification; the panel already reads the queue. Avoid `:00` times and pick off-cron minutes to reduce coincidence with other agents' runs [INFERENCE: hygiene, not a documented requirement].

If the scout needs the user's real Chrome via CDP and Chrome isn't running at 08:07, the wrapper should degrade to a Playwright headless run for the boards that allow it (JobSpy-style fetchers) and leave CDP-only boards for the interactive session [INFERENCE — design decision].

---

## 3. Multi-writer data store (Q3)

### Facts

- SQLite **WAL mode** (one `PRAGMA journal_mode=WAL;`, persisted): "readers do not block writers and a writer does not block readers"; but "there can only be **one writer at a time**"; all processes must be on the **same host** (WAL needs shared memory — no network filesystems); some queries can return `SQLITE_BUSY`; auto-checkpoint defaults to 1000 pages. https://www.sqlite.org/wal.html [FACT]
- Python ships `fcntl.flock()` for advisory byte-range/file locks on Unix: https://docs.python.org/3/library/fcntl.html [FACT]
- JSONL append-only: single `os.write` of a small record on a file opened `O_APPEND` is positioned atomically, so interleaving of *whole small records* is unlikely in practice, but POSIX gives no all-writers atomicity guarantee for regular files and a reader needs a compaction step; crashes mid-append can tear the last line. [INFERENCE]

### Comparison at CVSender's scale (hundreds of rows, 2-4 concurrent local writers)

| Option | Concurrency correctness | Human-readable/diffable | Effort | Verdict |
|---|---|---|---|---|
| CSV + `flock` | Correct if **every** writer locks (protocol discipline, easy to bypass) | Yes (it's the status quo) | 1-2h | Keep as stopgap only |
| CSV/JSONL append-only + compaction | Better for append; in-place status updates break the model; compaction = new race surface | Yes-ish | 0.5-1d | Skip — status updates dominate |
| **SQLite WAL** | Writer serialized by SQLite itself; readers never blocked; `busy_timeout` absorbs contention; no protocol discipline needed | Text-dumpable (`sqlite3 db .dump`, CSV views); binary core file | 0.5-1d incl. migration | **Recommended** |

### Recommended locking protocol (stopgap, CSV era)

```python
import fcntl, contextlib, os

@contextlib.contextmanager
def csv_locked(path, mode="a+", timeout=10.0):
    """All writers MUST go through this. Never open data CSVs directly."""
    fd = os.open(path + ".lock", os.O_CREAT | os.O_RDONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)          # blocking; add timeout alarm if desired
        yield open(path, mode, newline="")
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
# Protocol: lock → read-modify-write whole file → flush+fsync → release.
# Readers take LOCK_SH the same way. The .lock sidecar is gitignored.
```

### Recommended target (SQLite era)

```python
con = sqlite3.connect("data/cvsender.db", timeout=5.0)
con.execute("PRAGMA journal_mode=WAL")      # once; persists in the file
con.execute("PRAGMA busy_timeout=5000")     # wait instead of instant SQLITE_BUSY
con.execute("PRAGMA synchronous=NORMAL")    # WAL doc: only checkpoint fsyncs then
# writers:
with con:  # BEGIN IMMEDIATE on first write; commits serialized, readers unaffected
    con.execute("INSERT OR IGNORE INTO offer_queue(job_url, ...) VALUES (?, ...)", row)
```

Schema notes: `UNIQUE(job_url)` (or hash of `(company,title,location)` for boards that rotate URLs) makes dedupe a constraint, not a procedure — CommandJobs shipped exactly this as migration `006_unique_applications_job_id` [FACT]. Keep `git`-friendliness with a committed export: `sqlite3 -header -csv data/cvsender.db "SELECT * FROM offer_queue" > data/offer_queue_export.csv` run by the panel on write, so diffs stay reviewable [INFERENCE: convenience choice].

---

## 4. Email auto-verification loop (Q4)

### Facts

- **Gmail API** Python quickstart: OAuth *Desktop app* client, `InstalledAppFlow` + `run_local_server(port=0)`, token persisted to `token.json`, scope `https://www.googleapis.com/auth/gmail.readonly`; requires a Google Cloud project + Gmail API enabled + OAuth consent screen. https://developers.google.com/workspace/gmail/api/quickstart/python [FACT]
- **Refresh-token expiry gotcha** (official OAuth2 doc): "A Google Cloud Platform project with an OAuth consent screen configured for an **external** user type and a publishing status of **'Testing'** is issued a refresh token **expiring in 7 days**, unless the only OAuth scopes requested are a subset of name/email/profile" — `gmail.readonly` is not in that subset. Other loss modes: password change (with Gmail scopes), 6 months disuse, >100 tokens per client. https://developers.google.com/identity/protocols/oauth2 [FACT]
- **IMAP path**: Google requires 2-Step Verification and **app passwords** (16-char, per-app revocable) for IMAP/SMTP clients; "less secure apps" password auth is retired. https://support.google.com/accounts/answer/185833 and https://support.google.com/accounts/answer/6010255 [FACT]; Workspace tenants additionally need IMAP enabled by admin: https://support.google.com/a/answer/9003945 [FACT]

### Recommendation for ~1-2 verification mails/week

**IMAP + app password, not Gmail API.** Reasons: (a) the API's Testing-mode token dies weekly → you'd have to publish the app (unverified restricted scope = warning screen + 100-user cap, workable but setup-heavy: GCP project, consent screen, branding) or re-auth every week [FACT + INFERENCE]; (b) `imaplib` + `email` stdlib only, no dependencies — fits the stdlib-panel stack; (c) 2h vs ~1 day effort. Security notes: an app password grants **full mailbox IMAP access** (no read-only mode) until revoked — store it in macOS Keychain, never in the repo; scope the mailbox rule with a Gmail filter/label so the watcher pattern-matches narrowly [FACT re: no read-only IMAP scope is a protocol property; INFERENCE re: storage practice].

Watcher sketch (runs from the same LaunchAgent or a second one, every ~30 min via `StartInterval`):

```python
import imaplib, email, re
M = imaplib.IMAP4_SSL("imap.gmail.com")
M.login("user@gmail.com", app_password_from_keychain)
M.select("INBOX")
typ, data = M.search(None, '(UNSEEN FROM "teamtailor" SUBJECT "confirm")')
for num in data[0].split():
    typ, msg_data = M.fetch(num, "(RFC822)")
    msg = email.message_from_bytes(msg_data[0][1])
    # walk parts → regex https://…/confirm[ations]?token=… → mark verified + notify
```

Flow: apply via Teamtailor → panel row gets `verification_needed=1` → watcher extracts the confirm link → opens it headlessly (or drops it into the panel with an "open" button) → row → `verified`, notification "CodiLime application verified". **Quick win before any of this**: a panel button that opens `https://mail.google.com/mail/u/0/#search/from:teamtailor newer_than:7d` — zero credentials, kills most of the manual fetch time [INFERENCE: URL form is Gmail's documented search-in-URL scheme, widely used; verify once].

---

## 5. Outcome & follow-up tracking (Q5)

- **State machine (ATS-lite).** Keep it minimal and event-shaped: `applied → verified → screening → interview → offer | rejected | expired`, stored as `status` + `status_changed_at` on the application row, optionally with an append-only `application_events(application_id, from, to, at, note)` table. Precedent: CommandJobs' migrations added `discarded`, `applied`, `applied_date`, `application_notes`, then a **unique application per job** — i.e., the same minimal columns this domain actually needs [FACT]. `expired` exists because CVSender demonstrably loses offers to expiry; backfill it from the offer-queue `first_seen_at` + board-reported age [INFERENCE].
- **Follow-up flow = a query, not a feature**: `SELECT * FROM applications WHERE status IN ('applied','verified','screening') AND status_changed_at < date('now', '-7 days')` → panel "Needs follow-up" section + one daily osascript count. n is per-status (applied: 7d, screening: 5d, interview: 3d) [INFERENCE: defaults; tune].
- **LinkedIn tracker data.** There is **no public/official API** for an individual job seeker's application data [INFERENCE; LinkedIn jobs APIs are partner-facing, and scraping is contractually prohibited — see prior repo research: `research/2026-08-26-agent-stack-alternatives.md`, LinkedIn User Agreement §8.2.2]. However, the logged-in **internal Voyager GraphQL** endpoint behind `linkedin.com/my-items/saved-jobs/?cardType=APPLIED` is scriptable from a session that already has cookies + `csrf-token`: query `voyagerSearchDashClusters` with `flagshipSearchIntent:SEARCH_MY_ITEMS_JOB_SEEKER, cardType:APPLIED` returns title, company, location, jobUrl, postedTime, trackingId and even an unread/update indicator; public gists demonstrate pagination and field extraction (created 2025-03, updated 2026-05). https://gist.github.com/barretts/dfd0f1f776d79b557a392174ced47b56 [FACT that the gist works this way; usability inside CVSender follows from the existing CDP real-Chrome session — INFERENCE]. Practical use: a **reconciliation job** that marks CVSender rows whose LinkedIn card shows employer activity; low frequency (weekly), read-only, and keep it behind a manual trigger.
- **Response/outcome capture otherwise**: Teamtailor application-status mails + LinkedIn "your application was viewed" notifications are the two automatable signals; everything else stays human-set status in the panel [INFERENCE].

---

## 6. Agent-framework reliability notes for long-running browser workflows (Q6, brief)

- **browser-use/workflow-use** (4,165★, AGPL-3.0): "deterministic, self-healing workflows (RPA 2.0)" — record (or generate from one agent run) a semantic workflow with variables; replay **deterministically, no LLM**, falling back to the AI agent only when a step fails. Self-described as very early, "not production". The *pattern* — cache the happy path, pay LLM cost only on breakage — is the right model for CVSender's per-board scout steps. https://github.com/browser-use/workflow-use [FACT]
- **browser-use `rerun_history`**: agent execution histories can be saved and re-run (example `examples/features/rerun_history.py`); open issues (#1273, #3044) show serialization/replay edge cases — treat replay as an accelerant, not a guarantee [FACT that both exist; INFERENCE on maturity]. https://github.com/browser-use/browser-use
- **AIHawk / invisible_playwright**: persistent `--profile-dir` (logins survive restarts) + `--seed` (reproducible browser identity) are the two cheapest reliability wins for login-walled boards, and are directly portable to a Playwright/CDP setup [FACT for the flags' behavior as documented; INFERENCE on portability]. Its docs set (`agent-retry-loops-rate-limits.md`, `run-ai-agent-on-a-schedule.md`, `why-does-my-ai-agent-get-blocked.md`) is a checklist CVSender should mirror in `learning/` [FACT the docs exist].
- Checkpointing long runs: CVSender's director/worker model should persist per-offer state *before* each browser action (queue row → `applying`), so a crashed worker resumes from the queue instead of re-driving the board [INFERENCE: design guidance from the above].

---

## 7. Prioritized improvement backlog

### Quick wins (< 1 day each)

| # | Item | Effort | Payoff | Sources |
|---|---|---|---|---|
| QW1 | launchd LaunchAgent daily scout + wrapper + logs (§2) | 2-3h | Kills the "manual scouting" pain; wake-safe scheduling | Apple doc; launchd.plist(5); sarmento walkthrough |
| QW2 | `fcntl.flock` CSV shim for both data files (§3.4) | 1-2h | Ends write races today; zero migration risk | Python fcntl docs |
| QW3 | osascript notifications on queue/new-match events (§2) | 30min | Offers stop dying unnoticed | Apple notifications guide |
| QW4 | Panel "check verification mail" button → Gmail search URL (§4) | 30-60min | Removes most of the manual Gmail fetch | Gmail search-in-URL [verify once] |
| QW5 | Follow-up view: silence-based query on existing Status/date columns (§5) | 1h | Follow-ups exist before the DB migration | — |

### Bigger builds (each ≤ ~3 days)

| # | Item | Effort | Payoff | Sources |
|---|---|---|---|---|
| B1 | SQLite WAL store: one DB (queue, applications, events), CSV views for diffs, migration from both CSVs (§3) | 1-2d | Concurrency-safe by construction; dedupe as UNIQUE constraint; enables everything below | sqlite.org/wal.html; CommandJobs migrations |
| B2 | IMAP verification watcher (app password from Keychain) (§4) | 0.5d | Teamtailor verifications complete themselves; ~1-2 mails/wk justified | Google app-password docs; OAuth 7-day doc (why not API first) |
| B3 | Outcome state machine + events + per-status reminders (§5) | 1d | Real response tracking; notification-driven follow-ups | CommandJobs schema precedent |
| B4 | Incremental scout fetchers: JobSpy-style `hours_old` per board + blacklists/YAML answers + "couldn't queue" report (§1) | 2-3d | Fewer, fresher candidates; less agent time per board | JobSpy README; EasyApplyJobsBot |
| B5 | LinkedIn my-items reconciliation job (§5.3) | 1d (fragile, keep read-only + manual trigger) | Employer-side signal (viewed/status) into outcomes | barretts gist; ToS caveat from prior repo research |

### Recommended daily-cadence design (assembled)

```
08:07 & 17:42 launchd (wake-safe)                      §2
  → headless scout: incremental fetch per board, YAML blacklists   §1, §4(B4)
  → dedupe: INSERT OR IGNORE on job_url hash into SQLite (WAL)     §3
  → notify: "12 new offers queued" (osascript)                     §2
user reviews panel → accepts/rejects (panel writes via WAL db)    §3
director session applies accepted offers (per-row state first)    §6
Teamtailor apply → verification_needed → IMAP watcher → verified  §4
T+7d silence → follow-up section + notification                   §5
weekly → LinkedIn my-items reconciliation (manual trigger)        §5
```

Sequencing advice: QW1+QW2+QW3 in one sitting (they're independent); B1 next (everything else wants the DB); then B2, B3; B4/B5 when the core loop is boring.

## 8. Sources

- Apple, *Daemons and Services Programming Guide — Scheduling Timed Jobs*: https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html
- `launchd.plist(5)` man page: https://keith.github.io/xcode-man-pages/launchd.plist.5.html
- Known-good LaunchAgent walkthrough (2026-03-23): https://devops.sarmento.org/en/posts/scheduling-tasks-on-macos-with-launchd-no-cron-no-workarounds/
- Apple, *Mac Automation Scripting Guide — Displaying Notifications*: https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/DisplayNotifications.html
- SQLite WAL: https://www.sqlite.org/wal.html
- Python `fcntl`: https://docs.python.org/3/library/fcntl.html
- Gmail API Python quickstart: https://developers.google.com/workspace/gmail/api/quickstart/python
- Google OAuth2 (refresh-token expiration section): https://developers.google.com/identity/protocols/oauth2
- Google app passwords: https://support.google.com/accounts/answer/185833 ; less-secure-apps sunset: https://support.google.com/accounts/answer/6010255 ; Workspace IMAP: https://support.google.com/a/answer/9003945
- AIHawk: https://github.com/feder-cr/Jobs_Applier_AI_Agent_AIHawk
- JobSpy: https://github.com/cullenwatson/JobSpy (now under speedyapply/)
- CommandJobs: https://github.com/nicobrenner/commandjobs
- EasyApplyJobsBot: https://github.com/GabeGiro/EasyApplyJobsBot
- LinkedInJobsAssistant: https://github.com/mdkim/LinkedInJobsAssistant
- workflow-use: https://github.com/browser-use/workflow-use ; rerun_history example: https://github.com/browser-use/browser-use/blob/main/examples/features/rerun_history.py
- LinkedIn applied-items GraphQL gist: https://gist.github.com/barretts/dfd0f1f776d79b557a392174ced47b56
- Prior repo research (LinkedIn ToS context): `research/2026-08-26-agent-stack-alternatives.md`
