# CVSender: Provider-Agnostic Alternatives Research (Agent Harness + Skills + Browser Automation)

**Research date: 2026-08-26.** All facts below were verified against primary sources (official docs, spec sites, GitHub repos, vendor pages) on this date unless marked `[INFERENCE]` (reasoned, not directly verified) or `[UNVERIFIED]` (secondary source only). Dates shown are as visible on the source pages.

**Context recap.** CVSender today = Claude Code CLI (harness + `SKILL.md` skills invoked as `/cvskill`, SETUP.md/SESSION_STATUS.md as prompt-state files) + "Claude in Chrome" extension (`claude --chrome`; vendor tools: ToolSearch, read_page, find, javascript_tool, read_network_requests, navigate/click). Goal: remove Anthropic lock-in.

---

## 1. Agent CLI harnesses (state: Aug 2026)

### Comparison table

| Harness | Vendor lock-in / BYOK / local models | MCP | Custom slash-commands | SKILL.md skills (open standard) | AGENTS.md | License / maturity |
|---|---|---|---|---|---|---|
| **OpenAI Codex CLI** | ChatGPT plan sign-in **or** API key **or** custom `model_providers` in `config.toml` **or** `--oss` local mode (`oss_provider = lmstudio\|ollama`) — openAI-agnostic at transport level | Yes (`mcp_servers` in `~/.codex/config.toml`, `codex mcp add`) | Yes (`~/.codex/prompts` custom prompts; skills/plugins are the primary mechanism) | **Yes, native** — `.agents/skills` (repo), `~/.agents/skills` (user), explicit `$skill` or implicit match | **Yes** (`~/.codex/AGENTS.md` + repo `AGENTS.md`, nested) | **Apache-2.0**, open source (github.com/openai/codex), very active |
| **Gemini CLI** ⚠️ | Gemini-only (Google OAuth / Gemini API key / Vertex AI); **consumer tiers sunset 2026-06-18** → Antigravity CLI; survives for enterprise Code Assist + paid API keys | Yes (`mcpServers` in `settings.json`) | Yes — TOML command files (`.gemini/commands/*.toml`, `{{args}}`, `!{shell}`, `@{file}`) | **Yes, native** — `~/.gemini/skills` / `.gemini/skills` **plus `.agents/skills` alias**; `activate_skill` tool w/ consent prompt; `/skills` UI; `gemini skills install` | GEMINI.md is the documented context file (AGENTS.md support not verified) | **Apache-2.0**, open source; **consumer product being wound down** |
| **Antigravity CLI** (Google, successor) | Google-only [INFERENCE: no third-party provider mechanism documented; built for Gemini models] | Yes (Antigravity MCP docs; both Playwright MCP & Chrome DevTools MCP ship Antigravity configs) | Extensions→"Antigravity plugins" | **Yes** — blog: keeps "Agent Skills, Hooks, Subagents, Extensions (now as Antigravity plugins)" | Not verified | Repo public (github.com/google-antigravity/antigravity-cli), **no LICENSE file found at root** [checked 2026-08-26] — treat as proprietary-adjacent; young (launched ≤2026-05-19), Go, multi-agent/async |
| **OpenCode** | **Most provider-agnostic**: 75+ LLM providers via AI SDK + Models.dev, local models, `/connect` per-provider auth, custom `baseURL` for any OpenAI-compatible endpoint; ChatGPT Plus / GitHub Copilot / GitLab Duo subscriptions usable; Claude Pro/Max plugin removed in v1.3.0 (Anthropic prohibits subscription reuse) | Yes (local + remote MCP servers, `opencode.json`/`/mcp`) | Yes — markdown command files (`.opencode/commands/*.md` / `~/.config/opencode/commands/`), `$ARGUMENTS`, ``!`shell` ``, `@file` refs | **Yes, native — and reads `.claude/skills/` directly** (plus `.opencode/skills`, `.agents/skills`, project+global); skill permissions system; loads via `skill` tool | **Yes** (`AGENTS.md` + `CLAUDE.md` fallback compat!) | **MIT** (anomalyco/opencode, ex-sst), very active |
| **Aider** ⚠️ | BYOK multi-provider (OpenAI, Anthropic, Gemini, DeepSeek, Ollama, OpenAI-compatible APIs) | **No** (no MCP) | **No** file-based custom commands (in-chat commands only) | **No** SKILL.md support; AGENTS.md is only a feature *suggestion* (issue #4363) — own config: `.aider.conf.yml`, `CONVENTIONS.md` via `--read` | No (see above) | **Apache-2.0**; **maintenance-mode signals**: last stable release v0.86.2 = **2025-08-13** (releases.atom), dev tags to Feb 2026; community issue #4751 (2026-01-07) asks about "slower pace" |
| **pi** (badlogic/pi-mono) | Provider-agnostic by design ("minimal terminal coding harness… adapt pi to your workflows") | Yes [INFERENCE: pi/omp has MCP support; not re-verified this session] | Yes (extensions/skills) | **Yes** — listed on agentskills.io adopters carousel; skills doc in repo (`packages/coding-agent/docs/skills.md`) | Yes [INFERENCE] | Open source; note: the user's own `omp` harness is built on pi, i.e., **already provider-agnostic with skills** |

Other 2026-notable harnesses visible in the agentskills.io adopter list (verified listing, capabilities not individually audited): Cursor, VS Code, GitHub Copilot, Goose (Block), Amp, OpenHands, Junie (JetBrains), Factory, Roo Code, Letta, Databricks Genie Code. Source: https://agentskills.io/home (retrieved 2026-08-26).

### Key harness facts & sources

**Codex CLI**
- Apache-2.0, local-first coding agent: https://github.com/openai/codex (README, retrieved 2026-08-26).
- Auth: ChatGPT-plan sign-in or API key ("You can also use Codex with an API key, but this requires additional setup") — same README.
- Custom model providers + local models: config reference documents `model_provider`, `model_providers`, `openai_base_url`, `oss_provider = "lmstudio | ollama"` (`codex --oss`): https://learn.chatgpt.com/docs/config-file/config-reference (retrieved 2026-08-26). Community guides confirm Azure/local-LLM wiring: https://codex.danielvaughan.com/2026/04/23/codex-cli-custom-model-providers-configuration-guide/ [UNVERIFIED secondary].
- Skills = open standard, progressive disclosure, `.agents/skills` repo/user/admin tiers, `$skill` explicit or implicit invocation, `[[skills.config]]` enable/disable, plugins for distribution: https://learn.chatgpt.com/docs/build-skills (retrieved 2026-08-26).
- AGENTS.md global+repo, precedence by proximity: https://learn.chatgpt.com/docs/customization/overview (retrieved 2026-08-26); dedicated guide https://developers.openai.com/codex/guides/agents-md.
- MCP: `codex mcp add playwright npx "@playwright/mcp@latest"` documented in Playwright MCP README (see §3).

**Gemini CLI / Antigravity CLI transition** (major 2026 event)
- Google Developers Blog, **2026-05-19**, "An important update: Transitioning Gemini CLI to Antigravity CLI": Gemini CLI + Code Assist IDE extensions **stop serving requests for Google AI Pro/Ultra and free individual users on 2026-06-18**; enterprise Code Assist Standard/Enterprise unchanged; "Gemini CLI will remain accessible via paid Gemini and Gemini Enterprise Agent Platform API keys." Antigravity CLI = Go-based, multi-agent async, shared engine with Antigravity 2.0 desktop; keeps "Agent Skills, Hooks, Subagents, and Extensions (now as Antigravity plugins)." https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli
- Gemini CLI Agent Skills doc (page dated **2026-04-30**): discovery tiers incl. `~/.agents/skills` / `.agents/skills` aliases, `activate_skill` + user consent, `/skills list|link|disable|enable|reload`, `gemini skills install <git-repo>`: https://geminicli.com/docs/cli/skills/
- Gemini CLI custom commands (TOML, `{{args}}`, shell `!{...}` with confirmation, `@{file}` multimodal injection): https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/custom-commands.md
- Gemini CLI license Apache-2.0 (LICENSE at repo root, verified via raw fetch 2026-08-26); 100k+ GitHub stars per the blog post.
- **Implication for CVSender: Gemini CLI is not a durable consumer choice post-June-2026; the durable Google path is Antigravity CLI (young, Google-locked).**

**OpenCode**
- License MIT (LICENSE "Copyright (c) 2025 opencode", verified raw fetch 2026-08-26); repo moved sst/opencode → **anomalyco/opencode** (docs now link there).
- Providers page: "75+ LLM providers" via AI SDK + Models.dev, local models, `/connect`, `baseURL` overrides, Bedrock/Azure/etc. recipes; OpenCode Zen/Go = optional hosted model plans; Claude Pro/Max subscription plugins removed as of 1.3.0 ("Anthropic explicitly prohibits this"): https://opencode.ai/docs/providers/
- Skills page: discovery from `.opencode/skills`, `~/.config/opencode/skills`, **`.claude/skills` (project+global, "Claude-compatible")**, **`.agents/skills` (project+global)**; recognized frontmatter = name/description/license/compatibility/metadata; skill `permission` patterns (`allow|ask|deny`): https://opencode.ai/docs/skills/
- Rules page: `AGENTS.md` (project+global) with **`CLAUDE.md` fallback compatibility** and env kill-switches: https://opencode.ai/docs/rules/
- Commands: https://opencode.ai/docs/commands/ ; MCP servers (local+remote): https://opencode.ai/docs/mcp-servers/

**Aider**
- License Apache-2.0 (LICENSE.txt verified via raw fetch). Provider matrix (OpenAI/Anthropic/Gemini/DeepSeek/Ollama/OpenAI-compatible): https://aider.chat/docs/llms.html
- Release cadence: latest stable **v0.86.2 published 2025-08-13**; only dev tags since (releases.atom, retrieved 2026-08-26: entries v0.86.3.dev 2026-02-12). Community concern about direction/pace: issue #4751 opened 2026-01-07 ("pace of updates and releases seems a bit slower"); earlier #4584 "No new releases since early Aug".
- No MCP, no SKILL.md skills, no file-based slash commands → **worst fit for CVSender's skill-driven architecture** despite provider freedom.

---

## 2. Agent Skills portability (the SKILL.md question)

**Yes — Agent Skills is now an open, vendor-neutral standard at https://agentskills.io** with a formal spec, reference validator (`skills-ref validate`), and a broad adopter list that extends far beyond Anthropic.

### The spec (verified 2026-08-26)
Source: https://agentskills.io/specification
- A skill = directory with `SKILL.md` (required) + optional `scripts/`, `references/`, `assets/`.
- Frontmatter: `name` (required; ≤64 chars, `[a-z0-9-]`, must match directory name), `description` (required; 1–1024 chars), `license`, `compatibility` (≤500 chars), `metadata` (string map), `allowed-tools` (space-separated pre-approved tools; **experimental, support varies per implementation**).
- Progressive disclosure: metadata (~100 tokens) at startup → full SKILL.md (<5k tokens recommended) on activation → resources on demand.
- Validation: https://github.com/agentskills/agentskills (`skills-ref validate ./my-skill`).

### Native non-Anthropic adopters (each link = vendor's own skills doc, from the agentskills.io adopter list, retrieved 2026-08-26: https://agentskills.io/home)
- **OpenAI Codex / ChatGPT** — https://developers.openai.com/codex/skills (skills "build on the open agent skills standard"; explicit `$skill`/`/skills` or implicit invocation)
- **Gemini CLI** — https://geminicli.com/docs/cli/skills/ (standard-based, `.agents/skills` alias)
- **OpenCode** — https://opencode.ai/docs/skills/ (reads `.claude/skills` **and** `.agents/skills`)
- **Cursor** (https://cursor.com/docs/context/skills), **VS Code** (https://code.visualstudio.com/docs/copilot/customization/agent-skills), **GitHub Copilot** (https://docs.github.com/en/copilot/concepts/agents/about-agent-skills), **Goose** (https://block.github.io/goose/docs/guides/context-engineering/using-skills/), **Amp** (https://ampcode.com/manual#agent-skills), **OpenHands**, **Junie**, **Factory**, **Roo Code**, **Letta**, **pi** (https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/skills.md), and ~25 more.
- Microsoft ships **Playwright CLI + SKILLS** as a skills-based alternative to Playwright MCP for coding agents ("CLI invocations are more token-efficient"): https://github.com/microsoft/playwright-cli (linked from Playwright MCP README). Browser-use also distributes itself as an installable skill (`browser-use skill install`) — see §3. **Skills are converging into the cross-vendor packaging layer, including for browser tooling.**

### How portable is `/cvskill` today? (CVSender's SKILL.md skill)
- **Frontmatter/body: fully portable.** The required fields (`name`, `description`) and body Markdown are the standard; Anthropic-specific extras (e.g., Claude-style `allowed-tools`) are optional/experimental and ignored gracefully (OpenCode docs: "Unknown frontmatter fields are ignored").
- **Invocation differs per harness:** Claude Code `/cvskill` → Codex `$cvskill` or `/skills` selection; Gemini CLI implicit activation via `activate_skill` (no slash-name invocation documented); OpenCode loads via `skill` tool (can also be triggered by description).
- **Location:** keep one copy in **`.agents/skills/cvskill/`** — that exact path is natively scanned by Codex, Gemini CLI, OpenCode (and Cursor/VS Code per their docs) → single source of truth across harnesses. OpenCode will even read the existing `.claude/skills/cvskill/` as-is, zero rewrite.
- **What won't port automatically:** instructions that reference Claude-in-Chrome vendor tools (`javascript_tool`, `read_network_requests`, ToolSearch, `read_page`, `find`) must be rewritten against the chosen browser layer's tool names (see §3) — the skill *format* is portable, tool *bindings* are not.

---

## 3. Vendor-neutral browser automation for agents

### Comparison table

| Tool | Real user Chrome (logins) | MCP | JS eval in page (shadow-DOM uploads) | Network inspection | Screenshots | License / maturity | Detection/ToS posture |
|---|---|---|---|---|---|---|---|
| **Playwright MCP** (Microsoft) | **Yes** — `--extension` connects to running Chrome/Edge via Playwright Extension; or persistent profile `--user-data-dir` (logins persist); `--isolated`+`--storage-state` for clean contexts | Yes (`npx @playwright/mcp@latest`; config snippets for ~15 clients) | **Yes** — `browser_evaluate` (element-scoped) | **Yes** — `browser_network_requests` (numbered list) + `browser_network_request` (full headers/body, can save to file) | **Yes** — `browser_take_screenshot` (+ `browser_snapshot` accessibility tree) | Apache-2.0 (microsoft/playwright-mcp), very active, MS-backed; **headed by default** | Accessibility-tree-first (no stealth); extension mode = your real profile/fingerprint |
| **Chrome DevTools MCP** (Google ChromeDevTools org) | **Yes** — `--browser-url=http://127.0.0.1:9222` attaches to your already-running Chrome (same mechanism Antigravity uses); default = launches own Chrome/Chrome-for-Testing; `--headless`/`--slim` modes | Yes (+ ships as Claude Code **plugin: MCP + skills**; VS Code plugin; standalone **CLI** without MCP) | **Yes** — `evaluate_script` | **Yes** — `list_network_requests` / `get_network_request`; + console logs w/ source maps, perf traces, Lighthouse | **Yes** — `take_screenshot`, `take_snapshot`, `screencast` | Apache-2.0 (ChromeDevTools/chrome-devtools-mcp), official Chrome team, active; telemetry on by default (`--no-usage-statistics` to opt out) | Official tool driving real Chrome = best fingerprint authenticity via `--browser-url` |
| **browser-use** | **Yes** — documented example "Reuse your existing Chrome profile with saved logins" (`examples/browser/real_browser.py`); CLI "connect it to my browser" | Yes (docs.browser-use.com MCP server integration) | Yes (Playwright under the hood → page.evaluate) [INFERENCE] | Yes [INFERENCE: Playwright-based] | Yes | **MIT** (README FAQ), Python ≥3.11, very active; claims #1 Odysseys leaderboard 87.4%; cloud = stealth/proxies/captcha (paid) | OSS agent runs locally free; cloud explicitly markets "stealth… avoid detection" — ToS risk is on you |
| **Stagehand** (Browserbase) | Local Chrome via CDP possible (Playwright-style APIs); typically paired with Browserbase cloud | Not an MCP server itself — it's an SDK (TS/Python/Go) your code/agent calls | Yes — Playwright-compatible page APIs; **explicit closed-Shadow-DOM & OOP-iframe support** ("native support for complex DOM structures like out-of-process iframes and closed Shadow DOMs") | Via Playwright/CDP [INFERENCE] | Yes (`screenshot`) | **MIT** (README), active, Browserbase-backed, v4 docs | Neutral; cloud recommended for anti-bot |
| **Skyvern** | **Yes** — "Control your own browser (Chrome)… with all your cookies, logins, and extensions" via `chrome://inspect` remote debugging (port 9222) + `skyvern init browser` | MCP server [UNVERIFIED — not confirmed this session] | Yes (Playwright extension; `page.act/extract/validate/prompt`) | Via Playwright [INFERENCE] | Yes (vision-based approach) | **AGPL-3.0** (LICENSE verified) — note copyleft; active; cloud adds anti-bot/proxy/CAPTCHA | Markets anti-bot in cloud; AGPL matters if you embed/modify |
| **Browserbase** | Cloud only (managed Chrome fleet) | Via Stagehand/their MCP [UNVERIFIED] | Via Stagehand | Yes (network-level security features) | Yes | Commercial: Free / $20 / $99 / Custom (https://www.browserbase.com/pricing) | Managed fingerprinting/proxies = infrastructure choice, doesn't fix site ToS |
| **Steel** | Cloud-first browser infra for agents; open-source **steel-browser** core | Steel CLI/SDK; "Steel Skills" initiative (skills-based agent integration) | Via CDP/Playwright | Yes | Yes | **Apache-2.0** (steel-dev/steel-browser LICENSE verified); steel.dev active (Launch Week v3, 2026) | Same as above |
| **OpenAI Atlas / ChatGPT agent mode** | Was a ChatGPT-signed-browser; **DEAD** — Atlas stops working **2026-08-09**; capabilities fold into ChatGPT desktop app (multi-tab, downloads, account logins) + **ChatGPT Chrome extension/sidebar** | n/a (product, not MCP) | n/a | n/a | n/a | Proprietary; help.openai.com "Evolving Atlas into ChatGPT for browser-based agentic work" (updated ~2026-07); TechCrunch 2026-07-09 | No API/scripting surface for CVSender — **not a replacement** |

### Sources (browser section)
- Playwright MCP README incl. full options table (`--extension`, `--user-data-dir`, `--isolated`, `--storage-state`, `--headless`, `--executable-path`, `--init-script`) and tool list (`browser_evaluate`, `browser_network_requests`, `browser_network_request`, `browser_take_screenshot`): https://github.com/microsoft/playwright-mcp (retrieved 2026-08-26); extension docs: https://playwright.dev/mcp/configuration/browser-extension ; token-efficiency CLI+SKILLS sibling: https://github.com/microsoft/playwright-cli
- Chrome DevTools MCP README + tool reference: https://github.com/ChromeDevTools/chrome-devtools-mcp ; tools verified from `docs/tool-reference.md`: `evaluate_script`, `list_network_requests`, `get_network_request`, `take_screenshot`, `take_snapshot`, `upload_file`, `fill_form`, `click`, `screencast_*` (retrieved 2026-08-26)
- browser-use README (MIT, real-Chrome-profile example, CLI skill install for "Claude Code, Codex, Cursor…", Odysseys claim, cloud stealth/captcha, profile-use sync): https://github.com/browser-use/browser-use (retrieved 2026-08-26); job-application demo: `examples/use-cases/apply_to_job.py`
- Stagehand README (MIT, act/observe/extract, closed Shadow DOM + OOP iframe support, TS/Python/Go): https://github.com/browserbase/stagehand ; docs v4: https://docs.stagehand.dev
- Skyvern README (AGPL-3.0 verified; control-own-Chrome section; `page.act/extract/validate/prompt`; cloud anti-bot/proxy/CAPTCHA; quickstart SQLite/Postgres): https://github.com/Skyvern-AI/skyvern
- Browserbase pricing: https://www.browserbase.com/pricing ; Steel: https://steel.dev/ + https://github.com/steel-dev/steel-browser (Apache-2.0) + https://steel.dev/blog/introducing-steel-skills
- Atlas deprecation: https://help.openai.com/en/articles/20001371-evolving-atlas-into-chatgpt-for-browser-based-agentic-work ("Atlas is scheduled to stop working on August 9, 2026") + https://techcrunch.com/2026/07/09/openai-is-shutting-down-atlas-but-its-ai-browser-ambitions-are-still-growing/

### ToS / detection risk on job boards (verified)
- **LinkedIn User Agreement §8.2.2** (effective **2025-11-03**): you agree **not** to "Develop, support or use software, devices, scripts, robots or any other means or processes (such as crawlers, **browser plugins and add-ons** or any other technology) to scrape or copy the Services, including profiles and other data." Source: https://www.linkedin.com/legal/user-agreement — note this wording covers *browser extensions/plugins*, i.e., it reaches Claude-in-Chrome-style tooling too, not just headless bots.
- `[INFERENCE]` Risk gradient: (1) automating form-filling of your own applications with human-in-the-loop approval is materially lower risk than bulk scraping — you're not "scraping or copying" data wholesale; (2) driving your **real, logged-in Chrome profile** (Playwright MCP `--extension`, DevTools MCP `--browser-url`, Skyvern CDP attach, browser-use real-profile mode) preserves genuine fingerprint/cookies → far fewer bot challenges than fresh headless profiles; (3) scale and rate are the tripwire (LinkedIn is known for aggressive throttling of automated actions `[INFERENCE]`); (4) Polish boards (JustJoin.it, Pracuj.pl, NoFluffJobs, TheProtocol, Bulldogjob) publish ToS I did not verify individually this session — check each before automating `[TODO for user]`; ATS forms (Traffit/eRecruiter/SmartRecruiters) are employer-side endpoints where you submit your own data — lowest risk surface, and direct-apply URLs often work without the board session.

### Mapping CVSender's Claude-in-Chrome tool surface → replacements
| Claude in Chrome tool | Playwright MCP | Chrome DevTools MCP |
|---|---|---|
| navigate / click | `browser_navigate`, `browser_click` | `navigate_page`, `click`, `fill_form`, `upload_file` |
| read_page / find | `browser_snapshot` (a11y tree) + ref-based clicks | `take_snapshot` / `list_console_messages` |
| javascript_tool (shadow-DOM upload JS) | `browser_evaluate` | `evaluate_script` |
| read_network_requests | `browser_network_requests` / `browser_network_request` | `list_network_requests` / `get_network_request` |
| screenshots | `browser_take_screenshot` | `take_screenshot` / `screencast_*` |
| ToolSearch (skill discovery) | harness-native skills (`$skill` / `activate_skill` / `skill` tool) | same |

Both MCP servers are **harness-agnostic**: the same server config runs under Codex (`codex mcp add …`), OpenCode, Gemini/Antigravity, Claude Code, Cursor, Copilot, Goose — i.e., the browser layer can be decoupled from the harness choice entirely.

---

## 4. Synthesis: three concrete stacks without Anthropic lock-in

### Option A — **OpenCode + Playwright MCP (`--extension`)** ← lowest migration friction
- **Harness:** OpenCode (MIT; 75+ providers incl. GLM/GPT/Gemini/local Ollama; swap models per task).
- **Browser:** Playwright MCP in extension mode driving the user's *actual* Chrome with all job-board logins; `browser_evaluate` for shadow-DOM file uploads; `browser_network_requests` for ATS submit verification; screenshots as before.
- **Migration effort: ~minimal.** OpenCode natively reads `.claude/skills/` → `/cvskill` SKILL.md works **unchanged** (verified docs); it also reads `CLAUDE.md` as rules fallback. Rewrite only the tool-name references inside SKILL.md (javascript_tool → browser_evaluate etc.). SETUP.md/SESSION_STATUS.md → fold into `AGENTS.md` + keep as skill `references/`.
- **Tradeoffs:** newest governance (repo moved sst→anomalyco; watch stability); a11y-tree snapshots differ from Claude-in-Chrome's DOM model → selectors need a one-time pass; extension mode is Chromium-only (fine — CVSender targets Chrome).
- **Cost:** BYO model API keys (or local = free); all components Apache/MIT.

### Option B — **Codex CLI + Chrome DevTools MCP (`--browser-url`)** ← most institutional backing
- **Harness:** Codex CLI (Apache-2.0; ChatGPT plan login, or API key, or `--oss` with LM Studio/Ollama for zero-OpenAI usage).
- **Browser:** official Chrome DevTools MCP attached to the user's running Chrome via CDP 9222 — richest toolset for CVSender's needs in one place: `upload_file` + `evaluate_script` (shadow-DOM), `fill_form`, network request inspection, screenshots, screencast. Also ships as a **plugin bundling MCP + skills**, showing the skills+MCP pairing pattern.
- **Migration effort: low.** Move skill to `.agents/skills/cvskill/` (spec-identical); invocation becomes `$cvskill`; AGENTS.md replaces SETUP.md conventions. MCP wiring is one `codex mcp add` line.
- **Tradeoffs:** OpenAI-centric defaults (cloud features push ChatGPT); granular approval prompts (incl. `skill_approval`) need tuning for a semi-attended apply loop; DevTools MCP telemetry on by default (opt-out flag exists).
- **Cost:** ChatGPT Plus/Pro or API; or local models via OSS mode (quality tradeoff).

### Option C — **Keep pi/omp harness (already provider-agnostic) + browser-use or Playwright MCP as a skill** ← least architectural change
- The user's existing `omp`/pi stack is itself listed as an Agent Skills adopter (agentskills.io) and is provider-agnostic by design — the *harness* lock-in may already be solved; only the browser layer needs replacing.
- **Browser:** either Playwright MCP (as in A) or **browser-use CLI** (`browser-use skill install` registers a skill into "Claude Code, Codex, Cursor…" harnesses; connects to the user's browser; real-Chrome-profile reuse documented; job-application filling is literally their README example). browser-use = MIT, with optional paid cloud only if you ever want stealth/proxies (not advisable for ToS reasons anyway).
- **Tradeoffs:** pi/omp is a smaller-community harness (bus factor); browser-use agent loop is less deterministic than raw MCP tools (it's an autonomous agent, not a toolset) — for CVSender's approval-gated flow, prefer MCP tools under harness control; keep human-approval queue unchanged.
- **Cost:** BYO keys; everything local/free.

**Not recommended paths:** Gemini CLI (consumer sunset 2026-06-18; paid-API/enterprise only); Antigravity CLI (too young, Google-locked, no visible OSS license); Aider (no skills/MCP/slash-command files + maintenance-mode signals — would force a rewrite of the entire skill architecture); OpenAI Atlas (dead 2026-08-09); LinkedIn scraping of any kind (User Agreement §8.2.2 explicitly bans plugins/bots scraping).

### Migration checklist common to A/B/C
1. Keep skill in `.agents/skills/cvskill/` (works in Codex + Gemini + OpenCode simultaneously).
2. Rewrite SKILL.md's tool references from Claude-in-Chrome names to the chosen MCP server's tools (mapping table above).
3. SETUP.md/SESSION_STATUS.md → `AGENTS.md` (global) + skill `references/` (state files can stay as plain files the skill reads/writes — all three harnesses give agents file R/W).
4. Shadow-DOM upload scripts: port `javascript_tool` payloads to `browser_evaluate`/`evaluate_script` — same JS, new envelope.
5. Verify network-inspection parity on Traffit/eRecruiter/SmartRecruiters submit flows (both MCP servers expose full headers+body, incl. save-to-file).
6. Re-check each Polish job board's ToS before automating; keep apply-rate human-scale; keep the human approval gate (also the strongest ToS-defensible posture).

---

## 5. Dead / volatile projects explicitly flagged
- **OpenAI ChatGPT Atlas** — dead: stopped working 2026-08-09 (official help article + TechCrunch 2026-07-09).
- **Gemini CLI (consumer)** — sunset 2026-06-18 for free/Pro/Ultra; continues only for enterprise + paid API keys (Google blog 2026-05-19).
- **Aider** — not dead, but maintenance-mode signals: last stable release 2025-08-13 (v0.86.2), dev-only tags since through 2026-02, open community question about direction (#4751, 2026-01-07).
- **Antigravity CLI** — alive but nascent (born ≤2026-05-19); no visible LICENSE at repo root; feature parity with Gemini CLI explicitly "not 1:1 out of the gate" (Google blog).

## 6. Full source list
1. agentskills.io — spec: https://agentskills.io/specification ; adopters: https://agentskills.io/home ; repo: https://github.com/agentskills/agentskills (all retrieved 2026-08-26)
2. Codex skills: https://learn.chatgpt.com/docs/build-skills ; customization/AGENTS.md: https://learn.chatgpt.com/docs/customization/overview ; config reference (model_providers, oss, skills.config): https://learn.chatgpt.com/docs/config-file/config-reference ; repo/license: https://github.com/openai/codex
3. Gemini CLI→Antigravity sunset: https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli (2026-05-19) ; skills: https://geminicli.com/docs/cli/skills/ (updated 2026-04-30) ; custom commands: https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/custom-commands.md ; Antigravity CLI: https://github.com/google-antigravity/antigravity-cli
4. OpenCode: providers https://opencode.ai/docs/providers/ ; skills https://opencode.ai/docs/skills/ ; rules https://opencode.ai/docs/rules/ ; commands https://opencode.ai/docs/commands/ ; MCP https://opencode.ai/docs/mcp-servers/ ; LICENSE (MIT) verified from raw.githubusercontent.com/anomalyco/opencode/master/LICENSE
5. Aider: https://aider.chat/docs/llms.html ; releases.atom (v0.86.2, 2025-08-13) ; issue #4751 (2026-01-07): https://github.com/Aider-AI/aider/issues/4751 ; issue #4363 (AGENTS.md suggestion)
6. Playwright MCP: https://github.com/microsoft/playwright-mcp ; extension: https://playwright.dev/mcp/configuration/browser-extension ; Playwright CLI+SKILLS: https://github.com/microsoft/playwright-cli
7. Chrome DevTools MCP: https://github.com/ChromeDevTools/chrome-devtools-mcp (README + docs/tool-reference.md, retrieved 2026-08-26)
8. browser-use: https://github.com/browser-use/browser-use (README, retrieved 2026-08-26)
9. Stagehand: https://github.com/browserbase/stagehand (MIT) ; https://docs.stagehand.dev
10. Skyvern: https://github.com/Skyvern-AI/skyvern (AGPL-3.0 verified) ; https://www.skyvern.com/pricing
11. Browserbase: https://www.browserbase.com/pricing ; Steel: https://steel.dev/ , https://github.com/steel-dev/steel-browser (Apache-2.0 verified), https://steel.dev/blog/introducing-steel-skills
12. OpenAI Atlas deprecation: https://help.openai.com/en/articles/20001371-evolving-atlas-into-chatgpt-for-browser-based-agentic-work ; https://techcrunch.com/2026/07/09/openai-is-shutting-down-atlas-but-its-ai-browser-ambitions-are-still-growing/
13. LinkedIn User Agreement §8.2.2 (effective 2025-11-03): https://www.linkedin.com/legal/user-agreement
