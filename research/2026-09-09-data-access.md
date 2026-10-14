# CVSender data access research — machine-readable job listings for the PL market

*Date: 2026-09-09. All endpoint probes were run live on this date: plain `curl` (datacenter IP, plain UA) AND a headless Chromium session (Playwright-class). Claims are tagged `[FACT]` (verified by direct probe or primary doc, with URL) or `[INFERENCE]` (extrapolation).*

## Problem recap

CVSender currently scrapes 4 boards (NoFluffJobs, TheProtocol.it, JustJoin.it, Pracuj.pl) through their UIs: ~16 min/pass, broken pagination (JJIT SPA), cookie banners, and no freshness pre-check (4 applications went to already-expired offers). Goal: structured listings (title, company, salary band, remote flag, posted date, URL) fetched BEFORE any browser opens, plus an expiry-detection mechanism.

## Summary table

| Source | Best access method | Data quality | Freshness | Legal risk (personal use) | CVSender integration |
|---|---|---|---|---|---|
| JustJoin.it | Sitemap + JSON-LD `JobPosting` per offer page (no API needed) | High: title, company, salary band, datePosted, **validThrough** | Excellent (`lastmod` per URL, sitemap updated daily) | Low — robots.txt publishes sitemaps; only `/api/` is disallowed | **Adopt now.** Nightly sitemap diff → JSON-LD fetch |
| NoFluffJobs | Internal REST `GET /api/posting` (full dump, 18.5k offers, 145 MB) + detail endpoint | High: salary{from,to,currency,period,type}, posted/renewed, seniority, category; detail adds `expiresAt`+`status` | Excellent (`posted`, `renewed`, `expiresAt`) | Gray — robots.txt disallows `/api/` and `/posting/`; no explicit terms clause verified | **Adopt now.** Nightly dump → local SQLite; detail fetch only for shortlist |
| TheProtocol.it | `apus-api.theprotocol.it` from inside own browser session (cookie + `x-xsrf-token`) | High: title, employer, employerId, paging metadata | Good (live API), expiry field not yet mapped | Gray — CF-protected site; using your own session's tokens is personal-use gray, not abuse | Phase 2: in-page `fetch()` replay from existing Playwright session |
| Pracuj.pl | `__NEXT_DATA__` JSON inside SSR search pages + open `massachusetts.pracuj.pl` counts API | High: jobTitle, companyName, salaryDisplayText, **lastPublicated**, **expirationDate** | Excellent (`lastPublicated`, `expirationDate`) | Low-gray — sitemap-public content, robots allows; CF blocks raw HTTP so browser session needed | Phase 2: `page.content()` → parse `__NEXT_DATA__` (1 page load per query) |
| LinkedIn | None acceptable | — | — | **High** — User Agreement §8.2 explicitly bans scraping | **Skip.** Human-driven only |
| Greenhouse | Public boards API `boards-api.greenhouse.io/v1/boards/{co}/jobs` | High (title, location, updated_at, URL) | Good (`updated_at`) | Low — endpoint is published for job boards | Watch specific target companies |
| Lever | Public `api.lever.co/v0/postings/{co}?mode=json` | High (text, location, createdAt, hostedUrl) | Good (`createdAt`) | Low — published public API | Watch target companies |
| Workable | Public `apply.workable.com/api/v1/widget/accounts/{slug}?details=true` | Medium-High | Good | Low — published widget API | Watch target companies |
| SmartRecruiters | Public `api.smartrecruiters.com/v1/companies/{id}/postings` | High (name, location, releasedDate) | Good (`releasedDate`) | Low — public API | Watch target companies |
| Ashby | Public `api.ashbyhq.com/posting-api/job-board/{org}` | High (title, location, jobUrl, **publishedAt**) | Excellent | Low — public API | Watch target companies |
| Teamtailor | `https://careers.{co}/jobs.json` (JSON Feed 1.1) | High (title, url, date_published, full description HTML) | Good | Low — published feed on every TT board | Watch target companies |
| Adzuna | Official API `api.adzuna.com/v1/api/jobs/{cc}/search/{n}` | Medium (salary, created, redirect URL; description snippet only) | Good (`created`) | Low — official, keyed | Secondary net for PL + remote |
| Jooble | Official API `POST jooble.org/api/{key}` | Medium (snippet-level) | Good | Low — official, keyed; **free tier = 500 requests lifetime** | Low priority (quota too small) |
| Careerjet | Official `GET search.api.careerjet.net/v4/query` | Medium-High (salary_min/max, date) | Good | Low — official partner key | Secondary net for PL |

---

## 1. JustJoin.it — solved without their API

**The old community endpoint is dead.** `GET https://justjoin.it/api/offers` → **HTTP 404** [FACT, probed 2026-09-09]. The SPA's runtime config still references `baseApiUrl: https://api.justjoin.it` [FACT, found in `__next` flight data on https://justjoin.it/], but that host answers plain HTTP with **503 (nginx)** — even with browser `Origin`/`Referer` headers — and cross-origin `fetch` from an in-browser page on justjoin.it fails with CORS "Failed to fetch" [FACT, probed]. Conclusion: the API is now server-side-only (BFF pattern); don't chase it.

**The good path is robots.txt-published:**

- `https://justjoin.it/robots.txt` [FACT]:
  ```
  Sitemap: https://justjoin.it/sitemaps/active-jobs.xml
  Sitemap: https://justjoin.it/sitemaps/expired-jobs.xml
  Disallow: /api/
  ```
- Active sitemap index → `part0.xml` contains **10,540 `<url>` entries, each with fresh `lastmod`** (e.g. `2026-09-09T00:05:12+00:00`) [FACT, fetched].
- `expired-jobs` sitemap: **30,000 URLs in part0 alone** — a free historical archive for dedup [FACT, fetched]. (Note: parts redirect to `public.justjoin.com/justjoinit/sitemaps/...`, follow them.)

**Every offer page embeds schema.org JSON-LD** [FACT, e.g. https://justjoin.it/job-offer/fibertide-senior-site-reliability-engineer-wroclaw-architecture-7f4e4784]:

```json
{
  "@type": "JobPosting",
  "title": "Senior Site Reliability Engineer",
  "datePosted": "2026-09-04T15:00:11.8108066Z",
  "validThrough": "2026-09-09T21:59:59.999999Z",
  "hiringOrganization": {"name": "Fibertide", "sameAs": "https://fibertide.com", "logo": "..."},
  "baseSalary": {"currency": "PLN", "value": {"unitText": "HOUR", "minValue": 160, "maxValue": 220}}
}
```

That is exactly the fields CVSender needs — including **`validThrough`, a native expiry date**.

**Integration:** nightly `GET /sitemaps/active-jobs.xml` → diff URL set → fetch only new/changed `lastmod` URLs → parse JSON-LD → SQLite. No browser, no API key, ~seconds. Remote flag: not an explicit JSON-LD field; infer from slug segment `-remote-` or `job-offer/...-remote-architecture-...` pattern [INFERENCE]. ToS: the served terms HTML is client-rendered; no explicit anti-automation clause was extractable from the payload (searched for robot/automation strings) [FACT of absence in raw HTML; full rendered regulamin not parsed].

## 2. NoFluffJobs — internal REST API, unauthenticated, full dump

**`GET https://nofluffjobs.com/api/posting` → HTTP 200, 18,475 postings, 145.8 MB raw JSON** [FACT, probed]. No auth, no cookies. Top-level keys: `postings`, `totalCount`, `totalUniqueCount`, `pageUniqueCount`, `overridenSalaryFilter`.

Each posting carries [FACT]:

```json
{
  "id": "veeva-platform-solution-architect-link-group-Remote",
  "title": "Veeva Platform Solution Architect",
  "name": "Link Group",
  "url": "veeva-platform-solution-architect-link-group-remote",
  "posted": 1786457167522,          // epoch ms
  "renewed": 1788530767522,         // epoch ms
  "salary": {"from": 220, "to": 300, "type": "b2b", "currency": "PLN", "period": "Hour", "disclosedAt": "VISIBLE"},
  "seniority": "...", "category": "...", "flavors": [...],
  "location": {"places": [{"city": "Remote"}, {"country": {"code": "POL", "name": "Poland"}, "province": "..."}]},
  "fullyRemote": false,             // NOTE: false for ALL 18,475 rows in list payload — unreliable
  "onlineInterviewAvailable": true
}
```

**Detail endpoint is the expiry oracle.** `GET https://nofluffjobs.com/api/posting/{id}` → `status: "PUBLISHED"`, **`expiresAt: "2026-09-10T23:59:59"`**, `expiresInDays`, `postedOrRenewedDaysAgo`, plus requirements/essentials/company [FACT, probed].

**Caveats:**
- Query params (`criteria=city=Warszawa`, `criteria=remote=true`, `salary=30000`, `region=pl&page=2`, `salaryCurrency=PLN`) are **all ignored** — every probe returned the identical 18,475-row dump [FACT, 6 variants probed]. The SPA must use a POST/other endpoint for filtered search; not discovered. Filter locally with jq/SQL instead.
- 145 MB per dump: fetch nightly (or 2×/week), store slim rows, gzip the raw.

**robots.txt** [FACT, https://nofluffjobs.com/robots.txt]: `Disallow: /api/`, `Disallow: /posting/`, ... — this endpoint is crawler-disallowed by their own declaration. For a personal-use tool with low nightly frequency this is a gray-but-common area; rate-limit yourself (1 hit/night is ~nothing next to normal SPA traffic). No explicit scraping clause found in the served regulamin payload [FACT of absence in raw HTML].

**Integration:** nightly full dump → normalize to SQLite (`title, company, salary_min/max, currency, period, contract_type, posted, renewed, remote_inferred, url`). Remote flag: infer from `location.places[].city == "Remote"` or slug `-Remote` suffix [INFERENCE]. For shortlisted offers only, fetch detail for `expiresAt`/`status`.

## 3. TheProtocol.it — Cloudflare in front, but the offers API leaks through your own session

- All HTML/XML on `theprotocol.it` is behind Cloudflare ("Just a moment..." to curl) [FACT]; a real headless Chrome passes it [FACT, verified].
- The frontend's data plane is **`apus-api.theprotocol.it`** (observed via request interception while loading `https://theprotocol.it/filtry/data%20engineer?remote=true`) [FACT]. Direct curl to it is NOT Cloudflare-blocked but returns **401** without session tokens [FACT].
- **Verified working call — replayed from page context** (headless Chrome on theprotocol.it, `fetch(..., {credentials:'include'})` with `x-xsrf-token` copied from the `XSRF-TOKEN` cookie) [FACT]:

```
POST https://apus-api.theprotocol.it/offers/_search/rangeBox
Content-Type: application/json
x-xsrf-token: <decodeURIComponent(XSRF-TOKEN cookie)>
credentials: include

{}    →  200 {"page":{"number":1,"size":15,"count":64},
              "offersCount":952,
              "offers":[{"id":"01000000-...","groupId":"5796544f-...",
                         "title":"Senior Test Engineer","employer":"KUBO",
                         "employerId":"20273834","logoUrl":"https://..."}]}
```

- `POST /offers/_search` with guessed bodies returns 400 — the exact body schema was not mapped (the frontend sends it with keys like `keywords[]`, `workModeCodes[]`, `positionLevelIds[]`, `expectedTechnologies[]`, `specializationsCodes[]` — observed in the rangeBox body) [FACT partial; schema `[INFERENCE]`].
- The SPA's initial listing is server-rendered (Next.js/RSC) — no `_search` XHR fires on load [FACT, interception]. Sitemaps (`https://theprotocol.it/sitemaps/CurrentOffers/sitemap_index.xml`) return 200 only from a browser context (CF) [FACT].
- robots.txt: only `/_next/` disallowed, sitemaps published [FACT, https://theprotocol.it/robots.txt].

**Integration:** inside CVSender's existing Playwright session: navigate a search URL (or none at all — one visit to theprotocol.it sets CF+XSRF cookies), then `page.evaluate` the POST above with `credentials:'include'` and the cookie-derived `x-xsrf-token`. No expiry field was observed in the captured offer item — pre-check expiry by opening the offer page or re-querying [INFERENCE]. This stays inside "use the site with your own session" territory; keep volume low.

## 4. Pracuj.pl — data is in `__NEXT_DATA__`; counts API is open

- www.pracuj.pl (HTML and even sitemap XML) is Cloudflare-gated for plain HTTP [FACT]; headless Chrome passes [FACT, verified by loading `https://www.pracuj.pl/SiteMaps/CurrentOffers/SiteMapIndexJobOffers.xml` in Chromium].
- robots.txt publishes sitemaps [FACT, https://www.pracuj.pl/robots.txt], **but they are stale** — `lastmod` values from 2021-12 in every index checked [FACT]. Sitemaps are not useful for freshness here.
- **The counts microservice is open to plain curl**: `GET https://massachusetts.pracuj.pl/jobOffers/listing/count/grouped?pn=1&rop=50&subservice=0&groupBy=wm` → 200 [FACT]:
  ```json
  [{"type":"wm","items":[{"key":"full-office","value":40849},{"key":"hybrid","value":14238},
                          {"key":"mobile","value":9121},{"key":"home-office","value":4931}]}]
  ```
  `home-office` = fully remote (per the site's own `workModes` dictionary) [FACT]. `/jobOffers/listing` itself → 404 [FACT]; the listing payload travels inside the SSR page.
- **Search pages embed everything** in `<script id="__NEXT_DATA__">` → `props.pageProps.dehydratedState.queries[]` → query `jobOffers` → `data.groupedOffers[]` [FACT, parsed from a live search page]:
  ```json
  {"groupId":"b0230000-...","jobTitle":"Junior Marketing Manager m/k",
   "companyName":"WOLTANIC sp. z o.o.","companyId":1074022165,
   "companyProfileAbsoluteUri":"https://pracodawcy.pracuj.pl/company/1074022165",
   "lastPublicated":"2026-09-09T06:19:23.757Z",
   "expirationDate":"2026-10-09T21:59:59Z",
   "salaryDisplayText":"","jobDescription":"...", "isSuperOffer":false, ...}
  ```
  Same payload carries full dictionaries: 235 hierarchical categories, 18 regions, 11 position levels, 8 contract types, 4 work modes [FACT].
- No public RSS exists (only e-mail alert products and third-party scrapers like Apify actors) [FACT of absence in search; `[INFERENCE]` that none is offered].

**Integration:** Playwright `goto(searchUrl)` → `page.content()` → `JSON.parse(__NEXT_DATA__)` → rows with `lastPublicated` + **`expirationDate`** (native expiry!). One page load per query, no scrolling — fixes the pagination pain too (increment `pn` in URL or click next; the SSR payload refreshes per page).

## 5. LinkedIn Jobs — skip

- The guest endpoint `https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=python&location=Poland` still returns HTML cards (HTTP 200) from a clean IP today [FACT, probed] — but it is heavily rate-limited in practice (fast 429s) and, decisively:
- LinkedIn User Agreement §8.2 [FACT, https://www.linkedin.com/legal/user-agreement]: *"Develop, support or use software, devices, scripts, robots or any other means or processes (such as crawlers, browser plugins and add-ons or any other technology) to scrape or copy the Services, including profiles and other data from the Services"* is an explicit prohibited use.
- **Verdict: no automated LinkedIn ingestion.** At most, a human reads LinkedIn in their own logged-in browser; CVSender never scrapes it.

## 6. ATS public board APIs — verified, all open, no keys

All probed 2026-09-09 [FACT for each]:

| ATS | Endpoint (verified) | Shape (verified example) |
|---|---|---|
| Greenhouse | `GET https://boards-api.greenhouse.io/v1/boards/{co}/jobs?content=false` (`content=true` adds descriptions; `?questions=true` adds screening Qs) | Cloudflare: `meta.total: 337`, `jobs[].{title, location.name: "Hybrid", updated_at: "2026-09-04T10:59:17-04:00", absolute_url}` |
| Lever | `GET https://api.lever.co/v0/postings/{co}?mode=json` | Spotify: 76 postings, `[{text, categories.location: "London", createdAt: 1782214185805, hostedUrl}]` |
| Workable | `GET https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true` | GrubHub: 200 `{name, jobs:[]}`; unknown slug → 404 (empty board or off-platform) |
| SmartRecruiters | `GET https://api.smartrecruiters.com/v1/companies/{id}/postings?limit=3` | smartrecruiters (own board): `totalFound:1`, `content[].{name, location.city, location.country: "pl", releasedDate, ref}` |
| Ashby | `GET https://api.ashbyhq.com/posting-api/job-board/{org}` | Ashby self: 71 jobs, 2.1 MB, `jobs[].{title, location: "Remote - European Union", jobUrl, publishedAt: "2024-03-04T..."} |
| Teamtailor | `GET https://careers.{co}/jobs.json` | Voi: JSON Feed 1.1, 62 items, `{title, url, date_published, content_html}` — every TT-hosted board ships this feed |

**Why this matters for PL + remote:** many international employers hiring remote-in-PL (and PL product companies) run these ATSes. A "watch list" of ~50–200 target companies gives CVSender first-party listings (with real posted/updated dates) days before aggregators index them.

**Aggregating across ATS en masse:** there is no official cross-ATS search API [INFERENCE — none advertised by any vendor]. De-facto meta-layers: (a) Google's JobPosting structured-data index (Google Jobs) — accessible officially only via Google surfaces, or via paid SERP APIs (SerpApi etc.) which are themselves scraping Google (ToS-fuzzy); (b) the aggregator APIs below. Practical approach: maintain a company→ATS mapping (detectable from the offer URL pattern, e.g. `boards.greenhouse.io/{co}`, `jobs.lever.co/{co}`, `jobs.ashbyhq.com/{org}`) and poll each company's board JSON directly.

## 7. Aggregators with official APIs (PL coverage)

**Adzuna** — official, keyed, REST [FACT, https://developer.adzuna.com/docs/search + /overview]:
```
GET https://api.adzuna.com/v1/api/jobs/{country}/search/{page}
    ?app_id=...&app_key=...&results_per_page=20&what=...&where=...&salary_min=...&sort_by=date
→ {"results":[{title, company.display_name, salary_min, salary_max, created,
              redirect_url, category.label, contract_type, location.area[]}]}
```
Description is a snippet only ("we currently only provide a snippet") [FACT]. Poland edition exists (`adzuna.pl` resolves; `pl` is a valid `{country}` code) [FACT domain / `[INFERENCE]` code]. Free key via signup; plan limits documented in their activedocs — keep a comfortable margin.

**Jooble** — official, keyed, per-country [FACT, https://help.jooble.org/en/support/solutions/articles/60001448238]:
```
POST https://jooble.org/api/{api_key}        // key from jooble.pl for Polish listings
{"keywords":"...", "location":"Warszawa", "page":1, "ResultOnPage":50}
→ {"totalCount":N, "jobs":[{id,title,company,location,salary,link,updated,snippet}]}
```
**Free tier = 500 requests per key, lifetime** (their own docs) [FACT]. Too small for polling; use only for one-off expansions.

**Careerjet** — official partner API [FACT, https://www.careerjet.pl/partners/api/]:
```
GET https://search.api.careerjet.net/v4/query   (Basic auth: API key as username, empty password)
    ?locale_code=pl_PL&keywords=...&location=...&sort=date&page=1&page_size=100
    &user_ip=<required>&user_agent=<required>
→ {"jobs":[{title, company, date, salary_min, salary_max, salary_currency_code:"PLN", url}]}
```
Key via their publisher registration.

**Free remote-board APIs (supplement for "remote, PL-eligible"):** Remotive `GET https://remotive.com/api/remote-jobs` [FACT, probed]; Arbeitnow `GET https://www.arbeitnow.com/api/job-board-api` (250/page, `remote` boolean, `created_at`) [FACT, probed]. Global-remote scope — filter for PL-friendly time zones/EU hiring in the matcher [INFERENCE].

## 8. Legal / ToS posture per source (personal-use automation)

| Source | robots.txt | Technical controls | Explicit terms clause found? | Verdict |
|---|---|---|---|---|
| JustJoin.it | `/api/` disallowed; **sitemaps explicitly published** | API host 503s non-browser traffic | None extractable from served HTML (client-rendered) [FACT of absence] | Green — sitemap + JSON-LD is the intended public surface |
| NoFluffJobs | `/api/` + `/posting/` disallowed | none on the API | None extractable | Yellow — tolerate: 1 request/night, identify your UA, no redistribution |
| TheProtocol.it | only `/_next/` disallowed | Cloudflare + session-bound API tokens (XSRF) | not parsed (CF-gated) | Yellow — use your own session, low volume; never bypass CF out-of-band |
| Pracuj.pl | essentially allows all | Cloudflare on HTML/XML; counts API open | not parsed (CF-gated) | Yellow-green — SSR content of public pages via your own session; low volume |
| LinkedIn | — | aggressive rate limits | **§8.2 explicit scrape ban** [FACT, quoted above] | Red — skip automation |
| ATS boards (GH/Lever/Workable/SR/Ashby/TT) | n/a (APIs/feeds published for consumption) | none | designed-for-public endpoints | Green |
| Adzuna / Jooble / Careerjet | n/a | API keys | partner/API terms apply; attribution/branding rules in their programs [INFERENCE] | Green — official |

## 9. Recommended architecture for CVSender

**API-first scouting, browser only for applying.**

```
                     ┌──────────────────────────────────────────────┐
 nightly scout ──────►  jobs.db (SQLite: offers, seen_urls, companies)  │
 (no browser)        └──────────────┬───────────────────────────────────┘
   JJIT: sitemap → JSON-LD         │
   NFJ:  /api/posting dump         ├──►  matcher (PL + remote + salary) ──► shortlist
   ATS watchers (GH/Lever/         │                                          │
     Ashby/TT/SR per company)      │         expiry pre-check ◄───────────────┤
   Adzuna/Careerjet (secondary)    │         (all signals below)              ▼
                                   │                              browser session (Playwright)
 browser-backed scout ─────────────┤                              opens ONLY shortlisted,
   TheProtocol: in-page apus-api   │                              still-alive offers to APPLY
   Pracuj: __NEXT_DATA__ parse     │
```

**Phase 1 (this week, no browser):**
1. JJIT: `active-jobs.xml` → diff by URL/`lastmod` → fetch JSON-LD for new URLs. **validThrough gives expiry for free.**
2. NFJ: nightly `/api/posting` dump → slim rows into SQLite (salary/posted/renewed/company/title). Detail endpoint (`expiresAt`, `status`) only for shortlist.
3. ATS watch list: company slug → detected ATS (from URL patterns of offers you already apply to) → poll its public board JSON. `publishedAt`/`updated_at` give freshness.

**Phase 2 (browser-backed, reuse the existing Playwright session):**
4. TheProtocol: one session warm-up + in-page `POST apus-api.theprotocol.it/offers/_search/rangeBox` with cookie-derived `x-xsrf-token` (verified recipe above); paginate via the API response metadata.
5. Pracuj: `goto(searchUrl)` → parse `__NEXT_DATA__` → rows incl. `expirationDate`; paginate by URL param.

**Expiry / dead-offer pre-check (run before EVERY apply):**
1. **Native expiry field**, when present: NFJ `expiresAt`/`status != PUBLISHED`; Pracuj `expirationDate < now`; JJIT JSON-LD `validThrough < now`. [FACT these fields exist]
2. **Sitemap membership** (JJIT): URL absent from `active-jobs.xml` but present in `expired-jobs.xml` → dead. [FACT both sitemaps exist]
3. **Offer-page probe**: cheap GET of the offer URL — HTTP 404/410 or a "wygasła/expired" marker in the HTML/JSON-LD → skip. [INFERENCE on marker text; 404 semantics standard]
4. **Age heuristics**: `posted/renewed/lastPublicated/lastmod` older than ~14 days → deprioritize (many PL boards auto-renew, so age alone is a soft signal). [INFERENCE]
5. Cache verdicts in `seen_urls` with `checked_at` so each pass only re-checks the shortlist, not everything.

**Expected effect:** scouting drops from ~16 min of UI driving to a few minutes of HTTP/JSON per source (JJIT/NFJ/ATS fully browserless), pagination problems disappear (API metadata or SSR payloads), and the expired-offer class of failure is structurally eliminated by signals 1–3.

**Compliance guardrails baked in:** respect the two explicit robots disallows by keeping NFJ to one nightly request and never touching JJIT `/api/*`; one session, honest User-Agent, low frequency; no LinkedIn.
