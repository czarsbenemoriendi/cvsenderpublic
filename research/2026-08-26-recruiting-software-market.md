# Candidate-Side Job Application Automation — Market Research (as of 2026-08-26)

Purpose: build-vs-buy inputs for a homegrown Polish job-board agent (browses JustJoin.it / Pracuj.pl / NoFluffJobs / TheProtocol.it / Bulldogjob / Indeed.pl / LinkedIn, matches to CV, human-approval queue, autofills ATS forms (Traffit/eRecruiter/SmartRecruiters), CSV log, interview learning cards).

Legend: **[V]** = verified against primary source (linked, with date read). **[S]** = secondary source only. **[INFERENCE]** = reasoned, not directly verified. All "read" dates = 2026-08-26 unless noted.

---

## 1. Auto-apply tools — status, pricing, mechanism, board coverage

| Tool | Status Aug 2026 | Pricing | Apply mechanism | Boards beyond LI/Indeed/Glassdoor | Polish boards | Privacy posture |
|---|---|---|---|---|---|---|
| **JobRight** (jobright.ai) | **[V]** Alive — "Jobright Agent", claims 2M users, 8M+ jobs, "90% job search automation", auto-apply + tailored resume | **[S]** Free-first; paid "Turbo" tier exists but **pricing not public** (ApplyAll review, Aug 2026: "Strong Matching, but You Still Apply… paid pricing is not public"; zplatform review confirms tiers) | **[V]** Cloud: agent matches, tailors resume, fills forms, submits ("application forms are filled, and every submission is tracked") | **[V]** Aggregated hub of "nearly all" jobs incl. Greenhouse/Lever ATS postings | **No** — no PL boards advertised | **[V]** Cloud: CV + preferences uploaded to US service |
| **LazyApply** (lazyapply.com) | **[V]** Alive (10k+ users claim, active reviews) | **[V]** Basic **$99/yr** (15 apps/day), Premium **$149/yr** (150/day), Ultimate **$999/yr** (1500/day), 30-day refund | **[V]** Chrome extension ("Job GPT") autofill + bot apply; claims "profiles will never get blocked" | **[V]** LinkedIn, Indeed, ZipRecruiter, Dice, Greenhouse; **USA & Canada focus** | **No** | **[V]** Extension runs locally w/ your accounts; CV on their cloud; requires Gmail account |
| **LoopCV** (loopcv.pro) | **[V]** Alive (50k+ users, Trustpilot link, **has Polish-language marketing**: loopcv.pro/pl/autoapply/) | **[V]** Free forever plan (limited auto-apply, no CC); paid **from €9.99/mo**; 7-day refund (≤10% quota used) | **[V]** Hybrid: cloud scans **30+ boards** daily + submits; **"Loopcv Apply Tool" browser extension** applies on your behalf when board login is required — *without storing your password* | **[V]** 30+ boards (EU incl.); specific list not verified | **[S]** No official JustJoin/Pracuj support found — **[INFERENCE]** not supported natively | **[V]** CV uploaded to cloud; extension local for logged-in flows |
| **Sonara** (sonara.ai) | **[V-S]** Alive **under new operator**: privacy policy (upd. 2025-07-21) names **BOLD LLC** as operator (Monster/CareerBuilder partner branding); earlier shutdown rumors (Nox "Sonara Shut Down" article) refer to the *previous* product. Site returned 503/timeout to checkers (incl. my fetch) — **flag: verify checkout before paying** | **[S]** **No public pricing** (sonara.ai/pricing → 404 as of 2026-08-12, ApplyAll) | **[V-S]** Cloud auto-apply, no human review before submission | Aggregated feed; Monster/CareerBuilder partners | **No** | **[V-S]** CV + preferences to cloud; operator history unclear (data continuity unknown) |
| **Massive** (usemassive.com) | **[V]** Alive ("Trusted by 100,000+ Jobseekers", iOS app "Swipe & Apply") | **[S]** **$59/mo** per Nox/ApplyAll reviews (their /pricing returned HTTP 400 to me; not re-verified on-page) | **[V]** Cloud bot: finds & applies daily, "set it and forget it" | Own curated tech-company feed | **No** | Cloud CV |
| **OfferGun** (offergun.com) | **[V]** Alive — **but it is NOT a job tool**: real-estate offer automation for investors (MLS auto-fill, $199/mo, 1 state incl.). If it ever was a job auto-applier, it isn't now | $199/mo (+$99/mo/state) | Real-estate contract fill | n/a | n/a | n/a |
| **AIApply** (aiapply.co) | **[V]** Alive — active Trustpilot reviews through **April 2026** | **[S]** **$29/mo** (Scoutify review title, tested Oct 2025-ish) | **[V]** Cloud auto-apply: scans, matches, generates tailored resume+cover letter, submits ("emails those companies on your behalf at scale") | Aggregated; incl. UK/EU listings (Stripe/London example) | **No** | Cloud CV; "2,064,348 users" claim |
| **Simplify Jobs** (simplify.jobs) | **[V]** Alive (docs updated ~2 months ago) | **[V]** Copilot autofill **free**; Simplify+ **$19.99/week / $39.99/month / $89.99/3-months** | **[V]** **Autofill, not unattended apply** — Chrome extension "Simplify Copilot" fills applications; + AI-generated answers/cover letters you review | **[V]** Works across most web ATS forms (workday/Greenhouse-style) incl. their job board | **No** (extension would fill NFN/eRecruiter forms generically — **[INFERENCE]**, no PL-specific support) | Local-first extension; profile cloud-synced |
| **CareerFlow** (careerflow.ai) | **[V]** Alive | **[V]** Free (limited autofill); Premium **$8.99/week or $23.99/month**; Premium Plus $19.99/week (adds AI mock interviews) | **[V]** Chrome extension **autofill** (limited free) + tracker + LinkedIn optimizer; **not** unattended apply | Generic web-form autofill | **No** | Cloud profile |
| **Teal** (tealhq.com) | **[V]** Alive | **[V]** Free forever plan; Teal+ **$13/week** (weekly-only billing) | **[S]** **No auto-apply** — tracker, resume builder/keyword matching, AI credits ("Best Free Job Tracker, but No Auto-Apply", aitoolspolice 2026) | Tracker imports from anywhere | n/a | Cloud |
| **Huntr** (huntr.co) | **[V]** Alive | **[V]** Free (unlimited **application autofills**, 100 tracked jobs); Pro **$40/mo** or $30/mo billed quarterly / $26.66/mo biannual | **[V]** Chrome extension autofill ("fill application forms with a single click") + AI resume tailoring; **not** unattended apply | Generic ATS-form autofill | **No** | Cloud |
| **JobScan** (jobscan.co) | **[V]** Alive — **Auto Apply is a new feature** ("New" badge) | **[S]** Included with paid plans; exact price not re-verified (plan page exists at app.jobscan.co/plan) | **[V]** **Review-gated auto-apply**: "finds matching jobs, drafts a tailored application for each, and **waits for your review before submitting**" | ATS-focused aggregator | **No** | Cloud |
| Other current leaders (**[S]**, not individually verified): JobCopilot, ApplyAll (humans apply for you, one-time fee, interview-guarantee refund), FastApply ($14/mo+), OfferJetAI ($19 CAD), Wobo, Jobr, Nox, LoopCV competitors listed on applyall.com/guides/best-auto-apply-services | — | — | Mix of cloud bots + human-done-for-you | Mostly US/global aggregators | **No** | Cloud |

**Bottom line (board coverage):** every surveyed commercial tool targets LinkedIn/Indeed/Glassdoor/US-centric aggregators or generic web-form autofill. **None advertises native support for JustJoin.it, Pracuj.pl, NoFluffJobs, TheProtocol.it, or Bulldogjob.** LoopCV is the only one marketing in Polish (dedicated /pl/ pages) but its 30+ board list does not publicly include Polish boards. **[INFERENCE]** the Polish-board coverage gap is real and unserved commercially.

---

## 2. Newer agentic offerings (2025–2026)

- **ChatGPT agent (OpenAI)** — **[V]** launched **2025-07-17**; virtual computer, visual browser, terminal, connectors; permission-gated actions; browser "takeover mode" for logins (passwords not stored); at launch "still working on enabling access for the European Economic Area and Switzerland" (page now banner-flagged outdated). People demonstrably use agent mode for job applications (widely reported experiments; e.g. LinkedIn posts on Operator/agent applying to 100 jobs). **[INFERENCE]** this is the closest "Claude-agnostic" generic equivalent of the user's agent, but it is per-task, supervised, not a standing queue + CSV pipeline.
- **Open-source self-hosted (the real "custom-board" segment):**
  - **AIHawk** — **[V]** alive at `github.com/feder-cr/Jobs_Applier_AI_Agent_AIHawk` (renamed from Auto_Jobs_Applier_AIHawk; old org paths 404). Python + Playwright + LLM; LinkedIn/Indeed-centric; fully self-hostable; you write your own board modules.
  - **`noQuli/pracuj.pl_auto_job_applier`** — **[V-S]** GitHub Python app automating applications specifically on **pracuj.pl** (existence verified via search results; repo activity not audited).
  - **`pandawidkur/ai-job-search-pl`** — **[V-S]** Polish job-search AI repo (same caveat).
  - **[INFERENCE]** A small Polish OSS ecosystem exists precisely because no commercial product covers these boards — supporting "build".
- **Human-in-the-loop services** — **[S]** ApplyAll (people submit applications, refund guarantee), Scale.jobs — a 2025-26 trend away from pure bots toward accountability.
- **Polish/EU-local products:**
  - **Rocket (Just Join IT — justjoin.it + rocketjobs.pl)** — **[V]** mobile app (iOS/Android) launched **Nov 2025**; **[V]** >10,000 users by ~Mar 2026 (CEO Piotr Nowosielski, LinkedIn). **[V]** features (Telix.pl, 2026-04-24): aggregated "nearly all" Polish offers, AI matching, **auto-generated tailored CVs**, **"aplikowanie jednym kliknięciem i wypełnianie formularzy aplikacyjnych"** (one-click apply + application-form autofilling), interview-prep simulations, salary data. **This is the closest off-the-shelf equivalent of the user's agent — but only inside the Just Join IT ecosystem, as a mobile app, no public API/self-host, pricing unverified.** **[S]** App Store listing exists (id6753708081).
  - **LoopCV Polish pages** — **[V]** localized marketing, no PL boards.
  - **Huunt** (huunt.ai) — German-market AI job search w/ Polish-language pages — **[S]**.
  - **Voice agents applying on your behalf**: no verified 2026 candidate-side voice-apply product found; employer-side AI interview agents exist (Indeed "Interview On Demand"). **[INFERENCE]** not yet a candidate-side category.
  - **ATS-side context** — **[V]** eRecruiter blog: "Aplikowanie bez CV w systemie eRecruiter" (apply without CV); Traffit help docs cover consent-by-action — ATS vendors are lowering friction on their side.

---

## 3. Platform-native quick apply (what's already automated without third parties)

- **Pracuj.pl** — **[V]** *"Aplikuj szybko"*: one-click apply from Pracuj profile; data auto-transmitted into eRecruiter; if no extra questions, "klik i aplikacja wpada do systemu"; **[V]** 6 of 10 applications in Strefa Pracuj use it; candidates apply **3× faster** (Pracuj.pl data, Mar 2023). **[V]** *"Multiaplikowanie"*: after any application, screen offers **5 similar recommended offers to apply to with one click**. **[V]** *"Proste aplikowanie"* eRecruiter↔Pracuj integration: 2-step forms, fields pre-filled from Pracuj profile, partial applications still land in ATS. **[V]** AI recommendations article in help center. Default ON per recruitment; employer can disable.
- **JustJoin.it / Rocket Jobs (Just Join IT)** — **[V]** ecosystem of Candidate Profiles + "Baza Dopasowanych Talentów" + **Rocket app** (§2) — i.e., one-click apply and form autofill are becoming first-party.
- **TheProtocol.it** — **[V-S]** WIPO trademark record lists "the:protocol" as a trademark of **Grupa Pracuj sp. z o.o.** → TheProtocol is part of the Grupa Pracuj group (with Pracuj.pl, Aplikuj.pl, eRecruiter). **[S]** Their LinkedIn promotes fast-application flow. **[INFERENCE]** Pracuj-style quick apply mechanics likely apply group-wide; unverified for TheProtocol specifically.
- **NoFluffJobs** — **[V]** Candidate Profile (login via Google/Facebook/LinkedIn) with: application status tracking, **CV-match score per offer**, per-offer competition stats. Salary-match transparency program. No evidence of one-click multi-apply.
- **LinkedIn** — **[V]** Easy Apply / "Apply with LinkedIn" plugins (defined in User Agreement); AI job matches/recommendations; **[V]** 2025-11-03 User Agreement §8.2 explicitly bans bots/plugins for scraping and "unauthorized automated methods" (§8.2.13) — native quick apply is the sanctioned path.
- **Indeed (pl.indeed.com)** — **[V]** Indeed Apply (Easily Apply/Simple Apply), automated recruiter-notice workflows, profile-based application content suggestions (AI-generated, review-gated).

**Implication [INFERENCE]:** first-party quick apply now covers the "one-click for offers on one board" case *per board*. Nothing platform-native does: **cross-board matching against one CV, a human-approval queue, one unified log, or interview learning cards** — which is exactly the user's agent's remaining value.

---

## 4. Risk / ToS — automated applying

- **LinkedIn** — **[V]** User Agreement (effective **2025-11-03**), §8.2 Don'ts: (2) no software/scripts/robots/**browser plugins** to scrape or copy the Services; (13) no "bots or other unauthorized automated methods to access the Services… send or redirect messages… or otherwise drive inauthentic engagement"; §3.4 reserves the right to restrict/suspend accounts. **Applying via third-party bots sits squarely in the banned zone** (scraping + automated access). Enforcement vs individual job seekers: no public 2024-2026 case found against a *candidate* — **[S]** enforcement reporting focuses on account restrictions after automated-activity detection (e.g., LazyApply ban-risk articles: PitchHired "Is LazyApply Safe in 2026? Ban & Refund Risks"). **[INFERENCE]** realistic risk = account restriction, not lawsuits.
- **Indeed** — **[V]** Terms of Service (**Last Updated 2026-07-17**), §A.3.5 "Limits": Indeed may cap **daily application counts**, and — verbatim — **"Use of any automation, scripting, or bots to automate the Indeed Apply process outside of Indeed's official vendors and tooling is prohibited."** Also requires email/phone verification. (Notably, the 2026 ToS now *defines* "Agentic AI" and acknowledges employer-side agentic AI receiving applications — the legal ground is shifting, not settled.)
- **Polish boards** — **[V]** Grupa Pracuj regulamin exists (grupapracuj.pl/prywatnosc/regulamin); **no explicit public clause about candidate-side automation/bots was located** in this pass (not fully text-audited — flag). JustJoin/NoFluffJobs ToS on bots: not audited. **[V]** Practical evidence matters more: eRecruiter gives employers a kill-switch for quick apply, and **[V]** a real employer (Michał Kosecki, eRecruiter customer, LinkedIn post ~June 2026) disabled "szybkie aplikowanie" because it "omijało cały nasz formularz i przy każdej pozycji mieliśmy 'brak odpowiedzi kandydata', a kandydat nawet o tym nie wiedział" — quick apply sent default CV and skipped all custom questions. Commenter (Mick Griffin): average posting now gets ~242 applications. **[INFERENCE]** employers' anti-friction backlash is the live risk for *any* apply automation, first-party or third-party; human-approval + tailored answers (the user's design) is the mitigating pattern.
- **ATS side (Traffit/eRecruiter/SmartRecruiters)** — **[V]** eRecruiter "Proste aplikowanie" explicitly documents that applications submitted after step 1 land in the employer's ATS **even without answers** — silent data-quality failures are a known, documented failure mode of autofill pipelines.

---

## 5. Build-vs-buy inputs

**Price comparison (subscription vs self-run agent API cost):**
- Commercial subscriptions: **$0 (LoopCV/Simplify/Huntr free tiers) → €9.99/mo (LoopCV) → $29/mo (AIApply) → ~$40/mo (Huntr Pro) → ~$59/mo (Massive) → $13/wk (Teal+) → $99–999/yr (LazyApply)**. **[V]** except Massive/AIApply/JobRight figures which are **[S]**.
- Self-run agent marginal cost **[INFERENCE, order-of-magnitude]**: per application ≈ scrape/parse offer + CV match + question answering ≈ 50–150k LLM tokens → $0.05–$0.45 at current mid-tier API prices ($1–3/M tokens); at 10–20 curated applications/day ≈ **$15–$270/mo**, plus $0 infra if browser runs locally (Playwright). So a self-run agent costs *comparable to a mid-tier subscription* while covering boards no vendor covers. ChatGPT-agent-style supervision (40–400 msgs/mo on Plus/Pro, 2025 pricing) is too rate-limited for a daily pipeline — **[INFERENCE]**.
- Hidden buy-side costs: weekly-billed tiers (Teal $13/wk, CareerFlow $8.99/wk, Simplify $19.99/wk) reset the "monthly" mental model; unpublished pricing (Sonara, JobRight) prevents comparison; refund windows are narrow (LazyApply 30 days, LoopCV 7 days ≤10% usage). **[V]**

**Privacy:**
- All cloud auto-appliers require uploading CV + contact data + preferences to their servers (US/EU SaaS); Sonara additionally has an unexplained operator change (BOLD LLC) with unknown data continuity. **[V]**
- Extension-autofill tools (Simplify, Huntr, CareerFlow, LazyApply) keep the apply action local (credentials stay in your browser) but sync profile data to cloud. **[V]**
- Self-run agent: CV and logs stay on your machine; the only external exposure is your chosen LLM API (configurable, incl. local models) — and the boards/ATS themselves, which see your data either way. **[INFERENCE]**

**Coverage gap for Polish boards (the decisive factor):**
- **Zero surveyed commercial tools advertise JustJoin.it / Pracuj.pl / NoFluffJobs / TheProtocol.it / Bulldogjob support. [V — absence of claims across all official pages read]**
- The only off-the-shelf product matching the user's feature set is **Rocket** (Just Join IT) — but it is (a) confined to the JJIT ecosystem, (b) a mobile app without API/self-host/CSV export, (c) pricing unverified. **[V/S]**
- Platform-native quick apply (Pracuj "Aplikuj szybko" + "Multiaplikowanie", JJIT profiles) already removes most form-filling pain *per board* — so a homegrown agent's marginal value concentrates in: cross-board CV matching, the human-approval queue, unified CSV logging, tailored answers to ATS custom questions (the exact thing employers complain is missing — §4), and interview learning cards.
- OSS (AIHawk + the two pracuj.pl repos) proves the build path is viable and maintained, and supports arbitrary/custom boards by construction.

**Net assessment [INFERENCE]:** Build (or keep building) is justified for the Polish-board scope; buy only for LinkedIn/Indeed-scale spraying if ever needed (LoopCV/AIApply), noting LinkedIn/Indeed ToS prohibit exactly that — which the user's human-approval queue partially, but not fully, mitigates (ToS bans the *automation of access/apply*, not just impersonation).

---

## Sources (primary unless noted; all read 2026-08-26)

- LoopCV pricing/FAQ: https://www.loopcv.pro/pricing/ · Polish landing: https://www.loopcv.pro/pl/autoapply/
- LazyApply homepage/pricing: https://lazyapply.com/
- Sonara status: https://applyall.com/guides/sonara-review (competitor review, facts dated 2026-08-12/20/24) + https://www.sonara.ai/ (503 to fetchers)
- Massive: https://usemassive.com/ (pricing page 400; $59/mo per https://noxjobs.com/compare/massive-usemassive-review-trustpilot-rating)
- OfferGun (real estate): https://www.offergun.com/
- AIApply Auto Apply: https://aiapply.co/auto-apply (reviews to Apr 2026); price $29/mo per https://scoutify.com/blog/aiapply-review/
- Simplify+ pricing (official help): https://help.simplify.jobs/articles/5623502-whats-included-in-simplify-features-and-pricing
- CareerFlow pricing: https://www.careerflow.ai/premium
- Teal pricing: https://www.tealhq.com/pricing
- Huntr pricing: https://huntr.co/pricing
- JobScan Auto Apply (review-gated): https://www.jobscan.co/auto-apply
- JobRight agent page: https://jobright.ai/ai-agent (pricing non-public per https://applyall.com/guides/jobright-review)
- Rocket (Just Join IT): https://www.telix.pl/inne/aplikacje/2026/04/pierwsza-polska-aplikacja-z-ai-ktora-znajdzie-prace-i-przygotuje-do-rozmowy-2/ (2026-04-24) · App Store: https://apps.apple.com/ar/app/rocket-asystent-kariery/id6753708081 · CEO user milestone: https://pl.linkedin.com/posts/piotrnowosielski_wystartowali%C5%9Bmy-z-rocketem-w-listopadzie-activity-7437104051428769793-Omj-
- Pracuj.pl quick apply: https://pomoc.erecruiter.pl/pl/articles/6300468-proste-aplikowanie-z-pracuj-pl · Multiaplikowanie: https://pomoc.pracuj.pl/hc/pl/articles/7292550511516-Multiaplikowanie · AI on Pracuj: https://pomoc.pracuj.pl/hc/pl/articles/29647698976540
- Employer disables quick apply (Jun 2026): https://pl.linkedin.com/posts/michalkosecki_wie%C5%9Bci-z-rekrutacji-w-miniony-wy%C5%82%C4%85czyli%C5%9Bmy-activity-7467471778077085698-yZ5b
- NoFluffJobs profile: https://nofluffjobs.com/pl/profile
- TheProtocol ↔ Grupa Pracuj trademark: https://www.trademarkelite.com/wipo/trademark/trademark-detail/1625202/the-protocol
- LinkedIn User Agreement (eff. 2025-11-03), §8.2: https://www.linkedin.com/legal/user-agreement
- Indeed Terms of Service (upd. 2026-07-17), §A.3.5: https://www.indeed.com/legal
- ChatGPT agent (2025-07-17): https://openai.com/index/introducing-chatgpt-agent/
- AIHawk: https://github.com/feder-cr/Jobs_Applier_AI_Agent_AIHawk · pracuj.pl bot: https://github.com/noQuli/pracuj.pl_auto_job_applier · PL job search: https://github.com/pandawidkur/ai-job-search-pl
- eRecruiter apply-without-CV: https://erecruiter.pl/blog/aplikowanie-bez-cv-systemie-erecruiter/
- Secondary landscape roundups (bias noted — mostly vendor-owned): applyall.com/guides/best-auto-apply-services, noxjobs.com, blog.fastapply.co

## Verification caveats (could not verify as of 2026-08-26)

1. **Sonara** — site blocked automated fetch (503); "alive" rests on ApplyAll's dated checks + BOLD LLC privacy policy; pricing unknown. **Verify checkout manually before any decision.**
2. **JobRight paid pricing** — not public anywhere found.
3. **Massive $59/mo** — secondary only (their pricing endpoint errored).
4. **Rocket pricing/business model** — not published in sources found.
5. **Grupa Pracuj / JustJoin / NoFluffJobs ToS text on bots** — not audited line-by-line; only LinkedIn & Indeed clauses verified verbatim.
6. **LoopCV's exact 30-board list** — not enumerated; Polish-board support absence is inferred from marketing, not a tested negative.
7. **TheProtocol quick-apply mechanics** — inferred from group ownership + posts, not verified on-site.
