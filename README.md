# CVSender

> **Pochodzenie projektu:** to repozytorium wywodzi się z pierwotnego projektu
> [cvsenderpublic na GitLabie](https://gitlab.com/lubowskitobiasz/cvsenderpublic)
> i jest jego rozwinięciem. Licencja (PolyForm Noncommercial 1.0) pozostaje bez
> zmian — patrz plik `PolyForm Noncommercial License 1.0`.

Automatyzacja szukania i aplikowania na oferty pracy razem z agentem
kodującym (domyślnie [omp](https://github.com/badlogic/pi-mono); działa z
każdym harnessem wspierającym standard [Agent Skills](https://agentskills.io),
np. OpenAI Codex CLI czy OpenCode): agent przegląda portale z ofertami,
dopasowuje je do Twojego CV, aplikuje przez formularz danej oferty (nigdy
e-mailem, nigdy bez Twojej zgody na konkretną ofertę), i loguje wszystko w
CSV. Dochodzi do tego lokalny panel przeglądowy (statystyki, kolejka ofert
do zaakceptowania, karty wiedzy do nauki na rozmowy rekrutacyjne).

## Wymagania

- Agent wspierający [Agent Skills](https://agentskills.io) — domyślnie
  **omp**. Skill workflow jest w repo pod `.agents/skills/cvskill/` i omp
  wykrywa go automatycznie (wywołanie `/skill:cvskill`).
- **Chrome z rozszerzeniem OMP Browser Relay** — jednorazowa instalacja:
  `omp browser-relay install`, potem włącz rozszerzenie w Chrome
  (najlepiej w dedykowanym profilu, np. `CVSender`). Agent steruje Twoim
  prawdziwym, zalogowanym Chrome — sesje logowań na portalach z ofertami
  zostają. Bez tego automatyczne przeglądanie ofert i wypełnianie
  formularzy nie zadziała — SETUP.md sam to sprawdzi i powie Ci dokładnie
  czego brakuje, jeśli czegoś nie ma.
- Python 3 (bez dodatkowych zależności) — do lokalnego panelu.

## Start

1. Sklonuj to repo i otwórz je w swoim agencie (domyślnie omp).
2. Napisz do agenta: **"przeczytaj SETUP.md i skonfiguruj mnie"**.

Agent przeprowadzi Cię przez krótką rozmowę — dane kontaktowe, CV,
preferencje (widełki, tryb pracy, forma współpracy) i platformy z ofertami —
i sam wypełni wszystko, czego potrzebuje reszta systemu. To wszystko, czego
potrzebujesz zrobić ręcznie.

Po konfiguracji: użyj **`/skill:cvskill`**, żeby zacząć szukać i aplikować
na oferty, albo uruchom lokalny panel — instrukcja w
[JAK_URUCHOMIC.md](JAK_URUCHOMIC.md).

## Co jest w środku

| Plik/katalog | Rola |
|---|---|
| `AGENTS.md` | Punkt startowy agenta (konwencja AGENTS.md) — kieruje do reszty. |
| `SETUP.md` | Jednorazowa konfiguracja — czyta to agent, nie Ty. |
| `SESSION_STATUS.md` | Bieżący status projektu (agent czyta to na początku każdej sesji). |
| `.agents/skills/cvskill/SKILL.md` | Workflow i twarde reguły wyszukiwania/aplikowania — wywoływane jako `/skill:cvskill` (omp) / `$cvskill` (Codex CLI). Odwołuje się do capability przeglądarki, nie narzędzi konkretnego vendora (mapowanie w Appendix). |
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
