# Cheap model providers for terminal coding agents — how to wire them up (as of 2026-10-14)

Purpose: SETUP.md Step 0.2b recommended "omp + GLM" because of the
2026-09-04 cost measurement (~227 USD Claude Code + Claude in Chrome /
Sonnet 5 vs ~10 USD omp + Browser Relay / GLM-5.2 for comparable work).
That conflates two independent choices — the **harness** (omp/pi,
OpenCode, Claude Code, Codex CLI, …) and the **model provider** (Z.ai GLM,
Moonshot Kimi, DeepSeek, MiniMax, OpenRouter, Anthropic …). This note
documents how each provider plugs into each harness, so a user can pick a
cheap provider without being locked to one.

Markers: **[V]** verified on the provider's / harness's own docs page or
local CLI help on 2026-10-14; **[3P]** third-party source only;
**[INFERENCE]** reasoning, not stated by a source.

## 1. Key findings

1. **Model and harness are separable.** Every surveyed provider publishes
   setup for several terminal agents, and the open harnesses (omp/pi,
   OpenCode) ship the major cheap providers as built-ins. [V]
2. **Where the measured savings came from** (2026-09-04 audit): 2–4×
   smaller context per turn (text a11y snapshots instead of full page
   snapshots/screenshots) + a cheaper model (output ~3.4× cheaper) +
   session hygiene (cache-read of a growing conversation dominated cost in
   *both* harnesses). Only the second factor is about the provider.
   [INFERENCE from the audit numbers]
3. **Claude Code + non-Claude model works but is unsupported.** Providers
   expose Anthropic-compatible endpoints for `ANTHROPIC_BASE_URL`, yet
   Anthropic "doesn't support routing Claude Code to non-Claude models
   through any gateway" [V, code.claude.com/docs/en/llm-gateway]. Claude in
   Chrome requires a `/login` claude.ai session and is kept off for API-key
   / long-lived-token auth [V, code.claude.com/docs/en/chrome]; with a
   third-party `ANTHROPIC_AUTH_TOKEN` the browser therefore has to come
   from Playwright MCP instead. [INFERENCE — not tested]
4. **"Coding plans" are tool-scoped.** Z.ai: the GLM Coding Plan "is
   limited to use within the following officially supported tools" (ZCode,
   Claude Code, Claude for IDE, Codex, OpenCode, Pi, Cursor, Cline, TRAE,
   Qoder, Droid, Kilo Code, Roo Code, Crush, Goose, Eigent) and needs the
   dedicated coding endpoint — "Incorrect endpoint configuration will
   result in inability to use GLM Coding Plan subscription quota." [V,
   docs.z.ai/devpack/tool/others]. omp is not named; it is a pi fork and
   ships a `zai` provider (our own setup runs `zai/glm-5.3-flash`) — treat
   plan eligibility for omp as **[INFERENCE]**, check Z.ai terms.

## 2. Wiring matrix

| Provider | omp / pi | OpenCode | Claude Code | Codex CLI |
|---|---|---|---|---|
| **Z.ai — GLM Coding Plan** | built-in; `ZAI_API_KEY` (global coding plan) or `/login` [V pi.dev] | `/connect` → **Z.AI Coding Plan** [V opencode.ai] | `~/.claude/settings.json` `env`: `ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic`, `ANTHROPIC_AUTH_TOKEN=<key>`, `API_TIMEOUT_MS=3000000`, model slots `ANTHROPIC_DEFAULT_{OPUS,SONNET,HAIKU}_MODEL` (GLM-5.3 / GLM-5.3-Flash); or helper `npx @z_ai/coding-helper` [V docs.z.ai/devpack/tool/claude] | officially supported tool; OpenAI-compatible coding endpoint `https://api.z.ai/api/coding/paas/v4` [V docs.z.ai] |
| **Moonshot — Kimi** | built-in; `MOONSHOT_API_KEY`, Kimi For Coding `KIMI_API_KEY` [V pi.dev] | `/connect` → **Moonshot AI** [V opencode.ai] | Anthropic-compatible endpoint, official guide `platform.kimi.ai/docs/guide/claude-code-kimi`; `https://api.moonshot.ai/anthropic` per [3P] | OpenAI-compatible `https://api.moonshot.ai/v1` [V platform.kimi.ai] |
| **DeepSeek** | built-in; `DEEPSEEK_API_KEY` [V pi.dev] | `/connect` → **DeepSeek** [V opencode.ai] | `ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic`, `ANTHROPIC_AUTH_TOKEN=<key>`; `deepseek-v4-pro` main, `deepseek-v4-flash` for Haiku/subagents [V api-docs.deepseek.com] | — (not checked) |
| **MiniMax** | built-in; `MINIMAX_API_KEY` [V pi.dev] | `/connect` → **MiniMax** [V opencode.ai] | setup wizard `npx -y mmx-cli@latest agent setup` (Claude Code, Codex CLI, OpenCode, Grok CLI, Hermes Agent, Pi) [V platform.minimax.io] | same wizard [V] |
| **OpenRouter** (one key, many models, pay-per-token) | built-in; `OPENROUTER_API_KEY` [V pi.dev] | `/connect` → **OpenRouter** [V opencode.ai] | `ANTHROPIC_BASE_URL=https://openrouter.ai/api`, `ANTHROPIC_AUTH_TOKEN=$OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY=""` (must be explicitly empty), model slugs via `ANTHROPIC_DEFAULT_*_MODEL` / `CLAUDE_CODE_SUBAGENT_MODEL`; `/status` to confirm [V openrouter.ai] | — (not checked) |
| **Anthropic (Claude)** | built-in; `ANTHROPIC_API_KEY` [V pi.dev] | built-in | native; subscription via `/login` — the only setup where Claude in Chrome works [V] | — |

Other harnesses: omp model roles via `--model`, `--smol` (cheap/fast
model for light tasks), `--slow`, `--plan` [V `omp --help` 18.4.1] — lets a
cheap model do browsing and a stronger one do matching/answers. Pi custom
OpenAI-compatible endpoints: `~/.pi/agent/models.json` with `baseUrl`,
`api: "openai-completions"`, `apiKey`, `models` [V pi.dev/docs/latest/models].

## 3. Recommendation (provider-agnostic)

1. **Harness first:** an open harness (omp/pi or OpenCode) — provider
   choice stays a one-line switch (`/connect`, `/login`, `/model`), and the
   omp browser path is the one that measured 2–4× smaller per-turn context.
2. **Provider by billing model:**
   - flat monthly coding plan (Z.ai GLM, Kimi For Coding, MiniMax) —
     predictable cost; respect each plan's tool list and endpoint;
   - pay-per-token with free choice of model — OpenRouter;
   - existing Claude Pro/Max subscription — Claude Code + Claude in Chrome
     is the zero-setup option but the most expensive one measured; apply
     the session-hygiene rules.
3. **Cheap model for the browsing loop, stronger model for judgment** —
   via omp roles (`--smol`) or Claude Code's
   `ANTHROPIC_DEFAULT_HAIKU_MODEL` / `CLAUDE_CODE_SUBAGENT_MODEL`.
4. **Session hygiene applies everywhere:** one platform per session,
   offer browsing in subagents, text over screenshots.
5. **Keys:** the user enters API keys themselves (env var, harness
   `auth.json`, keychain). Agents never paste keys into chat or the repo.

## 4. Open questions / not verified

- Whether the Z.ai GLM Coding Plan terms cover omp (only "Pi" is listed).
- Kimi's exact Anthropic-compatible base URL on its own docs page (only
  [3P] confirms `https://api.moonshot.ai/anthropic`).
- Codex CLI config snippets for DeepSeek / OpenRouter.
- Whether Claude Code with a third-party `ANTHROPIC_AUTH_TOKEN` disables
  Claude in Chrome — consistent with the docs, not tested.
- Cost of any of these vs the 2026-09-04 measurement — only GLM was
  measured.

## Sources

- Z.ai — Claude Code setup: https://docs.z.ai/devpack/tool/claude
- Z.ai — other tools / supported list: https://docs.z.ai/devpack/tool/others
- Claude Code — LLM gateways: https://code.claude.com/docs/en/llm-gateway
- Claude Code — Chrome: https://code.claude.com/docs/en/chrome
- OpenRouter — Claude Code integration: https://openrouter.ai/docs/guides/guides/claude-code-integration
- DeepSeek — Claude Code: https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code/
- DeepSeek — Anthropic API: https://api-docs.deepseek.com/guides/anthropic_api
- Moonshot/Kimi — agent support: https://platform.kimi.ai/docs/guide/agent-support
- MiniMax — agent setup wizard: https://platform.minimax.io/docs/token-plan/agent-setup.md
- OpenCode — providers: https://opencode.ai/docs/providers/
- pi — providers: https://pi.dev/docs/latest/providers ; models: https://pi.dev/docs/latest/models
- omp — local `omp --help`, `omp models --help` (v18.4.1)
