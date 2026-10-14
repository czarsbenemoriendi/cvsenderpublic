# CVSender — agent bootstrap

This file is the cross-harness entry point (AGENTS.md convention, read by
omp, Codex CLI, OpenCode, and other coding agents).

0. **Fresh clone — do this first, before anything else:** if
   `data/aboutme.md.template` / `data/cv_info.md.template` exist and
   `data/aboutme.md` / `data/cv_info.md` do not, **rename** them — just drop
   the `.template` suffix (`mv data/aboutme.md.template data/aboutme.md`,
   same for `cv_info.md`). Rename, don't copy: from then on
   `data/aboutme.md` and `data/cv_info.md` are the **single source of truth
   (SSOT)** for the user's data — every step (SETUP.md, the skill, the panel)
   reads and writes only them, and no `.template` file should remain.
   The real files are gitignored, so personal data never reaches the repo.
1. **Read `SESSION_STATUS.md` in full before doing anything else** — it is
   the single source of truth for project state, decisions, and next steps.
2. **The job-search workflow lives in the skill**
   `.agents/skills/cvskill/SKILL.md` — invoke it as `/skill:cvskill` (omp),
   `$cvskill` (Codex CLI), or load the file directly by path. Its hard
   rules are non-negotiable; it references browser *capabilities* only and
   maps them to concrete tools in its appendix.
3. **All data paths are relative to the repository root** (e.g.
   `data/cvsender.db`, not `../data/...`).
4. User-facing docs (`README.md`, `SETUP.md`, `JAK_URUCHOMIC.md`,
   `SESSION_STATUS.md`) are in Polish — keep that convention. `MIGRATION_PLAN.md`
   and `research/` are in English.
5. Never commit personal data (`data/aboutme.md`, `data/cv_info.md`,
   `data/*.pdf`, `data/cvsender.db`*, `data/search_profile.json`,
   `data/salary_policy.json` — already covered by `.gitignore`).
