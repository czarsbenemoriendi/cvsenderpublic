# Status projektu: automatyzacja aplikowania o pracę (CVSender)

> **Dla nowej sesji agenta (domyślnie omp):** przeczytaj ten plik w całości, zanim zaczniesz
> cokolwiek robić w tym projekcie. To jest jedyne źródło prawdy o tym, co już
> zrobione, co ustalone, i co zostało do zrobienia. Szczegółowe zasady
> działania (workflow, twarde reguły, lekcje o formularzach ATS) są w
> `.agents/skills/cvskill/SKILL.md` — ten plik odsyła tam zamiast duplikować treść.
>
> **Jeśli `data/aboutme.md` lub `data/cv_info.md` nadal zawierają nawiasy
> `[PLACEHOLDER]`**, projekt nie jest jeszcze skonfigurowany — przeczytaj
> najpierw `SETUP.md` i przeprowadź użytkownika przez konfigurację, zanim
> zaczniesz szukać ofert.
> Pełny dziennik sesji: `data/logs/session_diary.md` (lokalny, nie kommitowany — patrz "Dziennik sesji" niżej).

## Cel

Agent (harness-agnostycznie — po migracji: omp z narzędziem `browser` w trybie OMP Browser Relay; wcześniej Claude Code + "Claude in Chrome"; patrz `MIGRATION_PLAN.md`) przegląda oferty pracy na
platformach z `data/links.md`, dopasowuje je do CV użytkownika
(`data/cv_info.md`), wysyła CV do pasujących ofert przez formularz
aplikacyjny danej oferty, i loguje każdy wynik w bazie `data/cvsender.db`
(SQLite, helpery `lib/store.py`; dawniej `applications.csv`) —
sprawdzając wcześniej, czy dana oferta nie była już obsłużona (brak
duplikatów).

**Rola/słowa kluczowe użytkownika:** _(do uzupełnienia podczas `SETUP.md`, Krok 2)_

## Struktura katalogów w `CVSender/`

```
CVSender/
├── AGENTS.md               ← punkt startowy agenta (konwencja AGENTS.md)
├── SESSION_STATUS.md      ← ten plik, punkt startowy
├── SETUP.md                ← jednorazowa konfiguracja (dane osobowe, CV, preferencje)
├── MIGRATION_PLAN.md       ← plan migracji z Claude na podejście harness-agnostyczne
├── .agents/skills/cvskill/SKILL.md ← workflow + twarde reguły (`/skill:cvskill` w omp)
├── research/               ← raporty z badań: alternatywy agentowe, rynek softu rekrutacyjnego
├── frontend/
│   ├── server.py            ← lokalny panel (stdlib Python, zero zależności)
│   └── static/
│       └── index.html
└── data/
    ├── aboutme.md               ← dane kontaktowe/preferencje do formularzy (SSOT; w repo tylko aboutme.md.template)
    ├── cv_info.md               ← pełna treść CV do dopasowywania ofert (SSOT; w repo tylko cv_info.md.template)
    ├── <dowolna_nazwa>.pdf       ← plik CV do załączania (dashboard sam go znajdzie)
    ├── links.md                  ← platformy + status + notatki
│   ├── cvsender.db               ← SQLite: lejek (applications), korpus+kolejka (offers)
│   │                               — jedyne źródło prawdy od 2026-09-14 (CSV skasowane)
    └── learning/                 ← karty wiedzy zakładki NAUKA (jeden JSON na technologię)

| Plik | Rola |
|---|---|
| `.agents/skills/cvskill/SKILL.md` | Workflow, twarde reguły, lekcje ATS + Appendix z mapowaniem capability→narzędzia (omp `browser` / Playwright MCP / Claude-in-Chrome). Wywoływalny jako `/skill:cvskill` (omp) / `$cvskill` (Codex CLI). Ścieżki do danych wskazują na `data/...` względem korzenia repo. |
| `SESSION_STATUS.md` | Ten plik — status projektu, punkt startowy nowej sesji. |
| `SETUP.md` | Jednorazowy proces konfiguracji — czytany przez agenta, przeprowadza użytkownika przez pytania i wypełnia `data/aboutme.md`, `data/cv_info.md`, umieszcza CV PDF, dostosowuje `data/links.md`. |
| `data/aboutme.md` | Dane kontaktowe i preferencje kandydata do formularzy. |
| `data/search_profile.json` | Profil wyszukiwania (osobisty, gitignorowany; szablon `search_profile.example.json`) — rola, słowa kluczowe, reguły punktacji ofert, filtr feedów. Tworzony w `SETUP.md` (Krok 3). |
| `data/cv_info.md` | Pełna treść CV (doświadczenie, umiejętności, edukacja) do dopasowywania ofert. |
| `data/links.md` | Tabela platform ze statusem i notatkami o specyfice każdej. |
| `data/cvsender.db` | **Jedyne źródło prawdy lejka (od 2026-09-14; CSV `applications.csv`/`offerstosend.csv` skasowane).** SQLite (helpery `lib/store.py`): tabela `applications` — log prób (kolumny `applied_date, company, position, level, match, job_url, source, status, method, notes` + derywowane `state`/`state_changed_at`); tabela `offers` — korpus zeskanowanych ofert + kolejka propozycji (`decision` ∈ `pending` / `accepted` / `postponed_future` / `postponed_no_send` / `handled` — źródło prawdy; `set_offer_decision` działa na całej grupie dedup_key). |
| `frontend/server.py` + `frontend/static/index.html` | Lokalny panel z czterema zakładkami: **GŁÓWNA** (statystyki, "Wymaga Twojej działania" — filtruje tabelę `applications` (DB) po `Status` zaczynającym się od "Blocked", tabela `applications`, oraz "Propozycje do przejrzenia" — wiersze `Decision=pending` z przyciskami ✓ Akceptuj / ⏳ Odłóż na przyszłość / ✕ Odłóż – nie wysyłać), **PRZYGOTOWANE** (`Decision=accepted`, z przyciskiem ↩ Cofnij do przeglądu), **ODŁOŻONE** (`postponed_future` + `postponed_no_send`, z przyciskiem ↩ Przywróć), **NAUKA** (siatka kart technologii z `data/learning/*.json` — teoria + pytania rekrutacyjne, wyszukiwarka filtruje na żywo). Nawigacja przez `location.hash` (`#main`/`#prepared`/`#postponed`/`#learning`). Stdlib only (`http.server`), zero zależności. Uruchomienie: patrz `JAK_URUCHOMIC.md`. |
| `data/learning/*.json` | Karty wiedzy zakładki NAUKA — jeden plik JSON na technologię. **Katalog zaczyna pusty** — karty generuje `SETUP.md` (Krok 5) na podstawie CV użytkownika i realnych ofert znalezionych podczas konfiguracji, nie jest to gotowa lista uniwersalna. Schemat: `{slug, name, tagline, sections: [{title, body}], questions: [{q, a}]}`. `body`/`a` mogą zawierać prosty markdown (`**pogrubienie**`, listy `- linia`) renderowany po stronie klienta. Dodanie nowej karty później: dopisać `<slug>.json` w tym katalogu wg schematu — panel podejmie go automatycznie. |
| `data/logs/session_diary.md` | **Lokalny dziennik sesji (nie kommitowany; `data/logs/` w `.gitignore`)** — pełne narracje, mogą zawierać realne dane użytkownika. Konwencja: sekcja "Dziennik sesji" niżej. |

## Stan bieżący

> Generowany z `data/cvsender.db` — odświeżaj na początku i końcu sesji.

- Instancja świeża: konfiguracja (`SETUP.md`) jeszcze nie przeprowadzona.
- Brak `data/cvsender.db` — lejek i kolejka puste; panel pokazuje puste
  zakładki (odczyty z pustego magazynu w pamięci), a akcje zapisu zwracają
  503, dopóki baza nie zostanie utworzona przez pierwszy przebieg skauta/skilla.

## Kluczowe decyzje / ustalenia

- **CSV zamiast SQLite/Excel** — czytelne dla człowieka, łatwe do grepowania
  po URL/firmie żeby uniknąć podwójnej aplikacji.
  **(Nadpisane 2026-09-14:** SQLite `data/cvsender.db` jako jedyne źródło;
  CSV skasowane, panel bez fallbacku — brak DB = HTTP 503**.)**
  **(Doprecyzowane 2026-10-14:** brak/pusta DB → endpointy GET zwracają
  puste wyniki, żeby świeża instancja nie straszyła błędami; 503 tylko dla
  POST.**)**
- **Autonomia wysyłki — wersja 1 (obowiązująca):** każda wysyłka CV wymaga
  wyraźnego potwierdzenia użytkownika przed kliknięciem "Aplikuj"/"Wyślij".
  Wersja "auto-apply na podstawie dopasowania + szans, bez potwierdzenia per
  oferta" jest tylko koncepcją — **nie przełączać się na nią samodzielnie**,
  wymaga jawnej zgody użytkownika.
- **Metoda wysyłki:** wyłącznie przez przycisk "Aplikuj"/"Aplikuj szybko"/
  formularz na stronie oferty. Część platform przekierowuje na formularz ATS
  pracodawcy (Traffit, eRecruiter) w nowej karcie — to normalne, nie błąd.
  Nigdy nie wysyłamy e-mailem.
- **Logowanie na platformy jest ręczne** — jeśli platforma wymaga logowania
  i pojawia się prompt OAuth/Google one-tap, nie klikamy go sami — prosimy
  użytkownika o ręczne zalogowanie.
- **Widełki finansowe:** wpisujemy zawsze jedną kwotę (nie zakres). Szczegóły
  i przykłady: `.agents/skills/cvskill/SKILL.md`, twarda reguła 6.
- **Dziennik sesji:** pełne narracje sesyjne trzymamy w
  `data/logs/session_diary.md` (lokalny, nigdy nie kommitowany).
  `SESSION_STATUS.md` = operating manual + "Stan bieżący" (poniżej).

## Status platform (`links.md`)

Wszystkie platformy w `data/links.md` mają status `Nietestowany` —
statusy i notatki per-platforma (cookie bannery, quirki wyszukiwania)
uzupełnia automatyzacja po faktycznych wizytach.


## 2026-09-09 (b): Funnel architecture + shortlist-first panel

**Problem:** panel pokazywał płaską tabelę 19 875 wierszy (surowy korpus) —
nieużywalna. Stary flow agentowy wyciągał ~10-15 KURATOWANYCH ofert na raz.
**Rozwiązanie (dyrektor zatwierdził):** lejek z trwałym dedupem, inkrementalnym
matcherem, nocnym prunerem i UI shortlist-first.

### Architektura

```
sitemaps/APIs → scout (incremental) ──► seen_urls (TRWAŁY dedup, sha256 url)
                                     └─► offers (korpus; ogranicza go pruner)
matcher (kursor meta.last_matched_at) ─► offers.match_score 0-100
                                         + match_reasons (json [{"rule","delta"}])
shortlist (widok człowieka) = match_score >= 60 AND decision='pending'
                              AND NOT expired        ← to jest KOLEJKA w panelu
nocny pruner:
  a) expired AND match_score < 60 AND starsze niż 14 dni → DELETE
     (hash zostaje w seen_urls — nightly dump nigdy nie wskrzesi oferty)
  b) expired AND match_score >= 60 AND state='new' → state='expired'
     (zostaje w DB jako ślad audytowy, poza shortlistą)
```

- `offers.state` = cykl maszynowy (new → expired/archived); `decision` =
  nadal decyzja człowieka (accepted/postponed_*/pending). "Shortlisted" jest
  pochodną score, nie kolumną.
- `seen_urls(url_hash PK, url, first_seen, last_seen)` — zapis w każdej
  upsertce skauta (`store.upsert_offer`); widziany-a-brakujący-w-offers URL
  = przycięty przez prunera = nie wraca.

### Jak odpalić ręcznie

```
python3 scout/matcher.py --db data/cvsender.db          # inkrementalnie (kursor)
python3 scout/matcher.py --db data/cvsender.db --full   # cały korpus
python3 scout/pruner.py --db data/cvsender.db --dry-run # co by usunął
python3 scout/pruner.py --db data/cvsender.db           # na serio
```

launchd/scout.sh — kolejność stage'y: jjit → nfj → **matcher → pruner** → ats.

### Reguły punktacji (deterministyczne; źródło: profil wyszukiwania)

Reguły roli/stacku **nie są wpisane w kod** — pochodzą z
`data/search_profile.json` (osobisty, gitignorowany; szablon
`data/search_profile.example.json`; schemat w `lib/profile.py`). Profil
buduje `SETUP.md` (Krok 3) z kwestionariusza + CV i pokazuje użytkownikowi
do akceptacji. Bez osobistego profilu matcher i feeds używają przykładu
(DevOps) z ostrzeżeniem.

- reguły `scoring` profilu: ±N, gdy termin trafi w `title` / `musthave`
  (tytuł + pierwsze 200 znaków wymagań) / `text` (tytuł + notatki + opis),
- `location`: bonus za remote i region EU/PL, kara za on-site w miastach z
  listy profilu (gdy brak "remote"),
- +10 midpoint widełek ≥ `default_net_pln` z `data/salary_policy.json`
  (godzinowe × hourly_divisor; nie-PLN nigdy nie punktują), −100 expired.
  Clamp 0-100.
- Każdy powód ma `label` z profilu — panel pokazuje go przy ofercie.
- Podgląd punktacji dla hipotetycznej oferty:
  `python3 scout/matcher.py --try "<tytuł>" --location "<lokalizacja>" [--salary MIN-MAX]`.
  Po zmianie profilu: `python3 scout/matcher.py --db data/cvsender.db --full`.
- Zagraniczne feedy (`scout/feeds.py`) zapisują tylko oferty z tytułem
  pasującym do `feeds.include_title` profilu; tag Jobicy i kategoria
  Remotive też z profilu.

### Strojenie progu

`SHORTLIST_THRESHOLD = 60` w `lib/store.py` (używa go matcher, /api/shortlist
i statystyki panelu). Podnoszenie progu → krótsza kolejka;
obniżanie → szersza. Zmiana = edycja jednej stałej + reinstall.

### Zasady retencji korpusu

Pruner domyślnie: usuwa martwe (expires_at w przeszłości) niskie wyniki
(< 60) starsze niż 14 dni; martwe wysokie wyniki znaczy state='expired' i
trzyma je wiecznie (audyt). Oferty bez expires_at i bez score pruner omija.

### Panel: KOLEJKA / DO AKCJI / WYSŁANE / ODŁOŻONE / NAUKA

- KOLEJKA (start): karty shortlisty (score, source, pensja, wygasa, top-3
  powody, ✓/⏳/✕ → POST decision po job_url), stronicowanie 20/stronę;
  „Pokaż wszystko" = tryb korpusu z filtrami (q, source, remote, expiring_days,
  sort) i infinite scroll po 20 (IntersectionObserver; żaden widok nie ładuje
  całej tabeli).
- DO AKCJI: wiersze blocked + follow-up >7 dni + przycisk Gmail.
- WYSŁANE: 50/strona infinite scroll, wyszukiwanie po stronie serwera (q),
  rozwijany wiersz → metoda/dopasowanie/notatki + edytor + status.
- PLATFORMY (od 2026-10-14): podgląd tabeli z `data/links.md` (platforma,
  URL, status, notatki) przez `/api/platforms` — tylko odczyt, edycja = plik.
- API: /api/offers i /api/applications mają twardy limit 200/request (default
  20/50); /api/shortlist, /api/stats (liczniki badge'y); POST decision/update
  przyjmują job_url/id (stare index-routes zostają).
- Pierwsze ładowanie strony transferuje TYLKO: /api/stats,
  /api/shortlist?limit=20&offset=0, /api/config. Zero tabel hurtowych.

## Dziennik sesji

Pełne, datowane narracje z sesji (co zrobione, decyzje użytkownika, lekcje)
żyją w `data/logs/session_diary.md` — **lokalnie, nigdy nie kommitowane**
(`data/logs/` jest w `.gitignore`), bo mogą zawierać realne dane użytkownika.
Na końcu każdej sesji: dopisz tam wpis i odśwież "Stan bieżący" wyżej.
