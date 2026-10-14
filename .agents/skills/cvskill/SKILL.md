---
name: cvskill
description: Search job listings, match them against the candidate's CV, apply through the offer's own "Apply" button/form, and log every result to the SQLite funnel store (data/cvsender.db via lib/store.py) without duplicates. Use when the user asks to look for job offers, find jobs, apply to a posting, or check application status/history.
user-invocable: true
compatibility: any harness with Agent Skills support and a browser automation layer (see Tool bindings appendix)
---

# cvskill — CV application automation

Automates the job-search → match → apply → log loop described in
`SESSION_STATUS.md` at the repository root (always the source of truth for
current status, open questions, and next steps — read it first if this
session hasn't already).

**Before first use, run `SETUP.md`** (repo root) if `data/aboutme.md` and
`data/cv_info.md` are missing (fresh clone: only `data/*.md.template` exist —
rename them by dropping `.template`, see `AGENTS.md` step 0) or still contain
`[PLACEHOLDER]`-style brackets instead of real values — this skill relies
entirely on those files, which are the single source of truth for the
user's data.

**Tool naming rule:** this document references generic browser
*capabilities* — `navigate`, `click`, `fill`/`select`, `page-structure`,
`js-in-page`, `network-inspect`, `upload`, `screenshot` — never vendor tool
names. Map them to concrete tools for your harness via the **Tool bindings**
appendix at the bottom.

## Data files (all paths relative to the repository root — the git repo containing this skill)

- `data/aboutme.md` — contact details and preferences to fill into application
  forms: name, email, phone, address, LinkedIn URL, English level, availability
  (map free-text availability like "ASAP" to the platform's own "ASAP"/
  "immediately" option when one exists instead of defaulting to a longer
  notice period), preferred contract type (pick the one it says is preferred
  when a form forces a single choice), salary expectation (given as a
  *range* — always enter a single number, per the rule below), and a canned
  message for free-text "something about yourself" fields. Re-read this file
  each session; the user updates it directly and expects those values used
  as-is, not overridden with generic/safe defaults.
- `data/cv_info.md` — full CV text (skills, experience, education) to
  match against listings. Use this for matching instead of re-parsing a PDF
  each time.
- the CV PDF in `data/` — whatever single PDF file the user has dropped
  there (the dashboard auto-detects it) — the actual file to attach when a
  form requires a CV upload.
- `data/links.md` — table of job platforms with a **Status** column
  (Nietestowany / Działa / Nie działa / Wymaga logowania). Skip rows marked
  "Nie działa". Update the status the first time you actually visit a
  platform in a session, or whenever its behavior changes — never guess a
  status without visiting.
- `data/cvsender.db` (SQLite; helpers in `lib/store.py` — read it before
  writing store code) — the only funnel store since 2026-09-14 (the old
  `applications.csv` / `offerstosend.csv` files are gone). Two tables
  matter to this skill:
  - `applications` — the log of applications actually sent (or rejected).
    Columns: `applied_date, company, position, level, match, job_url,
    source, status, method, notes` plus derived `state`/`state_changed_at`.
    Any row whose `status` starts with `"Blocked"` (rules 9 and 10)
    automatically surfaces in the panel's red "Wymaga Twojej działania"
    tab — keep using exactly that prefix (e.g. `Blocked - needs manual
    action`). Append via `store.add_application(conn, {...})`; move a row
    through the funnel via `store.set_application_state(conn, app_id,
    state)` (`status` is free text the funnel `state` is derived from).
  - `offers` — the scouted corpus AND the **proposal queue**: matched
    candidates waiting for the user's go-ahead. The `decision` column is
    the source of truth: `pending` (default, not yet reviewed — shortlist/
    "Oferty dla Ciebie" tab), `accepted` (ready to send — "Czekają na
    wysłanie" section of that tab), `postponed_future` / `postponed_no_send`
    (parked — "Odłożone" tab), and
    `handled` (accepted offer already processed by an agent — hidden from
    every tab). Queue a new match via `store.upsert_offer(conn, {job_url,
    company, title, level, match, source, notes, decision})`; flip a
    decision via `store.set_offer_decision(conn, job_url, decision)` — it
    applies to the offer's whole dedup-key group, so sibling reposts can't
    resurface an offer the user already decided on. Quick check:
    `sqlite3 data/cvsender.db "SELECT company, title, decision FROM offers WHERE decision='accepted';"`
  The user makes these decisions through the local panel
  (`frontend/server.py` + `frontend/static/index.html` — run
  `python3 frontend/server.py` from the repository root, then open
  http://127.0.0.1:8765) at their own pace, independent of any chat
  session; the panel's tabs mirror the `decision` states (shortlist groups
  `pending`, "Czekają na wysłanie" is `accepted`, "Odłożone" covers both postponed
  variants, `handled` shows nowhere). See hard rule 2 for exactly how this
  queue is used. The same server also exposes `GET /api/cv-file` serving
  the CV PDF (legacy byte path for the hard-rule-10 workaround; note
  Chrome's Local Network Access protection blocks in-page `fetch()` of it
  from public https ATS pages — rule 10 workaround B now passes bytes via
  script-call arguments instead); it's not part of the panel UI.
- `data/logs/session_diary.md` — **local session diary, never committed**
  (`data/logs/` is gitignored; the file may hold real user data). Append a
  dated entry at the end of every working session: what was done, the
  user's decisions, lessons learned. The committed `SESSION_STATUS.md`
  keeps only the operating manual plus a regenerable "Stan bieżący"
  snapshot — never move user-identifying details there.

## Hard rules (do not skip)

1. **Dedup before showing any candidate.** Check the DB for the offer URL
   (and company+position as a fallback if URLs get redirected/shortened)
   before presenting or queuing it:
   `store.get_offer(conn, url)` for the corpus/queue and
   `conn.execute("SELECT 1 FROM applications WHERE job_url = ?", (url,))`
   for already-applied offers. Never show, queue, or apply to something
   already logged (`applications`) or already queued/decided (`offers` with
   any `decision`).
2. **Never apply without `decision='accepted'` in the offers table (current
   policy, v1).** A matched candidate is never applied to on the strength of
   match quality alone — do not silently switch to auto-apply even if match
   confidence looks high (see `SESSION_STATUS.md` for the current policy
   decision). Concretely:
   - Upsert every new match into `offers` with `decision='pending'` — this
     is the durable queue the user reviews via the local panel (see Data
     files above), independent of whether a chat is open.
   - **If actively chatting with the user right now**, you may still present
     the candidate inline (company, position, level, match rationale, URL)
     and ask directly — that's just a faster path to the same gate. Treat an
     explicit "yes/wyślij/tak" as the user setting `decision='accepted'` for
     that offer: run `store.set_offer_decision(conn, job_url, 'accepted')`
     before proceeding (keep the DB in sync with what actually happened, so
     the panel never shows something as pending that was already decided in
     chat).
   - **Before starting a new search pass**, check `offers` for leftover
     rows with `decision='accepted'` from earlier (panel review that
     happened outside a chat) and apply to those first, per rule 3.
   - Only ever click anything that submits an application for an offer that
     is `decision='accepted'` at that moment. A still-`pending` offer —
     freshly queued or sitting unreviewed in the panel — must not be applied
     to; move on to the next candidate instead of blocking on it.
   - Once an offer is applied to (success or failure), **set its decision
     to `'handled'`** and log the outcome to `applications` (rule 4) —
     accepted-and-handled offers don't linger in the "to send" tab.
   - If the user rejects a queued candidate (in chat, or by telling you to
     drop a panel row), set its decision to `'handled'` (or a `postponed_*`
     decision if they want it parked) and log it to `applications` with
     `Status = Rejected by user` (rule 4) so it's never re-shown or
     re-queued.
3. **Apply only via the offer's own "Apply"/"Aplikuj" button or in-page
   form.** No email applications. Offers sometimes redirect to a company's
   own careers site after clicking Apply — follow it and handle the actual
   form there; don't treat the redirect itself as a failure.
4. **Log every attempt**, success or failure, to the `applications` table
   via `store.add_application(conn, {...})` —
   including ones the user rejected at the confirmation step (Status =
   `Rejected by user`) so they're never re-shown.
5. **Never invent a `links.md` status.** Only mark a platform Działa / Nie
   działa / Wymaga logowania after actually navigating there this session.
6. **Salary field.** `aboutme.md` gives a **monthly** range. If a form asks
   for an **hourly** rate instead, convert first — divide the range by the
   user's stated monthly working hours (commonly ~160h/month if not
   specified) to get an hourly range. Then:
   - If the offer's own stated hourly floor is **higher** than the top of
     your computed range, use the **offer's floor**, not a value invented
     above it (e.g. offer states 130–165 PLN/h and your computed range tops
     out at 125 → enter 130).
   - If the offer's floor **falls within or below** your computed range, use
     a value from **your own range** (prefer the top, unless the offer
     suggests otherwise) — never inflate to the offer's upper end just
     because it's higher.
   - The "match the offer's floor" clause is real but isn't unconditional
     license to go arbitrarily high — when in doubt, favor the top of the
     user's own computed range over the offer's floor. If a submission looks
     off before you click submit, stop and check with the user rather than
     guessing.
   Enter **only the number** (e.g. "125 PLN/h"), never a long explanatory
   description — some forms show a long note as invalid/odd.
   The concrete numbers come from `data/salary_policy.json` (personal,
   gitignored; template: `data/salary_policy.example.json`). Compute the
   answer with `python3 lib/salary.py <job_url> [min] [max] [currency] [period]`
   — it encodes the rules above and prints the value plus its reasoning.
7. **Login is manual, not automated.** If a platform sits behind a login wall
   (e.g. LinkedIn) and a Google "Kontynuuj jako <name>" one-tap prompt
   appears, do not click it yourself — that's an OAuth/SSO grant, which
   requires explicit per-instance user permission (session safety rules).
   Ask the user to log in manually in the browser and continue once they
   confirm, or get explicit permission first if they'd rather you click it.
8. **Note any 1st-degree contact at the employer** (LinkedIn shows "N kontakt
   pracuje/pracują tutaj" on an offer) in the `applications` row's `notes`
   — a warm contact is worth flagging even though reaching out to them
   directly is a separate action for the user, not something to do
   automatically.
9. **Never create an account or enter a password to apply**, on any platform,
   regardless of user instruction — this is a hard safety boundary, not a
   judgment call. If the only path to apply is creating an account (email +
   password) or an OAuth signup, stop, log the row to `applications` with
   `Status = Blocked - needs manual action` and a notes entry explaining
   exactly what's required, set the offer's decision to `'handled'`, and tell the
   user they need to do it themselves.
10. **If a required file upload (usually the CV) can't be reached through the
    page-structure view** (the accessibility snapshot only exposes an
    unrelated file input, e.g. a profile-photo uploader, or none at all —
    happens with some ATS built on shadow-DOM web components), **do not click
    the visible dropzone/"Choose a file" text directly** — that opens a
    native OS file picker outside the tools' reach and leaves the browser
    as blocked (same as rule 9 — `Blocked - needs manual action`, set the
    offer's decision to `'handled'`, explain what was filled in and what was missing) if none
    applies or they fail.
    - **Workaround A — direct path upload (`upload` capability):** if the
      real `<input type="file">` can be reached by any selector (including
      shadow-piercing ones), set the file by *local path* directly on that
      input — no OS picker is ever opened. Prefer this whenever available.
    - **Workaround B — js-in-page injection with bytes passed in the call:**
      run JS in the ATS tab's own context (`js-in-page` capability) and
      construct the `File` from the CV bytes passed **as an argument to the
      script call** (base64 → `atob` → `Uint8Array` → `new File([...],
      "<cv filename>.pdf", {type: "application/pdf"})` — verified
      byte-perfect 2026-08-26). Then build a `DataTransfer`,
      `dt.items.add(file)`, set `input.files = dt.files` on the shadow-DOM
      file input (found via direct JS traversal, e.g. walking
      `el.shadowRoot` since the page-structure view can't see into it), then
      dispatch `input` and `change` events on it. This never opens a native
      OS picker. Note: the in-page script call can report a timeout if the
      SPA auto-advances to the next form step mid-response (destroying the
      JS execution context) — treat a post-timeout screenshot showing
      navigation to a new step/URL as likely-successful, but still look for
      an explicit confirmation (e.g. a final "Application submitted!"
      success page) before logging the whole application as `Applied`.
      - **Do NOT fetch() the CV from the local panel** (`http://127.0.0.1:8765/api/cv-file`)
        inside a public https page: Chrome's Local Network Access protection
        (verified 2026-08-26) makes that fetch hang indefinitely with no
        error. The panel endpoint remains useful only for same-origin/manual
        use — pass bytes via script-call arguments instead.
    - **Hardened dropzones:** some widgets actively clear synthetic file
      assignments on their own `change` handler (verified 2026-08-26:
      SmartRecruiters "oneclick-ui" Easy Apply `SPL-DROPZONE` — resets
      `input.files` after `change`, ignores `drop` events and
      path-piercing uploads). If assignment verifies empty after dispatch,
      do not keep trying — fall back to blocked (rule 9 flow) or, if the
      resume field is optional, fill the remaining fields manually and note
      in the `applications` row's `notes` that the CV was not attached.
11. **Store hygiene:** write through the `lib/store.py` helpers
    (`store.add_application`, `store.upsert_offer`,
    `store.set_offer_decision`) — never hand-edit `data/cvsender.db` with
    ad-hoc INSERT/UPDATE SQL, or the derived columns (`state`,
    `state_changed_at`, `dedup_key`) go stale. After writing, spot-check
    with a SELECT rather than assuming the write landed:
    `sqlite3 data/cvsender.db "SELECT id, company, status, state FROM applications ORDER BY id DESC LIMIT 3;"`
12. **Never click/solve a reCAPTCHA or other bot-detection widget**, even a
    single "I'm not a robot" checkbox — this is a hard session safety
    boundary (same class as rule 9), not a judgment call. If a form's last
    remaining step before submit is a reCAPTCHA, fill in and verify every
    other field first, leave the tab open exactly as-is, and tell the user
    directly that they need to solve the CAPTCHA and click the submit/Apply
    button themselves — don't log it as `Applied` (nothing was submitted
    yet) and leave the offer's decision at `'accepted'` until it actually
    gets sent.
13. **Upsert each matched candidate into `offers` immediately after
    evaluating it — never hold a batch of candidates in memory to write "at
    the end."**
    An agent that evaluates many good candidates during a long
    search pass but keeps them only in memory to write in one batch at the
    end risks losing all of them if the session gets cut off (rate limit,
    crash, user stopping the session) before writing anything — with no way
    to recover them, even from the agent's own transcript. Append-as-you-go
    means a mid-search interruption only costs the candidate currently being
    evaluated, not the whole pass. This applies to any long search/matching
    loop over multiple listings, whether run inline or as a background agent.
14. **Match the language of any free text you write to the job posting's own
    language.** If the listing is in English, every free-text field you
    author or edit — cover letter, "something about yourself," answers to
    screening questions, translated work-experience entries — must be in
    English, never Polish, regardless of what language the platform's own UI
    chrome is in or what language a profile auto-fill pulled from. This is
    also why LinkedIn Easy Apply's auto-filled Work Experience descriptions
    (pulled from the Polish-language profile) must be translated before
    submitting to an English-language posting — see the per-platform notes
    below for the ChainGPT/Workable case this was first caught on.

## Workflow

1. **Check browser control is available.** The session must expose the
   browser capabilities from the appendix (at minimum `navigate`, `click`,
   `page-structure`). If they're unavailable, tell the user directly and
   stop — don't attempt the workflow without them.
2. **Load context**: read `data/aboutme.md`, `data/cv_info.md`,
   `data/links.md`, then open the store: `store.connect('data/cvsender.db')`.
   If `aboutme.md` or `cv_info.md` still contain `[PLACEHOLDER]` brackets,
   stop and tell the user to run `SETUP.md` first.
3. **Handle any leftover `decision='accepted'` offers first** (rule 2) —
   apply to those before searching for anything new.
4. **Pick platforms** from `data/links.md` with status Działa or Nietestowany
   (test the untested ones as you go, updating their status).
5. **For each platform, loop through a fixed keyword set** derived from
   the search profile — `search_keywords` in `data/search_profile.json`
   (written by `SETUP.md` Step 3 from the questionnaire + CV; if it is
   missing, derive keywords from `cv_info.md`/`aboutme.md` and suggest the
   user re-runs `SETUP.md` Step 3). Don't stop after one keyword. The same
   profile's `scoring` rules are what the matcher uses to rank the queue —
   treat them as the user's stated priorities when judging a listing.
   Search each keyword on the current platform before moving to the next
   platform, respecting the remote/hybrid preference in `aboutme.md`. Prefer
   a platform's own recency/publication-date filter (e.g. "last week") over
   its unfiltered full result set when the platform is fast-moving enough
   that a month-old posting is likely already closed — check what's
   available and pick accordingly instead of reviewing everything unfiltered.
   When a search's results are dominated by a technology the CV has zero
   experience in (no tie to the core skills in `cv_info.md` / the profile's
   positive `scoring` rules), judge each listing on its own merits rather
   than blanket-skipping the keyword — a strong tie to the user's other
   skills, an unusually high rate, or an explicit "we care about fundamentals, not the specific
   framework" clause can still make it worth queuing (see the tool-bindings
   Appendix's per-platform notes and prior session outcomes for the
   calibration this has already converged on).
6. **For each listing found**:
   - Dedup check in the DB (rule 1)
     — skip if already logged or already queued/decided.
   - Read the listing, determine `Level` (Junior/Mid/Senior/Other) and a
     short `Match` rationale against the CV. A listing doesn't need an
     exact keyword match to be worth showing — for Junior/Mid roles, broad
     technology overlap with the CV's stack is a reasonable basis for
     applying even without a perfect fit; note that reasoning in `Match`.
   - Upsert it into `offers` with `decision='pending'` (rule 2). If
     actively chatting, you may also present it and get an immediate
     yes/no — treat "yes" as `decision='accepted'` (apply right away) and
     "no" as a rejection (log to `applications`, set decision to `'handled'`).
   - If accepted (now or later, via the panel): apply via the in-page Apply
     flow (rule 3), filling contact fields from `aboutme.md` and attaching
     the CV PDF where a file upload is required; then set the offer's
     decision to `'handled'` and log the outcome to `applications` (rule 4).
7. **At the end of a session**, close the loop in three places: if any
   platform statuses in `links.md` changed, make sure the file reflects
   them; append a dated entry to `data/logs/session_diary.md` (local,
   never committed); and refresh the "Stan bieżący" snapshot in
   `SESSION_STATUS.md` (regenerate the counts from `data/cvsender.db`).

**Reporting to the user while searching:** don't narrate each listing you
skim and reject — that's noise. Log the reasoning in the `offers` row's
`notes` only for candidates you actually queue. Give the user a brief update
at natural checkpoints (finishing a keyword, finishing a platform, or when
something time-sensitive/notable turns up), not a play-by-play. A "what I
covered" summary belongs at the end of a platform/keyword loop, in 1-3
lines — company names and one-line verdicts, not full rationale per
rejection — or on request, not proactively after every single item.

## Filling third-party ATS forms (Traffit and similar)

Several platforms' "Aplikuj" button doesn't submit anything itself — it opens
the employer's own ATS form (often Traffit, e.g. `*.traffit.com`) in a new
tab, sometimes after an intermediate "did it work?" tracking prompt on the
original site (TheProtocol.it does this — answer its "Czy udało Ci się
zaaplikować?" honestly after the real application went through). Handle the
new tab, then close it once done and return to the original tab.

Lessons learned filling these forms (applies broadly, not just to Traffit):
- **Combobox/autocomplete fields (country, city) need an actual selection**
  from the dropdown suggestion list (click the suggestion, or arrow-down +
  Enter) — typing text alone can leave the field looking filled but
  registering as empty/invalid on submit. Clear and retype a few characters,
  wait briefly, and confirm a real suggestion list rendered before picking one.
- **Traffit city-search comboboxes require correct local-language diacritics.**
  Typing an ASCII-only city name (e.g. "Wroclaw" instead of "Wrocław") can
  silently return zero results (API call returns HTTP 204, confirmed via
  `network-inspect`) while the correctly-accented spelling returns the
  real suggestion list. If a city combobox shows no suggestions no matter
  what, retype the city name with correct diacritics before concluding the
  field is broken. Also: a sibling "Kraj" (country) select can keep showing
  a stale red "Pole wymagane" error even after a real selection is made and
  the city is correctly chosen — this matches the general stale-error-text
  lesson below; submit and judge by the actual outcome page.
- **A dependent dropdown can silently reset** when a sibling one changes (e.g.
  picking a city can blank out the already-picked country) even though it
  still visually shows the old value — re-check linked fields after fixing one.
- **"Pole wymagane" / required-field error text can stay visible even after
  the field is correctly filled.** Don't loop retrying because the message
  hasn't disappeared — attempt submit and judge success from the actual
  outcome (redirect to a thank-you/confirmation page), not the stale label.
- **Consent checkboxes:** check every checkbox marked with a required
  asterisk (*) — the form won't submit without them, even if one covers
  "future recruitment processes" as well as this one. Leave *unmarked*
  (optional) broader-consent checkboxes unchecked by default, to keep data
  use scoped to this specific application unless the user says otherwise.
- **Some numeric fields (e.g. salary) reject units/text and want a bare
  integer** — a submit can fail with a "must be a whole number"-style error
  even though the label implies a currency/unit. If a text-plus-number value
  gets rejected, retry with just the digits, no currency/unit suffix (seen
  on eRecruiter-style forms).
- **Shadow-DOM / web-component ATS forms (e.g. SmartRecruiters "Easy
  Apply")** can hide the real file input from the page-structure view
  entirely — see hard rule 10 for the upload/js-in-page workarounds; fall
  back to blocked only if neither applies.
- **A confirmation/thank-you page with unexpected copy isn't necessarily a
  failure — check the network log (`network-inspect`) before assuming so.**
  An employer can reuse one generic "thank you" template for multiple
  purposes (e.g. a newsletter opt-in and an actual application submission),
  which can look like the form silently failed or expired. Before logging an
  ambiguous post-submit landing page as blocked/failed, check the network
  traffic for a conversion/tracking event tied to the application (search
  for the platform's own language for "sent"/"applied"/"cv") rather than
  trusting the page's title or copy alone.
- **Pracuj.pl's plain "Aplikuj" button (not just "Aplikuj szybko") can redirect to a login.pracuj.pl password prompt** even for an email that already has an account — do not enter a password (hard rule 9). Look for an "Aplikuj bez logowania" (apply without logging in) link on that same login screen; it skips authentication entirely and drops you straight into the real application form (often a third-party ATS like Elevato in a new tab), no account created.
- **After multi-step forms with dynamic content** (an "Add" section
  appearing, a multi-select turning a field into chips), re-screenshot
  before the next blind-coordinates click — the page can reflow/scroll and a
  queued click can land on the wrong field entirely. Don't chain multiple
  blind clicks across a layout-changing action.

## Captcha & fingerprint handoff playbook (deterministic)

Condensed from `research/2026-09-09-antibot-form-driving.md` (§5 taxonomy,
§6 reliability checklist) — read that for the full rationale and citations.

**Pre-submit widget audit** (read-only, paste-safe in page context):

| What you find | Meaning | Action |
|---|---|---|
| `.g-recaptcha[data-sitekey]` visible checkbox | reCAPTCHA v2 checkbox | **Handoff: exactly one human click** |
| `.grecaptcha-badge` present, `grecaptcha.getResponse()` non-empty | invisible v2 solved itself on real Chrome | proceed |
| `.grecaptcha-badge` present, token empty | invisible v2 not yet scored | wait a few seconds, re-check; still empty at submit -> handoff |
| `window.turnstile` / `.cf-turnstile` auto-completing (spinner, no checkbox) | Turnstile non-interactive/invisible | wait for token, proceed |
| Turnstile checkbox visible | managed mode, interaction required | **Handoff: exactly one human click** |
| hCaptcha / Arkose | out of scope | **Handoff** |
| `data-size="invisible"` on `.g-recaptcha` | invisible v2 | same as badge rows |

**Fingerprint-gated native apply modals (JustJoin.it is the known case):**
the modal POST is verified server-side (`recruitmentProcess.fingerprintVerificationFailed`);
synthetic fills + an attached CDP session plausibly poison the verdict.
Therefore: **prefill 100% of the modal, solve nothing, leave it filled, and
hand off with exactly ONE human action** (the captcha box if present, else
submit). One submit attempt only — retries worsen the IP/profile verdict.
Log the row as `Blocked - handoff 1 click` with what remains to click.
External-apply redirects (eRecruiter, Greenhouse, Elevato) have no such gate —
fully automated there.

**Dead-button / overlay checks** (before declaring a form broken):
1. Hit-test: `document.elementFromPoint(rect.centerX, rect.centerY)` — if the
   hit is not the target or its descendant, an overlay eats the click
   (`.cdk-overlay-container`, cookie walls). Close/wait/retry; `location.reload()`
   as the fallback.
2. Network probe: wrap `window.fetch` + `XMLHttpRequest.prototype.open` with a
   counter, dispatch the full pointer sequence (pointerdown/mousedown/pointerup/
   mouseup/click), then read the counter after ~3 s — zero requests => dead UI;
   try the platform's known escape hatch instead of hammering.
3. Trusted-click escalation: one real CGEvent/cliclick click (screen-space
   coords = window position + element rect, mind devicePixelRatio 2) before
   concluding a widget is broken.

**React portals & remounts:** menus render into `document.body` — search
document-wide (`[class*="select__option"]`), re-query inside a retry loop,
verify via `[class*="select__single-value"]`. Never cache element refs across
awaits on hydrating SPAs; re-confirm `isConnected` after any URL/history
change. Controlled inputs: native setter + `input`/`change` events, else the
form state diverges silently from what the UI shows.

## Per-platform notes (from real testing — see `links.md` for the full table)

- **JustJoin.it:** best case — 1-click Apply with the candidate profile
  (name/email/CV) already attached, *if* still logged in — the session can
  log out between sessions, in which case "Apply" shows a "We see you're
  back! Did you manage to complete your application? / Create an
  account..." upsell modal with a "Skip" link at the bottom — click Skip
  (never "Yes, create my profile", that's account creation, see hard rule 9)
  and continue to the actual application form that opens underneath/in a
  new tab. Also: JustJoin.it's own "N day left" countdown can be stale — the
  underlying employer ATS listing (e.g. SmartRecruiters) may already show
  "this job has expired" even while JustJoin.it still advertises time
  remaining; check the real form before assuming the posting is live.
  Modal dismissal note (verified 2026-08-26, omp relay): the modal's visible
  "Close modal" icon button can time out on `click` (obstructed hit target) —
  pressing **Escape** dismisses it reliably; never click "Create an
  account/profile".
- **NoFluffJobs:** "Aplikuj" opens the employer's own ATS (e.g. Traffit) in a
  new tab.
- **TheProtocol.it:** "Aplikuj" opens the employer's own ATS in a new tab,
  *and* TheProtocol separately asks "Czy udało Ci się zaaplikować?" (tak/nie)
  back on its own tab afterward — answer that too once the real application
  succeeded.
- **LinkedIn Jobs:** sits behind a login wall (see hard rule 7). Once logged
  in, filter by seniority via "Wszystkie filtry" → "Poziom doświadczenia".
  "Aplikuj" is often "Odpowiedzi zarządzane poza LinkedIn", redirecting to
  the employer's ATS in a new tab. Check the offer card for "N kontakt(y)
  pracuje/pracują tutaj" and log any 1st-degree contact (hard rule 8).
- **Pracuj.pl:** has both a "Poziom stanowiska" checkbox filter (praktykant/
  junior/mid/senior/…) and a "Tryb pracy" filter (stacjonarna/hybrydowa/
  zdalna) in the left sidebar. "Aplikuj szybko" on the offer page itself
  shows CV/contact fields already pre-filled from the user's Pracuj.pl
  profile, then redirects to an **eRecruiter** form (`system.erecruiter.pl`,
  a different ATS than Traffit) that's *also* pre-filled from the same
  profile. eRecruiter forms often add employer-specific required questions
  (e.g. "how did you hear about us", a B2B daily/hourly rate expectation, "did
  you know about working here before") — answer honestly/per rule 6, and
  note eRecruiter's consent checkboxes are commonly **all optional** (no
  required asterisk) — leave them unchecked by default same as any other
  optional broader-consent box.
- **RocketJobs.pl:** same company as JustJoin.it. Seniority filter is under
  "+1 Filtr" → scroll down to "Doświadczenie" (junior/mid/senior/…) —
  careful, "Wymiar pracy" (Freelance/B2B/etc.) sits right above it and is
  easy to click by mistake. Applications go to the employer's own ATS in a
  new tab.
- **Bulldogjob.pl:** clicking "Aplikuj" itself can **require being logged
  into Bulldogjob.pl** (login or "Nie mam konta" signup, no guest path) —
  that part is always blocked per hard rule 9; ask the user to log in
  manually. But once the user is logged in and navigates to the offer
  themselves, "Aplikuj" can redirect to the *employer's own* ATS as a guest
  form that needs no account of its own — don't assume every
  Bulldogjob-sourced application is blocked; check what "Aplikuj" actually
  opens once the user has a session.
- **We Work Remotely / RemoteOK:** tend to be low-value for niche
  DevOps/infra searches — categories skew senior or target a specific
  foreign local market, and can be polluted with unrelated listings. Both
  have "Auto-Apply with AI"-style buttons — never use them, they're
  third-party automation outside our control. Don't spend much time here
  unless the mix of listings changes.

## Open items

See `SESSION_STATUS.md` → for what's still undecided for this deployment
(e.g. whether to move from "confirm every application" to a more autonomous
auto-apply policy). Don't implement a more autonomous behavior until that's
explicitly resolved with the user.

## Appendix — Tool bindings (capability → concrete tool per harness)

Never use a vendor tool name in the rules above — only these capabilities.
Bind them to your harness here:

| Capability | omp `browser` tool (primary) | Playwright MCP (fallback) | Claude-in-Chrome (legacy) |
|---|---|---|---|
| navigate | `tab.goto(url)` | `browser_navigate` | navigate |
| click | `tab.click("eN")` / CSS selector | `browser_click` | click |
| fill / select | `tab.fill` / `tab.select` | `browser_fill` / `browser_select_option` | type / select |
| page-structure (a11y snapshot with element refs) | `tab.observe()` / `tab.ariaSnapshot()` — `[ref=eN]`, shadow-root aware; `tab.ref(id)` / `tab.id(n)` resolve handles | `browser_snapshot` | `read_page` / `find` |
| js-in-page (run JS in the page's own context; shadow-DOM traversal) | browser `run` code: `tab.evaluate(...)` or raw puppeteer `page` | `browser_evaluate` | `javascript_tool` |
| upload (set file on an input by local path — no OS picker) | `tab.uploadFile(selector, path)` | `browser_file_upload` | — (use js-in-page) |
| network-inspect (verify submits, debug silent failures) | `tab.waitForResponse(pattern)`; raw `page` request events (interception is run-scoped — capture within one `run` cell) | `browser_network_requests` / `browser_network_request` | `read_network_requests` |
| screenshot | `tab.screenshot()` | `browser_take_screenshot` | screenshot |
| availability check (workflow step 1) | `browser` tool present in the session | MCP server connected | ToolSearch |
| skill invocation | `/skill:cvskill` | n/a (harness-level) | `/cvskill` |

Notes:
- The dashboard's `GET http://127.0.0.1:8765/api/cv-file` endpoint
  (`frontend/server.py`) is a **legacy fallback only**: Chrome Local Network
  Access (verified 2026-08-26) makes public-https pages' `fetch()` of it
  hang with no error. The verified byte path is rule 10 workaround B —
  pass base64 CV bytes as an argument to the js-in-page call (byte-perfect
  roundtrip confirmed). Keep the panel running for the approval queue; the
  endpoint itself is no longer load-bearing.
- omp Browser Relay mode (`app.relay: true` / `browser.relay` setting;
  extension installed via `omp browser-relay install`) drives the user's
  real, logged-in Chrome — the operational replacement for Claude-in-Chrome.
  Use `app.target: "<url substring>"` to adopt the right tab without
  stealing focus.
