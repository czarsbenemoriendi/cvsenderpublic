# Foreign Job Portals for a Poland-Based Remote Vue/Nuxt Developer (as of 2026-09-15)

Purpose: complement the existing CVSender board coverage (JustJoin.it, NoFluffJobs, TheProtocol, Pracuj, LinkedIn, Indeed PL + nightly ATS watchlist over greenhouse/lever/workable/smartrecruiters/ashby/teamtailor APIs) with **foreign sources that add net-new coverage** for the target candidate: Vue/Nuxt + fullstack TypeScript, 5+ yrs, PHP + Rust backend, Playwright/automation and AI-assisted development (Claude Code etc.) as differentiators, Wrocław-based, **remote only (or hybrid near Wrocław)**, B2B contractor (Polish sole trader) preferred, English B2 (not C1), **no visa sponsorship possible**.

Legend: **VERIFIED** = checked against the portal itself (site/API/board content) on **2026-09-15**. **REPORTED** = secondary-source claim or status-only check. **[INFERENCE]** = reasoned, not directly verified. Excluded as dead: StackOverflow Jobs (already known dead — excluded without re-checking). We Work Remotely and RemoteOK: previously assessed low-value for the Vue/Nuxt niche — mentioned briefly only, not re-researched per scope.

Reality frame for every entry below: Poland is EU — any **EU/EEA-country** role (remote under an EU entity, or hybrid in DE/NL/CZ/Nordics…) is legally open to a Polish contractor or employee without sponsorship. **UK, US, Canada, Switzerland** roles are out of scope unless the company hires EU-remote through an EU entity. Boards dominated by visa-required markets are flagged. Salary context: compared against the user's own target from `data/salary_policy.json` — foreign EU/US-client remote rates for a senior Vue/TS profile commonly exceed typical PL B2B targets **[INFERENCE from general market data, not per-listing verified in this pass]**; where a listing/platform plausibly pays above it, this is called out.

---

## 1. TL;DR — top actions for this profile

1. **Jobicy** — the surprise net-new win: public JSON API with `tag=vue` returned **31 Vue-tagged remote jobs** at read time. One-line addition to the nightly scout. **VERIFIED**.
2. **Remotive** — public JSON API (attribution terms apply, ~4 pulls/day advised) with a software-dev category; solid EU-remote share. **VERIFIED** (API + full terms text in payload).
3. **Himalayas** — actively maintained public JSON API (cursor-pagination maintenance note dated 2026-08-21 inside the payload), strong remote/EU filtering. **VERIFIED** (API; human site 403s bots).
4. **Working Nomads** — public `/api/exposed_jobs/` JSON feed (45 jobs at read) plus dedicated `remote-europe-jobs` and `remote-poland-jobs` category pages. **VERIFIED**.
5. **ATS watchlist expansion** — the highest-leverage move overall: verified live Vue/TS roles at **n8n** ("Remote - Europe | TS/Vue/NodeJS"), **Storyblok** (hires remote in **Poland** specifically), **GitLab** (Senior Frontend Engineer, Vue), **Typeform**, **Supabase** — all on the public Greenhouse/Ashby APIs the scout already speaks. See §6.
6. **GermanTechJobs.de** — the best English-first German board; automation via sitemap (540 URLs verified); watch the German-language reality outside Berlin. **VERIFIED** (alive + sitemap).
7. **Freelance/B2B channels with rate upside**: **Toptal / Gun.io / Arc.dev / Braintrust** all verified alive and open to EU-based contractors; **Lemon.io** explicitly sources EU (incl. CEE) devs for US startups. **Malt** is the odd one out — Poland is not a verifiable Malt market, likely blocking PL-based registration **[INFERENCE]**. English B2 is a real constraint chiefly at Toptal/Arc vetting stages (both advertise English-fluency vetting).

**Bottom line:** do not add more US-centric boards (Jobspresso, WWR, RemoteOK — wrong geography or already assessed low-value). The net-new coverage is: (a) 3–4 JSON-feed boards wired into the scout, (b) a foreign EU-remote company watchlist polled on ATS APIs, (c) 2–3 vetting-based B2B freelance networks applied to manually (they cannot be scraped — the apply is the work).

---

## 2. Remote-first boards (global/EU) — per-portal verification

### Remotive — `https://remotive.com` — **VERIFIED** (API)
- **Focus/region:** global remote, all categories; strong programming/software-dev slice.
- **PL/EU-remote fit:** every listing carries `candidate_required_location`; "Worldwide" and EU-country entries appear; contractors apply direct. Good fit.
- **English:** board language English; listing English expectations vary by client, typically conversational-plus for dev roles.
- **Vue/front volume:** software-dev category returned **16 recent jobs** at read, none Vue-titled that moment — modest but curated; frontend roles appear regularly **[INFERENCE from category feed]**.
- **B2B friendliness:** mix of employment/contract listings; no platform-side contractor handling — direct with employer.
- **Feed:** JSON API **VERIFIED** — `https://remotive.com/api/remote-jobs?category=software-dev`. Terms (in payload): link back + credit Remotive, no republishing to third-party aggregators (Jooble/LinkedIn/etc.), ~4 pulls/day max, excessive requests blocked, private API from $5k/mo.
- **Verdict:** **add to scout** (respect the rate limit; filter `candidate_required_location` for Worldwide/EU).

### Himalayas — `https://himalayas.app/jobs` — **VERIFIED** (API)
- **Focus/region:** modern remote-job aggregator, all categories, strong remote-first company base.
- **PL/EU-remote fit:** remote-only by construction; company profiles state hiring regions — many EU/worldwide.
- **English:** English throughout.
- **Vue/front volume:** first API page (20 jobs) had 0 frontend titles at read; board volume rotates **[V for the page, INFERENCE for the rate]**.
- **B2B friendliness:** direct-to-employer listings; no contractor handling.
- **Feed:** JSON **VERIFIED** — `https://himalayas.app/jobs/api`; payload contains a maintenance note "21/08/2026: Cursor pagination is now available" → actively maintained. Human site is Cloudflare-gated (403 to scrapers) — poll the API instead.
- **Verdict:** **add to scout.**

### Jobicy — `https://jobicy.com` — **VERIFIED**
- **Focus/region:** remote-first board, dev/design/marketing; smaller than Remotive but tag-driven.
- **PL/EU-remote fit:** remote-only board; region filters (incl. Europe) on the API.
- **English:** English throughout.
- **Vue/front volume:** `tag=vue` → **31 jobs at read** — best Vue-signal of any board tested.
- **B2B friendliness:** mixed contract/full-time; direct employer links.
- **Feed:** JSON **VERIFIED** — `https://jobicy.com/api/v2/remote-jobs?count=50&tag=vue` (supports industry/tag/region/count params).
- **Verdict:** **add to scout — top pick.**

### Working Nomads — `https://www.workingnomads.com` — **VERIFIED**
- **Focus/region:** curated global remote, "30K+ jobs" claim on site.
- **PL/EU-remote fit:** dedicated category pages `/remote-europe-jobs` and `/remote-poland-jobs` **VERIFIED** in site nav; location-filterable listings.
- **English:** English throughout.
- **Vue/front volume:** exposed API returned **45 jobs, 1 frontend** at read (API exposes a rotating subset; site itself is larger).
- **B2B friendliness:** contract and full-time mixed; "Remote Contract jobs" category exists **VERIFIED**.
- **Feed:** JSON **VERIFIED** — `https://www.workingnomads.com/api/exposed_jobs/` (footer-documented "API" link).
- **Verdict:** **add to scout.**

### Wellfound (ex-AngelList Talent) — `https://wellfound.com/jobs` — **VERIFIED alive** (HTTP 200)
- **Focus/region:** startup jobs, heavily US; EU-remote startup subset exists.
- **PL/EU-remote fit:** filterable by region, but a large share of listings are US-visa-bound — wrong default for this candidate; EU-remote requires manual filtering.
- **English:** startup-recruiting register, effectively C1 expectations at top startups **[REPORTED]**.
- **Vue/front volume:** not scrapeable in this pass (Cloudflare) — **REPORTED** moderate.
- **B2B friendliness:** employment-oriented; equity framing; not contractor-first.
- **Feed:** none public; SPA + Cloudflare → browser automation only.
- **Verdict:** **manual browsing only, low priority.**

### Welcome to the Jungle (absorbed Otta in 2024 — merger REPORTED) — `https://www.welcometothejungle.com` — **VERIFIED alive** (HTTP 200)
- **Focus/region:** big EU coverage (FR/DE/ES/UK + more), rich company profiles; remote filters available.
- **PL/EU-remote fit:** good for *discovering EU companies that hire remote*, less for direct PL-remote volume.
- **English:** interface EN; listing languages vary (FR/DE heavy outside EN filters).
- **Vue/front volume:** not scrapeable in this pass (SPA) — REPORTED high for EU generally.
- **B2B friendliness:** employment-oriented.
- **Feed:** none public.
- **Verdict:** **manual use as company-discovery engine** → feed found companies into the ATS watchlist (§6).

### JustRemote — `https://justremote.co` — **VERIFIED alive**
- **Focus/region:** global remote board (2000+ jobs claim; "hidden jobs" Power Search upsell).
- **PL/EU-remote fit:** Poland listed among "Applicant Locations" pages **VERIFIED** — listings accepting PL candidates exist.
- **English:** English throughout.
- **Vue/front volume:** low in sampled front page (mostly sales/CS); developer category exists.
- **B2B friendliness:** mixed; contract labels visible.
- **Feed:** none found at `/rss` (0 items at probe).
- **Verdict:** low priority; monitor only.

### Jobspresso — `https://jobspresso.co` — **VERIFIED alive**
- **Focus/region:** hand-curated remote (tech/marketing/support); **sampled 20 latest listings: overwhelmingly US/Canada-located** (Hopper, 1Password, AllTrails, Rula…) — VERIFIED from homepage listing block.
- **PL/EU-remote fit:** poor — geography is wrong for EU-remote.
- **English:** English; US-market norms.
- **Vue/front volume:** ~0 in sample.
- **B2B friendliness:** n/a given geography.
- **Feed:** RSS exists but returned **0 items** (stale) at probe.
- **Verdict:** **skip.**

### We Work Remotely & RemoteOK — brief, per prior low-value assessment
- WWR: RSS **VERIFIED** working (`https://weworkremotely.com/categories/remote-programming-jobs.rss`, 9 items/page) — usable feed if ever wanted; board itself previously assessed low-value for Vue/Nuxt.
- RemoteOK: `/api` exists but **flaky** (parseable JSON in 1 of 3 attempts; UA required) — throttle + retry if ever wired in. Not re-researched further per scope.

### Others status-checked (alive, HTTP 200, not deep-verified) — **REPORTED**
- **NoDesk** (`nodesk.co`) — remote directory/aggregator, US-leaning; skip.
- **Dynamite Jobs** (`dynamitejobs.com`) — remote board, US-heavy; skip.
- **Jobgether** (`jobgether.com`) — large aggregator with alert emails; mixed listing quality; skip for scout (aggregators double-count).
- **WeLoveDevs** (`welovedevs.com`) — French-market developer board (FR/EN); useful only if French appears.
- **EuropeLanguageJobs** (`europelanguagejobs.com`) — language-jobs board; roles usually require German/French/etc. — mismatch for B2-English-only.
- **Relocate.me** (`relocate.me`) — **visa-sponsorship-centric — the inverse of this candidate's constraint**; excluded by design.

---

## 3. Country-specific English-friendly boards

### GermanTechJobs.de — `https://germantechjobs.de` — **VERIFIED alive**
- **Focus/region:** German tech market; English-language UI; per-role language filters (English/German).
- **PL/EU-remote fit:** roles are mostly Germany-anchored (hybrid/onsite); a remote-DE subset exists — legal for a PL contractor, viable only when the role is truly remote.
- **English:** the board's core promise is surfacing English-first roles; outside Berlin-startup land, German B2+ is commonly required **[REPORTED]**.
- **Vue/front volume:** search endpoint is JS-gated to scrapers — not counted this pass; board is known to carry steady frontend volume **[REPORTED]**.
- **B2B friendliness:** German market is contractor-friendly (Werkvertrag/Freiberufler culture) **[REPORTED]**; board lists employer jobs mostly.
- **Feed:** **sitemap.xml with 540 URLs VERIFIED** (no RSS found at `/en/rss`). Best German-board automation route: diff sitemap nightly.
- **Verdict:** watch via sitemap; filter Remote + English.

### BerlinStartupJobs.com — `https://berlinstartupjobs.com` — **VERIFIED alive**
- **Focus/region:** Berlin startups. Read-time: **140 jobs, 32 IT/Software Dev, TypeScript skill tag (6), 1 freelance job**, own salary survey.
- **PL/EU-remote fit:** weak — roles overwhelmingly Berlin-based ("Senior Frontend Developer – TypeScript, React…" etc.); Berlin-hybrid doesn't commute from Wrocław.
- **English:** English-first board (German version optional) **VERIFIED**.
- **Vue/front volume:** small but real; TypeScript-tagged roles confirmed in nav **VERIFIED**.
- **B2B friendliness:** freelance category exists but is nearly empty (1).
- **Feed:** **RSS VERIFIED** — `/feed/` (12 items).
- **Verdict:** low value for PL-remote; keep the RSS only if Berlin startups ever open EU-remote roles.

### EnglishJobs.de — `https://englishjobs.de` — **VERIFIED alive**
- **Focus/region:** Germany-wide aggregator of "no German required" jobs: **20,554 jobs, 1,321 remote** at read.
- **PL/EU-remote fit:** the remote category is the only relevant slice; non-remote roles imply relocation (legal for PL citizens, but candidate is remote-only).
- **English:** by definition English-friendly, though listings span all industries.
- **Vue/front volume:** low IT density — aggregator mixes warehouse/logistics/entry-level with IT **VERIFIED from category counts**.
- **B2B friendliness:** not filtered; employers vary.
- **Feed:** none found (`/rss` 0 items).
- **Verdict:** marginal; occasional English-only German remote IT roles; not scout-worthy at current noise.

### IamExpat.nl — `https://www.iamexpat.nl/career/jobs-netherlands` — **VERIFIED alive**
- **Focus/region:** expat job board for NL in English (recruiters + international companies).
- **PL/EU-remote fit:** poor — NL roles are mostly Amsterdam-anchored; NL tech is English-tolerant for IT **[REPORTED]**, but candidate is remote-only.
- **English:** board in English by design.
- **Vue/front volume:** not extracted (board renders client-side); likely small.
- **B2B friendliness:** NL market handles contractors fine **[REPORTED]**; board itself is employment-tilted.
- **Feed:** none found at probed path.
- **Verdict:** skip — geography mismatch for PL-remote.

### TheHub — `https://thehub.io` — **VERIFIED alive**
- **Focus/region:** Nordic startups (DK/FI/IS/NO/SE) + EU; site itself is built on Nuxt.
- **PL/EU-remote fit:** explicit `countryCode=REMOTE` filter ("Remote jobs at Nordic startups") and EU filter **VERIFIED** in nav; sampled engineering roles were mostly city-anchored (Berlin/Copenhagen/Dublin/London) with a minority "Remote" (e.g. ICEYE Remote).
- **English:** Nordic IT works in English **[REPORTED]** — no local-language wall.
- **Vue/front volume:** low-moderate; `roles=frontenddeveloper` filter exists **VERIFIED** in filter URLs.
- **B2B friendliness:** not board-filtered; Nordic contractors common **[REPORTED]**.
- **Feed:** sitemap is a thin index (5 URLs); no API found.
- **Verdict:** manual monthly check of the Remote filter; low volume.

### StartupJobs.cz — `https://www.startupjobs.cz` — **VERIFIED alive**
- **Focus/region:** CEE startup board (Czech-rooted; Prague/Brno-heavy), CZ/EN interface toggle **VERIFIED**.
- **PL/EU-remote fit:** mostly onsite-CZ; some remote-CZ roles — closer to "hybrid near Wrocław" logic than any Western board.
- **English:** EN toggle + per-role language filter (English) **VERIFIED** in filter labels.
- **Vue/front volume:** steady CEE frontend volume **[REPORTED]**; not counted this pass.
- **B2B friendliness:** filter for cooperation type exists **VERIFIED** ("Typ spolupráce"); Czech startups commonly contract B2B **[REPORTED]**.
- **Feed:** sitemap index **VERIFIED** (10 URLs).
- **Verdict:** the best CEE-neighbour board; worth a human pass monthly, B2B culture is friendly.

**Visa-reality note:** UK-only boards (Work in Startups etc.), US boards, and Swiss boards are excluded by design — Skilled Worker / H-1B / CH permits all require sponsorship, which this candidate cannot use. Everything in §2–§3 that is EU-anchored carries no visa problem.

---

## 4. EU institutional

- **EURES** — `https://eures.europa.eu/` — **VERIFIED alive** (HTTP 200; legacy `ec.europa.eu/eures/eures-searchengine/page/jobs-search` path now 404). EU job-mobility portal, free, all member states. Reality: low IT-spec quality, employer/agency-driven, employment-contract oriented (not B2B), SPA with bot-gates (reader 403; no public job API found). *Verdict: compliance-value only; not worth automating.*

---

## 5. Freelance / contractor platforms (B2B fit)

### Toptal — `https://www.toptal.com` — **VERIFIED alive**
- "Top 3%" vetting network; Newsweek 2026 "#1 most reliable professional services" badge on homepage; client logos incl. **Anthropic** — a meaningful signal for a candidate whose differentiator is AI-assisted development.
- **Vetting/time:** multi-stage — English screen, timed tests, live interviews; weeks, no fee to apply **[REPORTED]**.
- **Rates:** typically well above PL B2B for senior FE ($60–100+/h) **[REPORTED]**.
- **B2B/PL fit:** yes — freelancers contract via Toptal globally; PL-based EU devs accepted **[REPORTED]**.
- **English:** **fluent spoken English expected — B2 is the main risk at the live-interview stages.**
- **Verdict:** **apply anyway**; accept the vetting cost, position the Claude-Code/automation stack.

### Malt — `https://www.malt.fr` — **VERIFIED alive**
- FR-led freelance marketplace ("850k–1M freelancers"), frontend/backend profile categories, Tech Trends 2026 report live on site.
- **Vetting/time:** none (profile marketplace; inbound missions).
- **Rates:** €450–700/day for senior TS devs **[REPORTED]**.
- **B2B/PL fit:** **Poland is not a verified Malt market** (malt.com blocked the bot; market-country list unverified) → **[INFERENCE]** PL-based freelancers likely cannot register on malt.fr (Malt ties profiles to its operating countries). Revisit if Malt opens PL or if a DE/ES entity route is acceptable.
- **English:** FR/DE client-facing language matters; EN clients exist in tech.
- **Verdict:** **skip for now**; geo-blocked for this candidate.

### Braintrust — `https://www.usebraintrust.com` — **VERIFIED alive**
- Now positioned as enterprise "AI-powered talent network" — talent marketplace (2M+ professionals, 100+ countries claim) + AI-recruiter products.
- **Vetting/time:** profile review; free for talent **[REPORTED]**.
- **Rates:** project-based; strong for AI-adjacent/eval/data work.
- **B2B/PL fit:** global pool, USD payouts, direct B2B contracts — PL eligible.
- **English:** B2 workable for async project work.
- **Verdict:** **register** — AI-training/eval gigs fit the Claude-Code profile precisely.

### Gun.io — `https://www.gun.io` — **VERIFIED alive**
- Vetted freelance network for US clients; "automated compliance… multi-currency payroll across 100+ countries"; **Vue.js devs visible among sample talent profiles on the homepage**.
- **Vetting/time:** vetting call + skills screen **[REPORTED]**.
- **Rates:** $75–150/h class **[REPORTED]** — above the PLN ceiling.
- **B2B/PL fit:** yes; platform handles global contractor compliance.
- **English:** strong conversational English needed for client calls.
- **Verdict:** **register** — explicitly markets Vue talent.

### Arc.dev — `https://arc.dev` — **VERIFIED alive**
- "Top 2%" vetted remote marketplace; freelance (hourly) + full-time; "450,000 talent in 190 countries"; client-facing copy states candidates are "fully vetted for domain expertise and **English fluency**" **VERIFIED on-page**.
- **Vetting/time:** screening incl. English — same B2 caveat as Toptal.
- **Rates:** solid; mostly US-startup clients **[REPORTED]**.
- **B2B/PL fit:** global remote OK.
- **Verdict:** **register**, expecting an English screen.

### Lemon.io — `https://lemon.io` — **VERIFIED alive**
- Marketplace sourcing "EU, LatAm, or US" devs for startups; 1.2% acceptance claim; contract or in-house; Trustpilot/G2 live.
- **Vetting/time:** lightweight, fast matching (~24h claim on site).
- **Rates:** mid-market ($40–70/h typical) **[REPORTED]** — can sit at/below a typical PL B2B hourly target; treat as volume, not upgrade.
- **B2B/PL fit:** explicitly recruits in Europe incl. CEE.
- **Verdict:** **register** as a fallback channel.

### Upwork / Fiverr — alive **[REPORTED]**
Commodity marketplaces; only worth it for narrow automation/Playwright niche gigs. Not re-researched per scope.

**Rate context:** foreign remote senior Vue/TS listings commonly quote €45–90k/yr equivalents, and vetted-network freelance rates start roughly where PL hourly B2B tops out **[INFERENCE from general market data — not per-listing verified in this pass]**. The networks above are the realistic path to pricing *above* the typical PL mid/senior B2B ceiling; job boards mostly re-list the same EU-remote salaried roles.

---

## 6. Watchlist expansion — EU-remote companies hiring Vue/TS, probed live via public ATS APIs (2026-09-15)

All checked **directly against public ATS JSON endpoints** (the same endpoints the existing nightly scout already supports). "Match" = title matching frontend/Vue/fullstack AND location matching remote/EU/Poland.

### Strongest hits — add immediately

| Company | ATS (endpoint) | Verified evidence (2026-09-15) |
|---|---|---|
| **n8n** | Ashby — `api.ashbyhq.com/posting-api/job-board/n8n` (38 jobs) | **"Sr AI Engineer \| Remote - Europe \| TS/Vue/NodeJS"**, "Sr Growth Engineer (Fullstack TS/Vue/NodeJS)", "Senior Product Engineer (TS/NodeJS/Vue)" — all live. n8n's editor is Vue-built; company fully remote-EU. **Top pick — Vue + TS + AI stack overlap is total.** |
| **Storyblok** | Greenhouse — `boards-api.greenhouse.io/v1/boards/storyblok/jobs` (17 jobs, all remote) | **"Documentation Engineer II - Poland [Remote]"** — Poland is a confirmed hiring country. The company is Nuxt/Vue-native (CMS built on Vue/Nuxt). Frontend eng not open this week — watch. |
| **GitLab** | Greenhouse — `boards-api.greenhouse.io/v1/boards/gitlab/jobs` (224 jobs) | **"Senior Frontend Engineer (Vue), Create: Repository Management [Remote, United Kingdom]"** live; GitLab posts per-country and the product is Vue-based. PL listing not present today; GitLab hires across many EU countries **[REPORTED]**. |
| **Typeform** | Greenhouse — `.../boards/typeform/jobs` (12 jobs) | "Full Stack Developer" open **[Remote DE/IE/NL/PT/ES/UK]** — EU-remote entities; no PL entity listed today. |
| **Supabase** | Ashby — `.../job-board/supabase` (60 jobs) | "Frontend Engineer [Remote, Global]" — fully remote; stack React/Next **[REPORTED]** — TS fits, Vue doesn't; include for the TS-fullstack angle. |

### Alive, worth watching (no frontend/EU-remote match at read time)
Grafana Labs (GH, 116 jobs — remote FE today = Canada/US only), GetYourGuide (GH, 51 — Berlin-hybrid), Celonis (GH, 261), Algolia (GH, 31), Vercel (GH, 87), Camunda (SmartRecruiters), DeliveryHero (SR), Klarna (SR), Babbel (SR), Pleo (Ashby, 24 — token `pleo` discovered from `pleo.io/en/careers`), Aircall (Lever, 77), Gorgias (Ashby, 17), Glia (Ashby, 23), Deel (Ashby, 0 exposed).

### Reported-but-unverified tokens (add once confirmed via their careers pages)
Pipedrive (careers moved; `/en/jobs` alive 200), Bolt, Veriff (Teamtailor — `/jobs.json` probe failed; needs per-company confirmation), Wunderflats, 10up / XWP / rtCamp (WordPress/PHP agencies — relevant to the PHP leg of the profile), idealo (Berlin, Vue-heavy **[REPORTED]**), Prezly, Directus, Meilisearch, Strapi.

**Suggested scout rule:** for each token, poll the ATS endpoint nightly; alert when `title ~ /front|vue|nuxt|full.?stack/i AND location ~ /remote|europe|poland|emea/i`.

---

## 7. Automation notes — feeds usable by the existing nightly scout

**JSON APIs (verified working 2026-09-15):**
- `https://jobicy.com/api/v2/remote-jobs?tag=vue&count=50` — tag filtering incl. `vue`; 31 hits at read.
- `https://remotive.com/api/remote-jobs?category=software-dev` — free; **terms: link back + credit Remotive, no republishing to third-party aggregators, ~4 pulls/day max, excessive requests blocked** (full legal text lives in the response).
- `https://himalayas.app/jobs/api` — JSON, cursor pagination (maintenance note dated 2026-08-21 in payload).
- `https://www.workingnomads.com/api/exposed_jobs/` — public JSON, footer-documented.
- ATS endpoints (already supported by the stack): `boards-api.greenhouse.io/v1/boards/{t}/jobs`, `api.lever.co/v0/postings/{t}?mode=json`, `api.ashbyhq.com/posting-api/job-board/{t}`, `api.smartrecruiters.com/v1/companies/{t}/postings`.
- Gaps found: **Teamtailor** `/jobs.json` failed for both probes (veriff/bolt) — needs per-company confirmation; **Workable** `v1/widget` returned empty payloads for all four probes (omnipresent/hotjar/qonto/toggl) — treat Workable accounts as browser-only until a working endpoint shape is found.

**RSS (verified):** `weworkremotely.com/categories/remote-programming-jobs.rss` (9 items/page), `berlinstartupjobs.com/feed/` (12 items).

**Sitemaps (verified):** `germantechjobs.de/sitemap.xml` (540 URLs — best German-board route), `startupjobs.cz/sitemap.xml`, `thehub.io/sitemap.xml` (thin index).

**No usable feed found:** JustRemote, Jobspresso (empty feed), EnglishJobs.de, IamExpat, EURES, and all profile-networks (Toptal/Malt/Braintrust/Gun.io/Arc/Lemon.io — inherently manual-apply). RemoteOK `/api` exists but flaky (2/3 timeouts — throttle + retry if ever used). Wellfound and Welcome to the Jungle: SPA + Cloudflare → browser automation only, not worth it per §2 verdicts.

---

## 8. Sources (primary unless noted; all read 2026-09-15)

- Remotive API + terms: `remotive.com/api/remote-jobs` (fetched; legal-notice fields in payload)
- Himalayas API: `himalayas.app/jobs/api` (payload incl. 2026-08-21 pagination note)
- Working Nomads: `workingnomads.com/remote-front-end-development-jobs`, `/api/exposed_jobs/`
- Jobspresso: `jobspresso.co/`, `/feed/`
- JustRemote: `justremote.co/`, `/rss`
- Wellfound: `wellfound.com/jobs` (HTTP 200)
- Welcome to the Jungle: `welcometothejungle.com/en` (HTTP 200)
- Jobicy: `jobicy.com/api/v2/remote-jobs?tag=vue`
- WWR RSS: `weworkremotely.com/categories/remote-programming-jobs.rss`
- RemoteOK: `remoteok.com/api` (flaky, 1/3 success)
- GermanTechJobs: `germantechjobs.de/sitemap.xml` (540 URLs), `/en/search?query=Vue` (JS-gated)
- BerlinStartupJobs: `berlinstartupjobs.com/` (job counts, categories), `/feed/`
- EnglishJobs.de: `englishjobs.de/` (20,554 jobs; 1,321 remote)
- IamExpat: `iamexpat.nl/career/jobs-netherlands`
- TheHub: `thehub.io/` (remote/EU filter links, sampled listings)
- StartupJobs.cz: `startupjobs.cz/`, `/sitemap.xml`
- EURES: `eures.europa.eu/` (200); legacy searchengine path (404)
- Toptal: `toptal.com/`
- Malt: `malt.fr/`
- Braintrust: `usebraintrust.com/`
- Gun.io: `gun.io/`
- Arc.dev: `arc.dev/`
- Lemon.io: `lemon.io/`
- ATS probes (fetched live): Greenhouse boards-api for gitlab, storyblok, typeform, grafanalabs, getyourguide, celonis, algolia, vercel, wunderflats (+ 404 probes); Ashby for n8n, supabase, posthog, langfuse, weaviate, gorgias, glia, deel, pleo; Lever for aircall, frontify; SmartRecruiters for camunda, deliveryhero, klarna, babbel; Workable widget for omnipresent, hotjar, qonto, toggl (empty payloads)
- Careers pages for token discovery: `pleo.io/en/careers`, `pipedrive.com/en/jobs`, `n8n.io/careers/`, `bolt.eu/en/careers/`, `veriff.com/careers`
- Status-only checks: nodesk.co, dynamitejobs.com, jobgether.com, welovedevs.com, relocate.me, europelanguagejobs.com, eu-startups.com/jobs (403)
