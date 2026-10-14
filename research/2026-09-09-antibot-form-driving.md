# Anti-Bot Countermeasures & Form-Driving Reliability — CVSender Research

Date: 2026-09-09. Scope: why JJIT native apply rejects us (`recruitmentProcess.fingerprintVerificationFailed`), what mitigation menu exists for CDP-detached/attached automation on a REAL Chrome profile, captcha taxonomy for our never-solve policy, and SPA dead-UI reliability patterns. Method: primary vendor docs, rebrowser/patchright/benchmark sources, and direct inspection of JJIT production HTML + our own relay extension source.

---

## 0. TL;DR — ranked actions

1. **Instrument the JJIT failure first (cheap, zero ToS risk).** Capture the actual POST `/api/candidate-api/applications` body + response. The apply payload carries `{fingerprint, captcha}` (both nullable) — see §1. We must know whether the failure is a missing/invalid fingerprint token, a missing reCAPTCHA v2 token, or a negative bot verdict before picking any mitigation.
2. **Adopt the "prefill + single human click" handoff for fingerprint-gated boards.** Agent fills 100% of the modal, user performs the submit click (and any captcha box). One click, board intent respected, zero bypass. [INFERENCE: only realistic long-term path for JJIT under our never-bypass rule.]
3. **Reduce CDP exposure during apply.** Our relay attaches `chrome.debugger` per tab (confirmed, §2.3). Attach late, detach before/around fingerprint-sensitive steps where feasible, and drive real clicks via macOS CGEvents (§4.2) so `isTrusted` events hit the submit path.
4. **Keep captcha handoff deterministic** using the detection table in §5: invisible/enterprise + Turnstile non-interactive/invisible auto-pass on real Chrome; checkbox widgets = exactly one human click.
5. **Not-for-us regardless of effectiveness:** captcha-solving services, fingerprint-spoofing stacks (antidetect browsers, custom Chromium), patched-Playwright applies to logged-in boards. They defeat controls the boards deployed deliberately, i.e. ToS/hostile; our own skill already hard-codes this rule for JJIT.

---

## 1. Diagnosis: what JJIT actually runs on the apply path

Direct evidence from `https://justjoin.it` production HTML (fetched 2026-09-09, Nuxt config payload):

- `"fingerprintingWorkerEndpoint":"https://id.justjoin.com/5kwvifmbvxthx5i/rvkjele7fghqcfm"` [FACT]. `id.justjoin.com` is JJIT's own origin (the endpoint answered `Cannot GET /fingerprint` — an Express-style Node backend), so fingerprint tokens are collected client-side and verified server-side at apply time. The two-opaque-token URL path shape matches Fingerprint Pro's proxied loader pattern, but the vendor is NOT confirmed — the endpoint itself is first-party. [INFERENCE on vendor; FACT on endpoint.]
- `"fingerprintingOnApply":{"name":"up.fingerprinting-on-apply","variant":"standard","enabled":true,"payload":{"fingerprint":null,"captcha":null}}` and `"fingerprintingOnExternalApply":false` [FACT]. Reads as: a feature-flagged "apply enrichment" attaches a fingerprint value and a captcha value to the native apply submission; external (redirect-to-ATS) applies are not fingerprinted. This exactly matches the observed split — our ATS redirects (eRecruiter, Elevato, Greenhouse) pass while JJIT *native* modal POSTs get 400 `recruitmentProcess.fingerprintVerificationFailed` (Pragmile, Kadromierz).
- `"googleRecaptchaV2Key":"6LeTZ-ErAAAAAA_fFNEN3N575ErA7CPrGYyZX50o"` [FACT] — reCAPTCHA v2 is wired into the product (the modal's captcha slot in the payload above).

What "verification failed" can mean, in order of plausibility for our stack:

1. **Negative automation verdict at fingerprint time.** The probe runs while our `chrome.debugger` CDP session is attached and while our driver has just dispatched synthetic `isTrusted:false` events and instant-filled fields. Fingerprint's Bot Detection docs explicitly classify Playwright/Puppeteer/Selenium-style automation as "bad bot" and combine "hundreds of browser attributes and network signals" server-side (docs.fingerprint.com/docs/bot-detection/overview) [FACT re: vendor capability; INFERENCE re: that being what tripped us].
2. **Runtime.enable-class CDP signal.** DataDome's June 2024 write-up (referenced by rebrowser) documents page-side detection of an attached CDP session via `Runtime.enable` -> `Runtime.consoleAPICalled` side effects; rebrowser confirms Cloudflare and DataDome use it and that "probably all others have it in their anti-bot arsenal" (rebrowser.net blog, §7) [FACT]. A probe triggered on the apply modal while we are attached would see us.
3. **Missing/bad captcha token.** If the modal requires a reCAPTCHA v2 token we never obtain (we never click captchas), the server may fold that into the same failure code. [INFERENCE — must be confirmed by instrumenting the POST body.]

**Disambiguation procedure (proposed):** before Submit, evaluate in page: does `grecaptcha?.getResponse()` return a non-empty token? Did the tab call `id.justjoin.com/...` (Network panel / performance entries)? Then submit once and diff request payload `fingerprint`/`captcha` fields vs a manual human submit on a throwaway offer. [FACT that fields exist; procedure is INFERENCE.]

Mobile web as an alternative client: no evidence found either way (no community reports of the mobile flow passing/failing automation checks). Untested. [INFERENCE/unknown]

---

## 2. CDP-detection mechanics (RQ1) and our exposure

### 2.1 The `Runtime.enable` leak
All mainstream drivers (Puppeteer, Playwright, Selenium wrappers) call CDP `Runtime.enable` to discover execution contexts; the browser then emits `Runtime.consoleAPICalled` events whose timing page JS can observe — "5 lines of JS", used by Cloudflare and DataDome (and by extension "probably all others" per rebrowser's testing). Console-Proxy or `console.debug={}` overrides do NOT defeat sophisticated detectors. Sources: rebrowser.net blog "How to fix Runtime.Enable CDP detection..." (URLs in §7); DataDome: datadome.co/threat-research/how-new-headless-chrome-the-cdp-signal-are-impacting-bot-detection/ [FACT].

Public test pages for whether an attach is detectable: `bot-detector.rebrowser.net`, `kaliiiiiiiiii.github.io/brotector/`, `deviceandbrowserinfo.com/are_you_a_bot`, `hmaker.github.io/selenium-detector/` [FACT].

### 2.2 What passes and what doesn't
- Real Chrome, headed, human-driven, CDP **not** attached: passes everything by definition.
- Real Chrome + CDP attach (our case): unpatched Playwright-style drivers trip `Runtime.enable` probes; rebrowser-patched drivers currently pass Cloudflare/DataDome probes per rebrowser tests [FACT vendor claim]. 2026 benchmark: rebrowser-playwright scored 24 OK / 2 gated / 5 blocked of 31 live targets — same as vanilla Playwright; the benchmark ran it on Chromium 136 and noted its repo looked stale (last commit Sept 2024), while rebrowser's README claims testing against Playwright 1.52 (Apr 2025). Reconciled view: the *approach* is sound but the Node drop-ins lag current Chrome. [FACT re numbers; INFERENCE re reconciliation]
- **Our relay is attach-based** [FACT]: `~/.omp/browser-relay/extension/background.js` line 124: `await chrome.debugger.attach({ tabId: msg.tabId }, "1.3")`. So during form driving a genuine CDP session exists on the tab, and if the relay's server layer uses the standard driver protocol, the classic leaks are live. We cannot apply rebrowser patches to this path without patching the relay's driver (out of our control).

### 2.3 Mitigations specific to CDP attach
- `REBROWSER_PATCHES_RUNTIME_FIX_MODE` style fixes (`addBinding` / `alwaysIsolated` / `enableDisable`) work by patching the *driver library*, not the browser — inapplicable to an extension-based relay unless its server uses patched playwright-core. [FACT re mechanism]
- `Page.createIsolatedWorld` execution (`alwaysIsolated`) avoids main-world MutationObserver detection but cannot reach main-context objects and not applicable to workers — relevant if we ever build a custom driver. [FACT]
- Minimize attach window: open/read the page with the least possible attached time; for the JJIT modal specifically, consider **filling while attached, detaching, then human click** — the probe most plausibly samples at modal open/submit; this is a heuristic, not a guarantee. [INFERENCE]

---

## 3. Mitigation menu for fingerprint-gated boards (RQ2), ranked

| # | Option | Effort | Risk it fails | ToS/ethics | Verdict |
|---|--------|--------|--------------|------------|---------|
| 1 | Instrument + understand (§1 procedure) | Low | — | Safe | Do now |
| 2 | Prefill + one human click (submit/captcha) | Low | Low | Aligned with board intent (human submits own application) | Adopt for JJIT and any fingerprint-gated native apply |
| 3 | Attach-window hygiene + real (CGEvent) clicks for the submit path | Medium | Medium | Gray-safe (real input, real browser, no spoofing) | Adopt opportunistically |
| 4 | Slow down humanize (typing cadence, cursor paths, jittered delays) | Low | Medium | Safe | Cheap insurance; note rebrowser's guidance that behavioral scripts don't fix protocol leaks [FACT] |
| 5 | Route apply step through a driver we control with rebrowser patches (separate automation Chrome profile, not the user's) | High | High (loses logged-in state, profile consistency) | Gray | Only for staging/scouting, not applies |
| 6 | Patchright (patched Playwright drop-in; fixes Runtime.enable, Console.enable, launch-flag leaks; Chromium-only; actively maintained — 4.4k stars, Aug 2026 push; benchmark 25 OK/3 gated/3 blocked) | Medium | Medium | Not-for-us on logged-in applies; fine for read-only scouting | Scouting only |
| 7 | nodriver/zendriver (CDP without driver shim; benchmark winner 28 OK/0 blocked/31) | High rewrite | Medium | Not-for-us for applies (fresh launch, no user profile); scouting alternative | Watchlist |
| 8 | Camoufox (Firefox engine-level spoof) | High | High (Firefox signature vs Chrome-real profile mismatch; proxycove documents IP-reputation coupling) | Not-for-us | Reject |
| 9 | Custom Chromium build (patch out `Runtime.consoleAPICalled`) | Very high | High (unique fingerprint bucket) | Not-for-us | Reject |
| 10 | Captcha-solving services / token farms | Medium | — | **Violates our policy and board ToS** | Never |
| 11 | Fingerprint-spoofing injection stacks on the user's real profile (JS proxies over console/navigator) | High | High (detectable per rebrowser; may poison the user's real profile reputation) | Not-for-us | Never |

Benchmark numbers from proxycove.com/en/blog/stealth-browsers-2026-nodriver-camoufox-patchright-benchmark (Ian Patterson 31-target live benchmark, May 2026; The Web Scraping Club July 2026 JS-fingerprint lab benchmark). Their headline caveat is directly relevant to us: tool layer and IP layer don't compensate for each other; profile consistency is what gets gated [FACT re findings]. We run on the user's residential IP + real Chrome — the best possible base layer — which argues for spending effort on *behavior/input realism*, not on swapping the browser.

---

## 4. Apply-step alternatives to the CDP relay (RQ3)

### 4.1 AppleScript "execute javascript" (no DevTools session at all)
Chrome exposes `execute javascript` via Apple Events. Requires one-time opt-in: View -> Developer -> Allow JavaScript from Apple Events (or pref `allow_javascript_apple_events`); JS runs in the page's normal main world of the *real* tab — same V8 context, cookies, extensions; no CDP session, no `Runtime.enable`, no `navigator.webdriver` [FACT re feature/opt-in; INFERENCE re detectability — nothing in page-land observes it, which is the point].

Proven pattern (dev.to write-up + mcp-chrome-tabs projects): `osascript -e 'tell application "Google Chrome" to tell active tab of front window to execute javascript "..."'`; async results via `document.title` or `localStorage` side-channel; JXA (`osascript -l JavaScript`) avoids escaping hell.

Honest limits for CVSender: foreground-tab-oriented (works on one tab at a time), no network interception, no `page.waitForResponse` equivalents (poll in-page instead), no file upload via native picker (but our `input[type=file]` + DataTransfer trick works in-page), and it can't press keys at OS level — only evaluate JS. Synthetic events dispatched from this channel are still `isTrusted:false`. Effort: low-medium. This channel alone does NOT fix the fingerprint block if the probe is behavior-based; it fixes the CDP-leak class.

### 4.2 macOS Accessibility / CGEvent native clicks (trusted input)
`osascript` System Events clicks or the `cliclick` utility post real CGEvents into the window server — the page receives `isTrusted:true` pointer/mouse events identical to a human's. Combine: read widget rects via AppleScript-JS (`getBoundingClientRect`), click via `cliclick dc:x,y` (double-cleanup: coords are in screen space; account for window position + devicePixelRatio 2 on M-series). This is the only way *we* can produce trusted clicks without CDP `Input.dispatchMouseEvent`. Effort: medium (coordinate plumbing, focus management). Feasibility: good; this is how macOS UI automation has always worked. [FACT re mechanisms; INFERENCE that trusted submit events matter to the probe]

### 4.3 Human-clicks-we-prefill (recommended default for gated boards)
Agent: navigate, fill every field, solve nothing, position the user with a one-line summary (what's filled, what single click remains). User: one click. Cost to user: seconds. This is effectively what our skill already does when it leaves the JJIT modal filled and logs `Blocked`; formalizing it as a *handoff status* (not a failure) makes the funnel honest. Effort: low. ToS: clean.

### 4.4 What doesn't work (keep documented)
- `--remote-debugging-port` on the default user-data-dir: blocked since Chrome >=136 [FACT, our own skill note] — CDP attach to the real profile is impossible anyway; the relay is the only CDP path.
- Launching stealth browsers with copied profiles: multi-GB, cookie-encryption bound to user's Keychain, and profile inconsistency gets gated (proxycove §consistency). [FACT/INFERENCE]

---

## 5. Captcha taxonomy for our never-solve policy (RQ4)

Decision table (policy: agent pre-fills everything, never clicks a widget; hands off at most one click):

| Widget (mode) | Fires on load? | Auto-passes on real Chrome? | Agent action |
|---|---|---|---|
| Cloudflare Turnstile — **Non-Interactive** | Yes (spinner visible) | **Yes** — "visitors will never be required or prompted to interact" [FACT] | Wait for token; proceed |
| Cloudflare Turnstile — **Invisible** | Yes, no visuals | **Yes** — runs fully in background [FACT] | Proceed; verify token exists if the form exposes it |
| Cloudflare Turnstile — **Managed**, low risk | Yes | Usually — checkbox only "if a further check is necessary" [FACT] | Detect state; if checkbox shown -> handoff (1 click) |
| Cloudflare Turnstile — **Managed**, high risk | Yes | **No** — checkbox interaction required | Handoff: exactly one human click |
| reCAPTCHA v2 — **invisible badge** | On submit trigger | Usually — "only the most suspicious traffic will be prompted" [FACT]; our LinkedIn/Greenhouse submits fire and pass | Proceed (this is our observed-good case) |
| reCAPTCHA v2 — **checkbox** | Yes | **No** | Handoff: one human click (JJIT modal case) |
| reCAPTCHA v3 (score-only) | Yes | Yes (scores; site decides) | Proceed |
| reCAPTCHA Enterprise | Config-dependent | Invisible/score variants auto-pass on real Chrome; image challenges never | Same rows as v2 equivalents [INFERENCE re enterprise defaults] |
| hCaptcha / Arkose | out of scope today | — | Handoff |

**Programmatic detection heuristics** (for the driver's pre-submit audit):
- Turnstile: `document.querySelector('.cf-turnstile')` (implicit render), `window.turnstile` global (explicit render: `turnstile.render/execute`) [FACT]. Mode itself is not exposed client-side; infer from widget visuals: spinner-only/auto-completing = non-interactive/invisible; checkbox appears = human needed. Appearance `interaction-only` shows the widget only when interaction is required — so "widget became visible" is itself the handoff signal [FACT].
- reCAPTCHA: `.g-recaptcha` div with `data-sitekey` (checkbox), `.grecaptcha-badge` (invisible badge present), globals `grecaptcha` / `grecaptcha.enterprise`; `grecaptcha.getResponse()` returns non-empty when solved [FACT — documented JS API: render/reset/getResponse]. `data-size="invisible"` marks invisible v2 [FACT].
- Practical pre-submit rule: if a checkbox-type widget is visible in the modal, stop after filling, log `Handoff - 1 click`, and tell the user precisely which box.

---

## 6. SPA reliability checklist for our driver (RQ5)

Baseline: Playwright's own actionability contract before `click()` — element resolves uniquely, visible, stable (not animating), **receives events** (hit-test at click point), enabled (playwright.dev/docs/actionability). Synthetic drivers bypass several of these; re-implement the missing ones:

1. **Overlay-swallowed clicks (NFJ geo-notification, LinkedIn `.jobs-loader`):** before clicking, hit-test `document.elementFromPoint(rect.centerX, rect.centerY)` — if it is not the target or its descendant, walk up the overlay stack (`.cdk-overlay-container`, cookie walls), close/wait/retry, then full `location.reload()` as fallback. [FACT: our skill already encodes this; matches Playwright's "receives events" check]
2. **Dead button detection (no network on click):** install a transient hook — wrap `window.fetch`/`XMLHttpRequest` (or PerformanceObserver resource entries) — then dispatch the full pointer sequence; if no request/spinner/state change within N s, mark the button dead and try the known escape hatches (LinkedIn: direct `/jobs/view/<id>/apply/?openSDUIApplyFlow=true`; NFJ: reload; JJIT: Escape the upsell loop). [INFERENCE: procedure; FACT: escape hatches from our own sessions]
3. **React portals & remounts (Greenhouse react-select, form re-mounts):** menus render into `document.body` — search document-wide (`[class*="select__option"]`), and re-query elements inside a retry loop within one evaluation; verify selection via `[class*="select__single-value"]`. Never cache element refs across awaits on hydrating SPAs. [FACT from our sessions]
4. **Stale hydration after route change:** after SPA navigation, re-`observe`/re-query everything; treat element handles as invalid on any URL/history change; confirm the fresh DOM answers (`isConnected`) before acting.
5. **Value-setting discipline:** native setter + `input`/`change` events for controlled React inputs (LinkedIn textareas case) — otherwise the form state silently diverges from what the UI shows. [FACT from our sessions]
6. **Trusted-first clicking:** prefer real CGEvent clicks (§4.2) for stubborn dropdowns (Zoho crux-picklists, NFJ multiselects) before concluding a widget is broken. [FACT from our sessions: real click worked where synthetic failed]
7. **One attempt rule for anti-bot-gated submits:** JJIT native modal — exactly one submit attempt; on `fingerprintVerificationFailed`, leave filled + `Blocked` + handoff note. (Existing hard rule; re-affirmed by this research — retries worsen the IP/profile verdict.) [FACT rule; INFERENCE re verdict pollution]

---

## 7. Citations

1. rebrowser.net — How to fix Runtime.Enable CDP detection: https://rebrowser.net/blog/how-to-fix-runtime-enable-cdp-detection-of-puppeteer-playwright-and-other-automation-libraries
2. rebrowser-patches README (fix modes, drop-ins, caveats): https://github.com/rebrowser/rebrowser-patches
3. DataDome — CDP signal: https://datadome.co/threat-research/how-new-headless-chrome-the-cdp-signal-are-impacting-bot-detection/
4. Bot-detection test pages: https://bot-detector.rebrowser.net/ , https://kaliiiiiiiiii.github.io/brotector/ , https://deviceandbrowserinfo.com/are_you_a_bot , https://hmaker.github.io/selenium-detector/
5. Patchright (leak list, maintenance status): https://github.com/Kaliiiiiiiiii-Vinyzu/patchright
6. 2026 stealth benchmarks (nodriver/Patchright/Camoufox/rebrowser numbers; IP-reputation coupling): https://proxycove.com/en/blog/stealth-browsers-2026-nodriver-camoufox-patchright-benchmark
7. Fingerprint — Bot Detection overview (bad-bot classification of Playwright/Puppeteer/Selenium; server-side verification): https://docs.fingerprint.com/docs/bot-detection/overview
8. JJIT production config (fingerprintingWorkerEndpoint, fingerprintingOnApply, googleRecaptchaV2Key) — fetched 2026-09-09 from https://justjoin.it (Nuxt payload; see §1 quotes)
9. Cloudflare Turnstile — widget modes/states: https://developers.cloudflare.com/turnstile/concepts/widget/ ; configurations (appearance/execution modes): https://developers.cloudflare.com/turnstile/get-started/client-side-rendering/widget-configurations/
10. Google reCAPTCHA — types (v2 checkbox / invisible badge / v3): https://developers.google.com/recaptcha/docs/versions ; v2 JS API (render/reset/getResponse, data-size=invisible): https://developers.google.com/recaptcha/docs/display
11. AppleScript + Chrome (execute javascript opt-in, patterns, limits): https://dev.to/haoyang_pang_a9f08cdb0b6c/the-browser-automation-cheat-code-nobody-talks-about-applescript-chrome-52ha ; Chromium feature context: https://issues.chromium.org/40092604 ; pref-seeding example: https://github.com/pokutuna/mcp-chrome-tabs/commit/7553639c4d765bc90e90167af57ade9e1de41108
12. Our stack: `~/.omp/browser-relay/extension/background.js` L123-126 (`chrome.debugger.attach`) [FACT]; `.agents/skills/cvskill/SKILL.md` + `cvsender-omp-relay-form-driving` skill (hard rules, click recipes, per-board quirks)
13. Playwright actionability/auto-waiting: https://playwright.dev/docs/actionability

### Open questions
- Confirm the fingerprint vendor behind `id.justjoin.com` (load the modal in a watched session and log the worker endpoint's JS) — would tell us which signal classes it collects.
- Whether a *detached* window (fill via CDP, detach, then human click) still trips the probe — one instrumented experiment answers it.
- Mobile-web JJIT apply flow as an automation client: untested, no community data found.

## 8. Per-board protection map (observed, last 7 days)

| Board / surface | Protection observed | Our outcome | Policy fit |
|---|---|---|---|
| JustJoin.it — native apply modal | Server-side fingerprint verification on POST (`recruitmentProcess.fingerprintVerificationFailed`); reCAPTCHA v2 wired via `googleRecaptchaV2Key`; `fingerprintingOnApply` flag attaches `{fingerprint, captcha}` (§1) [FACT] | 400 twice (Pragmile, Kadromierz) despite real logged-out Chrome via relay | Prefill + handoff; 1 attempt max (existing hard rule) |
| JustJoin.it — external apply (eRecruiter ATS) | `fingerprintingOnExternalApply:false` — no fingerprint gate [FACT] | Applied successfully (Wyższa Szkoła Kształcenia Zawodowego) | Fully automated OK |
| NoFluffJobs | Logged-out account-modal gate; geo-notification CDK overlay eats clicks [FACT] | UI battles; no hard bot rejection observed | Overlay checklist (§6.1); account gate -> Blocked |
| TheProtocol | `applyingType` in `__NEXT_DATA__` reveals flow; guest quick-apply has no login/bot gate observed [FACT] | OK | Fully automated OK |
| Pracuj.pl -> Elevato/PeopleForce guest ATS | Login wall on plain Aplikuj; guest link clean [FACT] | OK (Trineo) | Fully automated OK |
| LinkedIn Easy Apply (incl. Ceipal) | Invisible reCAPTCHA Enterprise fires on submit and passes on real Chrome [FACT observed]; Polish-profile autofill trap | OK (Proxify, Soda, Synthires, Crossing Hurdles) | Automated; audit language before Review |
| Greenhouse / Workable | Turnstile (Monterail case) + invisible captcha family; react-select portals; DOM remounts [FACT] | Turnstile non-interactive auto-passed where observed | Wait-for-token; remount checklist (§6.3) |
| Indeed.pl | Phone-verification wall appears spontaneously after browsing (no click needed to trigger) [FACT] | Navigating back to search URL clears it | Never engage the wall; treat as gate -> Blocked |

Pattern worth naming: **PL boards gate the native apply POST with fingerprinting; ATS redirects and guest flows do not.** The fingerprinted surface is small and well-defined — which makes the prefill+handoff model cheap.

## 9. Appendix — instrumentation snippets (throwaway, run in the live tab)

Pre-submit captcha audit (paste in page context; safe — read-only):
```js
({
  recaptchaCheckbox: !!document.querySelector('.g-recaptcha[data-sitekey]'),
  recaptchaInvisibleBadge: !!document.querySelector('.grecaptcha-badge'),
  recaptchaToken: (window.grecaptcha && grecaptcha.getResponse()) || null,
  enterprise: typeof window.grecaptcha !== 'undefined' && !!grecaptcha.enterprise,
  turnstileContainer: !!document.querySelector('.cf-turnstile'),
  turnstileApi: typeof window.turnstile !== 'undefined'
})
```
Decision: `recaptchaCheckbox` true, or a visible Turnstile checkbox -> handoff (1 click). Invisible badge with non-empty `recaptchaToken` -> proceed. [FACT re API; INFERENCE re mapping]

Dead-button probe (wrap once, then click, then read):
```js
window.__reqs = 0;
const of = window.fetch; window.fetch = (...a) => (window.__reqs++, of(...a));
const oo = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function(...a){ window.__reqs++; return oo.apply(this, a); };
// ...click...
// then: window.__reqs === 0 => dead UI
```
Same idea via `new PerformanceObserver(list => ...).observe({type:'resource'})` if patching is undesirable. [INFERENCE: our procedure]

Overlay hit-test audit:
```js
const b = el.getBoundingClientRect();
const top = document.elementFromPoint(b.x + b.width/2, b.y + b.height/2);
({covered: !el.contains(top) && top !== el, topIs: top && (top.tagName + '.' + top.className).slice(0, 80)})
```

JJIT failure diff (one-shot experiment, NOT a retry loop):
1. Open modal, fill everything via the normal driver.
2. Audit: captcha table above + `performance.getEntriesByType('resource').filter(e => e.name.includes('id.justjoin.com'))` — did the fingerprint worker get called at all?
3. Capture the failing POST: `performance` won't show bodies — use the relay one attempt and record status; compare against one manual human submit on a disposable offer. Fields of interest: `fingerprint`, `captcha` null vs populated. [INFERENCE]

AppleScript smoke test (no CDP at all):
```bash
osascript -e 'tell application "Google Chrome" to tell active tab of front window to execute javascript "document.title"'
```
Requires View -> Developer -> Allow JavaScript from Apple Events, then Chrome restart. [FACT]

---

Bottom line: the JJIT block is server-side verification of a client-collected fingerprint (+captcha) attached at apply time — not a UI bug on our side, and not something input tweaks alone credibly defeat. Within our never-bypass policy the durable answer is: instrument once to know which field fails, then make the *human* the submitter on fingerprint-gated surfaces (prefill + one click), while keeping full automation for the (majority) ATS-redirect and guest flows where no fingerprint gate exists.
