# SETUP — jednorazowa konfiguracja CVSender

> **To jest plik z instrukcjami dla agenta, nie dla człowieka.** Instrukcje
> są harness-agnostyczne — działają z każdym agentem wspierającym standard
> [Agent Skills](https://agentskills.io) (Claude Code, omp/oh-my-pi,
> OpenAI Codex CLI, OpenCode). **Nie każ użytkownikowi niczego
> doinstalowywać** — korzystaj z harnessu, w którym już pracuje (np. Claude
> Code). Jeśli użytkownik poprosił Cię o
> przeczytanie tego pliku (albo o "skonfigurowanie" / "setup" tego repo) —
> wykonaj poniższe kroki po kolei, prowadząc żywą rozmowę z użytkownikiem.
> Nie proś o wszystko naraz w jednym wielkim formularzu — pytaj sekcjami
> (patrz niżej), tłumacz po co dana informacja jest potrzebna, i pozwól
> użytkownikowi poprawić się w trakcie. Rób automatycznie wszystko, co da
> się zrobić bez pytania (sprawdzanie narzędzi, kopiowanie plików,
> wyszukiwanie w sieci, generowanie treści) — pytaj użytkownika tylko o to,
> czego naprawdę nie możesz ustalić sam (jego dane osobowe, preferencje,
> decyzje wymagające jego zgody).
>
> Cel tego procesu: wypełnić `data/aboutme.md` i `data/cv_info.md` prawdziwymi
> danymi użytkownika (obecnie mają placeholdery w nawiasach `[PLACEHOLDER]`),
> umieścić plik CV w `data/`, zbudować z odpowiedzi **profil wyszukiwania**
> (`data/search_profile.json` — punktacja, według której system wybiera
> oferty do kolejki), dostosować `data/links.md` do rynku/roli użytkownika, i wygenerować pierwsze karty NAUKA na podstawie jego CV i
> realnych ofert — tak żeby `/skill:cvskill` i panel mogły od razu ruszyć.

## Krok 0 — środowisko i punkt startowy (pipeline decyzyjny)

**Założenie wyjściowe: użytkownik nie ma NIC.** Nie ma rozszerzenia
przeglądarki, MCP, Node.js ani nawet Chrome'a. Przejdź kroki 0.1–0.7
**po kolei** i w każdym wykonaj dokładnie jedną gałąź (JEŚLI / W PRZECIWNYM
RAZIE). Nie pomijaj sprawdzeń „bo pewnie jest”: każdy warunek weryfikuj
poleceniem albo testem. Zasady obowiązujące w całym Kroku 0:

- **Rozszerzeń przeglądarki nie instalujesz sam.** Instaluje je
  użytkownik, ręcznie. Ty podajesz dokładne kroki i czekasz na potwierdzenie.
- **Polecenia instalacyjne w terminalu** (np. `brew install node`,
  `claude mcp add …`) uruchamiasz dopiero po zgodzie użytkownika. Pytasz
  narzędziem pytań wyboru, np. „Zainstaluj teraz” / „Zrobię to sam” /
  „Pomiń na razie”.
- **Brak przeglądarki nie blokuje setupu.** Kroki 1–5 (dane, CV, profil
  punktacji, panel, portale) działają bez niej. Gdy gałąź wymaga restartu
  sesji agenta albo działania użytkownika poza rozmową, zapisz to jako
  **zaległość** i idź dalej. Do zaległości wrócisz w 0.6 i w Kroku 7.
- Po każdej zmianie środowiska **sprawdź ponownie** test z 0.4. Nie
  zakładaj, że instalacja się udała.

### 0.1 — Szablony danych (świeży klon)

- JEŚLI istnieje `data/aboutme.md.template` ORAZ nie istnieje
  `data/aboutme.md` → zmień nazwę:
  `mv data/aboutme.md.template data/aboutme.md`.
- Analogicznie dla `data/cv_info.md.template` → `data/cv_info.md`.
- JEŚLI istnieje zarówno plik docelowy, jak i `.template` → **nie
  nadpisuj** pliku docelowego. Usuń tylko `.template` (plik docelowy jest
  jedynym źródłem prawdy, SSOT).
- W PRZECIWNYM RAZIE (pliki docelowe już są) → nic nie rób.

Od tej chwili `data/aboutme.md` i `data/cv_info.md` są **jedynym źródłem
prawdy (SSOT)** o danych użytkownika. Oba są w `.gitignore`.

### 0.2 — Rozpoznaj harness (w czym działasz)

Ustal to z własnego kontekstu (nazwa narzędzi, prompt systemowy). Nie pytaj
użytkownika, chyba że naprawdę nie da się tego ustalić.

- JEŚLI **Claude Code** → zapamiętaj gałąź **A**.
- W PRZECIWNYM RAZIE JEŚLI **omp (oh-my-pi)** → gałąź **B**.
- W PRZECIWNYM RAZIE JEŚLI **OpenAI Codex CLI** → gałąź **C**.
- W PRZECIWNYM RAZIE JEŚLI **OpenCode** → gałąź **D**.
- W PRZECIWNYM RAZIE (inny harness z Agent Skills / MCP) → gałąź **E**.

Sprawdź też Agent Skills: JEŚLI harness sam wykrywa skille z
`.agents/skills/` (omp, Codex CLI, OpenCode) → skill wywołasz natywnie
(`/skill:cvskill`, `$cvskill`). W PRZECIWNYM RAZIE (np. Claude Code) →
skill będzie wczytywany wprost ze ścieżki `.agents/skills/cvskill/SKILL.md`.
Niczego nie trzeba instalować.

### 0.2b — Rekomendacja setupu (koszt tokenów)

Pokaż użytkownikowi krótko (bez żargonu), **zanim** zaczniesz cokolwiek
instalować:

> **Zmierzyliśmy to (2026-09-04, logi sesji obu narzędzi):** ta sama praca
> (wyszukiwanie ofert, budowanie kolejki, aplikowanie) kosztowała
> **~227 USD w Claude Code + Claude in Chrome (model Sonnet 5)** i **~10 USD
> w omp + Browser Relay (model GLM-5.2)**, czyli **około 20 razy taniej**.
> Skąd ta różnica:
> 1. **Mniej danych na każdą turę (2–4 razy):** Claude in Chrome wysyła
>    agentowi pełne zrzuty i snapshoty stron (średnio 206–465 tys. tokenów
>    kontekstu na wywołanie). Przeglądarka omp czyta tekstowe drzewo
>    dostępności i robi celowane zapytania (57–145 tys.).
> 2. **Tańszy model:** GLM-5.2 ma output ~3,4 raza tańszy niż Sonnet 5.
> 3. **Największy koszt w obu narzędziach** to ponowne wczytywanie
>    rosnącej rozmowy. Najwięcej daje więc *higiena sesji*: krótkie sesje
>    (jedna platforma na sesję) i przeglądanie ofert w subagentach, które
>    startują z pustym kontekstem.

Wniosek dla użytkownika: oszczędność daje **harness**, który czyta strony
oszczędnie, **tani model** i **higiena sesji**. To trzy niezależne
wybory. Nie trzeba się wiązać z jednym dostawcą (GLM był tylko tym, który
zmierzyliśmy). Szczegóły i źródła: `research/2026-10-14-model-providers-for-terminal-agents.md`.

**Decyzja 1 — harness:**
- JEŚLI harness = **omp / pi** albo **OpenCode** → zostań. To
  rekomendowany wybór, bo dostawcę zmienia się jednym poleceniem
  (`/login` / `/connect`, potem `/model`). Przejdź do Decyzji 2.
- W PRZECIWNYM RAZIE JEŚLI harness = **Claude Code** → zapytaj
  (narzędziem pytań wyboru):
  - „**Przechodzę na omp / OpenCode**” → podaj kroki instalacji jako
    zaległość i **kontynuuj setup tutaj** (dane w `data/` są wspólne).
    Decyzję 2 podejmiecie już w nowym harnessie.
  - „**Zostaję w Claude Code, z moją subskrypcją Claude**” → gałąź A z
    0.5 (Claude in Chrome). Zapisz w `SESSION_STATUS.md` („Kluczowe
    decyzje”) zasady oszczędzania:
    - jedna sesja = jedna platforma, potem `/clear`,
    - przeglądanie list ofert w subagentach,
    - tekst zamiast zrzutów ekranu,
    - `claude --chrome` tylko na czas pracy z przeglądarką (bez
      „Enabled by default”).
  - „**Zostaję w Claude Code, ale z tańszym modelem**” → Decyzja 2, wiersz
    „Claude Code”. Uprzedź, że Anthropic oficjalnie nie wspiera Claude
    Code z modelami spoza Claude, a Claude in Chrome działa tylko przy
    logowaniu `/login`. Przeglądarka będzie więc szła przez Playwright MCP
    (gałąź A, punkt 4 w 0.5).
- W PRZECIWNYM RAZIE (Codex CLI, inne) → Decyzja 2 i zasady higieny sesji
  jak wyżej.

**Decyzja 2 — dostawca modelu** (zapytaj narzędziem pytań wyboru):
- „**Stały miesięczny plan do kodowania**” (Z.ai GLM Coding Plan, Kimi For
  Coding, MiniMax) → przewidywalny koszt. Uprzedź: plany są ograniczone do
  wymienionych przez dostawcę narzędzi i wymagają jego endpointu „coding”.
- „**Płacę za zużycie, chcę wybierać modele**” → OpenRouter (jeden klucz,
  wiele modeli) albo bezpośrednio DeepSeek.
- „**Mam już subskrypcję Claude**” → Anthropic. Najprostsze, ale w
  pomiarze najdroższe; obowiązują zasady oszczędzania.
- „**Doradź**” → harness omp/pi albo OpenCode + dowolny plan „coding”.
  Do przeglądania tańszy/szybszy model (omp: rola `--smol`), do oceny
  ofert i odpowiedzi w formularzach mocniejszy.

**Podpięcie** (zweryfikowane w dokumentacji 2026-10-14; klucz API
**wpisuje użytkownik**, a agent nigdy nie wkleja go do czatu ani do repo):

| Dostawca | omp / pi | OpenCode | Claude Code |
|---|---|---|---|
| Z.ai GLM Coding Plan | `/login` albo `ZAI_API_KEY` | `/connect` → „Z.AI Coding Plan” | `npx @z_ai/coding-helper` albo `env` w `~/.claude/settings.json`: `ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic`, `ANTHROPIC_AUTH_TOKEN` |
| Moonshot (Kimi) | `MOONSHOT_API_KEY` / `KIMI_API_KEY` | `/connect` → „Moonshot AI” | wg przewodnika `platform.kimi.ai/docs/guide/claude-code-kimi` |
| DeepSeek | `DEEPSEEK_API_KEY` | `/connect` → „DeepSeek” | `ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic`, `ANTHROPIC_AUTH_TOKEN` |
| MiniMax | `MINIMAX_API_KEY` | `/connect` → „MiniMax” | kreator `npx -y mmx-cli@latest agent setup` |
| OpenRouter | `OPENROUTER_API_KEY` | `/connect` → „OpenRouter” | `ANTHROPIC_BASE_URL=https://openrouter.ai/api`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_API_KEY=""` |

Po podpięciu: model wybierasz przez `/model` (omp/pi, OpenCode, Claude
Code). W Claude Code sprawdź `/status`, że aktywny jest właściwy base URL
i token. Codex CLI: korzystaj z instrukcji danego dostawcy (Z.ai, MiniMax
mają je oficjalnie). Nie zgaduj konfiguracji.

Zastrzeżenie, które też powiedz: pomiar dotyczy jednego użytkownika,
mieszanki prac i jednego dostawcy (GLM), a tokenizery się różnią.
„Wielokrotnie taniej” jest pewne, dokładna liczba „20×” już nie. Ceny i
nazwy modeli dostawców zmieniają się często, więc sprawdzaj je na ich
stronach.

### 0.3 — Wspólne wymagania systemowe

Sprawdź każde poleceniem i zanotuj wynik:

1. **Chrome.** macOS: `ls "/Applications/Google Chrome.app"`; Linux:
   `command -v google-chrome || command -v chromium`; Windows: sprawdź
   `Program Files\Google\Chrome`.
   - JEŚLI brak → poproś użytkownika o instalację z
     https://www.google.com/chrome/ i potwierdzenie. Do tego czasu wpisz
     „przeglądarka” do zaległości i przejdź do 0.6.
   - W PRZECIWNYM RAZIE → dalej.
2. **Dedykowany profil Chrome** (zalecany, np. `CVSender`). Zaproponuj go
   użytkownikowi, żeby agent nie mieszał się z jego prywatnymi kartami.
   Profil tworzy użytkownik: Chrome → ikona profilu → „Dodaj”. Nie blokuje
   dalszych kroków.
3. **Node.js ≥ 18** (`node -v`). Potrzebny tylko gałęziom korzystającym z
   Playwright MCP (A.4, C, D, E).
   - JEŚLI brak i gałąź go wymaga → zaproponuj instalację (macOS:
     `brew install node`, jeśli jest `brew`; inaczej instalator z
     https://nodejs.org). Uruchom dopiero po zgodzie.
   - W PRZECIWNYM RAZIE → dalej.

### 0.4 — Test sterowania przeglądarką

Wykonaj test: otwórz `https://example.com` i odczytaj strukturę strony
(nagłówek „Example Domain”).

- JEŚLI test się udał → przeglądarka gotowa. Powiedz to użytkownikowi
  jednym zdaniem i przejdź do **0.6**.
- W PRZECIWNYM RAZIE (brak narzędzi przeglądarki albo błąd połączenia) →
  przejdź do **0.5**, do gałęzi rozpoznanej w 0.2.

### 0.5 — Instalacja sterowania przeglądarką (gałąź z 0.2)

Każda gałąź kończy się tak samo:
- JEŚLI zmiana wymaga restartu sesji agenta → powiedz użytkownikowi
  dokładnie: „zrestartuj agenta i napisz *kontynuuj setup*”. Zapisz
  zaległość i przejdź do 0.6. Po restarcie zaczynasz od 0.4.
- W PRZECIWNYM RAZIE → powtórz test z 0.4.

**A — Claude Code** (źródło: code.claude.com/docs/en/chrome)
1. **Sprawdź warunki Claude in Chrome**:
   - JEŚLI Claude Code jest zalogowany kluczem API albo tokenem z
     `claude setup-token` (a nie przez `/login`), ALBO działa przez
     Bedrock / Vertex / Foundry, ALBO konto nie ma planu Pro / Max / Team /
     Enterprise, ALBO system to WSL → Claude in Chrome nie zadziała.
     Przejdź od razu do punktu 4 (Playwright MCP).
   - W PRZECIWNYM RAZIE → punkt 2.
2. Użytkownik instaluje rozszerzenie **Claude** (Claude in Chrome, wersja
   ≥ 1.0.36) z Chrome Web Store:
   https://chromewebstore.google.com/detail/claude/fcoeoabgfenejglbffodgkkbkcdhcgfn
   i loguje się w nim na **to samo konto i organizację** co Claude Code
   (sprawdzisz to przez `/status`). Działa też w Edge i innych
   przeglądarkach Chromium.
3. Włączenie w Claude Code:
   - JEŚLI bieżąca sesja nie ma narzędzi przeglądarki → użytkownik
     restartuje sesję poleceniem `claude --chrome` (zaległość + „napisz
     *kontynuuj setup*”). Żeby nie podawać flagi za każdym razem: `/chrome`
     → **Enabled by default**.
   - Weryfikacja: `/chrome` ma pokazać „Status: Enabled” i „Extension:
     Installed”. JEŚLI „Not detected” albo „Not connected” → zrestartuj
     Chrome (przy pierwszym włączeniu Claude Code instaluje plik native
     messaging, który Chrome czyta tylko przy starcie), potem `/chrome` →
     „Reconnect extension”. Następnie test z 0.4.
4. Awaryjnie **Playwright MCP** (wymaga Node ≥ 18 z 0.3), po zgodzie:
   `claude mcp add playwright -- npx @playwright/mcp@latest --extension`
   oraz rozszerzenie **Playwright Extension**, które instaluje użytkownik:
   https://chromewebstore.google.com/detail/playwright-extension/mmlmfjhmonkocbjadbfplnigmagldckm
   (opcjonalnie token z ikony rozszerzenia:
   `-e PLAYWRIGHT_MCP_EXTENSION_TOKEN=…`, wtedy nie trzeba zatwierdzać
   połączenia ręcznie). Wymaga restartu sesji.

**B — omp** (źródło: `omp browser-relay --help`, omp 18.x)
1. Po zgodzie użytkownika uruchom `omp browser-relay install`. Zapisze
   rozszerzenie na dysk (domyślnie `~/.omp/browser-relay/extension`) i
   wypisze kroki konfiguracji.
2. Użytkownik ładuje je ręcznie (nie ma go w Chrome Web Store): Chrome →
   `chrome://extensions` → włącz **Tryb dewelopera** → **Załaduj
   rozpakowane** → wskaż katalog z punktu 1. Najlepiej w profilu
   `CVSender`.
3. Relay uruchamia się sam, gdy narzędzie `browser` działa w trybie relay
   (`browser.relay` albo `app.relay: true`). Ręcznie: `omp browser-relay`.
4. JEŚLI narzędzie `browser` nie pojawiło się w sesji → restart omp.
   W PRZECIWNYM RAZIE test z 0.4.

**C — OpenAI Codex CLI** (źródło: README microsoft/playwright-mcp)
1. Wymaga Node ≥ 18 z 0.3. Dopisz do `~/.codex/config.toml` (po zgodzie
   użytkownika; nie nadpisuj istniejących wpisów):
   ```toml
   [mcp_servers.playwright]
   command = "npx"
   args = ["@playwright/mcp@latest", "--extension"]
   ```
2. Rozszerzenie **Playwright Extension** (link w A.4) instaluje
   użytkownik. Wymaga restartu Codex CLI.

**D — OpenCode** (źródło: README microsoft/playwright-mcp)
1. Wymaga Node ≥ 18 z 0.3. Dopisz do `~/.config/opencode/opencode.json`
   (po zgodzie; scal z istniejącym plikiem, nie nadpisuj go):
   ```json
   {
     "$schema": "https://opencode.ai/config.json",
     "mcp": {
       "playwright": {
         "type": "local",
         "command": ["npx", "@playwright/mcp@latest", "--extension"],
         "enabled": true
       }
     }
   }
   ```
2. Rozszerzenie **Playwright Extension** (link w A.4) instaluje
   użytkownik. Wymaga restartu OpenCode.

**E — inny harness**
1. JEŚLI harness obsługuje MCP → skonfiguruj Playwright MCP
   (`npx @playwright/mcp@latest --extension` + Playwright Extension).
   Format konfiguracji bierz z dokumentacji harnessu. Nie zgaduj ścieżek;
   jeśli ich nie znasz, zapytaj użytkownika.
2. W PRZECIWNYM RAZIE / gdy nic nie działa → **awaryjnie CDP**. Użytkownik
   uruchamia osobny Chrome z debug-portem, np. na macOS:
   `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 --user-data-dir="$HOME/.cvsender-chrome"`.
   Agent łączy się przez `npx @playwright/mcp@latest --cdp-endpoint http://127.0.0.1:9222`.
   Uprzedź, że to osobny profil: trzeba się w nim raz zalogować na portale.
3. Ostateczność: tryb headless, bez sesji logowań. Nadaje się tylko do
   przeglądania ofert, nie do aplikowania.

JEŚLI po przejściu gałęzi test z 0.4 nadal nie działa → nie próbuj w
kółko. Opisz użytkownikowi, co sprawdziłeś i na czym utknęło, zapisz
zaległość i przejdź do 0.6.

### 0.6 — Podsumowanie środowiska

Pokaż użytkownikowi krótką tabelę, np.:

| Element | Stan |
|---|---|
| Harness | Claude Code (gałąź A) |
| Skill `cvskill` | wczytywany ze ścieżki |
| Chrome | ✅ zainstalowany |
| Sterowanie przeglądarką | ⏳ zaległość: zainstaluj rozszerzenie „Claude”, potem `claude --chrome` |

- JEŚLI są zaległości → powiedz wprost, że kroki 1–5 robimy teraz, a
  przeglądanie ofert (Krok 6, punkt 1) i aplikowanie ruszą po ich
  domknięciu. Do tego czasu w Kroku 6 używaj wyszukiwania w sieci zamiast
  przeglądarki.
- W PRZECIWNYM RAZIE → „Środowisko gotowe” i dalej.

### 0.7 — Czy konfiguracja już była robiona?

Odczytaj `data/aboutme.md` i `data/cv_info.md`:
- JEŚLI zawierają nawiasy `[PLACEHOLDER]` → świeża instancja, przejdź do
  Kroku 1.
- W PRZECIWNYM RAZIE → konfiguracja już była. Zapytaj (narzędziem pytań
  wyboru): „Powtórzyć całość” / „Zmienić coś konkretnego” / „Tylko
  domknąć zaległości środowiska”. Postępuj zgodnie z wyborem.

## Krok 1 — brief o użytkowniku (→ `data/aboutme.md`)

Zanim zadasz pierwsze pytanie, powiedz użytkownikowi trzy rzeczy:

1. **Co budujemy:** w tym kroku zbierasz jego **brief** (dane kontaktowe +
   preferencje) i zapiszesz go w `data/aboutme.md` — to źródło, z którego
   automatyzacja wypełnia formularze aplikacyjne.
2. **Że potrzebujemy CV lokalnie w projekcie:** w Kroku 2 CV musi trafić do
   katalogu `data/` — zarówno treść (`data/cv_info.md`), jak i **plik PDF
   odłożony w `data/`**, bo panel i formularze ATS załączają go bezpośrednio
   z tego katalogu. Poproś użytkownika, żeby miał CV pod ręką (ścieżkę do
   pliku na dysku albo treść do wpisania) — szczegóły dopracujecie w
   Kroku 2.
3. **Że odpowiedzi z tego kwestionariusza staną się punktacją ofert** —
   patrz obowiązkowa sekcja niżej.

### Obowiązkowo przed pierwszym formularzem pytań: jak działa system punktowy

**Zanim po raz pierwszy użyjesz narzędzia pytań wyboru**, pokaż
użytkownikowi osobną, wyraźnie wyodrębnioną sekcję (np. z nagłówkiem
"Jak działa system punktowy") z prostym wyjaśnieniem. Użytkownik nie może
dopytać o nic w trakcie wybierania opcji, więc musi to przeczytać
wcześniej. Pisz bez żargonu, krótko, mniej więcej tak:

> **Jak działa system punktowy**
>
> Skaut codziennie pobiera tysiące ofert z portali. Żebyś nie musiał
> przeglądać wszystkich, każda oferta dostaje od **0 do 100 punktów** —
> im lepiej pasuje do Ciebie, tym więcej. Do Twojej kolejki w panelu
> trafiają tylko oferty z **co najmniej 60 pkt**.
>
> - **Punkty dodatnie** — za to, czego szukasz: Twoja rola w tytule,
>   Twoje technologie w wymaganiach, praca zdalna, widełki na Twoim
>   poziomie.
> - **Kara punktowa** — odjęcie punktów, gdy coś Ci nie pasuje (np. −20 za
>   ofertę stacjonarną, gdy szukasz tylko zdalnej). Oferta nie znika —
>   spada w rankingu i jeśli zejdzie poniżej 60 pkt, nie trafi do kolejki.
> - **Wykluczenie** — kara tak duża (−100), że oferta z danym elementem
>   nigdy nie trafi do kolejki, niezależnie od reszty.
>
> Przykład: "Senior DevOps Engineer, zdalnie, Kubernetes" → +25 (rola w
> tytule) +15 (Kubernetes) +20 (zdalnie) … = trafia do kolejki.
>
> Z Twoich odpowiedzi (rola, technologie, tryb pracy, miasto, widełki)
> zbuduję Twój **profil wyszukiwania**. W Kroku 3 pokażę Ci dokładną
> tabelę punktów i będziesz mógł ją poprawić.

Przy pytaniach, które wpływają na punktację (tryb pracy, miasto, widełki,
rola, technologie), krótko zaznaczaj to w treści pytania (np. dopisek
"— wpływa na punktację ofert").

### Wywiad

Następnie przeprowadź **comprehensive wywiad**, zadając **wszystkie
pytania — także otwarte — przez narzędzie do pytań wielokrotnego wyboru**
dostępne w Twoim harnessie (Claude Code: `AskUserQuestion`; omp: `ask`;
inne harnessy: odpowiednik), tak żeby przy każdym pytaniu użytkownik
widział gotowe opcje i mógł wybrać albo wpisać własną odpowiedź (pole
"Other"/własna odpowiedź). Nie zadawaj pytań zwykłym tekstem w rozmowie:

- **Pola zamknięte** — 2-4 sensowne opcje: forma współpracy (B2B / UoP /
  oba), tryb pracy (zdalna / hybrydowa / stacjonarna), poziom angielskiego
  (B1 / B2 / C1 / C2), dostępność ("od zaraz" / okres wypowiedzenia).
- **Pola otwarte** (imię i nazwisko, e-mail, telefon, adres, LinkedIn,
  widełki, tekst "o sobie") — też przez to narzędzie. W treści pytania
  napisz, że wartość wpisuje się w polu własnej odpowiedzi ("Other"), a
  jako opcje daj praktyczne skróty, np. "Weź z mojego CV" (odczytasz to z
  pliku w Kroku 2), znana już wartość (np. e-mail konta), "Pomiń" (dla pól
  opcjonalnych, jak data urodzenia), albo gotowe propozycje (widełki:
  2-3 typowe zakresy dla roli; "o sobie": 2-3 wygenerowane warianty
  tekstu w różnym tonie).
- Grupuj pytania tematycznie (do 3-4 na turę), tłumacz przy każdym, po co
  dana informacja jest potrzebna, i pozwól użytkownikowi poprawiać się w
  trakcie. Nie wyrzucaj wszystkiego jednym wielkim formularzem i nie męcz
  12 osobnymi promptami z rzędu.

Kompletna lista pól briefu (wszystkie muszą zostać pokryte):

- dane kontaktowe: imię i nazwisko, e-mail, telefon, adres (miasto
  wystarczy, ale niektóre formularze chcą ulicy i kodu pocztowego),
  opcjonalnie data urodzenia (niektóre polskie formularze o to pytają —
  użytkownik może odmówić, wtedy usuń ten wiersz z pliku zamiast zostawiać
  placeholder),
- link do LinkedIn (jeśli ma) oraz poziom angielskiego i innych języków
  istotnych dla szukanych ofert,
- dostępność (np. "od zaraz", "miesiąc wypowiedzenia"),
- preferowana forma współpracy: B2B, UoP, albo oba — i **którą wybrać, gdy
  formularz wymusza jeden wybór**,
- tryb pracy: wyłącznie zdalna / hybrydowa / stacjonarna — **i wybór
  awaryjny, gdy formularz wymusza jeden wybór** (to ważne pole,
  automatyzacja trzyma się go dosłownie; jeśli użytkownik akceptuje
  hybrydę, zapytaj też o miasto/promień),
- oczekiwania finansowe jako **zakres miesięczny** (np. "16 000–20 000
  PLN/mies.") plus liczba godzin roboczych w miesiącu do przeliczenia na
  stawkę godzinową, jeśli formularz o to zapyta (domyślnie przyjmij ~160h,
  jeśli użytkownik nie poda innej wartości). Wyjaśnij krótko, że reguła 6 w
  skillu `.agents/skills/cvskill/SKILL.md` opisuje jak automatyzacja wybiera
  konkretną liczbę względem widełek oferty — użytkownik nie musi tego teraz
  ustalać co do szczegółu,
- krótka wiadomość na pola typu "napisz coś o sobie" (2-3 zdania, w tonie
  jaki użytkownik lubi).

Po zebraniu odpowiedzi pokaż użytkownikowi **podsumowanie briefu do
akceptacji**, a potem **nadpisz cały plik `data/aboutme.md`** (Edit/Write),
zachowując strukturę nagłówków z obecnego szablonu, ale bez pustych
`[PLACEHOLDER]` — usuń wiersze, których użytkownik świadomie nie chce podać,
zamiast zostawiać je puste. Zamknij krok przypomnieniem: **w Kroku 2
potrzebny będzie plik CV (najlepiej PDF) do odłożenia w `data/`**.

## Krok 2 — CV (→ `data/cv_info.md` + plik PDF w `data/`)

Jeśli nie zrobiłeś tego wyraźnie w Kroku 1, przypomnij teraz wprost:
**CV musi trafić lokalnie do projektu** — treść do `data/cv_info.md`, a
plik PDF do katalogu `data/` (panel załącza go stamtąd przy aplikowaniu).

Zapytaj użytkownika, jak najwygodniej mu dostarczyć treść CV — zaproponuj
opcje:

1. **Ma gotowy plik PDF/DOCX na dysku** — poproś o ścieżkę, skopiuj go do
   `data/` (np. `cp "<ścieżka>" "data/<oryginalna nazwa>.pdf"` przez Bash;
   jeśli to DOCX, powiedz użytkownikowi że najlepiej dostarczyć PDF, bo
   dashboard i formularze ATS oczekują PDF-a). Następnie odczytaj treść
   pliku (narzędzie odczytu plików radzi sobie z PDF) i przepisz ją w
   Markdown do `data/cv_info.md`, zachowując strukturę sekcji z szablonu
   (Professional Summary, Technical Skills, Professional Experience,
   Education, Certifications...).
2. **Woli podyktować/wkleić treść CV na czacie** — zbierz doświadczenie,
   umiejętności, edukację, certyfikaty w rozmowie i zapisz to samo do
   `data/cv_info.md`. W takim wypadku **koniecznie przypomnij**, że będzie
   też potrzebny plik PDF w `data/` do faktycznego załączania w
   formularzach (część platform tego wymaga) — dopytaj czy użytkownik może
   go później wrzucić do `data/` ręcznie, albo eksportować CV z jakiegoś
   kreatora/LinkedIn i podać ścieżkę.

Nie ma znaczenia jak nazywa się plik PDF — `frontend/server.py` sam znajduje
dowolny pojedynczy plik `.pdf` w `data/`. Jeśli w `data/` znajdzie się
więcej niż jeden PDF, ostrzeż użytkownika że dashboard weźmie tylko jeden
(alfabetycznie pierwszy) — poproś o usunięcie/przeniesienie nadmiarowych.

Zapytaj też **jakiej roli/stanowiska i jakich technologii/słów kluczowych**
dotyczy poszukiwanie (np. "DevOps Engineer", "Backend Developer Python") —
przypomnij, że to **rdzeń punktacji ofert** (Krok 3), a do tego jest
potrzebne w Kroku 5 (dopasowanie `data/links.md`) i w Kroku 6 (generowanie
kart NAUKA). Zanotuj to też w `SESSION_STATUS.md` pod "Cel",
żeby kolejne sesje `/skill:cvskill` wiedziały czego szukać bez ponownego
pytania.

## Krok 3 — profil wyszukiwania i punktacja ofert (→ `data/search_profile.json` + `data/salary_policy.json`)

To jest moment, w którym odpowiedzi z kwestionariusza zamieniają się w
**punktację ofert**. Zacznij od wyjaśnienia (krótko, prostym językiem):

> Nocny skaut pobiera tysiące ofert z portali. Każda dostaje **0-100 pkt**
> według Twojego profilu wyszukiwania, a w kolejce w panelu lądują tylko
> oferty z **≥ 60 pkt**. Teraz ułożymy ten profil z tego, co mi
> powiedziałeś — i pokażę Ci go, zanim go zapiszę.

1. **Zaproponuj profil sam**, na podstawie: roli i słów kluczowych (Krok 2),
   umiejętności z `data/cv_info.md`, trybu pracy / miasta / widełek z
   `data/aboutme.md`. Dopytaj (narzędziem pytań wyboru) tylko o to, czego nie
   da się wywnioskować (przed pytaniem przypomnij różnicę między karą
   punktową a wykluczeniem — patrz Krok 1) — przede wszystkim:
   - **czego unikać** — technologie/obszary, których użytkownik nie chce
     (kara punktowa) albo w ogóle nie bierze pod uwagę (wykluczenie),
   - czy **role pokrewne** też go interesują (np. dla DevOps: SRE, Platform,
     Cloud Engineer) — rozszerza to dopasowanie tytułów.
2. **Zbuduj reguły** wg schematu z `data/search_profile.example.json`
   (semantyka pól: docstring `lib/profile.py`):
   - `scoring` — typowo: rola/synonimy w tytule (`where: "title"`, +25),
     kluczowe technologie z CV w wymaganiach (`"musthave"`, +15),
     technologie drugoplanowe gdziekolwiek w treści (`"text"`, +10),
     niechciane technologie w wymaganiach (`"musthave"`, −30), twarde
     wykluczenia (−100). Każda reguła ma czytelny `label` — to on pojawia
     się w panelu przy ofercie ("Kubernetes/Terraform +15").
   - `location` — wyłącznie zdalna: domyślne bonusy + kara dla dużych
     miast bez "remote"; hybryda w mieście X: kara tylko dla miast poza X
     (wpisz je w `onsite_penalty_cities`); stacjonarnie: obniż
     `remote_bonus`/`eu_remote_bonus` (np. 10 / 0).
   - `feeds` — `include_title` (rola + synonimy — tylko takie oferty z
     zagranicznych feedów trafią do bazy), `jobicy_tag` (jeden tag, np.
     `devops`, `python`), `remotive_category` (jedna z: `software-dev`,
     `devops`, `data`, `qa`, `design`, `product`, `marketing`, `sales`,
     `customer-support`, `hr`, `finance-legal`, `writing`, `all-others`).
   - `search_keywords` — 4-8 fraz, którymi skill przeszukuje portale.
   - `data/salary_policy.json` (szablon: `data/salary_policy.example.json`)
     — `default_net_pln` = kwota, którą użytkownik chce domyślnie wpisywać
     (zaproponuj środek zakresu z briefu i potwierdź), `hourly_divisor` =
     liczba godzin z briefu. Ta sama kwota daje ofercie +10 pkt, gdy
     widełki oferty jej sięgają.
3. **Po ostatnim pytaniu budującym profil pokaż podsumowanie profilu**
   (zanim go zatwierdzisz) — w formie **maksymalnie czytelnej wizualnie**:
   Markdown z nagłówkami, tabelami i symbolami, **nigdy surowy JSON**.
   Najpierw zapisz profil roboczo (`data/search_profile.json`) i przepuść
   przez matcher 3-4 przykładowe oferty — jedną idealną, jedną "prawie",
   jedną niechcianą — poleceniem:
   ```
   python3 scout/matcher.py --try "Senior DevOps Engineer" --location "Remote, Poland" --salary 18000-24000
   ```
   Wyniki wstaw do podsumowania (sekcja "Test na przykładach"). Układ
   podsumowania (wartości przykładowe — wstaw prawdziwe z profilu):

   ```markdown
   ## 🎯 Twój profil wyszukiwania

   | | |
   |---|---|
   | 👤 **Rola** | DevOps Engineer (+ SRE, Platform, Cloud) |
   | 🏠 **Tryb pracy** | wyłącznie zdalna |
   | 📄 **Umowa** | B2B lub UoP (przy wymuszonym wyborze: B2B) |
   | 💰 **Widełki** | 16 000–20 000 PLN netto/mies. · domyślnie wpisuję 18 000 |
   | 🗣️ **Angielski** | B2 |
   | 📅 **Dostępność** | od zaraz |
   | 🚦 **Próg kolejki** | **60 / 100 pkt** |

   ### ✅ Za co oferta dostaje punkty
   | Za co | Gdzie szukamy | Punkty |
   |---|---|---:|
   | DevOps / SRE / Platform | tytuł | **+25** |
   | Kubernetes / Terraform | wymagania | **+15** |
   | Praca zdalna | lokalizacja | **+20** |
   | Widełki ≥ 18 000 PLN | pensja | **+10** |

   ### ⚠️ Kary punktowe (oferta spada w rankingu)
   | Za co | Gdzie szukamy | Punkty |
   |---|---|---:|
   | Praca stacjonarna (Warszawa, Kraków…) bez remote | lokalizacja | **−20** |
   | Mainframe / SAP | wymagania | **−30** |

   ### ⛔ Wykluczenia (oferta nigdy nie trafi do kolejki)
   | Za co | Gdzie szukamy | Punkty |
   |---|---|---:|
   | Junior / Intern | tytuł | **−100** |

   ### 🧪 Test na przykładach
   | Oferta | Wynik | Kolejka? |
   |---|---:|:---:|
   | Senior DevOps Engineer · Remote PL · 18–24k | **85** | ✅ |
   | Cloud Engineer · Hybrid Warszawa | **45** | ❌ |
   | Junior SAP Consultant · Kraków | **0** | ❌ |

   ### 🔎 Wyszukiwanie
   - **Frazy na portalach:** `devops`, `sre`, `platform engineer`, …
   - **Feedy zagraniczne:** tylko tytuły z: DevOps, SRE, Platform · Jobicy: `devops` · Remotive: `devops`
   ```

   Zasady: grupuj reguły wg znaku (✅ plusy → ⚠️ kary → ⛔ wykluczenia),
   w każdej grupie sortuj malejąco wg wagi bezwzględnej, punkty
   wyrównuj do prawej i pogrubiaj, pomijaj puste sekcje. Etykiety reguł
   bierz z `label` profilu (to samo użytkownik zobaczy w panelu).

   Jeśli idealna oferta nie przekracza 60 pkt, albo niechciana go
   przekracza — popraw wagi i pokaż podsumowanie ponownie. Następnie
   zapytaj (narzędziem pytań wyboru), czy profil odpowiada temu, czego
   użytkownik szuka (np. "Zatwierdzam" / "Chcę zmienić wagi" / "Chcę
   dodać/usunąć reguły"), i nanieś poprawki.
4. Po akceptacji powiedz wprost, że profil **można zmienić w każdej chwili**
   (poproś agenta o ponowne przejście Kroku 3 albo edytuj
   `data/search_profile.json`), a po zmianie trzeba przeliczyć bazę:
   `python3 scout/matcher.py --db data/cvsender.db --full` — jeśli
   `data/cvsender.db` już istnieje, uruchom to od razu.
5. Od razu po zatwierdzeniu profilu przejdź do Kroku 4 (przewodnik po
   panelu).

## Krok 4 — przewodnik po panelu webowym

Zaraz po zatwierdzeniu podsumowania profilu (Krok 3) przeprowadź
użytkownika przez lokalny panel — tak, żeby wiedział, gdzie zobaczy oferty
wybrane według właśnie ustalonej punktacji i co z nimi robić.

1. **Uruchom panel** w tle wg `JAK_URUCHOMIC.md` (najpierw sprawdź, czy już
   nie działa na porcie 8765) i podaj link **http://127.0.0.1:8765**.
   Jeśli masz narzędzia przeglądarki — otwórz panel w nowej karcie i
   oprowadzaj po nim na żywo (klikaj kolejne zakładki, rób zrzuty ekranu);
   jeśli nie — poproś użytkownika, żeby otworzył link sam.
2. **Uprzedź, że panel jest na razie pusty** — baza `data/cvsender.db`
   startuje bez ofert i wypełni się po pierwszym przebiegu skauta /
   `/skill:cvskill`. Pokazujesz *gdzie* co się pojawi, nie gotowe dane.
3. **Oprowadź zakładka po zakładce** — każda w 2-3 zdaniach, prostym
   językiem, z odniesieniem do profilu z Kroku 3:

   | Zakładka | Co tu jest | Co tu robisz |
   |---|---|---|
   | **Oferty dla Ciebie** | Oferty z ≥ 60 pkt, jeszcze aktualne, czekające na Twoją decyzję. Na karcie: dopasowanie (np. 85/100), portal, widełki, „ważna do" i wszystkie powody punktacji (etykiety reguł z Twojego profilu). Niżej sekcja **Czekają na wysłanie** — oferty, które wybrałeś. | ✓ Chcę aplikować · ⏳ Później · ✕ Nie interesuje mnie; ↩ Cofnij w „Czekają na wysłanie". „Zobacz wszystkie zebrane oferty →" = wszystkie oferty z filtrami, także < 60 pkt (szare). |
   | **Wymaga uwagi** | Aplikacje, przy których asystent utknął (konto, logowanie, CAPTCHA, błąd formularza), i firmy milczące > 7 dni. | Dokończ ręcznie, „Spróbuj ponownie" albo „Rezygnuję"; przy milczeniu — „Zamknij temat". Przycisk Gmail szuka maili z linkiem potwierdzającym. |
   | **Moje aplikacje** | Wszystkie wysłane CV i ich etap (Wysłana → Potwierdzona → Rozmowa wstępna → Rozmowa → Oferta pracy, albo Odrzucona / Zamknięta). | Klik w etap filtruje listę; „✎ Zmień etap / notatki" — gdy firma się odezwie. |
   | **Odłożone** | Oferty z decyzją „Później" albo „Nie interesuje mnie". | ↩ Przywróć, jeśli zmienisz zdanie. |
   | **Portale** | Strony, które przegląda asystent (`data/links.md`): link wyszukiwania, status po ostatniej wizycie, notatki. | Podgląd; zmiany — w Kroku 5 albo edycją `data/links.md`. |
   | **Nauka** | Karty powtórkowe z technologii z Twojego CV i ofert (powstaną w Kroku 6). | Teoria + pytania rekrutacyjne przed rozmową. |
   | **❔ Jak to działa** | Cały proces w 4 krokach, skąd się biorą punkty, słowniczek. | Tu odsyłaj użytkownika, gdy się zgubi. |

   Pokaż też nagłówek: licznik „zebrane oferty", znacznik „odświeża się
   samo" (co 15 s) i przycisk „↻ Odśwież". Przy pustej bazie zakładka
   „Oferty dla Ciebie" pokazuje powitanie z opisem procesu i pierwszym
   krokiem — zacznij od niego.
4. **Zamknij przewodnik pytaniem** (narzędziem pytań wyboru), np.
   "Wszystko jasne — dalej" / "Pokaż jeszcze raz zakładkę …" / "Mam
   pytanie". Odpowiedz na wątpliwości i przejdź do Kroku 5.

## Krok 5 — platformy z ofertami (→ `data/links.md`)

`data/links.md` zawiera gotowy zestaw platform pod **polski rynek pracy**
i słowo kluczowe `devops` w URL-ach, ze statusem `Nietestowany` (nikt jeszcze
tego nie sprawdzał w tej instancji).

- Słowa kluczowe bierz z `search_keywords` profilu z Kroku 3.
- Jeśli użytkownik szuka pracy **w Polsce**, ale w innej roli niż DevOps:
  podmień `keyword=devops` (i podobne parametry) na jego słowo kluczowe w
  każdym URL-u tabeli — zrób to automatycznie, nie pytaj o każdy URL osobno.
- Jeśli użytkownik szuka pracy **poza Polską** albo chce dodać inne rynki:
  zostaw polskie platformy jeśli mogą się przydać (LinkedIn/We Work
  Remotely/RemoteOK są międzynarodowe), a dla lokalnych portali spróbuj
  najpierw sam znaleźć trafne propozycje (wyszukiwanie w sieci) zamiast od
  razu pytać użytkownika — dopisz je jako nowe wiersze tabeli (Platforma /
  URL / Status=Nietestowany / Notatki puste) i pokaż użytkownikowi co
  dodałeś do akceptacji/poprawki.
- Nie zgaduj URL-i platform, których nie znasz z pewnością — jeśli
  wyszukiwanie w sieci nie daje pewnego adresu wyszukiwarki ofert danej
  platformy, zapytaj użytkownika o link albo zostaw to jemu do uzupełnienia
  później, zamiast wpisywać zmyślony URL.
- Po zmianach pokaż użytkownikowi wynik w zakładce **Portale** panelu
  (czyta `data/links.md` na żywo — wystarczy „Odśwież").

## Krok 6 — karty NAUKA (→ `data/learning/*.json`)

`data/learning/` zaczyna **puste** (poza `.gitkeep`) — zakładka Nauka w
panelu będzie pusta, dopóki nie wykonasz tego kroku. Powiedz to użytkownikowi
wprost na początku tego kroku, żeby wiedział czego się spodziewać, i że
karty dopasujesz do jego CV i realnych ofert, a nie do gotowej, uniwersalnej
listy technologii.

1. **Zbierz próbkę realnych ofert.** Jeśli narzędzia przeglądarki są dostępne
   (patrz Krok 0), przejrzyj 5-10 aktualnych ofert dla roli/słów kluczowych
   ustalonych w Kroku 2 na 1-2 platformach z `data/links.md` (samo
   przeglądanie, jeszcze nie aplikowanie — to nie jest jeszcze pełny
   przebieg skilla). Jeśli przeglądarka nie jest dostępna, użyj wyszukiwania
   w sieci, żeby znaleźć kilka aktualnych ogłoszeń dla tej roli i wyciągnąć
   z nich wymagania technologiczne.
2. **Wybierz technologie do kart** — przetnij zbiór technologii/narzędzi
   pojawiających się najczęściej w zebranych ofertach ze zbiorem umiejętności
   z `data/cv_info.md`. Wybierz ok. 8-15 pozycji: priorytetowo te, które są
   i w CV użytkownika, i często wymagane w ofertach (na tym najbardziej mu
   zależy do powtórki przed rozmową); dorzuć kilka częstych w ofertach, ale
   nowszych dla użytkownika, jeśli CV sugeruje że są "w trakcie nauki".
3. **Wygeneruj kartę dla każdej wybranej technologii** jako
   `data/learning/<slug>.json` wg schematu:
   ```json
   {
     "slug": "kubernetes",
     "name": "Kubernetes",
     "tagline": "krótki podtytuł",
     "sections": [
       {"title": "Nazwa sekcji teorii", "body": "tekst, może zawierać **pogrubienie** i listy `- linia`"}
     ],
     "questions": [
       {"q": "Pytanie rekrutacyjne", "a": "Odpowiedź, ten sam prosty markdown"}
     ]
   }
   ```
   Cel: 7-10 sekcji teorii i 15-20 pytań rekrutacyjnych na kartę, pisane
   zrozumiale zarówno dla technika, jak i dla laika. Jeśli masz dostęp do
   subagentów — rozdziel technologie między kilka równoległych agentów
   robiących research (wyszukiwanie/odczyt stron) i piszących swoje karty
   niezależnie, to znacznie przyspiesza ten krok przy 8+ technologiach.
4. Poinformuj użytkownika, kiedy karty są gotowe i że są widoczne w zakładce
   Nauka panelu (uruchomionego w Kroku 4). Ten krok może zająć kilka minut przy większej
   liczbie technologii — możesz uprzedzić o tym użytkownika i kontynuować w
   tle, jeśli narzędzia na to pozwalają.

## Krok 7 — podsumowanie

Na koniec:
- Potwierdź, co zostało zapisane (krótkie podsumowanie, nie odczytuj
  całych plików na głos) — w tym ile kart NAUKA powstało i dla jakich
  technologii, oraz 2-3 zdania o profilu punktacji (za co oferta dostaje
  najwięcej punktów, czego unikamy).
- Przypomnij, że log i kolejka w `data/cvsender.db` (tabele `applications`
  i `offers`) startują puste — to oczekiwane, wypełnią się w miarę
  działania `/skill:cvskill`.
- Jeśli w Kroku 0 harness/przeglądarka nie były gotowe, przypomnij
  dokładnie czego jeszcze brakuje, zanim `/skill:cvskill` będzie mógł
  aplikować.
- Powiedz użytkownikowi, że może teraz uruchomić workflow skilla (omp:
  `/skill:cvskill`, Codex CLI: `$cvskill`, Claude Code: poproś agenta o
  wczytanie `SKILL.md`), żeby zacząć pierwsze wyszukiwanie i aplikowanie
  na oferty.
- Zaproponuj usunięcie tego pliku (`SETUP.md`) albo zostawienie go — obie
  opcje są ok, plik nie jest już potrzebny do działania po konfiguracji, ale
  nie przeszkadza jeśli zostanie (np. przyda się, gdy użytkownik zechce
  zresetować dane od zera albo dogenerować karty NAUKA dla nowej roli).
