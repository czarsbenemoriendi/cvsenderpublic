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

## Krok 0 — wymagane narzędzia i sprawdzenie punktu startowego

1. **Harness + sterowanie przeglądarką.** Nie wymagamy żadnego konkretnego
   narzędzia — **pracuj w harnessie, w którym już jest użytkownik** (np.
   Claude Code, omp, Codex CLI, OpenCode). Automatyczne przeglądanie ofert
   i wypełnianie formularzy (workflow skilla
   `.agents/skills/cvskill/SKILL.md`) wymaga:
   - **agenta wspierającego Agent Skills** — skill jest już w repo pod
     `.agents/skills/cvskill/`; wywołaj go w sposób naturalny dla harnessu
     (omp: `/skill:cvskill`, Codex CLI: `$cvskill`) albo wczytaj `SKILL.md`
     bezpośrednio ze ścieżki (np. Claude Code),
   - **sterowania przeglądarką** dopasowanego do harnessu: Claude Code —
     rozszerzenie "Claude in Chrome" albo Playwright MCP (najlepiej tryb
     `--extension` na prawdziwym Chrome); omp — narzędzie `browser` w trybie
     **OMP Browser Relay** (jednorazowo `omp browser-relay install` +
     włączenie rozszerzenia "OMP Browser Relay" w Chrome, najlepiej w
     dedykowanym profilu, np. `CVSender`); pozostałe harnessy — ich natywna
     warstwa przeglądarki albo Playwright MCP. Cel: agent steruje
     prawdziwym, zalogowanym Chrome użytkownika (sesje logowań zostają).
     Awaryjnie: Chrome z `--remote-debugging-port` (CDP) albo headless
     (mniej przydatny — brak sesji logowań).
   Sprawdź automatycznie, czy narzędzia przeglądarki są już dostępne w tej
   sesji (szybki test — otwórz stronę i odczytaj jej strukturę).
   - Jeśli są dostępne — świetnie, nic więcej nie trzeba robić, powiedz to
     użytkownikowi krótko i przejdź dalej.
   - Jeśli ich nie ma — wypisz użytkownikowi kroki instalacji **dla jego
     harnessu** (Claude Code: rozszerzenie "Claude in Chrome"; omp:
     `omp browser-relay install` + włączenie rozszerzenia w Chrome) jako
     coś do zrobienia **poza tą rozmową**, ale **nie przerywaj configu** —
     reszta setupu (dane, CV, profil punktacji, links.md, karty NAUKA) nie wymaga
     przeglądarki i można ją zrobić już teraz. Samo uruchomienie skilla
     (i przegląd ofert w Kroku 5) będzie wymagało dokończenia tych kroków.
2. **Świeży klon — szablony danych.** Repo zawiera tylko szablony
   `data/aboutme.md.template` i `data/cv_info.md.template`. Jeśli istnieją,
   a `data/aboutme.md` / `data/cv_info.md` jeszcze nie — **na samym początku
   zmień ich nazwy, usuwając końcówkę `.template`**
   (`mv data/aboutme.md.template data/aboutme.md`, analogicznie
   `cv_info.md`). Nie kopiuj — po zmianie nazwy pliki `data/aboutme.md` i
   `data/cv_info.md` są **jedynym źródłem prawdy (SSOT)** o danych
   użytkownika: wszystkie kolejne kroki czytają i nadpisują tylko je. Oba
   są w `.gitignore`, więc dane osobowe nie trafią do repozytorium.
3. Odczytaj `data/aboutme.md` i `data/cv_info.md`. Jeśli nie zawierają już
   nawiasów `[PLACEHOLDER]` — konfiguracja najwyraźniej już była zrobiona.
   Zapytaj użytkownika, czy chce ją powtórzyć/zaktualizować, czy tylko
   zmienić coś konkretnego, zamiast przechodzić przez wszystko od nowa.

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
3. **Że odpowiedzi z tego kwestionariusza staną się punktacją ofert.**
   Powiedz to wprost i bez żargonu, np.: *"To, co tu ustalimy (rola,
   technologie, tryb pracy, miasto, widełki), posłuży nie tylko do
   wypełniania formularzy — system zbuduje z tego Twój **profil
   wyszukiwania**: każda znaleziona oferta dostanie 0-100 punktów, a do
   Twojej kolejki trafią tylko te z co najmniej 60 pkt. W Kroku 3 pokażę Ci
   dokładnie, za co oferta dostaje i traci punkty, i będziesz mógł to
   poprawić."* Przy pytaniach, które wpływają na punktację (tryb pracy,
   miasto, widełki, rola, technologie), krótko zaznaczaj to w treści
   pytania (np. dopisek "— wpływa na punktację ofert").

Następnie przeprowadź **comprehensive wywiad — pytanie po pytaniu**,
korzystając z narzędzia do pytań wielokrotnego wyboru dostępnego w Twoim
harnessie (Claude Code: `AskUserQuestion`; omp: `ask`; inne harnessy:
odpowiednik), tak żeby przy każdym pytaniu użytkownik widział gotowe opcje
i mógł wybrać albo wpisać własną odpowiedź:

- **Pola zamknięte** pytaj przez to narzędzie, z 2-4 sensownymi opcjami:
  forma współpracy (B2B / UoP / oba), tryb pracy (zdalna / hybrydowa /
  stacjonarna), poziom angielskiego (B1 / B2 / C1 / C2), dostępność
  ("od zaraz" / okres wypowiedzenia).
- **Pola otwarte** (imię i nazwisko, e-mail, telefon, adres, LinkedIn,
  widełki, tekst "o sobie") zadawaj wprost w rozmowie — jedno pytanie na
  turę.
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
potrzebne w Kroku 4 (dopasowanie `data/links.md`) i w Kroku 5 (generowanie
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
   da się wywnioskować — przede wszystkim:
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
3. **Pokaż użytkownikowi punktację, zanim ją zapiszesz** — jako tabelę, nie
   JSON:

   | Za co | Gdzie szukamy | Punkty |
   |---|---|---|
   | DevOps/SRE/Platform | tytuł | +25 |
   | Kubernetes/Terraform | wymagania | +15 |
   | Praca zdalna | tytuł/lokalizacja | +20 |
   | Mainframe/SAP | wymagania | −30 |
   | ... | | |

   Zapisz profil roboczo (`data/search_profile.json`) i **zademonstruj go
   na 3-4 przykładowych ofertach** — jednej idealnej, jednej "prawie", jednej
   niechcianej — poleceniem:
   ```
   python3 scout/matcher.py --try "Senior DevOps Engineer" --location "Remote, Poland" --salary 18000-24000
   ```
   Wynik pokazuje liczbę punktów, czy oferta trafiłaby do kolejki, i
   rozbicie na reguły. Jeśli idealna oferta nie przekracza 60 pkt, albo
   niechciana go przekracza — popraw wagi i pokaż ponownie. Zapytaj
   użytkownika, czy punktacja odpowiada temu, czego szuka, i nanieś
   poprawki.
4. Po akceptacji powiedz wprost, że profil **można zmienić w każdej chwili**
   (poproś agenta o ponowne przejście Kroku 3 albo edytuj
   `data/search_profile.json`), a po zmianie trzeba przeliczyć bazę:
   `python3 scout/matcher.py --db data/cvsender.db --full` — jeśli
   `data/cvsender.db` już istnieje, uruchom to od razu.

## Krok 4 — platformy z ofertami (→ `data/links.md`)

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

## Krok 5 — karty NAUKA (→ `data/learning/*.json`)

`data/learning/` zaczyna **puste** (poza `.gitkeep`) — zakładka NAUKA w
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
   NAUKA panelu (Krok 6). Ten krok może zająć kilka minut przy większej
   liczbie technologii — możesz uprzedzić o tym użytkownika i kontynuować w
   tle, jeśli narzędzia na to pozwalają.

## Krok 6 — panel lokalny (opcjonalnie od razu)

Zapytaj, czy użytkownik chce od razu uruchomić panel (`JAK_URUCHOMIC.md`) —
jeśli tak, uruchom go w tle zgodnie z instrukcją tam zawartą i podaj link
http://127.0.0.1:8765.

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
