# CVSender

> **Pochodzenie projektu:** to repozytorium wywodzi się z pierwotnego projektu
> [cvsenderpublic na GitLabie](https://gitlab.com/lubowskitobiasz/cvsenderpublic)
> i jest jego rozwinięciem. Licencja (PolyForm Noncommercial 1.0) pozostaje bez
> zmian — patrz plik `PolyForm Noncommercial License 1.0`.

Automatyzacja szukania i aplikowania na oferty pracy razem z agentem
kodującym (działa z każdym harnessem wspierającym standard
[Agent Skills](https://agentskills.io) — Claude Code, omp, OpenAI Codex CLI,
OpenCode — użyj tego, w którym już pracujesz): agent przegląda portale z ofertami,
dopasowuje je do Twojego CV, aplikuje przez formularz danej oferty (nigdy
e-mailem, nigdy bez Twojej zgody na konkretną ofertę), i loguje wszystko w
CSV. Dochodzi do tego lokalny panel przeglądowy (statystyki, kolejka ofert
do zaakceptowania, karty wiedzy do nauki na rozmowy rekrutacyjne).

## Wymagania

- Agent wspierający [Agent Skills](https://agentskills.io) — np. **Claude
  Code**, omp, Codex CLI, OpenCode. Skill workflow jest w repo pod
  `.agents/skills/cvskill/` (standard Agent Skills) — użyj go w sposób
  naturalny dla swojego harnessu albo poproś agenta o wczytanie `SKILL.md`
  bezpośrednio ze ścieżki.
- **Sterowanie przeglądarką dopasowane do Twojego harnessu** — np. Claude
  Code: rozszerzenie "Claude in Chrome"; omp: rozszerzenie OMP Browser
  Relay (jednorazowo `omp browser-relay install`, potem włącz rozszerzenie
  w Chrome, najlepiej w dedykowanym profilu, np. `CVSender`). Agent steruje
  Twoim prawdziwym, zalogowanym Chrome — sesje logowań na portalach z
  ofertami zostają. Bez tego automatyczne przeglądanie ofert i wypełnianie
  formularzy nie zadziała — SETUP.md sam to sprawdzi i powie Ci dokładnie
  czego brakuje dla Twojego harnessu.
- Python 3 (bez dodatkowych zależności) — do lokalnego panelu.

## Rekomendowany setup (koszty)

Pomiar z logów sesji (2026-09-04), ta sama praca: **Claude Code + Claude in
Chrome (Sonnet 5) ~227 USD** vs **omp + Browser Relay (GLM-5.2) ~10 USD**,
czyli około **20 razy taniej**. Oszczędność składa się z trzech niezależnych
wyborów:
- **harnessu**, który czyta strony oszczędnie (omp przesyła 2–4 razy mniej
  danych na turę),
- **taniego modelu**, przy czym dowolnego, nie tylko GLM: Z.ai, Kimi,
  DeepSeek, MiniMax i OpenRouter podpina się do omp/pi, OpenCode i Claude
  Code,
- **higieny sesji**: jedna platforma na sesję, przeglądanie w subagentach.

Rekomendacja: otwarty harness (omp/pi albo OpenCode) + wybrany tani
dostawca. Ścieżka decyzji i tabela podpięcia: `SETUP.md`, Krok 0.2b; źródła:
`research/2026-10-14-model-providers-for-terminal-agents.md`.

## Start

1. Sklonuj to repo i otwórz je w swoim agencie (Claude Code, omp, Codex CLI
   — czymkolwiek pracujesz).
2. Napisz do agenta: **"przeczytaj SETUP.md i skonfiguruj mnie"**.

Agent przeprowadzi Cię przez krótką rozmowę — dane kontaktowe, CV,
preferencje (widełki, tryb pracy, forma współpracy) i platformy z ofertami —
i sam wypełni wszystko, czego potrzebuje reszta systemu. To wszystko, czego
potrzebujesz zrobić ręcznie.

Po konfiguracji: uruchom skill workflow (omp: `/skill:cvskill`, Codex CLI:
`$cvskill`, Claude Code: poproś agenta o wczytanie
`.agents/skills/cvskill/SKILL.md`), żeby zacząć szukać i aplikować na
oferty, albo uruchom lokalny panel — instrukcja w
[JAK_URUCHOMIC.md](JAK_URUCHOMIC.md).

## Co jest w środku

| Plik/katalog | Rola |
|---|---|
| `AGENTS.md` | Punkt startowy agenta (konwencja AGENTS.md) — kieruje do reszty. |
| `SETUP.md` | Jednorazowa konfiguracja — czyta to agent, nie Ty. |
| `SESSION_STATUS.md` | Bieżący status projektu (agent czyta to na początku każdej sesji). |
| `.agents/skills/cvskill/SKILL.md` | Workflow i twarde reguły wyszukiwania/aplikowania — wywoływane zgodnie z konwencją harnessu (`/skill:cvskill` w omp, `$cvskill` w Codex CLI; w Claude Code wczytaj plik bezpośrednio). Odwołuje się do capability przeglądarki, nie narzędzi konkretnego vendora (mapowanie w Appendix). |
| `MIGRATION_PLAN.md` + `research/` | Plan i badania (2026-08) migracji z podejścia Claude-centric na harness-agnostyczne. |
| `data/aboutme.md` | Twoje dane kontaktowe i preferencje (jedyne źródło prawdy). W repo jest tylko szablon `data/aboutme.md.template` — agent przy pierwszej konfiguracji zmienia jego nazwę na `aboutme.md`. |
| `data/cv_info.md` | Treść Twojego CV do dopasowywania ofert (jedyne źródło prawdy). W repo jest tylko szablon `data/cv_info.md.template` — jak wyżej. |
| `data/links.md` | Lista platform z ofertami pracy i ich status. |
| `data/cvsender.db` | SQLite: log wysłanych aplikacji (tabela `applications`) i kolejka ofert do akceptacji (tabela `offers`) — jedyne źródło prawdy lejka. |
| `data/learning/` | Karty wiedzy (teoria + pytania rekrutacyjne). Zaczyna puste — SETUP.md generuje je na podstawie Twojego CV i realnych ofert. |
| `frontend/` | Lokalny panel przeglądowy (`JAK_URUCHOMIC.md` opisuje uruchomienie). |

## Prywatność

Wszystkie dane (CV, dane kontaktowe, historia aplikacji) trzymane są
lokalnie w tym repo — log lejka w `data/cvsender.db` (SQLite), reszta w
Markdownie — nic nie jest wysyłane nigdzie poza faktycznym wypełnianiem
formularzy ofert, na które sam/a się zgodzisz. Jeśli planujesz wypchnąć
swój skonfigurowany fork na publiczne repo, pamiętaj żeby **nie
commitować** `data/aboutme.md`, `data/cv_info.md`, pliku CV PDF ani
`data/cvsender.db*` (baza z Twoimi realnymi danymi) — `.gitignore` już to
obejmuje.
